from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import date, datetime
import os

# DejaVu fontunu kaydet — Türkçe karakter desteği
pdfmetrics.registerFont(TTFont("DejaVu", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", "C:/Windows/Fonts/arialbd.ttf"))

FONT = "DejaVu"
FONT_BOLD = "DejaVu-Bold"


def generate_destruction_receipt(record: dict, approver: str) -> str:
    """
    İmha tutanağı PDF'i oluşturur.
    record: DataRecord alanlarını içeren dict
    approver: Onaylayan kişinin adı
    Döndürür: kaydedilen PDF dosyasının yolu
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    TUTANAK_DIR = os.path.join(BASE_DIR, "tutanaklar")
    os.makedirs(TUTANAK_DIR, exist_ok=True)
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(TUTANAK_DIR, f"imha_tutanagi_{record['id']}_{timestamp}.pdf")

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "title",
        fontName=FONT_BOLD,
        fontSize=16,
        alignment=1,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "subtitle",
        fontName=FONT,
        fontSize=10,
        alignment=1,
        textColor=colors.grey,
        spaceAfter=20,
    )
    label_style = ParagraphStyle(
        "label",
        fontName=FONT,
        fontSize=9,
        textColor=colors.grey,
    )
    value_style = ParagraphStyle(
        "value",
        fontName=FONT,
        fontSize=11,
    )
    section_style = ParagraphStyle(
        "section",
        fontName=FONT_BOLD,
        fontSize=11,
        textColor=colors.HexColor("#2c3e50"),
        spaceBefore=16,
        spaceAfter=8,
    )

    story = []

    # Başlık
    story.append(Paragraph("VERİ İMHA TUTANAĞI", title_style))
    story.append(Paragraph("Data Destruction Record", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2c3e50")))
    story.append(Spacer(1, 0.5 * cm))

    # Tutanak bilgileri tablosu
    info_data = [
        ["Tutanak No", f"SLG-{record['id']:04d}-{now.strftime('%Y%m%d%H%M%S')}"],
        ["Oluşturma Tarihi ve Saati", now.strftime("%d.%m.%Y %H:%M:%S")],
        ["Sistem", "Silge — Veri İmha ve Yaşam Döngüsü Takip Sistemi"],
    ]
    info_table = Table(info_data, colWidths=[4 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))

    # Veri Bilgileri
    story.append(Paragraph("VERİ BİLGİLERİ", section_style))

    record_data = [
        ["Veri Adı", record["name"]],
        ["Departman", record["department"]],
        ["Veri Kategorisi", record["category"]],
        ["Kritiklik Düzeyi", record["criticality"].upper()],
        ["Yasal Dayanak", record["legal_basis"]],
        ["Sisteme Giriş Tarihi", str(record["start_date"])],
        ["Saklama Süresi", f"{record['retention_days']} gün {record['retention_hours']} saat"],
        ["İmha Tarihi (Planlanan)", str(record["expiry_date"])],
    ]
    record_table = Table(record_data, colWidths=[5 * cm, 11 * cm])
    record_table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9f9f9")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    story.append(record_table)

    # İmha Onay Bilgileri
    story.append(Paragraph("İMHA ONAY BİLGİLERİ", section_style))

    approval_data = [
        ["İmhayı Onaylayan", approver],
        ["Onay Tarihi ve Saati", now.strftime("%d.%m.%Y %H:%M:%S")],
        ["İmha Yöntemi", "Sistem üzerinden güvenli silme"],
        ["Kayıt Durumu", "ARŞİVLENDİ"],
    ]
    approval_table = Table(approval_data, colWidths=[5 * cm, 11 * cm])
    approval_table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    story.append(approval_table)

    # İmza alanı
    story.append(Spacer(1, 1.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.3 * cm))

    imza_data = [
        ["Onaylayan", "", "Sistem Yöneticisi"],
        [approver, "", "Silge Otomatik Sistem"],
        ["İmza: _______________", "", "Tarih: " + date.today().strftime("%d.%m.%Y")],
    ]
    imza_table = Table(imza_data, colWidths=[6 * cm, 4 * cm, 6 * cm])
    imza_table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.grey),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(imza_table)

    # Yasal not
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.3 * cm))
    legal_note = ParagraphStyle("legal", fontName=FONT, fontSize=8, textColor=colors.grey)
    story.append(Paragraph(
        "Bu tutanak KVKK (6698 sayılı Kanun) ve GDPR kapsamında otomatik olarak üretilmiştir. "
        "Resmi denetimlerde delil niteliği taşır. Silge Veri İmha ve Yaşam Döngüsü Takip Sistemi.",
        legal_note
    ))

    doc.build(story)
    return filename
