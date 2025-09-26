import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_cloudinary():
    """Configure Cloudinary with credentials from environment variables"""
    try:
        # Get Cloudinary credentials from environment variables
        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
        api_key = os.environ.get("CLOUDINARY_API_KEY")
        api_secret = os.environ.get("CLOUDINARY_API_SECRET")
        
        if not all([cloud_name, api_key, api_secret]):
            logger.warning("Cloudinary credentials not found in environment variables")
            return False
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        
        logger.info("Cloudinary configured successfully")
        return True
    except Exception as e:
        logger.error(f"Error configuring Cloudinary: {str(e)}")
        return False

def upload_file_to_cloudinary(file_path, public_id=None, folder="ebooks"):
    """
    Upload a file to Cloudinary
    
    Args:
        file_path (str): Path to the file to upload
        public_id (str, optional): Public ID for the file. If not provided, Cloudinary will generate one.
        folder (str, optional): Folder to store the file in. Defaults to "ebooks".
        
    Returns:
        dict: Response from Cloudinary containing the URL and other metadata
    """
    try:
        # Configure Cloudinary if not already configured
        configure_cloudinary()
        
        # Upload file to Cloudinary
        response = cloudinary.uploader.upload(
            file_path,
            public_id=public_id,
            folder=folder,
            resource_type="auto"
        )
        
        logger.info(f"File uploaded to Cloudinary: {response['secure_url']}")
        return response
    except Exception as e:
        logger.error(f"Error uploading file to Cloudinary: {str(e)}")
        raise 