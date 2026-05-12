# Silge - Veri İmha ve Yaşam Döngüsü Takip Sistemi

KVKK ve GDPR kapsamında veri saklama sürelerini otomatik takip eden, süresi dolan verilerin denetimli imha sürecini yöneten, PDF tutanak üreten ve audit log tutan bir web uygulaması.

---

## Özellikler

- Kategori bazlı otomatik kritiklik sınıflandırması
- Yasal dayanağa göre saklama süresi otomatik hesaplama — o süreden fazlası girilemez
- Mali yıl sonu baz alma desteği (31 Aralık'tan itibaren hesaplama)
- Şirket politikası seçeneği - yasal maksimumu aşamaz
- Gün/saat bazında geri sayım, 5 saniyede bir güncelleme
- Süresi dolan kayıtlar için anlık uyarı banner'ı
- İmha onayında otomatik PDF tutanak üretimi (Türkçe karakter destekli)
- Dosya path takibi — imha anında orijinal dosya diskten silinir
- Her silme işlemi audit log'a kaydedilir (kim sildi, ne zaman, hangi kayıt)
- Dashboard — etkileşimli donut grafik, kritiklik bar chart, departman özeti, yaklaşan imhalar
- SQLite (geliştirme) → PostgreSQL (üretim) tek satır geçiş
- Docker ile tam containerized deployment

---

## Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, APScheduler |
| Frontend | React, Vite, Axios |
| Veritabanı | SQLite / PostgreSQL |
| PDF | ReportLab |
| Deployment | Docker, Docker Compose |

---

## Kurulum

### Docker ile (Önerilen)

```bash
git clone https://github.com/Taharuno/silge.git
cd silge

# .env dosyasını oluştur
cp .env.example .env

# Başlat
docker-compose up --build
```

- Frontend → `http://localhost:5173`
- Backend API → `http://localhost:8000/docs`

### Manuel Kurulum

**Backend:**
```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd silge-frontend
npm install
npm run dev
```

---

## Proje Yapısı

```
silge/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   │   ├── data_record.py
│   │   ├── audit_log.py
│   │   └── schemas.py
│   ├── routes/
│   │   ├── records.py
│   │   ├── dashboard.py
│   │   └── audit.py
│   ├── services/
│   │   └── pdf_service.py
│   └── scheduler/
│       └── tasks.py
├── silge-frontend/
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── pages/
│           ├── Dashboard.jsx
│           ├── Records.jsx
│           └── NewRecord.jsx
├── tests/
│   └── test_api.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Yasal Uyumluluk

| Veri Türü | Süre | Dayanak |
|---|---|---|
| Fatura / İrsaliye | 10 yıl | 6102 sayılı TTK |
| Çalışan Özlük Dosyası | 10 yıl | 5510 sayılı SGK |
| İş Sağlığı Verisi | 15 yıl | İSG Yönetmeliği |
| Sözleşme | 10 yıl | 6098 sayılı TBK |
| Aday CV | 6 ay | GDPR Madde 5 |
| Müşteri İletişim | 1 yıl | Ticari İletişim Yönetmeliği |

---

