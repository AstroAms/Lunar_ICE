from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import datetime
import io

def generate_pdf_report(mission_data, output_path="reports/mission_report.pdf"):
    """Generate a professional PDF mission report."""
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=22,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#4a4a4a'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#1a237e'),
        spaceBefore=16,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leading=16
    )
    
    story = []
    
    # Header
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("ISRO BHARATIYA ANTARIKSH HACKATHON", subtitle_style))
    story.append(Paragraph("LUNAR ICE MISSION PLANNER", title_style))
    story.append(Paragraph("Automated Mission Analysis Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a237e')))
    story.append(Spacer(1, 0.2*inch))
    
    # Mission info table
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    info_data = [
        ['Mission Date', now],
        ['Target Region', mission_data.get('region', 'Lunar South Pole')],
        ['Instruments Used', 'DFSAR (Radar) + OHRC (Imaging)'],
        ['Mission Status', 'ANALYSIS COMPLETE'],
    ]
    
    info_table = Table(info_data, colWidths=[5*cm, 11*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0,0), (0,-1), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (1,0), (1,-1), [colors.HexColor('#f5f5f5'), colors.white]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    # 1. Abstract
    story.append(Paragraph("1. ABSTRACT", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#1a237e')))
    story.append(Paragraph(
        "This report presents the results of an automated lunar ice detection and mission planning "
        "analysis conducted using Chandrayaan-2 DFSAR radar data and OHRC high-resolution imagery. "
        "The analysis pipeline computes Circular Polarization Ratio (CPR) and Degree of Polarization (DOP) "
        "to identify potential water-ice deposits in permanently shadowed regions near the lunar south pole. "
        "A safe landing site and optimized rover path to the ice deposits are subsequently computed.",
        body_style
    ))
    
    # 2. Ice Detection Results
    story.append(Paragraph("2. ICE DETECTION RESULTS", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#1a237e')))
    
    ice = mission_data.get('ice', {})
    ice_data = [
        ['Parameter', 'Value', 'Interpretation'],
        ['CPR Threshold', f"{mission_data.get('cpr_threshold', 1.0):.2f}", 'Values > 1.0 indicate ice'],
        ['DOP Threshold', f"{mission_data.get('dop_threshold', 0.3):.2f}", 'Values < 0.3 suggest ice'],
        ['Ice-Positive Pixels', f"{ice.get('ice_pixels', 0):,}", 'Pixels exceeding thresholds'],
        ['Estimated Ice Area', f"{ice.get('ice_area_km2', 0):.3f} km²", 'Surface area of ice deposits'],
        ['Estimated Ice Volume', f"{ice.get('ice_volume_m3', 0):,.0f} m³", 'Volume at 2m depth assumption'],
        ['Water Equivalent', f"{ice.get('water_mass_tonnes', 0):,.0f} tonnes", 'Potential water resource'],
    ]
    
    ice_table = Table(ice_data, colWidths=[6*cm, 5*cm, 5*cm])
    ice_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 7),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f0f4ff'), colors.white]),
    ]))
    story.append(ice_table)
    story.append(Spacer(1, 0.2*inch))
    
    # 3. Landing Site
    story.append(Paragraph("3. LANDING SITE ANALYSIS", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#1a237e')))
    
    ls = mission_data.get('landing_site', {})
    landing_data = [
        ['Parameter', 'Value', 'Safety Criterion'],
        ['Grid Position (Row, Col)', f"({ls.get('row',0)}, {ls.get('col',0)})", 'Best scored location'],
        ['Site Safety Score', f"{ls.get('score', 0)*100:.1f}%", 'Higher is better'],
        ['Slope at Site', f"{ls.get('slope_at_site', 0):.1f}°", 'Must be < 15°'],
        ['Hazard Level', f"{ls.get('hazard_at_site', 0):.3f}", 'Must be < 0.7'],
        ['Landing Assessment', 'APPROVED' if ls.get('score',0) > 0.4 else 'MARGINAL', 'Mission go/no-go'],
    ]
    
    lt = Table(landing_data, colWidths=[6*cm, 4*cm, 6*cm])
    lt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 7),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f0f4ff'), colors.white]),
    ]))
    story.append(lt)
    story.append(Spacer(1, 0.2*inch))
    
    # 4. Rover Path
    story.append(Paragraph("4. ROVER PATH PLANNING", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#1a237e')))
    
    rp = mission_data.get('rover_path', {})
    rover_data = [
        ['Parameter', 'Value'],
        ['Path Algorithm', 'A* (Optimal Pathfinding)'],
        ['Total Distance', f"{rp.get('distance_km', 0):.3f} km"],
        ['Distance (meters)', f"{rp.get('distance_m', 0):.1f} m"],
        ['Average Slope', f"{rp.get('avg_slope', 0):.1f}°"],
        ['Path Waypoints', f"{rp.get('waypoints', 0)}"],
        ['Estimated Traverse Time', f"{rp.get('distance_m', 0)/0.1/3600:.1f} hours (at 0.1 m/s)"],
    ]
    
    rt = Table(rover_data, colWidths=[8*cm, 8*cm])
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 7),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f0f4ff'), colors.white]),
    ]))
    story.append(rt)
    story.append(Spacer(1, 0.2*inch))
    
    # 5. Mission Score
    story.append(Paragraph("5. MISSION SUCCESS ASSESSMENT", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#1a237e')))
    
    ms = mission_data.get('mission_score', 85)
    story.append(Paragraph(
        f"Overall Mission Success Probability: <b>{ms:.1f}%</b><br/><br/>"
        f"This score is computed from four weighted components: ice detection confidence (35%), "
        f"landing site safety (30%), rover path feasibility (20%), and resource value assessment (15%). "
        f"A score above 70% is considered mission-viable.",
        body_style
    ))
    
    # 6. Methodology
    story.append(Paragraph("6. METHODOLOGY", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#1a237e')))
    story.append(Paragraph(
        "<b>Step 1 — Radar Processing (DFSAR):</b> The DFSAR compact polarimetry data is read and "
        "decomposed into HH and HV polarization channels.<br/><br/>"
        "<b>Step 2 — CPR Calculation:</b> CPR = HV / HH. Regions with CPR > 1.0 are flagged as "
        "potential ice bearing, consistent with findings from Spudis et al. (2013) and ISRO's "
        "Chandrayaan-1 Mini-RF observations.<br/><br/>"
        "<b>Step 3 — DOP Calculation:</b> DOP = (HH - HV) / (HH + HV). Low DOP in permanently "
        "shadowed regions corroborates the ice interpretation.<br/><br/>"
        "<b>Step 4 — Terrain Analysis (OHRC):</b> Slope and roughness maps are derived from the "
        "OHRC imagery gradient to identify safe, flat landing zones.<br/><br/>"
        "<b>Step 5 — Landing Site Selection:</b> A weighted scoring model combines ice proximity, "
        "slope safety, and hazard avoidance to select the optimal landing coordinate.<br/><br/>"
        "<b>Step 6 — Rover Path (A*):</b> The A* algorithm finds the shortest safe path from "
        "the landing site to the ice deposit, penalizing high-slope and high-hazard terrain.",
        body_style
    ))
    
    # Footer
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1a237e')))
    story.append(Paragraph(
        f"Generated by Lunar Ice Mission Planner | Bharatiya Antariksh Hackathon | {now}",
        ParagraphStyle('footer', parent=styles['Normal'], fontSize=8,
                      textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    doc.build(story)
    return output_path