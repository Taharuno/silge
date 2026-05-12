import { useState } from "react";
import axios from "axios";

// Mali yıl sonu baz alınması gereken kategoriler
const MALI_YIL_KATEGORILER = ["fatura", "finansal", "sözleşme", "özlük"];

// Bugünden 31 Aralık'a kalan gün sayısı
function getKalanGun() {
  const now = new Date();
  const yilSonu = new Date(now.getFullYear(), 11, 31);
  const diff = Math.ceil((yilSonu - now) / (1000 * 60 * 60 * 24));
  return Math.max(diff, 0);
}

function toDatetimeLocal(date) {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

// Kategori → Yasal dayanak → Maksimum süre eşleşme tablosu
const CATEGORY_MAP = {
  "fatura": {
    label: "Fatura / İrsaliye",
    dayanaklar: [
      { value: "6102 sayılı Türk Ticaret Kanunu", label: "6102 sayılı TTK", days: 3650, hours: 0 },
    ]
  },
  "özlük": {
    label: "Çalışan Özlük Dosyası",
    dayanaklar: [
      { value: "5510 sayılı SGK Kanunu", label: "5510 sayılı SGK Kanunu", days: 3650, hours: 0 },
    ]
  },
  "sağlık": {
    label: "Sağlık / Meslek Hastalığı Verisi",
    dayanaklar: [
      { value: "İSG Hizmetleri Yönetmeliği", label: "İSG Hizmetleri Yönetmeliği", days: 5475, hours: 0 },
    ]
  },
  "finansal": {
    label: "Finansal / Muhasebe",
    dayanaklar: [
      { value: "6098 sayılı Türk Borçlar Kanunu", label: "6098 sayılı TBK", days: 3650, hours: 0 },
      { value: "Ulusal vergi mevzuatı (AB ülkeleri)", label: "GDPR Vergi Mevzuatı (AB)", days: 2555, hours: 0 },
    ]
  },
  "sözleşme": {
    label: "Sözleşme",
    dayanaklar: [
      { value: "6098 sayılı Türk Borçlar Kanunu", label: "6098 sayılı TBK", days: 3650, hours: 0 },
    ]
  },
  "müşteri_iletişim": {
    label: "Müşteri İletişim Kaydı",
    dayanaklar: [
      { value: "Ticari İletişim ve Aracılar Yönetmeliği", label: "Ticari İletişim Yönetmeliği", days: 365, hours: 0 },
    ]
  },
  "aday_cv": {
    label: "Aday CV",
    dayanaklar: [
      { value: "GDPR Madde 5 — depolama sınırlaması", label: "GDPR Madde 5", days: 180, hours: 0 },
    ]
  },
  "erişim_logu": {
    label: "Erişim Logu",
    dayanaklar: [
      { value: "KVKK md. 7", label: "KVKK Madde 7", days: 730, hours: 0 },
    ]
  },
  "geçici": {
    label: "Geçici Operasyonel Veri",
    dayanaklar: [
      { value: "KVKK md. 7", label: "KVKK Madde 7", days: 30, hours: 0 },
    ]
  },
};

export default function NewRecord({ onSuccess }) {
  const [form, setForm] = useState({
    name: "",
    department: "",
    category: "",
    legal_basis: "",
    start_date: new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16),
    retention_days: "",
    retention_hours: "",
  });
  const [filePath, setFilePath] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [maxDays, setMaxDays] = useState(null);
  const [maxHours, setMaxHours] = useState(null);
  const [isPolicy, setIsPolicy] = useState(false);
  const [maliYilBaz, setMaliYilBaz] = useState(false);

  const selectedCategory = CATEGORY_MAP[form.category];
  const availableDayanaklar = selectedCategory
    ? [
        ...selectedCategory.dayanaklar,
        { value: "Şirket Politikası", label: "Şirket Politikası", days: null, hours: null },
      ]
    : [];

  const handleCategoryChange = (e) => {
    setForm({ ...form, category: e.target.value, legal_basis: "", retention_days: "", retention_hours: "" });
    setMaxDays(null);
    setMaxHours(null);
    setIsPolicy(false);
    setMaliYilBaz(false);
  };

  const handleDayanakChange = (e) => {
    const val = e.target.value;
    const cat = CATEGORY_MAP[form.category];
    if (!cat) return;

    if (val === "Şirket Politikası") {
      const legalMax = cat.dayanaklar[0];
      setMaxDays(legalMax.days);
      setMaxHours(legalMax.hours);
      setIsPolicy(true);
      setMaliYilBaz(false);
      setForm({ ...form, legal_basis: val, retention_days: "", retention_hours: "" });
    } else {
      const found = cat.dayanaklar.find(d => d.value === val);
      if (found) {
        setMaxDays(found.days);
        setMaxHours(found.hours);
        setIsPolicy(false);
        setMaliYilBaz(false);
        setForm({ ...form, legal_basis: val, retention_days: found.days, retention_hours: found.hours });
      }
    }
  };

  const handleDaysChange = (e) => {
    const val = parseInt(e.target.value) || 0;
    if (maxDays !== null) {
      const clampedDays = Math.min(val, maxDays);
      setForm({ ...form, retention_days: clampedDays });
    } else {
      setForm({ ...form, retention_days: val });
    }
  };

  const handleHoursChange = (e) => {
    const val = parseInt(e.target.value) || 0;
    const currentDays = parseInt(form.retention_days) || 0;
    // Toplam süre maksimumu aşmamalı
    if (maxDays !== null) {
      const totalMaxHours = maxDays * 24 + (maxHours || 0);
      const currentHours = currentDays * 24 + val;
      if (currentHours > totalMaxHours) return;
    }
    setForm({ ...form, retention_hours: Math.min(val, 23) });
  };

  const totalHours = () => (parseInt(form.retention_days) || 0) * 24 + (parseInt(form.retention_hours) || 0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (totalHours() < 1) {
      setError("Toplam saklama süresi en az 1 saat olmalıdır.");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("name", form.name);
      formData.append("department", form.department);
      formData.append("category", form.category);
      formData.append("legal_basis", form.legal_basis);
      formData.append("start_date", form.start_date);
      formData.append("retention_days", parseInt(form.retention_days) || 0);
      formData.append("retention_hours", parseInt(form.retention_hours) || 0);
      formData.append("mali_yil_baz", maliYilBaz ? "true" : "false");
      if (filePath) formData.append("file_path_only", filePath);

      await axios.post("http://localhost:8000/records/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || "Kayıt oluşturulamadı.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Yeni Veri Kaydı</h1>
        <p>Sisteme yeni bir veri varlığı ekle</p>
      </div>

      <div className="card form-card">
        {error && <div className="error-box">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-grid">

            <div className="form-group">
              <label>Veri Adı</label>
              <input name="name" value={form.name} onChange={e => setForm({...form, name: e.target.value})}
                placeholder="Örn: Çalışan Özlük Dosyası 2024" required />
            </div>

            <div className="form-group">
              <label>Departman</label>
              <input name="department" value={form.department} onChange={e => setForm({...form, department: e.target.value})}
                placeholder="Örn: İnsan Kaynakları" required />
            </div>

            {/* Kategori */}
            <div className="form-group">
              <label>Veri Kategorisi</label>
              <select value={form.category} onChange={handleCategoryChange} required>
                <option value="">Seçiniz...</option>
                {Object.entries(CATEGORY_MAP).map(([key, cat]) => (
                  <option key={key} value={key}>{cat.label}</option>
                ))}
              </select>
            </div>

            {/* Yasal Dayanak — kategori seçilince açılır */}
            <div className="form-group">
              <label>Yasal Dayanak</label>
              <select value={form.legal_basis} onChange={handleDayanakChange} required disabled={!form.category}>
                <option value="">Önce kategori seçiniz...</option>
                {availableDayanaklar.map(d => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
              {isPolicy && maxDays && (
                <small className="form-hint">
                  Şirket politikası yasal maksimumu aşamaz: {maxDays} gün
                </small>
              )}
            </div>

            <div className="form-group">
              <label>Sisteme Giriş Tarihi ve Saati</label>
              <input type="datetime-local" name="start_date" value={form.start_date}
                onChange={e => setForm({...form, start_date: e.target.value})} required />

            </div>

            {/* Saklama Süresi */}
            <div className="form-group">
              <label>
                Saklama Süresi
                {maxDays !== null && (
                  <span style={{color:"var(--text-dim)", fontWeight:400, marginLeft:"8px"}}>
                    (maks: {maxDays} gün)
                  </span>
                )}
              </label>
              <div className="duration-row">
                <div className="duration-input">
                  <input type="number" value={form.retention_days} onChange={handleDaysChange}
                    placeholder="0" min="0" max={maxDays || undefined}
                    disabled={!form.legal_basis} />
                  <span className="duration-unit">gün</span>
                </div>
                {!maliYilBaz && (
                  <div className="duration-input">
                    <input type="number" value={form.retention_hours} onChange={handleHoursChange}
                      placeholder="0" min="0" max="23"
                      disabled={!form.legal_basis} />
                    <span className="duration-unit">saat</span>
                  </div>
                )}
              </div>
              {totalHours() > 0 && (
                <div className="duration-preview">
                  Toplam: <strong>{totalHours()} saat</strong>
                  {maxDays !== null && (
                    <span style={{color: totalHours() === maxDays * 24 ? "var(--green)" : "var(--text-dim)"}}>
                      {" "}/ maks {maxDays * 24} saat
                    </span>
                  )}
                </div>
              )}
              {MALI_YIL_KATEGORILER.includes(form.category) && form.legal_basis && (
                <div style={{marginTop:"8px", display:"flex", alignItems:"center", gap:"8px", flexWrap:"wrap"}}>
                  <button
                    type="button"
                    onClick={() => setMaliYilBaz(!maliYilBaz)}
                    style={{
                      background: maliYilBaz ? "rgba(79,142,247,0.2)" : "rgba(79,142,247,0.08)",
                      border: maliYilBaz ? "1px solid var(--accent)" : "1px solid rgba(79,142,247,0.3)",
                      color:"var(--accent)", padding:"4px 12px", borderRadius:"5px",
                      fontSize:"11px", cursor:"pointer", fontFamily:"var(--font)",
                      fontWeight: maliYilBaz ? 600 : 400,
                    }}
                  >
                    {maliYilBaz ? "✓ Mali Yıl Sonu Baz Alındı" : "Mali Yıl Sonu Baz Al"}
                  </button>
                  <small style={{color:"var(--text-dim)", fontSize:"10px"}}>
                    {maliYilBaz
                      ? `İmha tarihi 31 Aralık ${new Date().getFullYear()} tarihinden itibaren hesaplanacak`
                      : "Açılırsa süre belge tarihinden değil, mali yıl kapanışından (31 Aralık) başlar"}
                  </small>
                </div>
              )}
            </div>

          </div>

          {/* Dosya Path */}
          <div className="form-group file-group">
            <label>İlgili Dosyanın Yolu (İsteğe Bağlı)</label>
            <input type="text" value={filePath} onChange={e => setFilePath(e.target.value)}
              placeholder="Örn: C:\Users\kullanici\Belgeler\dosya.pdf" />
            <small className="form-hint">
              Dosya sisteme yüklenmez — path kaydedilir, imha edilince orijinal yerinden silinir.
            </small>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={loading || !form.legal_basis}>
              {loading ? "Kaydediliyor..." : "Kayıt Oluştur"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
