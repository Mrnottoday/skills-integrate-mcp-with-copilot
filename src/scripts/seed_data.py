"""Seed or reset local JSON data for development."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage import seed_data  # noqa: E402


if __name__ == "__main__":
    path = seed_data()
    print(f"Seeded data at {path}")
