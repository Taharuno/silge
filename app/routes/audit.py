from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("/")
def get_audit_logs(db: Session = Depends(get_db)):
    """Tüm silme ve imha loglarını döndürür."""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
    return [
        {
            "id": log.id,
            "action": log.action,
            "record_id": log.record_id,
            "record_name": log.record_name,
            "department": log.department,
            "category": log.category,
            "performed_by": log.performed_by,
            "note": log.note,
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None,
        }
        for log in logs
    ]
