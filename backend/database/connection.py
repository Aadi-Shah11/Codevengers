# Database connection and session management

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from config import settings
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Create database engine with optimized settings
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
    echo=settings.DATABASE_URL.endswith("?debug=true"),  # Enable SQL logging in debug mode
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {
        "charset": "utf8mb4",
        "use_unicode": True,
        "autocommit": False
    }
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False
)

# Base class for database models
Base = declarative_base()

# Database session dependency for FastAPI
def get_db() -> Session:
    """
    Dependency function to get database session for FastAPI endpoints
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# Context manager for database sessions
@contextmanager
def get_db_session():
    """
    Context manager for database sessions in non-FastAPI contexts
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# Database initialization and table creation
def create_tables():
    """
    Create all database tables
    """
    try:
        # Import all models to ensure they're registered with Base
        from models import User, Vehicle, AccessLog, Alert
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    try:
        Base.metadata.drop_all(bind=engine)
        print("✅ Database tables dropped successfully")
        return True
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        return False

def check_connection():
    """
    Test database connection
    """
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            if result.fetchone():
                print("✅ Database connection successful")
                return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

# Event listeners for connection management
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Set database-specific settings on connection
    """
    if "mysql" in settings.DATABASE_URL:
        # MySQL-specific settings
        cursor = dbapi_connection.cursor()
        cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")
        cursor.execute("SET SESSION time_zone = '+00:00'")  # Use UTC
        cursor.close()

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """
    Called when a connection is retrieved from the pool
    """
    pass

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """
    Called when a connection is returned to the pool
    """
    pass

# Database health check
def health_check():
    """
    Comprehensive database health check
    """
    try:
        with get_db_session() as db:
            # Test basic query
            result = db.execute("SELECT 1 as test").fetchone()
            
            # Check if tables exist
            from models import User, Vehicle, AccessLog, Alert
            user_count = db.query(User).count()
            vehicle_count = db.query(Vehicle).count()
            log_count = db.query(AccessLog).count()
            alert_count = db.query(Alert).count()
            
            return {
                "status": "healthy",
                "connection": "ok",
                "tables": {
                    "users": user_count,
                    "vehicles": vehicle_count,
                    "access_logs": log_count,
                    "alerts": alert_count
                }
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }