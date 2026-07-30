from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.database.models import User, UserSettings
from app.core.config import Settings

settings = Settings()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password[:72], hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password[:72])


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, email: str, username: str, password: str, full_name: str = "") -> User:
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        full_name=full_name,
    )
    db.add(user)
    db.flush()

    settings = UserSettings(user_id=user.id)
    db.add(settings)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_from_token(db: Session, token: str) -> Optional[User]:
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        if email is None:
            return None
        return get_user_by_email(db, email)
    except JWTError:
        return None


def verify_google_token(credential: str) -> Optional[dict]:
    try:
        info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
        if info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            return None
        return info
    except Exception:
        return None


def google_auth(db: Session, credential: str) -> Optional[tuple[User, str]]:
    info = verify_google_token(credential)
    if not info:
        return None

    email = info.get("email")
    if not email:
        return None

    user = get_user_by_email(db, email)
    if not user:
        username = email.split("@")[0]
        base = username
        suffix = 1
        while get_user_by_username(db, username):
            username = f"{base}{suffix}"
            suffix += 1

        user = User(
            email=email,
            username=username,
            hashed_password="",
            full_name=info.get("name", ""),
        )
        db.add(user)
        db.flush()
        settings_row = UserSettings(user_id=user.id)
        db.add(settings_row)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.email})
    return user, token
