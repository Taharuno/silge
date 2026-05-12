from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.data_record import now_local

from app.database import get_db
from app.models.data_record import DataRecord, Status, Criticality

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/")
def get_dashboard(db: Session = Depends(get_db)):
    all_records = db.query(DataRecord).all()
    now = now_local()

    total = len(all_records)
    aktif = sum(1 for r in all_records if r.status == Status.aktif)
    onay_bekliyor = sum(1 for r in all_records if r.status == Status.onay_bekliyor)
    arsivlendi = sum(1 for r in all_records if r.status == Status.arsivlendi)

    yesil = sum(1 for r in all_records if r.status == Status.aktif and (r.expiry_date - now).total_seconds() > 30 * 86400)
    sari = sum(1 for r in all_records if r.status == Status.aktif and 0 < (r.expiry_date - now).total_seconds() <= 30 * 86400)
    kirmizi = sum(1 for r in all_records if r.status == Status.onay_bekliyor)

    kritik = sum(1 for r in all_records if r.criticality == Criticality.kritik and r.status != Status.arsivlendi)
    orta = sum(1 for r in all_records if r.criticality == Criticality.orta and r.status != Status.arsivlendi)
    dusuk = sum(1 for r in all_records if r.criticality == Criticality.dusuk and r.status != Status.arsivlendi)

    dept_summary = {}
    for r in all_records:
        if r.status == Status.arsivlendi:
            continue
        if r.department not in dept_summary:
            dept_summary[r.department] = {"toplam": 0, "onay_bekliyor": 0}
        dept_summary[r.department]["toplam"] += 1
        if r.status == Status.onay_bekliyor:
            dept_summary[r.department]["onay_bekliyor"] += 1

    aktif_records = [r for r in all_records if r.status == Status.aktif]
    yaklasan = sorted(aktif_records, key=lambda r: r.expiry_date)[:5]
    yaklasan_list = [
        {
            "id": r.id,
            "name": r.name,
            "department": r.department,
            "expiry_date": r.expiry_date.strftime("%Y-%m-%d %H:%M"),
            "remaining_label": r.remaining_label(),
            "criticality": r.criticality,
        }
        for r in yaklasan
    ]

    return {
        "ozet": {
            "toplam": total,
            "aktif": aktif,
            "onay_bekliyor": onay_bekliyor,
            "arsivlendi": arsivlendi,
        },
        "renk_dagilimi": {
            "yesil": yesil,
            "sari": sari,
            "kirmizi": kirmizi,
        },
        "kritiklik_dagilimi": {
            "kritik": kritik,
            "orta": orta,
            "dusuk": dusuk,
        },
        "departman_ozeti": dept_summary,
        "yaklasan_imhalar": yaklasan_list,
    }
