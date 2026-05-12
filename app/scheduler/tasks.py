from app.database import SessionLocal
from app.models.data_record import DataRecord, Status, now_local


def check_expired_records():
    """Her 5 saniyede çalışır. Süresi dolan aktif kayıtları onay_bekliyor'a geçirir."""
    db = SessionLocal()
    try:
        now = now_local()
        expired = db.query(DataRecord).filter(
            DataRecord.status == Status.aktif,
            DataRecord.expiry_date <= now
        ).all()

        for record in expired:
            record.status = Status.onay_bekliyor
            print(f"[Zamanlayıcı] Süresi doldu → {record.name} (ID: {record.id})")

        db.commit()
        if expired:
            print(f"[Zamanlayıcı] {len(expired)} kayıt güncellendi.")
    finally:
        db.close()
