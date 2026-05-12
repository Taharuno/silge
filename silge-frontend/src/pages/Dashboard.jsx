import { useEffect, useState, useRef } from "react";
import { getDashboard } from "../api";

function DonutChart({ data, total }) {
  const [hovered, setHovered] = useState(null);
  const cx = 100, cy = 100, r = 70, stroke = 28;
  const circumference = 2 * Math.PI * r;

  const segments = [
    { label: "Güvende", value: data.yesil, color: "#2ecc71" },
    { label: "Uyarı", value: data.sari, color: "#f1c40f" },
    { label: "Onay Bekliyor", value: data.kirmizi, color: "#e74c3c" },
  ];

  let offset = 0;
  const arcs = segments.map((seg) => {
    const pct = total > 0 ? seg.value / total : 0;
    const dash = pct * circumference;
    const gap = circumference - dash;
    const arc = { ...seg, dash, gap, offset };
    offset += dash;
    return arc;
  });

  const active = hovered !== null ? segments[hovered] : null;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "32px" }}>
      <svg width="200" height="200" viewBox="0 0 200 200">
        {total === 0 ? (
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="#2a2f42" strokeWidth={stroke} />
        ) : (
          arcs.map((arc, i) => (
            <circle
              key={i}
              cx={cx} cy={cy} r={r}
              fill="none"
              stroke={arc.color}
              strokeWidth={hovered === i ? stroke + 4 : stroke}
              strokeDasharray={`${arc.dash} ${arc.gap}`}
              strokeDashoffset={-arc.offset}
              strokeLinecap="butt"
              style={{ cursor: "pointer", transition: "stroke-width 0.15s", transform: "rotate(-90deg)", transformOrigin: "100px 100px" }}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
            />
          ))
        )}
        <text x={cx} y={cy - 8} textAnchor="middle" style={{ fontSize: "28px", fontWeight: 600, fill: active ? active.color : "var(--text)", fontFamily: "var(--mono)" }}>
          {active ? active.value : total}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle" style={{ fontSize: "11px", fill: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
          {active ? active.label : "aktif"}
        </text>
      </svg>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {segments.map((seg, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer", opacity: hovered !== null && hovered !== i ? 0.4 : 1, transition: "opacity 0.15s" }}
            onMouseEnter={() => setHovered(i)}
            onMouseLeave={() => setHovered(null)}>
            <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: seg.color, flexShrink: 0 }} />
            <span style={{ fontSize: "13px", color: "var(--text-dim)", flex: 1 }}>{seg.label}</span>
            <span style={{ fontFamily: "var(--mono)", fontSize: "14px", fontWeight: 500, color: "var(--text)" }}>{seg.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Dashboard({ onNavigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const dataRef = useRef(null);

  const fetchData = () => {
    getDashboard()
      .then((res) => {
        dataRef.current = res.data;
        setData({ ...res.data });
      })
      .catch(() => setError("API'ye bağlanılamadı. Backend çalışıyor mu?"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="loading">Yükleniyor...</div>;
  if (error) return <div className="error-box">{error}</div>;

  const { ozet, renk_dagilimi, kritiklik_dagilimi, departman_ozeti, yaklasan_imhalar } = data;

  return (
    <div className="dashboard">
      {/* Başlık + Donut yan yana */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "32px" }}>
        <div className="page-header">
          <h1>Dashboard</h1>
          <p>Veri envanterinizin anlık durumu</p>
        </div>
        <div className="card" style={{ flexShrink: 0 }}>
          <h2>Durum Dağılımı</h2>
          <DonutChart data={renk_dagilimi} total={ozet.aktif + renk_dagilimi.kirmizi} />
        </div>
      </div>

      {/* Acil Uyarı Banner */}
      {renk_dagilimi.kirmizi > 0 ? (
        <div style={{
          background: "rgba(231,76,60,0.1)",
          border: "1px solid rgba(231,76,60,0.4)",
          borderLeft: "4px solid #e74c3c",
          borderRadius: "8px",
          padding: "16px 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <span style={{ fontSize: "22px" }}>⚠</span>
            <div>
              <div style={{ fontWeight: 600, color: "#e74c3c", fontSize: "14px" }}>
                {renk_dagilimi.kirmizi} kayıt imha onayı bekliyor
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-dim)", marginTop: "2px" }}>
                Saklama süresi dolmuş veriler için imha onayı verilmesi gerekiyor.
              </div>
            </div>
          </div>
          <button className="btn-danger" onClick={() => onNavigate("records")} style={{ whiteSpace: "nowrap", flexShrink: 0 }}>
            Kayıtlara Git →
          </button>
        </div>
      ) : (
        <div style={{
          background: "rgba(46,204,113,0.07)",
          border: "1px solid rgba(46,204,113,0.25)",
          borderLeft: "4px solid #2ecc71",
          borderRadius: "8px",
          padding: "16px 20px",
          display: "flex",
          alignItems: "center",
          gap: "14px",
        }}>
          <span style={{ fontSize: "22px" }}>✓</span>
          <div>
            <div style={{ fontWeight: 600, color: "#2ecc71", fontSize: "14px" }}>
              Tüm kayıtlar kontrol altında
            </div>
            <div style={{ fontSize: "12px", color: "var(--text-dim)", marginTop: "2px" }}>
              Onay bekleyen veri yok. Sistem normal çalışıyor.
            </div>
          </div>
        </div>
      )}

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{ozet.toplam}</div>
          <div className="stat-label">Toplam Kayıt</div>
        </div>
        <div className="stat-card green">
          <div className="stat-value">{renk_dagilimi.yesil}</div>
          <div className="stat-label">Güvende</div>
        </div>
        <div className="stat-card yellow">
          <div className="stat-value">{renk_dagilimi.sari}</div>
          <div className="stat-label">Uyarı (30 gün)</div>
        </div>
        <div className="stat-card red">
          <div className="stat-value">{renk_dagilimi.kirmizi}</div>
          <div className="stat-label">Onay Bekliyor</div>
        </div>
        <div className="stat-card gray">
          <div className="stat-value">{ozet.arsivlendi}</div>
          <div className="stat-label">Arşivlendi</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <div className="card">
          <h2>Kritiklik Dağılımı</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {[
              { label: "Kritik", value: kritiklik_dagilimi.kritik, color: "#e74c3c" },
              { label: "Orta", value: kritiklik_dagilimi.orta, color: "#f39c12" },
              { label: "Düşük", value: kritiklik_dagilimi.dusuk, color: "#27ae60" },
            ].map((item) => {
              const total = (kritiklik_dagilimi.kritik + kritiklik_dagilimi.orta + kritiklik_dagilimi.dusuk) || 1;
              return (
                <div key={item.label} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <span style={{ width: "50px", fontSize: "12px", color: "var(--text-dim)" }}>{item.label}</span>
                  <div style={{ flex: 1, height: "6px", background: "#1e2333", borderRadius: "3px", overflow: "hidden" }}>
                    <div style={{ width: `${(item.value / total) * 100}%`, height: "100%", background: item.color, borderRadius: "3px" }} />
                  </div>
                  <span style={{ width: "20px", textAlign: "right", fontSize: "12px", color: "var(--text-dim)" }}>{item.value}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="card">
          <h2>Departman Özeti</h2>
          {Object.keys(departman_ozeti).length === 0 ? (
            <p className="empty-text">Henüz kayıt yok.</p>
          ) : (
            <table className="dept-table">
              <thead>
                <tr>
                  <th>Departman</th>
                  <th>Toplam</th>
                  <th>Onay Bekliyor</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(departman_ozeti).map(([dept, info]) => (
                  <tr key={dept}>
                    <td>{dept}</td>
                    <td>{info.toplam}</td>
                    <td>
                      {info.onay_bekliyor > 0 ? (
                        <span className="badge red">{info.onay_bekliyor}</span>
                      ) : (
                        <span className="badge green">0</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="card">
        <h2>Yaklaşan İmhalar</h2>
        {yaklasan_imhalar.length === 0 ? (
          <p className="empty-text">Yaklaşan imha yok.</p>
        ) : (
          <table className="records-table">
            <thead>
              <tr>
                <th>Veri Adı</th>
                <th>Departman</th>
                <th>Kritiklik</th>
                <th>İmha Tarihi</th>
                <th>Kalan Süre</th>
              </tr>
            </thead>
            <tbody>
              {yaklasan_imhalar.map((r) => (
                <tr key={r.id}>
                  <td>{r.name}</td>
                  <td>{r.department}</td>
                  <td>
                    <span className={`badge ${r.criticality === "kritik" ? "red" : r.criticality === "orta" ? "yellow" : "green"}`}>
                      {r.criticality}
                    </span>
                  </td>
                  <td>{r.expiry_date}</td>
                  <td>
                    <span className={r.hours_remaining <= 720 ? "days urgent" : "days"}>
                      {r.remaining_label}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>


    </div>
  );
}
