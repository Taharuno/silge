import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from app.main import app
from app.database import Base, get_db
from app.models.data_record import DataRecord, Status

# Test için ayrı bir in-memory SQLite veritabanı
TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


# Her testten önce tabloları sıfırla
@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


client = TestClient(app)


# ─── KAYIT OLUŞTURMA ────────────────────────────────────────────

def test_kayit_olustur():
    response = client.post("/records/", json={
        "name": "Test Faturası",
        "department": "Muhasebe",
        "category": "fatura",
        "legal_basis": "TTK Madde 82",
        "start_date": "2024-01-01",
        "retention_years": 10,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Faturası"
    assert data["criticality"] == "kritik"          # fatura → kritik
    assert data["expiry_date"] == "2034-01-01"      # 2024 + 10 yıl
    assert data["status"] == "aktif"


def test_gecersiz_saklama_suresi():
    response = client.post("/records/", json={
        "name": "Hatalı Kayıt",
        "department": "IT",
        "category": "geçici",
        "legal_basis": "Yok",
        "start_date": "2024-01-01",
        "retention_years": 0,       # 0 geçersiz
    })
    assert response.status_code == 422


# ─── LİSTELEME VE FİLTRELEME ───────────────────────────────────

def test_kayit_listele():
    # Önce iki kayıt ekle
    for i in range(2):
        client.post("/records/", json={
            "name": f"Kayıt {i}",
            "department": "IT",
            "category": "erişim_logu",
            "legal_basis": "İç Politika",
            "start_date": "2024-01-01",
            "retention_years": 2,
        })
    response = client.get("/records/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_departman_filtrele():
    client.post("/records/", json={
        "name": "İK Kaydı",
        "department": "İK",
        "category": "özlük",
        "legal_basis": "SGK",
        "start_date": "2024-01-01",
        "retention_years": 10,
    })
    client.post("/records/", json={
        "name": "Muhasebe Kaydı",
        "department": "Muhasebe",
        "category": "fatura",
        "legal_basis": "TTK",
        "start_date": "2024-01-01",
        "retention_years": 10,
    })
    response = client.get("/records/?department=İK")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["department"] == "İK"


# ─── TEK KAYIT GETIRME ──────────────────────────────────────────

def test_kayit_getir():
    create = client.post("/records/", json={
        "name": "Özlük Dosyası",
        "department": "İK",
        "category": "özlük",
        "legal_basis": "SGK",
        "start_date": "2020-01-01",
        "retention_years": 10,
    })
    record_id = create.json()["id"]
    response = client.get(f"/records/{record_id}")
    assert response.status_code == 200
    assert response.json()["id"] == record_id


def test_olmayan_kayit():
    response = client.get("/records/9999")
    assert response.status_code == 404


# ─── GÜNCELLEME ─────────────────────────────────────────────────

def test_kayit_guncelle():
    create = client.post("/records/", json={
        "name": "Eski Ad",
        "department": "IT",
        "category": "geçici",
        "legal_basis": "İç Politika",
        "start_date": "2024-01-01",
        "retention_years": 1,
    })
    record_id = create.json()["id"]
    response = client.patch(f"/records/{record_id}", json={"name": "Yeni Ad"})
    assert response.status_code == 200
    assert response.json()["name"] == "Yeni Ad"


# ─── İMHA ONAYI ─────────────────────────────────────────────────

def test_imha_onayi():
    # Süresi dolmuş bir kayıt elle ekle
    db = TestingSession()
    record = DataRecord(
        name="Eski Sözleşme",
        department="Hukuk",
        category="sözleşme",
        legal_basis="TBK",
        start_date=date(2010, 1, 1),
        retention_years=10,
        expiry_date=date(2020, 1, 1),
        criticality="orta",
        status=Status.onay_bekliyor,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    record_id = record.id
    db.close()

    response = client.post(f"/records/{record_id}/approve-deletion?approver=Test+Kullanici")
    assert response.status_code == 200
    assert response.json()["record"]["status"] == "arsivlendi"
    assert "tutanak" in response.json()


def test_aktif_kayda_imha_onayi_verilmez():
    create = client.post("/records/", json={
        "name": "Aktif Kayıt",
        "department": "IT",
        "category": "geçici",
        "legal_basis": "İç",
        "start_date": "2024-01-01",
        "retention_years": 5,
    })
    record_id = create.json()["id"]
    response = client.post(f"/records/{record_id}/approve-deletion?approver=Admin")
    assert response.status_code == 400


# ─── DASHBOARD ──────────────────────────────────────────────────

def test_dashboard_bos():
    response = client.get("/dashboard/")
    assert response.status_code == 200
    data = response.json()
    assert data["ozet"]["toplam"] == 0
    assert data["yaklasan_imhalar"] == []


def test_dashboard_dolu():
    client.post("/records/", json={
        "name": "Fatura",
        "department": "Muhasebe",
        "category": "fatura",
        "legal_basis": "TTK",
        "start_date": "2024-01-01",
        "retention_years": 10,
    })
    response = client.get("/dashboard/")
    assert response.status_code == 200
    data = response.json()
    assert data["ozet"]["toplam"] == 1
    assert data["ozet"]["aktif"] == 1
    assert data["kritiklik_dagilimi"]["kritik"] == 1
