from datetime import datetime, timedelta
from typing import Optional

class TokenStore:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TokenStore, cls).__new__(cls)
            cls._instance._microsoft_token = None
            cls._instance._token_expiry = None
        return cls._instance
    
    @property
    def microsoft_token(self) -> Optional[str]:
        """Get the stored Microsoft token"""
        # Check if token is expired
        if self._token_expiry and datetime.now() > self._token_expiry:
            print("Token expired, returning None")
            return None
        
        if not self._microsoft_token:
            print("No token available")
        else:
            print(f"Returning token (starts with): {self._microsoft_token[:15]}...")
            
        return self._microsoft_token
    
    @microsoft_token.setter
    def microsoft_token(self, value: str):
        """Set the Microsoft token"""
        if not value:
            print("Attempted to set empty token")
            return
            
        print(f"Setting new Microsoft token: {value[:15]}...")
        self._microsoft_token = value
        # Default expiry of 1 hour if not specified
        if not self._token_expiry:
            self._token_expiry = datetime.now() + timedelta(seconds=3600)
    
    def set_token_with_expiry(self, token: str, expires_in_seconds: int = 3600):
        """Set the token with an expiry time"""
        if not token:
            print("Attempted to set empty token")
            return False
            
        self._microsoft_token = token
        self._token_expiry = datetime.now() + timedelta(seconds=expires_in_seconds)
        print(f"Token set with expiry: {self._token_expiry}")
        return True
    
    def clear_token(self):
        """Clear the stored token"""
        self._microsoft_token = None
        self._token_expiry = None
        print("Token cleared")
    
    @property
    def is_token_valid(self) -> bool:
        """Check if the token exists and is not expired"""
        if not self._microsoft_token:
            print("Token validation failed: No token exists")
            return False
        if not self._token_expiry:
            print("Token validation warning: No expiry set, assuming valid")
            return True  # No expiry set, assume valid
            
        is_valid = datetime.now() < self._token_expiry
        if not is_valid:
            print(f"Token expired at {self._token_expiry}")
        else:
            time_remaining = self._token_expiry - datetime.now()
            print(f"Token valid. Expires in {time_remaining.total_seconds():.0f} seconds")
            
        return is_valid
    
    @property
    def token_expiry(self) -> Optional[datetime]:
        """Get the token expiry time"""
        return self._token_expiry
    
    @property
    def time_until_expiry(self) -> Optional[int]:
        """Get seconds until token expires"""
        if not self._token_expiry:
            return None
        
        seconds_remaining = (self._token_expiry - datetime.now()).total_seconds()
        return max(0, int(seconds_remaining))  # Don't return negative values
