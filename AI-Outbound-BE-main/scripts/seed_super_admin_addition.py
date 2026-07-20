"""
Migration Script: Add nimra.nawab@nuclieos.com as a super_admin

Creates the user if it does not exist yet (role=super_admin), or promotes
the existing user's role to super_admin if it does. Idempotent - safe to
run more than once.

Usage:
    python -m scripts.seed_super_admin_nimra --yes
    python -m scripts.seed_super_admin_nimra --yes --password "SomePassword123!"

If --password is omitted, a random password is generated and printed once
at the end (it is not stored anywhere in the repo).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import secrets

from config.database import get_users_collection
from services.auth_service import get_password_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TARGET_EMAIL = "nimra.nawab@nuclieos.com"
TARGET_NAME = "Nimra Nawab"


def seed_super_admin(password: str, name: str = TARGET_NAME, email: str = TARGET_EMAIL):
    users = get_users_collection()
    existing = users.find_one({"email": email})

    if existing:
        if existing.get("role") == "super_admin":
            logger.info(f"'{email}' is already a super_admin. Nothing to do.")
            return
        users.update_one({"email": email}, {"$set": {"role": "super_admin"}})
        logger.info(f"Promoted existing user '{email}' to super_admin.")
        return

    users.insert_one({
        "name": name,
        "email": email,
        "password": get_password_hash(password),
        "role": "super_admin",
        "businessName": None,
        "api_key": None,
    })
    logger.info(f"Created new super_admin user '{email}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"Add {TARGET_EMAIL} as a super_admin")
    parser.add_argument("--password", default=None, help="Password to set if a new user is created")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    generated_password = None
    password = args.password
    if password is None:
        generated_password = secrets.token_urlsafe(12)
        password = generated_password

    print("\n" + "=" * 60)
    print("SEED SUPER ADMIN")
    print("=" * 60)
    print(f"Email: {TARGET_EMAIL}")
    print(f"Name:  {TARGET_NAME}")
    print("Action: create as super_admin if missing, else promote role")
    print("=" * 60)

    if not args.yes:
        confirm = input("\nProceed? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled.")
            sys.exit(0)

    try:
        seed_super_admin(password=password, name=TARGET_NAME, email=TARGET_EMAIL)
        if generated_password:
            print("\n" + "=" * 60)
            print(f"Generated password (save this now, it will not be shown again):")
            print(f"  {generated_password}")
            print("=" * 60 + "\n")
    except Exception as e:
        logger.error(f"Failed to seed super_admin: {str(e)}")
        sys.exit(1)
