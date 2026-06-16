from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie

from app.database.db import get_db
from app.database.models import Video, VehicleEvent, AccidentEvent

router = APIRouter(prefix="/reports", tags=["Reports"])

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

# Usable page width: A4 (8.27in) minus left+right margins (1in each) = 6.27in
PAGE_WIDTH = 6.27 * inch


def create_pie_chart(data, labels):
    """Create a pie chart for vehicle distribution"""
    drawing = Drawing(200, 200)

    pie = Pie()
    pie.x = 25
    pie.y = 25
    pie.width = 150
    pie.height = 150

    non_zero_labels = []
    non_zero_data = []
    for label, value in zip(labels, data):
        if value > 0:
            non_zero_labels.append(f"{label} ({value})")
            non_zero_data.append(value)

    if non_zero_data:
        pie.data = non_zero_data
        pie.labels = non_zero_labels
    else:
        pie.data = [1]
        pie.labels = ["No Data"]

    colors_list = [
        colors.HexColor('#8B5CF6'),
        colors.HexColor('#F97316'),
        colors.HexColor('#F59E0B'),
        colors.HexColor('#6366F1'),
    ]

    for i in range(len(pie.data)):
        if i < len(colors_list):
            pie.slices[i].fillColor = colors_list[i]
        pie.slices[i].strokeWidth = 0.5
        pie.slices[i].strokeColor = colors.white
        pie.slices[i].fontName = 'Helvetica'
        pie.slices[i].fontSize = 8
        pie.slices[i].labelRadius = 1.2

    drawing.add(pie)
    return drawing


@router.get("/pdf/{video_id}")
def export_pdf_report(
    video_id: int,
    db: Session = Depends(get_db),
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    total_vehicles = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id).count()
    incoming     = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.direction == "incoming").count()
    outgoing     = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.direction == "outgoing").count()
    cars         = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.vehicle_type == "car").count()
    trucks       = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.vehicle_type == "truck").count()
    buses        = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.vehicle_type == "bus").count()
    motorcycles  = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.vehicle_type == "motorcycle").count()
    accidents    = db.query(AccidentEvent).filter(AccidentEvent.video_id == video_id).count()

    density_percentage = (total_vehicles / 500) * 100 if total_vehicles > 0 else 0
    if density_percentage > 70:
        density_level = "High"
    elif density_percentage > 40:
        density_level = "Medium"
    else:
        density_level = "Low"

    file_path = REPORT_DIR / f"traffic_report_video_{video_id}.pdf"

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=72, leftMargin=72,
        topMargin=72,   bottomMargin=72,
    )

    styles = getSampleStyleSheet()

    # ── Styles ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=20, textColor=colors.HexColor('#1E293B'),
        alignment=TA_CENTER, spaceAfter=6, fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle', parent=styles['Heading2'],
        fontSize=14, textColor=colors.HexColor('#475569'),
        alignment=TA_CENTER, spaceAfter=15, fontName='Helvetica'
    )
    section_title_style = ParagraphStyle(
        'SectionTitle', parent=styles['Heading3'],
        fontSize=14, textColor=colors.HexColor('#1E293B'),
        spaceAfter=8, spaceBefore=12, fontName='Helvetica-Bold'
    )
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#94A3B8'),
        alignment=TA_CENTER, fontName='Helvetica'
    )

    # ── Shared table style ────────────────────────────────────────────────────
    base_table_style = TableStyle([
        ('FONTNAME',      (0, 0), (-1,  0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1,  0), 10),
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 9),
        ('BACKGROUND',    (0, 0), (-1,  0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR',     (0, 0), (-1,  0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR',     (0, 1), (-1, -1), colors.HexColor('#0F172A')),
        ('ALIGN',         (0, 0), (0,  -1), 'LEFT'),
        ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
    ])

    content = []

    # ── Header ────────────────────────────────────────────────────────────────
    content.append(Paragraph("SMART TRAFFIC INTELLIGENCE SYSTEM", title_style))
    content.append(Paragraph("Traffic Analytics Report", subtitle_style))
    content.append(Spacer(1, 8))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0')))
    content.append(Spacer(1, 8))

    # ── Video Information ─────────────────────────────────────────────────────
    info_data = [
        ["Video ID:", str(video.id), "Filename:", video.filename],
        ["Road Type:", "Two Way", "Generated:", datetime.now().strftime('%d %b %Y, %I:%M:%S %p')],
    ]
    info_table = Table(info_data, colWidths=[1.1*inch, 1.77*inch, 1.1*inch, 2.3*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('TEXTCOLOR',     (0, 0), (0,  -1), colors.HexColor('#64748B')),
        ('TEXTCOLOR',     (2, 0), (2,  -1), colors.HexColor('#64748B')),
        ('TEXTCOLOR',     (1, 0), (1,  -1), colors.HexColor('#0F172A')),
        ('TEXTCOLOR',     (3, 0), (3,  -1), colors.HexColor('#0F172A')),
        ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
    ]))

    content.append(KeepTogether([
        Paragraph("Video Information", section_title_style),
        info_table,
        Spacer(1, 12),
    ]))

    # ── Traffic Summary ───────────────────────────────────────────────────────
    summary_data = [
        ["Metric",         "Value",                                        "Status"],
        ["Total Vehicles", str(total_vehicles),                            ""],
        ["Incoming",       str(incoming),                                  "↑"],
        ["Outgoing",       str(outgoing),                                  "↓"],
        ["Density",        f"{density_level} ({density_percentage:.0f}%)", "●"],
        ["Accidents",      str(accidents),                                 "⚠" if accidents > 0 else "✓"],
    ]
    summary_table = Table(summary_data, colWidths=[2.77*inch, 2*inch, 1.5*inch])
    summary_table.setStyle(base_table_style)

    content.append(KeepTogether([
        Paragraph("Traffic Summary", section_title_style),
        summary_table,
        Spacer(1, 12),
    ]))

    # ── Vehicle Classification ────────────────────────────────────────────────
    total = cars + trucks + buses + motorcycles
    vehicle_labels = ['Cars', 'Trucks', 'Buses', 'Motorcycles']
    vehicle_counts = [cars, trucks, buses, motorcycles]

    vehicle_data = [["Type", "Count", "Percentage"]]
    has_vehicles = False
    for label, count in zip(vehicle_labels, vehicle_counts):
        if count > 0:
            pct = f"{((count / total) * 100):.1f}%" if total > 0 else "0%"
            vehicle_data.append([label, str(count), pct])
            has_vehicles = True
    if not has_vehicles:
        vehicle_data.append(["No vehicles detected", "0", "0%"])

    # Inner table fits inside 3.77in left cell
    vehicle_table = Table(vehicle_data, colWidths=[1.6*inch, 1*inch, 1*inch])
    vehicle_table.setStyle(base_table_style)

    if total > 0:
        pie_chart = create_pie_chart(vehicle_counts, vehicle_labels)
        combined_table = Table([[vehicle_table, pie_chart]], colWidths=[3.77*inch, 2.5*inch])
        combined_table.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',         (0, 0), (0,   0), 'LEFT'),
            ('ALIGN',         (1, 0), (1,   0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('LEFTPADDING',   (1, 0), (1,   0), 10),
        ]))
        classification_content = combined_table
    else:
        classification_content = vehicle_table

    content.append(KeepTogether([
        Paragraph("Vehicle Classification", section_title_style),
        classification_content,
        Spacer(1, 12),
    ]))

    # ── Safety Monitoring ─────────────────────────────────────────────────────
    accident_status = "✓ Safe" if accidents == 0 else f"⚠ {accidents} incident(s)"
    accident_action = "No action needed" if accidents == 0 else "Investigate immediately"

    density_status = (
        "✓ Normal"    if density_level == "Low"    else
        "⚠ Monitor"   if density_level == "Medium" else
        "⚠ High Alert"
    )
    density_action = (
        "Normal"          if density_level == "Low"    else
        "Monitor traffic" if density_level == "Medium" else
        "Take action"
    )

    flow_status = "✓ Balanced" if abs(incoming - outgoing) < 50 else "⚠ Imbalanced"
    flow_action = "Normal"     if abs(incoming - outgoing) < 50 else "Review traffic flow"

    safety_data = [
        ["Metric",       "Status",        "Action Required"],
        ["Accidents",    accident_status, accident_action],
        ["Density",      density_status,  density_action],
        ["Traffic Flow", flow_status,     flow_action],
    ]

    safety_table = Table(safety_data, colWidths=[2*inch, 2.27*inch, 2*inch])
    safety_table.setStyle(base_table_style)

    if accidents > 0:
        safety_table.setStyle(TableStyle([('BACKGROUND', (1,1),(1,1), colors.HexColor('#FEE2E2')),
                                          ('TEXTCOLOR',  (1,1),(1,1), colors.HexColor('#DC2626'))]))
    else:
        safety_table.setStyle(TableStyle([('BACKGROUND', (1,1),(1,1), colors.HexColor('#DCFCE7')),
                                          ('TEXTCOLOR',  (1,1),(1,1), colors.HexColor('#16A34A'))]))

    if density_level == "High":
        safety_table.setStyle(TableStyle([('BACKGROUND', (1,2),(1,2), colors.HexColor('#FEE2E2')),
                                          ('TEXTCOLOR',  (1,2),(1,2), colors.HexColor('#DC2626'))]))
    elif density_level == "Medium":
        safety_table.setStyle(TableStyle([('BACKGROUND', (1,2),(1,2), colors.HexColor('#FEF3C7')),
                                          ('TEXTCOLOR',  (1,2),(1,2), colors.HexColor('#D97706'))]))

    # KeepTogether keeps the heading + all rows on the same page
    content.append(KeepTogether([
        Paragraph("Safety Monitoring", section_title_style),
        safety_table,
        Spacer(1, 15),
    ]))

    # ── Footer ────────────────────────────────────────────────────────────────
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0')))
    content.append(Spacer(1, 8))
    content.append(Paragraph(
        "<b>Generated by Smart Traffic Intelligence System</b><br/>"
        "Final Year Project - Muhammad Usman Ali | University of Management and Technology (UMT)",
        footer_style
    ))
    content.append(Spacer(1, 4))
    content.append(Paragraph("Page 1", footer_style))

    doc.build(content)

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"traffic_report_video_{video_id}.pdf",
    )