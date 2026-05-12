from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class DataRecordCreate(BaseModel):
    name: str
    department: str
    category: str
    legal_basis: str
    start_date: datetime
    retention_days: int = 0
    retention_hours: int = 0

    @field_validator("retention_days", "retention_hours")
    @classmethod
    def must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("Süre negatif olamaz.")
        return v

    def model_post_init(self, __context):
        total_hours = self.retention_days * 24 + self.retention_hours
        if total_hours < 1:
            raise ValueError("Toplam saklama süresi en az 1 saat olmalıdır.")


class DataRecordOut(BaseModel):
    id: int
    name: str
    department: str
    category: str
    legal_basis: str
    start_date: datetime
    retention_days: int
    retention_hours: int
    expiry_date: datetime
    criticality: str
    status: str
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    days_remaining: int
    hours_remaining: float
    remaining_label: str
    color_status: str

    model_config = {"from_attributes": True}


class DataRecordUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
