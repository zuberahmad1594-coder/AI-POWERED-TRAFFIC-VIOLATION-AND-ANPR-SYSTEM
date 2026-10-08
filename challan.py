import os
import sqlite3
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

VIOLATION_INFO = {
    "NO_HELMET": {
        "title": "Riding Two-Wheeler Without Helmet",
        "section": "Sec 129 r/w 194D MVA",
        "fine": "Rs. 1,000"
    },
    "PILLION_NO_HELMET": {
        "title": "Pillion Rider Without Helmet",
        "section": "Sec 129 r/w 194D MVA",
        "fine": "Rs. 1,000"
    },
    "TRIPLE_RIDING": {
        "title": "Overloading / Triple Riding on Two-Wheeler",
        "section": "Sec 128 r/w 194C MVA",
        "fine": "Rs. 1,000"
    },
    "WRONG_SIDE": {
        "title": "Driving Against Authorized Direction / Wrong-Side Flow",
        "section": "Sec 119/177, 184 MVA (Dangerous Driving)",
        "fine": "Rs. 1,500"
    },
    "ILLEGAL_STOPPING": {
        "title": "Obstruction of Traffic / Unauthorized Parking on Roadway",
        "section": "Sec 122 r/w 177 MVA",
        "fine": "Rs. 500"
    }
}

def make_challan(row, out_dir="challans"):
    os.makedirs(out_dir, exist_ok=True)
    info = VIOLATION_INFO.get(
        row["violation_type"],
        {"title": row["violation_type"], "section": "General MVA", "fine": "Rs. 1,000"}
    )
    path = os.path.join(out_dir, f"challan_{row['id']:06d}.pdf")
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, h - 20 * mm, "TRAFFIC ENFORCEMENT - E-CHALLAN DRAFT")

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.75, 0.1, 0.1)
    c.drawString(20 * mm, h - 27 * mm, "STATUS: PENDING HUMAN REVIEW - Official Draft Only")

    c.setFillColorRGB(0, 0, 0)
    lines = [
        f"Challan ID: CH-{row['id']:06d}",
        f"Date & Time: {row['ts']}",
        f"Camera Node: {row['camera_id']}",
        f"Vehicle Class: {row.get('vehicle_type', 'Vehicle').upper()}",
        f"Vehicle Number: {row['plate']}",
        f"Violation Type: {info['title']}",
        f"MVA Legal Section: {info['section']}",
        f"Fine Imposed: {info['fine']}",
        f"Generated Timestamp: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}"
    ]

    y = h - 42 * mm
    for line in lines:
        c.drawString(20 * mm, y, line)
        y -= 6.5 * mm

    c.drawString(20 * mm, y - 2 * mm, "Photographic Evidence Captured:")
    if row.get("image_path") and os.path.exists(row["image_path"]):
        c.drawImage(row["image_path"], 20 * mm, y - 110 * mm, width=170 * mm, height=100 * mm, preserveAspectRatio=True)

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(20 * mm, 15 * mm, "Automated computer vision detection. Verified by human officer prior to formal notification.")
    c.save()
    return path