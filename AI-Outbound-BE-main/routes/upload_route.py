from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from services.auth_service import get_current_user
from services.campaign_service import update_campaign_ebook
from models.user import User
import os
import shutil
from pathlib import Path
from typing import Optional
from config.cloudinary_config import upload_file_to_cloudinary, configure_cloudinary
from config.database import get_campaign_users_collection
import tempfile
import logging
import time
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload/ebook")
async def upload_ebook(
    file: UploadFile = File(...),
    campaign_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a PDF ebook file to Cloudinary
    """
    try:
        # Validate file type
        if not file.content_type == "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed"
            )

        # Check if campaign exists in campaign_users collection first
        if campaign_id:
            campaign_users_collection = get_campaign_users_collection()
            campaign = campaign_users_collection.find_one({"_id": ObjectId(campaign_id)})
            if not campaign:
                raise HTTPException(
                    status_code=404,
                    detail=f"Campaign with ID {campaign_id} not found"
                )

        # Check if Cloudinary is configured
        cloudinary_configured = configure_cloudinary()
        
        if cloudinary_configured:
            # Use Cloudinary for file storage
            logger.info("Using Cloudinary for file storage")
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                # Copy uploaded file to the temporary file
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name

            try:
                # Generate unique public_id for Cloudinary
                public_id = None
                if campaign_id:
                    public_id = f"campaign_{campaign_id}"
                else:
                    # Add timestamp to make the filename unique
                    timestamp = int(time.time())
                    user_id = str(current_user.id) if hasattr(current_user, 'id') else str(current_user._id)
                    public_id = f"user_{user_id}_{timestamp}"

                # Upload to Cloudinary
                logger.info(f"Uploading file to Cloudinary with public_id: {public_id}")
                cloudinary_response = upload_file_to_cloudinary(
                    tmp_path, 
                    public_id=public_id,
                    folder="ebooks"
                )
                
                # Get the secure URL from Cloudinary
                cloudinary_url = cloudinary_response['secure_url']
                logger.info(f"File uploaded to Cloudinary: {cloudinary_url}")

                # Update campaign with ebook information if campaign_id is provided
                if campaign_id:
                    # Update in campaign_users collection directly
                    campaign_users_collection = get_campaign_users_collection()
                    result = campaign_users_collection.update_one(
                        {"_id": ObjectId(campaign_id)},
                        {
                            "$set": {
                                "has_ebook": True,
                                "ebook_path": cloudinary_url,
                                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                            }
                        }
                    )
                    if result.modified_count == 0:
                        logger.warning(f"No documents updated for campaign {campaign_id}")

                # Return response in the format expected by the frontend
                return {
                    "path": cloudinary_url
                }
            finally:
                # Clean up the temporary file
                os.unlink(tmp_path)
        else:
            # Fallback to local file storage
            logger.warning("Cloudinary not configured, falling back to local file storage")
            
            # Create ebooks directory if it doesn't exist
            ebooks_dir = Path("public/ebooks")
            ebooks_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique filename
            unique_filename = f"{current_user._id}_{file.filename}"
            if campaign_id:
                unique_filename = f"{campaign_id}_{file.filename}"
            
            file_path = ebooks_dir / unique_filename
            # Update path to match the static file serving endpoint
            relative_path = f"/ebooks/{unique_filename}"

            # Save the file
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Update campaign with ebook information if campaign_id is provided
            if campaign_id:
                # Update in campaign_users collection directly
                campaign_users_collection = get_campaign_users_collection()
                result = campaign_users_collection.update_one(
                    {"_id": ObjectId(campaign_id)},
                    {
                        "$set": {
                            "has_ebook": True,
                            "ebook_path": relative_path,
                            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                        }
                    }
                )
                if result.modified_count == 0:
                    logger.warning(f"No documents updated for campaign {campaign_id}")

            # Return response in the format expected by the frontend
            return {
                "path": relative_path
            }

    except Exception as e:
        logger.error(f"Error uploading ebook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while uploading the file: {str(e)}"
        )
    finally:
        file.file.close() 