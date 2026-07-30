"""
Enhanced Authentication System with JWT and Role Management
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import structlog
from app.core.database import User

logger = structlog.get_logger()

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = "YOUR_SECRET_KEY_CHANGE_THIS_IN_PRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
class TokenData:
    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role

class AuthManager:
    """Comprehensive authentication manager with role-based access control"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash user password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify user password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: Optional[str] = None) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if token_type and payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected: {token_type}",
                )
            username = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    
    @staticmethod
    def require_role(required_role: str):
        """Dependency factory for role-based access control"""
        def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
            user_role = current_user.get("role")
            role_hierarchy = {"patient": 1, "healthcare_provider": 2, "admin": 3}
            
            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required role: {required_role}",
                )
            return current_user
        return role_checker
class SessionManager:
    """Session management with Redis backend"""
    
    def __init__(self):
        self.redis = redis.from_url("redis://localhost:6379/1", decode_responses=True)
        self.session_ttl = 3600
    
    def create_session(self, user_id: str, username: str, role: str) -> Dict[str, Any]:
        """Create new user session"""
        session_id = f"session:{user_id}:{datetime.utcnow().timestamp()}"
        session_data = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }
        
        self.redis.hmset(session_id, session_data)
        self.redis.expire(session_id, self.session_ttl)
        
        logger.info("User session created", user_id=user_id, session_id=session_id)
        
        return {
            "session_id": session_id,
            "session_data": session_data,
        }
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and return session data"""
        try:
            session_data = self.redis.hgetall(session_id)
            if not session_data:
                return None
            
            session_data = {k: v for k, v in session_data.items()}
            
            # Update last activity
            self.redis.hset(session_id, "last_activity", datetime.utcnow().isoformat())
            self.redis.expire(session_id, self.session_ttl)
            
            logger.debug("Session validated", session_id=session_id)
            return session_data
        except Exception as e:
            logger.error("Session validation error", session_id=session_id, error=str(e))
            return None
    
    def revoke_session(self, session_id: str):
        """Revoke user session"""
        self.redis.delete(session_id)
        logger.info("Session revoked", session_id=session_id)
    
    def cleanup_inactive_sessions(self, max_inactive_minutes: int = 30):
        """Clean up inactive sessions"""
        pattern = "session:*"
        session_ids = self.redis.keys(pattern)
        
        for session_id in session_ids:
            session_data = self.redis.hgetall(session_id)
            if session_data:
                last_activity = datetime.fromisoformat(session_data.get("last_activity"))
                inactive_minutes = (datetime.utcnow() - last_activity).total_seconds() / 60
                
                if inactive_minutes > max_inactive_minutes:
                    self.redis.delete(session_id)
                    logger.info("Inactive session cleaned up", session_id=session_id)
def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Dependency to extract and validate current user from token"""
    # First try to validate as access token
    try:
        payload = AuthManager.verify_token(token, "access")
        username = payload.get("sub")
        if username:
            return {
                "username": username,
                "role": payload.get("role"),
                "token_type": "access",
            }
    except HTTPException:
        pass
    
    # If access token validation fails, try refresh token
    try:
        payload = AuthManager.verify_token(token, "refresh")
        username = payload.get("sub")
        if username:
            return {
                "username": username,
                "role": payload.get("role"),
                "token_type": "refresh",
            }
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

# Role constants
ROLE_PATIENT = "patient"
ROLE_HEALTHCARE_PROVIDER = "healthcare_provider"
ROLE_ADMIN = "admin"

# Permission definitions
PERMISSIONS = {
    ROLE_PATIENT: ["read_medical_info", "access_chat", "view_own_conversations"],
    ROLE_HEALTHCARE_PROVIDER: [
        "read_medical_info", "access_chat", "view_own_conversations",
        "view_patient_records", "manage_prescriptions", "add_medical_notes"
    ],
    ROLE_ADMIN: [
        "read_medical_info", "access_chat", "view_all_conversations",
        "manage_users", "manage_system", "view_analytics", "export_data"
    ]
}
