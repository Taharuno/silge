import { useEffect, useState, useCallback, useRef } from "react";
import { getRecords, approveDeletion, deleteRecord } from "../api";

const STATUS_LABEL = {
  aktif: "Aktif",
  onay_bekliyor: "Onay Bekliyor",
  arsivlendi: "Arşivlendi",
};

const COLOR_MAP = {
  "yeşil": "green",
  "sarı": "yellow",
  "kırmızı": "red",
};

export default function Records() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ department: "", status: "", criticality: "" });
  const [tick, setTick] = useState(0);

  const fetchRecords = useCallback(() => {
    const params = {};
    if (filters.department) params.department = filters.department;
    if (filters.status) params.status = filters.status;
    if (filters.criticality) params.criticality = filters.criticality;
    getRecords(params)
      .then((res) => {
        setRecords(res.data);
        setTick(t => t + 1); // React'ı zorla render et
      })
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => {
    setLoading(true);
    fetchRecords();
    const interval = setInterval(fetchRecords, 30000);
    return () => clearInterval(interval);
  }, [fetchRecords]);

  const handleApprove = async (id) => {
    const approver = prompt("Onaylayan kişinin adı:");
    if (!approver) return;
    try {
      await approveDeletion(id, approver);
      alert("✓ İmha onaylandı. Tutanak oluşturuldu.");
      fetchRecords();
    } catch {
      alert("Hata oluştu.");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Bu kaydı ve ilişkili dosyayı silmek istediğinize emin misiniz?")) return;
    const performedBy = prompt("Silen kişinin adı:") || "Bilinmiyor";
    try {
      await deleteRecord(id, performedBy);
      fetchRecords();
    } catch {
      alert("Silme işlemi başarısız.");
    }
  };

  const handleDownload = (id) => {
    window.open(`http://localhost:8000/records/${id}/tutanak`, "_blank");
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Veri Kayıtları</h1>
        <p>Tüm veri varlıklarını görüntüle ve yönet</p>
      </div>

      <div className="filter-bar">
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">Tüm Durumlar</option>
          <option value="aktif">Aktif</option>
          <option value="onay_bekliyor">Onay Bekliyor</option>
          <option value="arsivlendi">Arşivlendi</option>
        </select>
        <select value={filters.criticality} onChange={(e) => setFilters({ ...filters, criticality: e.target.value })}>
          <option value="">Tüm Kritiklikler</option>
          <option value="kritik">Kritik</option>
          <option value="orta">Orta</option>
          <option value="düşük">Düşük</option>
        </select>
        <input
          type="text"
          placeholder="Departman filtrele..."
          value={filters.department}
          onChange={(e) => setFilters({ ...filters, department: e.target.value })}
        />
      </div>

      {loading ? (
        <div className="loading">Yükleniyor...</div>
      ) : records.length === 0 ? (
        <div className="empty-box">Kayıt bulunamadı.</div>
      ) : (
        <div className="card">
          <table className="records-table">
            <thead>
              <tr>
                <th>Veri Adı</th>
                <th>Departman</th>
                <th>Kategori</th>
                <th>Dosya</th>
                <th>Kritiklik</th>
                <th>İmha Tarihi</th>
                <th>Kalan Süre</th>
                <th>Durum</th>
                <th>İşlem</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={`${r.id}-${tick}`}>
                  <td><strong>{r.name}</strong></td>
                  <td>{r.department}</td>
                  <td>{r.category}</td>
                  <td>
                    {r.file_name ? (
                      <div>
                        <span className="file-badge">{r.file_name}</span>
                        <div style={{fontSize:"10px", color:"var(--text-dim)", marginTop:"2px", maxWidth:"160px", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap"}} title={r.file_path}>
                          {r.file_path}
                        </div>
                      </div>
                    ) : (
                      <span className="no-file">—</span>
                    )}
                  </td>
                  <td>
                    <span className={`badge ${r.criticality === "kritik" ? "red" : r.criticality === "orta" ? "yellow" : "green"}`}>
                      {r.criticality}
                    </span>
                  </td>
                  <td>{r.expiry_date}</td>
                  <td>
                    <span className={`dot ${COLOR_MAP[r.color_status] || "green"}`} />
                    {r.remaining_label}
                  </td>
                  <td>
                    <span className={`status-badge ${r.status === "onay_bekliyor" ? "red" : r.status === "arsivlendi" ? "gray" : "green"}`}>
                      {STATUS_LABEL[r.status]}
                    </span>
                  </td>
                  <td className="action-cell">
                    <button className="btn-delete" onClick={() => handleDelete(r.id)} title="Kaydı Sil">✕</button>
                    {r.status === "onay_bekliyor" && (
                      <button className="btn-danger" onClick={() => handleApprove(r.id)}>
                        İmhayı Onayla
                      </button>
                    )}
                    {r.status === "arsivlendi" && (
                      <button className="btn-download" onClick={() => handleDownload(r.id)}>
                        ↓ Tutanak
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
