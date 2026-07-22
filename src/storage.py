"""Persistence utilities for the Mergington High School API."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "db.json"

LEGACY_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_slug_id(prefix: str, raw_value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", raw_value.lower()).strip("-")
    slug = slug or "item"
    return f"{prefix}_{slug}"


def make_user_id(email: str) -> str:
    return make_slug_id("usr", email.strip().lower())


def _seed_database() -> dict:
    users_by_email = {}
    activities = []
    signups = []

    for name, details in LEGACY_ACTIVITIES.items():
        activity_id = make_slug_id("act", name)
        activities.append(
            {
                "id": activity_id,
                "name": name,
                "description": details["description"],
                "schedule": details["schedule"],
                "max_participants": details["max_participants"],
                "club_id": "club_general",
            }
        )

        for email in details["participants"]:
            normalized_email = email.strip().lower()
            if normalized_email not in users_by_email:
                users_by_email[normalized_email] = {
                    "id": make_user_id(normalized_email),
                    "email": normalized_email,
                    "name": None,
                    "grade_level": None,
                }

            signups.append(
                {
                    "id": make_slug_id("signup", f"{activity_id}-{normalized_email}"),
                    "activity_id": activity_id,
                    "user_id": users_by_email[normalized_email]["id"],
                    "created_at": now_iso(),
                }
            )

    return {
        "users": list(users_by_email.values()),
        "clubs": [
            {
                "id": "club_general",
                "name": "General Activities",
                "description": "Default club for initial activities",
            }
        ],
        "activities": activities,
        "memberships": [],
        "join_requests": [],
        "leave_requests": [],
        "activity_approvals": [],
        "announcements": [],
        "finance_entries": [],
        "signups": signups,
    }


def save_data(database: dict, db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text(json.dumps(database, indent=2), encoding="utf-8")


def load_data(db_path: Path = DB_PATH) -> dict:
    if not db_path.exists():
        database = _seed_database()
        save_data(database, db_path)
        return database

    with db_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def seed_data(db_path: Path = DB_PATH) -> Path:
    database = _seed_database()
    save_data(database, db_path)
    return db_path
