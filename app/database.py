from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()  # .env dosyasını oku

# Docker volume'da data/ klasörünü kullan, yoksa proje kökünde
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/silge.db")

# Klasör yoksa oluştur (SQLite için)
if DATABASE_URL.startswith("sqlite"):
    import pathlib
    db_path = DATABASE_URL.replace("sqlite:///", "").replace("./", "")
    pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)

# SQLite'a özel ayar — diğer veritabanlarında connect_args gerekmez
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Her request için bir DB oturumu açar, işlem bitince kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
