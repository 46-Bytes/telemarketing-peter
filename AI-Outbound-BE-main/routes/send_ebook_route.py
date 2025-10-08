import os
from fastapi import APIRouter, HTTPException, Request
from services.send_ebook_service import send_ebook_email
import logging
from bson import ObjectId
from pymongo.errors import PyMongoError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/send")
async def send_ebook(request: Request):
    try:
        data = await request.json()
        email = data["args"]["email"]
        campaign_id = data["args"]["campaign_id"]
        # name = data["args"]["user_name"]
        # Get owner name if provided
        #owner_name = data["args"].get("owner_name", None)
        
        logger.info(f"Received request to send ebook to: {email}")
        #logger.info(f"Owner name: {owner_name}")
        logger.info(f"Campaign ID: {campaign_id}")
        
        # Retrieve ebook path from database
        from config.database import get_users_collection, get_campaign_users_collection
        users = get_users_collection()
        
        campaign_users = get_campaign_users_collection()
        
        #if owner_name:
        #    user = users.find_one({"name": owner_name})
        #    logger.info(f"Looked up user by name: {owner_name}")
        #    logger.info(f"User found: {user}")
        
        if campaign_id:
            campaign_user = campaign_users.find_one({"_id": ObjectId(campaign_id)})
            logger.info(f"Looked up campaign by ID: {campaign_id}")
            logger.info(f"Campaign found: {campaign_user}")
        
        ebook_path = None
        
        # First check if user has an ebook path
        if campaign_user and "ebook_path" in campaign_user and campaign_user["ebook_path"]:
            ebook_path = campaign_user["ebook_path"]
            logger.info(f"Found ebook path in campaign: {ebook_path}")
            
            # If the ebook path is a Cloudinary URL, use it directly
            if ebook_path.startswith("http"):
                ebook_url = ebook_path
                logger.info(f"Using Cloudinary URL: {ebook_url}")
            else:
                # For backward compatibility with old paths
                # Convert relative path to absolute URL if needed
                base_url = request.base_url
                if ebook_path.startswith("public/"):
                    ebook_url = f"{base_url}{ebook_path[7:]}"  # Remove "public/" prefix
                else:
                    ebook_url = f"{base_url}{ebook_path}"
                    
                logger.info(f"Using converted URL: {ebook_url}")
            
            # Send the email with the ebook
            send_ebook_email(email, ebook_url)
            return {"message": "Email sent successfully", "ebook_path": ebook_path}
        else:
            # Fallback to default PDF if user or ebook path not found
            logger.warning(f"Ebook path not found for user. Using default PDF.")
            default_pdf = os.getenv("DEFAULT_PDF_URL")
            send_ebook_email(email, default_pdf)
            return {"message": "Email sent with default PDF", "ebook_path": default_pdf}
            
    except PyMongoError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Error sending ebook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
