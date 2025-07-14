"""
One-time data migration: SQLite -> Postgres
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from app.core.database import Base  # same Base for both!

# Import all models
from app.models.alert import Alert
from app.models.alert_enrichment import AlertEnrichment
from app.models.customer import Customer
from app.models.customer_detail import CustomerDetail
from app.models.module import Module
from app.models.publisher import PublisherList, PublisherEntry
from app.models.saved_search import SavedSearch
from app.models.source import Source
from app.models.user import User

# -------------------------------
# 1) Connect to SQLite
# -------------------------------
sqlite_engine = create_engine("sqlite:///./sentinel.db")
postgres_engine = create_engine("postgresql+psycopg2://sentinel_user:sentinel_pass@localhost:5432/sentinel_db")

# Use sessionmaker
SQLiteSession = sessionmaker(bind=sqlite_engine)
PostgresSession = sessionmaker(bind=postgres_engine)

sqlite_sess = SQLiteSession()
postgres_sess = PostgresSession()

# -------------------------------
# 3) Do the migration
# -------------------------------
def migrate_table(Model):
    print(f"Migrating: {Model.__tablename__}")

    sqlite_objs = sqlite_sess.query(Model).all()

    for obj in sqlite_objs:
        postgres_sess.merge(obj)  # merge ensures no dup PK conflicts

    postgres_sess.commit()
    print(f"Done: {Model.__tablename__}")

# -------------------------------
# 4) Run it in safe FK order!
# -------------------------------
if __name__ == "__main__":
    sqlite_sess = SQLiteSession()
    postgres_sess = PostgresSession()

    try:
        # FK parents first!
        migrate_table(Customer)
        migrate_table(CustomerDetail)
        migrate_table(Source)
        migrate_table(User)
        migrate_table(Alert)
        migrate_table(AlertEnrichment)

        migrate_table(Module)
        migrate_table(PublisherList)
        migrate_table(PublisherEntry)
        migrate_table(SavedSearch)
        # Add other tables here in FK-safe order!

    finally:
        sqlite_sess.close()
        postgres_sess.close()

    print("Migration complete.")
