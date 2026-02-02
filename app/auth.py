"""
Firebase authentication module.

Handles:
- Firebase Admin SDK initialization
- Token verification for protected endpoints
"""

import os
import json
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Security scheme - extracts Bearer token from Authorization header
security = HTTPBearer()


def init_firebase():
    """
    Initialize Firebase Admin SDK.

    Supports two modes:
    1. FIREBASE_SERVICE_ACCOUNT_JSON env var (JSON string, for production/Docker)
    2. FIREBASE_SERVICE_ACCOUNT env var (file path to serviceAccountKey.json, for local dev)
    """
    if firebase_admin._apps:
        return  # Already initialized

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")

    if service_account_json:
        # Parse JSON string from environment variable (useful for Docker/CI)
        cred = credentials.Certificate(json.loads(service_account_json))
    elif service_account_path:
        # Load from file path (useful for local development)
        cred = credentials.Certificate(service_account_path)
    else:
        raise ValueError(
            "Firebase credentials not configured. "
            "Set FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT env var."
        )

    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized!")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency that verifies the Firebase ID token.

    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            uid = user["uid"]

    Returns the decoded token containing uid, email, etc.
    Raises 401 if token is invalid or expired.
    """
    token = credentials.credentials

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
