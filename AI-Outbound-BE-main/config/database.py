# PyMongo - MongoDB Atlas connection setup
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
ATLAS_URI = os.getenv("MONGO_DB_URL")

try:
    client = MongoClient(ATLAS_URI)
    
    # Test the connection
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB!")
    
    db = client["sales_agent_db"]
    prospects_collection = db["prospects"]
    users_collection = db["users"]
    campaign_collection = db["campaigns"]
    campaign_users_collection = db["campaign_users"]

    # # Create unique index on phoneNumber
    # prospects_collection.create_index("phoneNumber", unique=True)
    users_collection.create_index("email", unique=True)
    campaign_collection.create_index("campaignName", unique=True)
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {str(e)}")
    raise

def get_database():
    return db

def get_prospects_collection():
    return prospects_collection

def get_users_collection():
    return users_collection

def get_campaigns_collection():
    return campaign_collection

def get_campaign_users_collection():
    return campaign_users_collection