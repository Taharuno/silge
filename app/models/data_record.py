from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum
import os

from app.database import Base

# Saat dilimi — TZ env değişkeninden oku, yoksa İstanbul
TZ_NAME = os.getenv("TZ", "Europe/Istanbul")

def now_local():
    """Sistem saat dilimine göre şimdiki zamanı döndürür."""
    try:
        import zoneinfo
        from datetime import timezone
        tz = zoneinfo.ZoneInfo(TZ_NAME)
        return datetime.now(tz).replace(tzinfo=None)
    except Exception:
        return datetime.now()


class Criticality(str, enum.Enum):
    kritik = "kritik"
    orta = "orta"
    dusuk = "düşük"


class Status(str, enum.Enum):
    aktif = "aktif"
    onay_bekliyor = "onay_bekliyor"
    arsivlendi = "arsivlendi"


CATEGORY_CRITICALITY_MAP = {
    "sağlık": Criticality.kritik,
    "özlük": Criticality.kritik,
    "finansal": Criticality.kritik,
    "fatura": Criticality.kritik,
    "muhasebe": Criticality.kritik,
    "sözleşme": Criticality.orta,
    "müşteri_iletişim": Criticality.orta,
    "aday_cv": Criticality.orta,
    "erişim_logu": Criticality.dusuk,
    "geçici": Criticality.dusuk,
}


class DataRecord(Base):
    __tablename__ = "data_records"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    category = Column(String, nullable=False)
    legal_basis = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    retention_days = Column(Integer, nullable=False)
    retention_hours = Column(Integer, default=0)
    expiry_date = Column(DateTime, nullable=False)
    criticality = Column(String, nullable=False)
    status = Column(String, default=Status.aktif)
    file_path = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    @staticmethod
    def calculate_expiry(start_date: datetime, retention_days: int, retention_hours: int = 0) -> datetime:
        return start_date + timedelta(days=retention_days, hours=retention_hours)

    @staticmethod
    def calculate_expiry_mali_yil(start_date: datetime, retention_days: int) -> datetime:
        retention_years = round(retention_days / 365)
        try:
            return start_date.replace(year=start_date.year + retention_years)
        except ValueError:
            return start_date.replace(year=start_date.year + retention_years, day=28)

    @staticmethod
    def assign_criticality(category: str) -> str:
        return CATEGORY_CRITICALITY_MAP.get(category, Criticality.orta).value

    def hours_remaining(self) -> float:
        delta = self.expiry_date - now_local()
        return round(delta.total_seconds() / 3600, 1)

    def days_remaining(self) -> int:
        delta = self.expiry_date - now_local()
        return max(int(delta.total_seconds() // 86400), 0)

    def color_status(self) -> str:
        hours = self.hours_remaining()
        if hours > 720:
            return "yeşil"
        elif hours > 0:
            return "sarı"
        else:
            return "kırmızı"

    def remaining_label(self) -> str:
        delta = self.expiry_date - now_local()
        total_seconds = delta.total_seconds()

        if total_seconds <= 0:
            return "Süresi doldu"

        total_minutes = int(total_seconds // 60)
        total_hours = int(total_seconds // 3600)
        days = int(total_seconds // 86400)

        if total_minutes < 60:
            return f"{total_minutes} dakika"
        elif total_hours < 24:
            minutes_left = total_minutes % 60
            if minutes_left > 0:
                return f"{total_hours} saat {minutes_left} dakika"
            return f"{total_hours} saat"
        else:
            hours_left = total_hours % 24
            if hours_left > 0:
                return f"{days} gün {hours_left} saat"
            return f"{days} gün"
