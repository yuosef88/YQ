"""
Database connection and session management.
Uses the new paths system for proper data persistence.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.models import Base
from core.paths import app_paths


# Create engine with the proper database path
DATABASE_URL = f"sqlite:///{app_paths.database_path}"
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine, 
    autocommit=False, 
    autoflush=False,
    expire_on_commit=False  # Prevent detached instance errors
)


def get_db_session():
    """Get a database session."""
    return SessionLocal()


def init_db():
    """Initialize database tables."""
    print(f"Initializing database at: {app_paths.database_path}")
    
    # Ensure the data directory exists
    app_paths.database_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


def get_db_info():
    """Get database information for debugging."""
    return {
        "database_url": DATABASE_URL,
        "database_path": str(app_paths.database_path),
        "database_exists": app_paths.database_path.exists(),
        "data_dir": str(app_paths.data_dir),
        "media_dir": str(app_paths.media_dir)
    }
