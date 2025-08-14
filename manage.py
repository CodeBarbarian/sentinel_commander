import os
import json
import sys
from pathlib import Path
import typer
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from alembic import command
from alembic.config import Config

from app.core.database import SessionLocal, engine
from app.models.user import User

app = typer.Typer(help="Sentinel Commander management CLI")

def _alembic_cfg() -> Config:
    return Config("alembic.ini")

def _env(var: str, default: str | None = None) -> str | None:
    v = os.environ.get(var, default)
    if v is None:
        raise RuntimeError(f"Missing required env var: {var}")
    return v

def _load_env():
    load_dotenv(dotenv_path=Path(".env"))

@app.command()
def doctor() -> None:
    """Run environment and connectivity checks."""
    _load_env()
    print("== Sentinel Commander Doctor ==")
    print(f"- APP_ENV: {os.getenv('APP_ENV')}")
    print(f"- DATABASE_URL: {os.getenv('DATABASE_URL')!r}")

    # DB connectivity check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection OK.")
    except OperationalError as e:
        print("Database connection FAILED:")
        print(f"  {e}")
        raise typer.Exit(code=1)

    # Alembic head/current check
    try:
        command.current(_alembic_cfg(), verbose=False)
        print("Alembic reachable.")
    except Exception as e:
        print("Alembic error:")
        print(f"  {e}")
        raise typer.Exit(code=1)

    # required dirs
    required_dirs = ["app/resources", "app/uploads", "app/tmp"]
    missing = []
    for d in required_dirs:
        p = Path(d)
        if not p.exists():
            missing.append(d)
    if missing:
        print(f"Creating required dirs: {', '.join(missing)}")
        for d in missing:
            Path(d).mkdir(parents=True, exist_ok=True)
    print("Filesystem OK.")


@app.command()
def migrate() -> None:
    """Apply Alembic migrations."""
    _load_env()
    command.upgrade(_alembic_cfg(), "head")
    print("Migrations applied (head).")


@app.command()
def secret(length: int = typer.Option(48, help="Secret length")) -> None:
    """Generate a secure secret for SECRET_KEY."""
    import secrets, string
    alphabet = string.ascii_letters + string.digits + "-_"
    key = "".join(secrets.choice(alphabet) for _ in range(length))
    print(key)


@app.command()
def create_admin(
        username: str = typer.Option(None, help="Admin username (default: ADMIN_USERNAME in .env or 'admin')"),
        password: str = typer.Option(None, help="Admin password (default: ADMIN_PASSWORD in .env or 'admin')"),
) -> None:
    """Create a default admin user if missing."""
    _load_env()
    from passlib.hash import bcrypt

    username = username or os.getenv("ADMIN_USERNAME", "admin")
    password = password or os.getenv("ADMIN_PASSWORD", "admin")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"User '{username}' already exists. Skipping.")
            return
        user = User(username=username, password_hash=bcrypt.hash(password), is_admin=True, is_active=True)
        db.add(user)
        db.commit()
        print(f"Created admin user '{username}'.")
    finally:
        db.close()


@app.command()
def seed_demo() -> None:
    """Insert example/demo data useful for first-run screenshots and UI."""
    _load_env()
    db = SessionLocal()
    try:
        # Example: a couple of alerts, a source, etc. Adjust to your models.
        from app.models.source import Source  # if you have one
        from app.models.alert import Alert

        if not db.query(Source).first():
            db.add(Source(name="Wazuh", display_name="Wazuh Manager", is_active=True))
            db.add(Source(name="Suricata", display_name="Suricata NIDS", is_active=True))
            db.commit()
            print("Seeded sources.")

        if not db.query(Alert).first():
            from datetime import datetime
            db.add_all([
                Alert(
                    message="Suspicious login attempt",
                    severity=8,
                    status="new",
                    created_at=datetime.utcnow(),
                    source_payload=json.dumps({"event": "auth_failed", "ip": "203.0.113.10"}),
                ),
                Alert(
                    message="Outbound connection to known bad IP",
                    severity=10,
                    status="in_progress",
                    created_at=datetime.utcnow(),
                    source_payload=json.dumps({"dst_ip": "198.51.100.77", "proto": "tcp", "port": 4444}),
                ),
            ])
            db.commit()
            print("Seeded demo alerts.")
    finally:
        db.close()


@app.command()
def bootstrap(
        create_db: bool = typer.Option(True, help="Create DB if not exists (Postgres)"),
        seed_admin: bool = typer.Option(True, help="Seed default admin"),
        demo: bool = typer.Option(False, help="Seed demo data"),
) -> None:
    """End-to-end first-run setup."""
    _load_env()
    url = os.getenv("DATABASE_URL", "")
    if create_db and url.startswith("postgres"):
        try:
            from urllib.parse import urlparse
            import psycopg2
            parsed = urlparse(url)
            target_db = parsed.path.lstrip("/")
            admin_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/postgres"
            with psycopg2.connect(admin_url) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
                    if not cur.fetchone():
                        cur.execute(f'CREATE DATABASE "{target_db}"')
                        print(f"✔ Created database '{target_db}'.")
        except Exception as e:
            print(f"Skipping DB create (maybe exists): {e}")

    # Ensure basic dirs
    for d in ["app/resources", "app/uploads", "app/tmp"]:
        Path(d).mkdir(parents=True, exist_ok=True)

    migrate()

    if seed_admin:
        create_admin()

    if demo:
        seed_demo()

    print("Bootstrap complete.")


@app.command()
def reset_db(confirm: bool = typer.Option(False, help="Set true to drop and recreate all tables (DANGEROUS)")) -> None:
    """Drop all tables & re-run migrations (use only in dev!)."""
    if not confirm:
        print("Refusing to reset DB without --confirm.")
        raise typer.Exit(code=1)
    _load_env()
    # Hard reset: drop all – safe only in dev!
    from sqlalchemy import inspect, MetaData
    meta = MetaData()
    meta.reflect(bind=engine)
    meta.drop_all(bind=engine)
    print("Dropped all tables.")
    migrate()
    print("Recreated schema.")
