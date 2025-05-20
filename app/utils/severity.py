# app/utils/severity.py

# Mapping numeric severity to label
SEVERITY_LABELS = {
    0: "Informational",
    1: "Low",
    2: "Low",
    3: "Low",
    4: "Low",
    5: "Low",
    6: "Low",
    7: "Medium",
    8: "Medium",
    9: "Medium",
    10: "Medium",
    11: "Medium",
    12: "High",
    13: "High",
    14: "High",
    15: "Critical"
}

# Optional: Support reverse lookup for filtering (e.g. in views)
SEVERITY_MAP = {
    "Informational": [0],
    "Low": [1, 2, 3, 4, 5, 6],
    "Medium": [7, 8, 9, 10, 11],
    "High": [12, 13, 14],
    "Critical": [15]
}

# Tactical color classes for frontend
SEVERITY_CSS_CLASSES = {
    "Informational": "severity-informational",
    "Low": "severity-low",
    "Medium": "severity-medium",
    "High": "severity-high",
    "Critical": "severity-critical",
    "Unknown": "severity-unknown"
}
