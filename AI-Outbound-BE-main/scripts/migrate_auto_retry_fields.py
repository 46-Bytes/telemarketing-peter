"""
Migration Script: Add Auto-Retry Fields to Existing Prospects

This script adds the new auto-retry fields to all existing prospects in the database.
Run this once after deploying the auto-retry feature.

Usage:
    python -m scripts.migrate_auto_retry_fields
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import get_prospects_collection
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_prospects():
    """
    Add auto-retry fields to all existing prospects that don't have them.
    """
    try:
        collection = get_prospects_collection()
        
        # Count total prospects
        total_prospects = collection.count_documents({})
        logger.info(f"Total prospects in database: {total_prospects}")
        
        # Find prospects missing auto-retry fields
        prospects_to_update = collection.count_documents({
            "$or": [
                {"autoRetryCount": {"$exists": False}},
                {"autoRetryScheduledDate": {"$exists": False}},
                {"autoRetryScheduledTime": {"$exists": False}},
                {"autoRetryAttempts": {"$exists": False}},
                {"autoRetryFailureEmailSent": {"$exists": False}}
            ]
        })
        
        logger.info(f"Prospects needing migration: {prospects_to_update}")
        
        if prospects_to_update == 0:
            logger.info("✅ All prospects already have auto-retry fields. No migration needed.")
            return
        
        # Confirm before proceeding
        print("\n" + "="*60)
        print("MIGRATION CONFIRMATION")
        print("="*60)
        print(f"This will add auto-retry fields to {prospects_to_update} prospects.")
        print("\nFields to be added:")
        print("  - autoRetryCount: 0")
        print("  - autoRetryScheduledDate: null")
        print("  - autoRetryScheduledTime: null")
        print("  - autoRetryAttempts: []")
        print("  - autoRetryFailureEmailSent: false")
        print("="*60)
        
        confirm = input("\nProceed with migration? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            logger.info("Migration cancelled by user.")
            return
        
        logger.info("Starting migration...")
        
        # Update all prospects that don't have the fields
        result = collection.update_many(
            {
                "$or": [
                    {"autoRetryCount": {"$exists": False}},
                    {"autoRetryScheduledDate": {"$exists": False}},
                    {"autoRetryScheduledTime": {"$exists": False}},
                    {"autoRetryAttempts": {"$exists": False}},
                    {"autoRetryFailureEmailSent": {"$exists": False}}
                ]
            },
            {
                "$set": {
                    "autoRetryCount": 0,
                    "autoRetryScheduledDate": None,
                    "autoRetryScheduledTime": None,
                    "autoRetryAttempts": [],
                    "autoRetryFailureEmailSent": False,
                    "updatedAt": {"$date": datetime.utcnow().isoformat() + "Z"}
                }
            }
        )
        
        logger.info(f"✅ Migration completed successfully!")
        logger.info(f"   - Matched: {result.matched_count} prospects")
        logger.info(f"   - Modified: {result.modified_count} prospects")
        
        # Verify migration
        remaining = collection.count_documents({
            "$or": [
                {"autoRetryCount": {"$exists": False}},
                {"autoRetryScheduledDate": {"$exists": False}},
                {"autoRetryScheduledTime": {"$exists": False}},
                {"autoRetryAttempts": {"$exists": False}},
                {"autoRetryFailureEmailSent": {"$exists": False}}
            ]
        })
        
        if remaining == 0:
            logger.info("✅ Verification passed: All prospects now have auto-retry fields.")
        else:
            logger.warning(f"⚠️  {remaining} prospects still missing fields. Please investigate.")
        
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"Total prospects:        {total_prospects}")
        print(f"Prospects updated:      {result.modified_count}")
        print(f"Prospects remaining:    {remaining}")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def verify_migration():
    """
    Verify that all prospects have the required auto-retry fields.
    """
    try:
        collection = get_prospects_collection()
        
        # Sample a few prospects to verify fields
        sample_prospects = list(collection.find({}).limit(5))
        
        print("\n" + "="*60)
        print("SAMPLE PROSPECTS (First 5)")
        print("="*60)
        
        for i, prospect in enumerate(sample_prospects, 1):
            print(f"\nProspect {i}:")
            print(f"  Phone: {prospect.get('phoneNumber', 'N/A')}")
            print(f"  autoRetryCount: {prospect.get('autoRetryCount', 'MISSING')}")
            print(f"  autoRetryScheduledDate: {prospect.get('autoRetryScheduledDate', 'MISSING')}")
            print(f"  autoRetryScheduledTime: {prospect.get('autoRetryScheduledTime', 'MISSING')}")
            print(f"  autoRetryAttempts: {len(prospect.get('autoRetryAttempts', []))} items")
            print(f"  autoRetryFailureEmailSent: {prospect.get('autoRetryFailureEmailSent', 'MISSING')}")
        
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        raise


def rollback_migration():
    """
    Rollback the migration by removing auto-retry fields from all prospects.
    USE WITH CAUTION - This will remove all auto-retry data!
    """
    try:
        collection = get_prospects_collection()
        
        print("\n" + "="*60)
        print("⚠️  WARNING: ROLLBACK MIGRATION")
        print("="*60)
        print("This will REMOVE auto-retry fields from ALL prospects!")
        print("All scheduled retries and attempt history will be LOST!")
        print("="*60)
        
        confirm = input("\nAre you ABSOLUTELY SURE you want to rollback? (type 'ROLLBACK' to confirm): ").strip()
        
        if confirm != "ROLLBACK":
            logger.info("Rollback cancelled.")
            return
        
        logger.info("Starting rollback...")
        
        result = collection.update_many(
            {},
            {
                "$unset": {
                    "autoRetryCount": "",
                    "autoRetryScheduledDate": "",
                    "autoRetryScheduledTime": "",
                    "autoRetryAttempts": "",
                    "autoRetryFailureEmailSent": "",
                    "autoRetryFailureEmailSentAt": ""
                },
                "$set": {
                    "updatedAt": {"$date": datetime.utcnow().isoformat() + "Z"}
                }
            }
        )
        
        logger.info(f"✅ Rollback completed!")
        logger.info(f"   - Modified: {result.modified_count} prospects")
        
    except Exception as e:
        logger.error(f"Error during rollback: {str(e)}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate auto-retry fields to prospects")
    parser.add_argument(
        "--action",
        choices=["migrate", "verify", "rollback"],
        default="migrate",
        help="Action to perform (default: migrate)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.action == "migrate":
            migrate_prospects()
            verify_migration()
        elif args.action == "verify":
            verify_migration()
        elif args.action == "rollback":
            rollback_migration()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)


