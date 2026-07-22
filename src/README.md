# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Persistent JSON storage in `src/data/db.json`
- Stable IDs for users, clubs, and activities
- CRUD APIs for core entities
- Seed script for local reset and migration from legacy in-memory data

## Getting Started

1. Install the dependencies:

   ```
   pip install -r ../requirements.txt
   ```

2. Run the application:

   ```
   uvicorn app:app --reload
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | Backward-compatible activities view used by frontend |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister from an activity |
| GET | `/users` | List users |
| POST | `/users` | Create user |
| PUT | `/users/{user_id}` | Update user |
| DELETE | `/users/{user_id}` | Delete user without signups |
| GET | `/clubs` | List clubs |
| POST | `/clubs` | Create club |
| PUT | `/clubs/{club_id}` | Update club |
| DELETE | `/clubs/{club_id}` | Delete club without activities |
| GET | `/activities/entities` | List normalized activity entities |
| POST | `/activities/entities` | Create activity |
| PUT | `/activities/entities/{activity_id}` | Update activity |
| DELETE | `/activities/entities/{activity_id}` | Delete activity and its signups |

## Seed and Migration

The backend now auto-creates `data/db.json` on first run using the legacy activity data from the original in-memory dataset.

To reset local data at any time:

```
python scripts/seed_data.py
```

## Data Model

The application uses a normalized data model with stable identifiers:

1. **Users** (id, email, name, grade_level)
2. **Clubs** (id, name, description)
3. **Activities** (id, club_id, name, description, schedule, max_participants)
4. **Signups** (id, user_id, activity_id, created_at)
5. Placeholder collections for upcoming workflows:
   - memberships
   - join_requests
   - leave_requests
   - activity_approvals
   - announcements
   - finance_entries

All data is stored in `data/db.json`, so records persist across server restarts.
