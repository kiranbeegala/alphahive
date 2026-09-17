import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load from stockpulse-india .env or local .env
stockpulse_env = "/Users/kiranbeegala/.gemini/antigravity/scratch/stockpulse-india/.env"
if os.path.exists(stockpulse_env):
    load_dotenv(stockpulse_env)
else:
    load_dotenv()

class AngelOneSmartClient:
    def __init__(self):
        self.api_key = os.getenv("ANGEL_API_KEY", "")
        self.client_id = os.getenv("ANGEL_CLIENT_ID", "") or os.getenv("ANGEL_CLIENT_CODE", "")
        self.password = os.getenv("ANGEL_PASSWORD", "") or os.getenv("ANGEL_PIN", "")
        self.totp_secret = os.getenv("ANGEL_TOTP_SECRET", "")
        
        self.smart_api = None
        self.auth_token = None
        self.refresh_token = None
        self.feed_token = None
        self.is_authenticated = False
        self.last_auth_error = None
        self.token_expiry = 0

    def has_valid_credentials(self) -> bool:
        """Checks if credentials are provided and not placeholder text."""
        placeholders = ["your_api_key_here", "your_client_id_here", "your_password_here", "your_totp_secret_here", ""]
        return bool(
            self.api_key and self.api_key not in placeholders and
            self.client_id and self.client_id not in placeholders and
            self.password and self.password not in placeholders
        )

    def generate_totp(self) -> Optional[str]:
        if not self.totp_secret or "your_totp_secret_here" in self.totp_secret:
            return None
        try:
            import pyotp
            totp = pyotp.TOTP(self.totp_secret.replace(" ", ""))
            return totp.now()
        except Exception as e:
            self.last_auth_error = f"TOTP generation failed: {e}"
            return None

    def authenticate(self) -> Dict[str, Any]:
        """
        Authenticates with AngelOne SmartAPI and generates session token using TOTP.
        """
        if not self.has_valid_credentials():
            self.last_auth_error = "Missing or placeholder credentials in .env (ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_PASSWORD, ANGEL_TOTP_SECRET)"
            return {
                "success": False,
                "status": "UNCONFIGURED",
                "message": "AngelOne SmartAPI credentials in .env are currently template placeholders. Enter your real AngelOne API keys to enable live exchange order routing.",
                "error": self.last_auth_error,
                "credentials_present": {
                    "api_key": bool(self.api_key and "your_" not in self.api_key),
                    "client_id": bool(self.client_id and "your_" not in self.client_id),
                    "password": bool(self.password and "your_" not in self.password),
                    "totp_secret": bool(self.totp_secret and "your_" not in self.totp_secret)
                }
            }

        try:
            from SmartApi import SmartConnect
            self.smart_api = SmartConnect(api_key=self.api_key)
            
            totp_val = self.generate_totp()
            if not totp_val:
                return {
                    "success": False,
                    "status": "TOTP_ERROR",
                    "message": "Failed to generate TOTP from secret key. Check ANGEL_TOTP_SECRET format.",
                    "error": self.last_auth_error
                }

            # Generate Session
            data = self.smart_api.generateSession(self.client_id, self.password, totp_val)
            
            if data and data.get("status") is True and data.get("data"):
                auth_data = data["data"]
                self.auth_token = auth_data.get("jwtToken")
                self.refresh_token = auth_data.get("refreshToken")
                self.feed_token = auth_data.get("feedToken")
                self.is_authenticated = True
                self.token_expiry = time.time() + 18 * 3600 # Session lasts ~18 hours
                
                return {
                    "success": True,
                    "status": "AUTHENTICATED",
                    "client_id": self.client_id,
                    "message": "Successfully authenticated with AngelOne SmartAPI. Ready for live NSE streaming and execution.",
                    "jwt_token_preview": f"{self.auth_token[:15]}..." if self.auth_token else None,
                    "feed_token_preview": f"{self.feed_token[:15]}..." if self.feed_token else None
                }
            else:
                err_msg = data.get("message", "Authentication returned status false") if data else "Empty response"
                self.last_auth_error = err_msg
                return {
                    "success": False,
                    "status": "AUTH_FAILED",
                    "message": f"AngelOne API login failed: {err_msg}",
                    "error": err_msg
                }
        except Exception as e:
            self.last_auth_error = str(e)
            return {
                "success": False,
                "status": "EXCEPTION",
                "message": f"Error connecting to AngelOne SmartAPI: {e}",
                "error": str(e)
            }

    def get_profile(self) -> Dict[str, Any]:
        if not self.is_authenticated or not self.smart_api:
            return {"error": "Not authenticated"}
        try:
            return self.smart_api.getProfile(self.refresh_token)
        except Exception as e:
            return {"error": str(e)}

angel_client = AngelOneSmartClient()
