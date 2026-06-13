"""Create an API user and print the generated API key.

Usage:
    python scripts/create_user.py [free|paid] [email]

Example:
    python scripts/create_user.py paid alice@example.com
"""
import secrets
import sys
import uuid

sys.path.insert(0, ".")

from app.models.db import SessionLocal, init_db
from app.models.user import User


def create_user(tier: str = "free", email: str | None = None) -> None:
    init_db()
    api_key = f"sk-{secrets.token_hex(16)}"
    user = User(id=str(uuid.uuid4()), api_key=api_key, tier=tier, email=email)
    db = SessionLocal()
    try:
        db.add(user)
        db.commit()
        print(f"Created {tier} user")
        print(f"API Key: {api_key}")
        if email:
            print(f"Email:   {email}")
    finally:
        db.close()


if __name__ == "__main__":
    tier = sys.argv[1] if len(sys.argv) > 1 else "free"
    email = sys.argv[2] if len(sys.argv) > 2 else None
    create_user(tier, email)
