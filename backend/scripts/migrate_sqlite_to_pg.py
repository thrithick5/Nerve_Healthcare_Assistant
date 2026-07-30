import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.connection import Base
from app.database.models import User, Conversation, Message, ConversationFile, UserSettings


def migrate():
    # Try resolving relative to the script first, then fallback to current working directory
    sqlite_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "healthcare.db"))
    if not os.path.exists(sqlite_db_path):
        sqlite_db_path = os.path.abspath("data/healthcare.db")
        
    if not os.path.exists(sqlite_db_path):
        print(f"[ERROR] SQLite database not found at {sqlite_db_path}")
        return

    sqlite_url = f"sqlite:///{sqlite_db_path}"
    pg_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/nerve_health")

    print(f"Reading from SQLite: {sqlite_url}")
    print(f"Writing to PostgreSQL: {pg_url}")

    sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    pg_engine = create_engine(pg_url)

    # Ensure PostgreSQL schema is created
    Base.metadata.create_all(bind=pg_engine)

    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=pg_engine)

    sqlite_db = SqliteSession()
    pg_db = PgSession()

    try:
        # 1. Users
        users = sqlite_db.query(User).all()
        print(f"Migrating {len(users)} users...")
        for u in users:
            existing = pg_db.query(User).filter_by(id=u.id).first()
            if not existing:
                new_u = User(
                    id=u.id,
                    email=u.email,
                    username=u.username,
                    hashed_password=u.hashed_password,
                    full_name=u.full_name,
                    is_active=u.is_active,
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                )
                pg_db.add(new_u)
        pg_db.commit()

        # 2. Conversations
        convs = sqlite_db.query(Conversation).all()
        print(f"Migrating {len(convs)} conversations...")
        for c in convs:
            existing = pg_db.query(Conversation).filter_by(id=c.id).first()
            if not existing:
                new_c = Conversation(
                    id=c.id,
                    user_id=c.user_id,
                    title=c.title,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
                pg_db.add(new_c)
        pg_db.commit()

        # 3. Messages
        msgs = sqlite_db.query(Message).all()
        print(f"Migrating {len(msgs)} messages...")
        for m in msgs:
            existing = pg_db.query(Message).filter_by(id=m.id).first()
            if not existing:
                new_m = Message(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    sources=m.sources,
                    created_at=m.created_at,
                )
                pg_db.add(new_m)
        pg_db.commit()

        # 4. Conversation Files
        cfiles = sqlite_db.query(ConversationFile).all()
        print(f"Migrating {len(cfiles)} conversation files...")
        for f in cfiles:
            existing = pg_db.query(ConversationFile).filter_by(id=f.id).first()
            if not existing:
                new_f = ConversationFile(
                    id=f.id,
                    conversation_id=f.conversation_id,
                    filename=f.filename,
                    source=f.source,
                    ocr_text=f.ocr_text,
                    created_at=f.created_at,
                )
                pg_db.add(new_f)
        pg_db.commit()

        # 5. User Settings
        usettings = sqlite_db.query(UserSettings).all()
        print(f"Migrating {len(usettings)} user settings...")
        for s in usettings:
            existing = pg_db.query(UserSettings).filter_by(id=s.id).first()
            if not existing:
                new_s = UserSettings(
                    id=s.id,
                    user_id=s.user_id,
                    theme=s.theme,
                    language=s.language,
                )
                pg_db.add(new_s)
        pg_db.commit()

        # Reset Postgres sequences so primary keys auto-increment properly after imported IDs
        print("Resetting PostgreSQL primary key sequences...")
        tables = ["users", "conversations", "messages", "conversation_files", "user_settings"]
        with pg_engine.connect() as conn:
            for t in tables:
                conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), COALESCE(max(id), 1)) FROM {t};"))
            conn.commit()

        print("Migration from SQLite to PostgreSQL completed successfully!")

    except Exception as e:
        pg_db.rollback()
        print(f"[ERROR] Migration failed: {e}")
        raise e
    finally:
        sqlite_db.close()
        pg_db.close()


if __name__ == "__main__":
    migrate()
