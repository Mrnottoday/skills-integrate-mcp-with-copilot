"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
import os
from pathlib import Path

try:
    from .storage import (
        load_data,
        save_data,
        make_user_id,
        make_slug_id,
        now_iso,
    )
except ImportError:
    from storage import (
        load_data,
        save_data,
        make_user_id,
        make_slug_id,
        now_iso,
    )

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

database = load_data()


class UserCreate(BaseModel):
    email: str
    name: str | None = None
    grade_level: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    grade_level: str | None = None


class ClubCreate(BaseModel):
    name: str
    description: str = ""


class ClubUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ActivityCreate(BaseModel):
    name: str
    description: str
    schedule: str
    max_participants: int = Field(gt=0)
    club_id: str


class ActivityUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    schedule: str | None = None
    max_participants: int | None = Field(default=None, gt=0)
    club_id: str | None = None


def persist() -> None:
    save_data(database)


def get_activity_by_name(activity_name: str):
    for activity in database["activities"]:
        if activity["name"] == activity_name:
            return activity
    return None


def get_activity_by_id(activity_id: str):
    for activity in database["activities"]:
        if activity["id"] == activity_id:
            return activity
    return None


def get_user_by_id(user_id: str):
    for user in database["users"]:
        if user["id"] == user_id:
            return user
    return None


def get_user_by_email(email: str):
    lowered = email.strip().lower()
    for user in database["users"]:
        if user["email"].lower() == lowered:
            return user
    return None


def get_club_by_id(club_id: str):
    for club in database["clubs"]:
        if club["id"] == club_id:
            return club
    return None


def participants_for_activity(activity_id: str):
    participants = []
    for signup in database["signups"]:
        if signup["activity_id"] == activity_id:
            user = get_user_by_id(signup["user_id"])
            if user:
                participants.append(user["email"])
    return participants


def activity_to_legacy_view(activity: dict):
    return {
        "description": activity["description"],
        "schedule": activity["schedule"],
        "max_participants": activity["max_participants"],
        "participants": participants_for_activity(activity["id"]),
    }


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    response = {}
    for activity in database["activities"]:
        response[activity["name"]] = activity_to_legacy_view(activity)
    return response


@app.get("/activities/entities")
def get_activity_entities():
    return database["activities"]


@app.get("/activities/entities/{activity_id}")
def get_activity_entity(activity_id: str):
    activity = get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@app.post("/activities/entities")
def create_activity(activity: ActivityCreate):
    if not get_club_by_id(activity.club_id):
        raise HTTPException(status_code=404, detail="Club not found")

    for existing in database["activities"]:
        if existing["name"].lower() == activity.name.lower():
            raise HTTPException(status_code=400, detail="Activity name already exists")

    new_activity = {
        "id": make_slug_id("act", activity.name),
        "name": activity.name,
        "description": activity.description,
        "schedule": activity.schedule,
        "max_participants": activity.max_participants,
        "club_id": activity.club_id,
    }
    database["activities"].append(new_activity)
    persist()
    return new_activity


@app.put("/activities/entities/{activity_id}")
def update_activity(activity_id: str, payload: ActivityUpdate):
    activity = get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    updates = payload.model_dump(exclude_none=True)
    if "club_id" in updates and not get_club_by_id(updates["club_id"]):
        raise HTTPException(status_code=404, detail="Club not found")

    if "max_participants" in updates:
        current_signups = len(participants_for_activity(activity_id))
        if updates["max_participants"] < current_signups:
            raise HTTPException(status_code=400, detail="Cannot set max below current signups")

    activity.update(updates)
    persist()
    return activity


@app.delete("/activities/entities/{activity_id}")
def delete_activity(activity_id: str):
    activity = get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    database["activities"] = [a for a in database["activities"] if a["id"] != activity_id]
    database["signups"] = [s for s in database["signups"] if s["activity_id"] != activity_id]
    persist()
    return {"message": f"Deleted activity {activity_id}"}


@app.get("/users")
def get_users():
    return database["users"]


@app.get("/users/{user_id}")
def get_user(user_id: str):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users")
def create_user(user: UserCreate):
    existing = get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = {
        "id": make_user_id(user.email),
        "email": user.email.strip().lower(),
        "name": user.name,
        "grade_level": user.grade_level,
    }
    database["users"].append(new_user)
    persist()
    return new_user


@app.put("/users/{user_id}")
def update_user(user_id: str, payload: UserUpdate):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.update(payload.model_dump(exclude_none=True))
    persist()
    return user


@app.delete("/users/{user_id}")
def delete_user(user_id: str):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    has_signups = any(signup["user_id"] == user_id for signup in database["signups"])
    if has_signups:
        raise HTTPException(status_code=400, detail="Cannot delete user with signups")

    database["users"] = [u for u in database["users"] if u["id"] != user_id]
    persist()
    return {"message": f"Deleted user {user_id}"}


@app.get("/clubs")
def get_clubs():
    return database["clubs"]


@app.get("/clubs/{club_id}")
def get_club(club_id: str):
    club = get_club_by_id(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@app.post("/clubs")
def create_club(club: ClubCreate):
    club_id = make_slug_id("club", club.name)
    if get_club_by_id(club_id):
        raise HTTPException(status_code=400, detail="Club name already exists")

    new_club = {
        "id": club_id,
        "name": club.name,
        "description": club.description,
    }
    database["clubs"].append(new_club)
    persist()
    return new_club


@app.put("/clubs/{club_id}")
def update_club(club_id: str, payload: ClubUpdate):
    club = get_club_by_id(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    club.update(payload.model_dump(exclude_none=True))
    persist()
    return club


@app.delete("/clubs/{club_id}")
def delete_club(club_id: str):
    club = get_club_by_id(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    has_activities = any(activity["club_id"] == club_id for activity in database["activities"])
    if has_activities:
        raise HTTPException(status_code=400, detail="Cannot delete club with activities")

    database["clubs"] = [c for c in database["clubs"] if c["id"] != club_id]
    persist()
    return {"message": f"Deleted club {club_id}"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    activity = get_activity_by_name(activity_name)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    current_participants = participants_for_activity(activity["id"])
    normalized_email = email.strip().lower()

    if len(current_participants) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")

    if normalized_email in current_participants:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    user = get_user_by_email(normalized_email)
    if not user:
        user = {
            "id": make_user_id(normalized_email),
            "email": normalized_email,
            "name": None,
            "grade_level": None,
        }
        database["users"].append(user)

    signup = {
        "id": make_slug_id("signup", f"{activity['id']}-{user['id']}-{now_iso()}"),
        "activity_id": activity["id"],
        "user_id": user["id"],
        "created_at": now_iso(),
    }
    database["signups"].append(signup)
    persist()
    return {"message": f"Signed up {normalized_email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    activity = get_activity_by_name(activity_name)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    normalized_email = email.strip().lower()
    user = get_user_by_email(normalized_email)
    if not user:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    signup = None
    for entry in database["signups"]:
        if entry["activity_id"] == activity["id"] and entry["user_id"] == user["id"]:
            signup = entry
            break

    if not signup:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    database["signups"].remove(signup)
    persist()
    return {"message": f"Unregistered {normalized_email} from {activity_name}"}
