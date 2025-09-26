from config.database import get_users_collection as db_get_users_collection
from fastapi import HTTPException
from bson import ObjectId
from services.auth_service import get_password_hash

def get_users():
    try:
        users_collection = db_get_users_collection()
        users = list(users_collection.find())
        
        transformed_users = [{ 
            "id": str(user["_id"]),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "role": user.get("role", ""),
            "businessName": user.get("businessName", ""),
            "api_key": user.get("api_key", ""),
        } for user in users]
        
        return {
            "status": "success",
            "message": "Users retrieved successfully",
            "data": transformed_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")

def get_user_by_id(user_id: str):
    try:
        users_collection = db_get_users_collection()
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        return {
            "id": str(user["_id"]),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "role": user.get("role", ""),
            "businessName": user.get("businessName", ""),
            "api_key": user.get("api_key", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

def update_user(user_id: str, user_data: dict):
    try:
        users_collection = db_get_users_collection()
        
        # Check if user exists
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update data
        update_data = {
            "api_key": user.get("api_key", "")
        }
        if "name" in user_data:
            update_data["name"] = user_data["name"]
        if "email" in user_data:
            # Check if email already exists for another user
            existing_user = users_collection.find_one({"email": user_data["email"], "_id": {"$ne": ObjectId(user_id)}})
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already in use by another user")
            update_data["email"] = user_data["email"]
        if "businessName" in user_data:
            update_data["businessName"] = user_data["businessName"]
        if "role" in user_data:
            update_data["role"] = user_data["role"]
        if "password" in user_data and user_data["password"]:
            # Hash the new password
            update_data["password"] = get_password_hash(user_data["password"])
        if "api_key" in user_data:
            update_data["api_key"] = user_data["api_key"]
        
        # Update the user
        if update_data:
            users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
        
        return {
            "status": "success",
            "message": "User updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

