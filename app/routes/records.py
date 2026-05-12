from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import os

from app.database import get_db
from app.models.data_record import DataRecord, Status
from app.models.audit_log import AuditLog
from app.models.schemas import DataRecordCreate, DataRecordOut, DataRecordUpdate

router = APIRouter(prefix="/records", tags=["Veri Kayıtları"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def detect_file_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in {"jpg", "jpeg", "png", "gif", "webp", "bmp"}:
        return "image"
    elif ext in {"mp4", "avi", "mov", "mkv", "webm"}:
        return "video"
    elif ext in {"txt", "pdf", "doc", "docx", "xls", "xlsx", "csv"}:
        return "document"
    return "other"


@router.post("/", response_model=DataRecordOut, status_code=201)
def create_record(
    name: str = Form(...),
    department: str = Form(...),
    category: str = Form(...),
    legal_basis: str = Form(...),
    start_date: str = Form(...),
    retention_days: int = Form(0),
    retention_hours: int = Form(0),
    file_path_only: Optional[str] = Form(None),
    mali_yil_baz: str = Form("false"),
    db: Session = Depends(get_db),
):
    total_hours = retention_days * 24 + retention_hours
    if total_hours < 1:
        raise HTTPException(status_code=422, detail="Toplam saklama süresi en az 1 saat olmalıdır.")

    parsed_date = datetime.fromisoformat(start_date)

    # Mali yıl baz alınacaksa, o yılın 31 Aralık'ından itibaren hesapla
    if mali_yil_baz == "true":
        yil_sonu = datetime(parsed_date.year, 12, 31, 23, 59, 59)
        expiry = DataRecord.calculate_expiry_mali_yil(yil_sonu, retention_days)
    else:
        expiry = DataRecord.calculate_expiry(parsed_date, retention_days, retention_hours)

    criticality = DataRecord.assign_criticality(category)

    file_path = file_name = file_type = None
    if file_path_only and file_path_only.strip():
        file_path = file_path_only.strip().strip('"').strip("'")
        file_name = os.path.basename(file_path)
        file_type = detect_file_type(file_name)

    record = DataRecord(
        name=name,
        department=department,
        category=category,
        legal_basis=legal_basis,
        start_date=parsed_date,
        retention_days=retention_days,
        retention_hours=retention_hours,
        expiry_date=expiry,
        criticality=criticality,
        file_path=file_path,
        file_name=file_name,
        file_type=file_type,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _enrich(record)


@router.get("/", response_model=List[DataRecordOut])
def list_records(
    department: Optional[str] = None,
    criticality: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(DataRecord)
    if department:
        query = query.filter(DataRecord.department == department)
    if criticality:
        query = query.filter(DataRecord.criticality == criticality)
    if status:
        query = query.filter(DataRecord.status == status)
    return [_enrich(r) for r in query.all()]


@router.get("/{record_id}", response_model=DataRecordOut)
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(DataRecord).filter(DataRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    return _enrich(record)


@router.patch("/{record_id}", response_model=DataRecordOut)
def update_record(record_id: int, payload: DataRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(DataRecord).filter(DataRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return _enrich(record)


@router.post("/{record_id}/approve-deletion")
def approve_deletion(record_id: int, approver: str, db: Session = Depends(get_db)):
    from app.services.pdf_service import generate_destruction_receipt
    record = db.query(DataRecord).filter(DataRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    if record.status != Status.onay_bekliyor:
        raise HTTPException(status_code=400, detail="Bu kayıt imha onayı durumunda değil.")

    if record.file_path:
        clean_path = record.file_path.strip().strip('"').strip("'")
        candidate_paths = [clean_path, os.path.join(BASE_DIR, clean_path)]
        for path in candidate_paths:
            if os.path.exists(path):
                os.remove(path)
                print(f"[İmha] Dosya silindi: {path}")
                break
        record.file_path = None
        record.file_name = None
        record.file_type = None

    record.status = Status.arsivlendi
    db.commit()
    db.refresh(record)
    enriched = _enrich(record)
    generate_destruction_receipt(enriched, approver)
    return {
        "message": "İmha onaylandı. Tutanak oluşturuldu.",
        "record": enriched,
        "tutanak_url": f"/records/{record_id}/tutanak",
    }


@router.get("/{record_id}/tutanak")
def download_tutanak(record_id: int, db: Session = Depends(get_db)):
    record = db.query(DataRecord).filter(DataRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    if record.status != Status.arsivlendi:
        raise HTTPException(status_code=400, detail="Bu kayıt için henüz tutanak oluşturulmamış.")
    TUTANAK_DIR = os.path.join(BASE_DIR, "tutanaklar")
    pdf_path = None
    if os.path.exists(TUTANAK_DIR):
        matches = [f for f in os.listdir(TUTANAK_DIR) if f.startswith(f"imha_tutanagi_{record_id}_")]
        if matches:
            pdf_path = os.path.join(TUTANAK_DIR, sorted(matches)[-1])
    if not pdf_path:
        from app.services.pdf_service import generate_destruction_receipt
        pdf_path = generate_destruction_receipt(_enrich(record), "Sistem")
    return FileResponse(path=pdf_path, media_type="application/pdf", filename=f"imha_tutanagi_{record_id}.pdf")


@router.get("/{record_id}/dosya")
def download_file(record_id: int, db: Session = Depends(get_db)):
    record = db.query(DataRecord).filter(DataRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    if not record.file_path or not os.path.exists(record.file_path):
        raise HTTPException(status_code=404, detail="Bu kayda ait dosya bulunamadı.")
    return FileResponse(path=record.file_path, filename=record.file_name)


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, performed_by: str = "Bilinmiyor", db: Session = Depends(get_db)):
    record = db.query(DataRecord).filter(DataRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")

    # Silmeden önce log tut
    log = AuditLog(
        action="silindi",
        record_id=record.id,
        record_name=record.name,
        department=record.department,
        category=record.category,
        performed_by=performed_by,
        note=f"Kayıt manuel olarak silindi. Durum: {record.status}",
    )
    db.add(log)

    if record.file_path:
        candidate_paths = [record.file_path, os.path.join(BASE_DIR, record.file_path)]
        for path in candidate_paths:
            if os.path.exists(path):
                os.remove(path)
                break
    db.delete(record)
    db.commit()


def _enrich(record: DataRecord) -> dict:
    data = {c.name: getattr(record, c.name) for c in record.__table__.columns}
    data["days_remaining"] = record.days_remaining()
    data["hours_remaining"] = record.hours_remaining()
    data["remaining_label"] = record.remaining_label()
    data["color_status"] = record.color_status()
    return data
