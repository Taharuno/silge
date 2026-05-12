from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)        # "silindi" | "imha_onaylandi"
    record_id = Column(Integer, nullable=False)    # Silinen kaydın ID'si
    record_name = Column(String, nullable=False)   # Kayıt adı
    department = Column(String, nullable=True)     # Departman
    category = Column(String, nullable=True)       # Kategori
    performed_by = Column(String, nullable=False)  # Kim yaptı
    note = Column(String, nullable=True)           # Ek not
    created_at = Column(DateTime, server_default=func.now())
