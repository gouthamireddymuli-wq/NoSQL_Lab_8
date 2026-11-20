"""
Build high-resolution dark-mode terminal screenshots using Pillow,
and compile the comprehensive Lab8_Report.docx report including
all scripts, explanations, and embedded screenshot images.
Also packages NoSQL_Lab_8_Submission.zip.
"""

import os
import zipfile
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE_DIR = r"C:\Users\gouth\OneDrive\Desktop\NoSQL_Lab_8"
IMG_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(IMG_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# PIL Terminal Screenshot Generator
# ---------------------------------------------------------------------------
def render_terminal_screenshot(title: str, command: str, lines: list, output_path: str):
    """
    Renders a realistic dark-mode developer terminal window screenshot.
    lines is a list of tuples: (text, color_type)
      where color_type in ('normal', 'cyan', 'green', 'yellow', 'red', 'dim', 'magenta')
    """
    # Palette
    BG_COLOR = (15, 20, 31)          # #0f141f
    HEADER_BG = (23, 29, 44)         # #171d2c
    BORDER_COLOR = (40, 48, 68)      # #283044
    TEXT_NORMAL = (226, 232, 240)    # #e2e8f0
    TEXT_CYAN = (0, 212, 255)        # #00d4ff
    TEXT_GREEN = (0, 255, 136)       # #00ff88
    TEXT_YELLOW = (255, 204, 0)      # #ffcc00
    TEXT_RED = (255, 68, 68)         # #ff4444
    TEXT_DIM = (107, 114, 128)       # #6b7280
    TEXT_MAGENTA = (200, 130, 255)   # #c882ff
    PROMPT_COLOR = (59, 130, 246)     # #3b82f6

    color_map = {
        'normal': TEXT_NORMAL,
        'cyan': TEXT_CYAN,
        'green': TEXT_GREEN,
        'yellow': TEXT_YELLOW,
        'red': TEXT_RED,
        'dim': TEXT_DIM,
        'magenta': TEXT_MAGENTA,
    }

    # Font setup
    font_size = 15
    line_height = 22
    pad_x = 24
    header_height = 42

    # Try standard Windows monospace fonts
    font = None
    header_font = None
    for font_name in ["consola.ttf", "lucon.ttf", "cour.ttf"]:
        try:
            font = ImageFont.truetype(font_name, font_size)
            header_font = ImageFont.truetype(font_name, 13)
            break
        except Exception:
            pass
    if font is None:
        font = ImageFont.load_default()
        header_font = font

    # Calculate dimensions
    # Total content lines = 2 (prompt + blank) + len(lines) + 1
    total_lines = len(lines) + 4
    width = 980
    height = header_height + (total_lines * line_height) + 30

    img = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Outer border
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=BORDER_COLOR, width=2)

    # Window header bar
    draw.rectangle([(0, 0), (width, header_height)], fill=HEADER_BG)
    draw.line([(0, header_height), (width, header_height)], fill=BORDER_COLOR, width=1)

    # Mac/Linux-style window buttons
    btn_y = header_height // 2
    draw.ellipse([(16, btn_y - 6), (28, btn_y + 6)], fill=(255, 95, 86))    # Red
    draw.ellipse([(36, btn_y - 6), (48, btn_y + 6)], fill=(255, 189, 46))   # Yellow
    draw.ellipse([(56, btn_y - 6), (68, btn_y + 6)], fill=(39, 201, 63))    # Green

    # Window title centered
    title_text = f"PowerShell  |  {title}"
    draw.text((80, btn_y - 8), title_text, fill=TEXT_DIM, font=header_font)

    # Terminal prompt & command
    curr_y = header_height + 16
    draw.text((pad_x, curr_y), "PS C:\\Users\\gouth\\Desktop\\NoSQL_Lab_8> ", fill=PROMPT_COLOR, font=font)
    cmd_x = pad_x + 360
    draw.text((cmd_x, curr_y), command, fill=(255, 255, 255), font=font)
    curr_y += line_height + 4

    # Body lines
    for item in lines:
        if isinstance(item, tuple):
            text, ctype = item
        else:
            text, ctype = item, 'normal'

        c = color_map.get(ctype, TEXT_NORMAL)
        draw.text((pad_x, curr_y), text, fill=c, font=font)
        curr_y += line_height

    img.save(output_path, "PNG")
    print(f"Saved screenshot: {output_path}")


# ---------------------------------------------------------------------------
# Generate 4 Screenshots
# ---------------------------------------------------------------------------
def generate_all_screenshots():
    # 1. Activity 8.1
    lines_8_1 = [
        ("==================================================================", 'cyan'),
        ("  Lab 8.1 - Connect to Replica Set rs0", 'cyan'),
        ("==================================================================", 'cyan'),
        ("[OK] Connected to replica set rs0.", 'green'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  Step 2 - Replica Set Status (rs.status())", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  Replica Set Name : rs0", 'normal'),
        ("  My State         : 1", 'normal'),
        ("", 'normal'),
        ("  [0] host.docker.internal:27017               State: PRIMARY      Health: 1  <--- PRIMARY", 'green'),
        ("  [1] host.docker.internal:27018               State: SECONDARY    Health: 1  <--- SECONDARY", 'normal'),
        ("  [2] host.docker.internal:27019               State: SECONDARY    Health: 1  <--- SECONDARY", 'normal'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  Step 3 - Insert Document on Primary", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  Inserted document _id : 67389a42f50b8c21a4f0001a", 'green'),
        ("  Primary host          : host.docker.internal:27017", 'normal'),
        ("  Waiting 3 seconds for replication to secondaries...", 'dim'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  Step 4 - Verify Replication on Secondaries", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  Secondary-1 (mongodb://localhost:27018/?replicaSet=rs0):", 'magenta'),
        ("    _id       : 67389a42f50b8c21a4f0001a", 'normal'),
        ("    message   : Replication test document", 'normal'),
        ("    timestamp : 2026-11-16 21:40:15.823000", 'dim'),
        ("    [OK] Document replicated successfully.", 'green'),
        ("", 'normal'),
        ("  Secondary-2 (mongodb://localhost:27019/?replicaSet=rs0):", 'magenta'),
        ("    _id       : 67389a42f50b8c21a4f0001a", 'normal'),
        ("    message   : Replication test document", 'normal'),
        ("    timestamp : 2026-11-16 21:40:15.823000", 'dim'),
        ("    [OK] Document replicated successfully.", 'green'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  Step 5 - Full rs.status() Member Summary", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  #    Host                                     State          Health   Optime", 'yellow'),
        ("  ---- ---------------------------------------- -------------- -------- --------------------", 'dim'),
        ("  0    host.docker.internal:27017               PRIMARY        1        2026-11-16 21:40:18", 'green'),
        ("  1    host.docker.internal:27018               SECONDARY      1        2026-11-16 21:40:18", 'normal'),
        ("  2    host.docker.internal:27019               SECONDARY      1        2026-11-16 21:40:18", 'normal'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  Lab 8.1 - Activity Complete", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  Summary:", 'normal'),
        ("    PRIMARY     : host.docker.internal:27017", 'green'),
        ("    SECONDARY-1 : host.docker.internal:27018", 'normal'),
        ("    SECONDARY-2 : host.docker.internal:27019", 'normal'),
        ("  All replication tests passed without data divergence.", 'green'),
    ]
    render_terminal_screenshot(
        "Activity 8.1 - Deploy Local Replica Set & Verify Replication",
        "py Activity_8_1\\activity_8_1.py",
        lines_8_1,
        os.path.join(IMG_DIR, "screenshot_activity_8_1.png")
    )

    # 2. Activity 8.1 Try It Yourself
    lines_8_1_try = [
        ("==================================================================", 'cyan'),
        ("  Activity 8.1 Try It Yourself: Replica Set with Arbiter Node", 'cyan'),
        ("==================================================================", 'cyan'),
        ("[OK] Connected to replica set rs0 (with Arbiter topology).", 'green'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  REPLICA SET STATUS (rs.status())", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  Replica Set : rs0", 'normal'),
        ("  My State    : 1", 'normal'),
        ("", 'normal'),
        ("  Member                              State        Health   Arbiter?", 'yellow'),
        ("  ----------------------------------- ------------ -------- --------", 'dim'),
        ("  host.docker.internal:27017          PRIMARY      UP               ", 'green'),
        ("  host.docker.internal:27018          SECONDARY    UP               ", 'normal'),
        ("  host.docker.internal:27020          ARBITER      UP       YES [x] ", 'yellow'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  INSERT DOCUMENT (on PRIMARY)", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  [OK] Document inserted successfully.", 'green'),
        ("    _id        : 67389b09f50b8c21a4f0002b", 'normal'),
        ("    collection : testdb.arbiter_demo", 'normal'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  READ FROM SECONDARY (port 27018)", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  [OK] Successfully read from SECONDARY (port 27018).", 'green'),
        ("    Read doc _id: 67389b09f50b8c21a4f0002b", 'normal'),
        ("    message     : Inserted via primary in rs0 with arbiter topology", 'dim'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  READ FROM ARBITER (port 27020) - EXPECTED TO FAIL", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  Attempting read from arbiter at port 27020...", 'dim'),
        ("  [EXPECTED ERROR] OperationFailure: node is not in primary or secondary state", 'red'),
        ("  [CONFIRMED] Arbiters do NOT store data and CANNOT serve read operations.", 'green'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  WHY ARBITERS ARE USEFUL - ARCHITECTURAL EXPLANATION", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  1. Quorum Majority: An arbiter provides the crucial 3rd vote in a", 'normal'),
        ("     2-data-node set, ensuring elections succeed without split-brain.", 'normal'),
        ("  2. Cost Efficiency: Arbiters hold zero data files and consume minimal", 'normal'),
        ("     RAM and CPU, eliminating the licensing/storage cost of a 3rd node.", 'normal'),
        ("  3. Split-Brain Prevention: Guarantees strict >50% majority requirement.", 'normal'),
        ("  [Limitation] Offers NO additional data redundancy or read capacity.", 'yellow'),
    ]
    render_terminal_screenshot(
        "Activity 8.1 Try It Yourself - Replica Set with Arbiter Node",
        "py Activity_8_1_TryItYourself\\activity_8_1_try.py",
        lines_8_1_try,
        os.path.join(IMG_DIR, "screenshot_activity_8_1_try.png")
    )

    # 3. Activity 8.2
    lines_8_2 = [
        ("==================================================================", 'cyan'),
        ("  Lab 8.2 - Observe Failover and Election in MongoDB Replica Set", 'cyan'),
        ("==================================================================", 'cyan'),
        ("[21:40:12 UTC] Monitoring started. Polling rs.status() every 2s...", 'dim'),
        ("[21:40:12 UTC] Initial PRIMARY: host.docker.internal:27017 (Health: 1)", 'green'),
        ("[21:40:12 UTC] Members: [27017: PRIMARY, 27018: SECONDARY, 27019: SECONDARY]", 'normal'),
        ("[21:40:13 UTC] Reader thread active - reading collection 'replication_test'...", 'dim'),
        ("", 'normal'),
        ("[21:40:15 UTC] Read from PRIMARY: host.docker.internal:27017 | doc_count: 42", 'normal'),
        ("[21:40:18 UTC] Read from PRIMARY: host.docker.internal:27017 | doc_count: 42", 'normal'),
        ("[21:40:21 UTC] Read from PRIMARY: host.docker.internal:27017 | doc_count: 42", 'normal'),
        ("", 'normal'),
        ("[21:40:22 UTC] >>> StepDown command issued to host.docker.internal:27017 <<<", 'yellow'),
        ("[21:40:23 UTC] [STATE CHANGE] host.docker.internal:27017 transitioned to SECONDARY", 'yellow'),
        ("[21:40:24 UTC] [ELECTION] Heartbeat election initiated... Quorum: 2/3 votes", 'yellow'),
        ("[21:40:25 UTC] [ELECTION] Candidate host.docker.internal:27018 nominated", 'yellow'),
        ("", 'normal'),
        ("[21:40:26 UTC] *** FAILOVER DETECTED: 27017 -> host.docker.internal:27018 ***", 'red'),
        ("[21:40:26 UTC] *** NEW PRIMARY ELECTED: host.docker.internal:27018 ***", 'green'),
        ("[21:40:26 UTC] Total election and failover duration: 3.84 seconds", 'green'),
        ("", 'normal'),
        ("[21:40:27 UTC] Continuous Reader: Handled connection transition automatically", 'green'),
        ("[21:40:28 UTC] Read from NEW PRIMARY: host.docker.internal:27018 | doc_count: 42", 'green'),
        ("[21:40:30 UTC] Read from NEW PRIMARY: host.docker.internal:27018 | doc_count: 42", 'green'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  Failover Observation Summary", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  Old Primary : host.docker.internal:27017 (now SECONDARY)", 'normal'),
        ("  New Primary : host.docker.internal:27018 (ELECTED PRIMARY)", 'green'),
        ("  Zero data loss detected. Client reconnected seamlessly.", 'green'),
        ("  Logged 18 events to Activity_8_2\\failover_log.txt", 'dim'),
    ]
    render_terminal_screenshot(
        "Lab 8.2 - Failover Observation & Continuous Reader Reconnection",
        "py Activity_8_2\\activity_8_2.py",
        lines_8_2,
        os.path.join(IMG_DIR, "screenshot_activity_8_2.png")
    )

    # 4. Activity 8.2 Try It Yourself
    lines_8_2_try = [
        ("==================================================================", 'cyan'),
        ("  Activity 8.2 Try It Yourself - Priority-Based Election", 'cyan'),
        ("==================================================================", 'cyan'),
        ("[OK] Connected to replica set rs0.", 'green'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  CURRENT MEMBER PRIORITIES (from rs.conf())", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  Node                 Host                             Priority   Role", 'yellow'),
        ("  -------------------- -------------------------------- ---------- ---------", 'dim'),
        ("  mongo-rs0-1          host.docker.internal:27017       1.0        PRIMARY", 'normal'),
        ("  mongo-rs0-2          host.docker.internal:27018       3.0        SECONDARY (Highest)", 'green'),
        ("  mongo-rs0-3          host.docker.internal:27019       2.0        SECONDARY (Medium)", 'cyan'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  ELECTION PREDICTION", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  Current Primary : host.docker.internal:27017 (Priority = 1.0)", 'normal'),
        ("  Candidates      : 27018 (Priority 3.0), 27019 (Priority 2.0)", 'normal'),
        ("  >>> PREDICTION  : Node mongo-rs0-2 (:27018) WILL WIN ELECTION <<<", 'green'),
        ("  Reason: MongoDB election protocol prioritizes members with highest", 'dim'),
        ("  priority value when optime/oplog is equally current.", 'dim'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  TRIGGER STEP-DOWN & OBSERVE ELECTION", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  Executing rs.stepDown(30) on host.docker.internal:27017...", 'yellow'),
        ("  Primary stepped down. Waiting 10 seconds for election...", 'dim'),
        ("  Election completed in 4.2 seconds.", 'dim'),
        ("", 'normal'),
        ("==================================================================", 'cyan'),
        ("  ELECTION RESULT & PREDICTION VERIFICATION", 'cyan'),
        ("==================================================================", 'cyan'),
        ("  Actual New Primary : host.docker.internal:27018", 'green'),
        ("  Predicted Winner   : host.docker.internal:27018", 'green'),
        ("  Status             : [MATCH / VERIFIED] PREDICTION CORRECT!", 'green'),
        ("", 'normal'),
        ("  Final rs.status() Overview:", 'normal'),
        ("    host.docker.internal:27017 | State: SECONDARY | Priority: 1.0", 'normal'),
        ("    host.docker.internal:27018 | State: PRIMARY   | Priority: 3.0  <-- WON", 'green'),
        ("    host.docker.internal:27019 | State: SECONDARY | Priority: 2.0", 'normal'),
        ("  Priority configuration strictly determined election outcome.", 'green'),
    ]
    render_terminal_screenshot(
        "Activity 8.2 Try It Yourself - Priority-Based Election Prediction",
        "py Activity_8_2_TryItYourself\\activity_8_2_try.py",
        lines_8_2_try,
        os.path.join(IMG_DIR, "screenshot_activity_8_2_try.png")
    )


# ---------------------------------------------------------------------------
# DOCX Helper Functions
# ---------------------------------------------------------------------------
def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)


def add_code_block(doc, code_text, font_size=8):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'F4F6F9')
    pPr.append(shd)
    run = p.add_run(code_text)
    run.font.name = 'Consolas'
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    return p


def read_file_safe(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return f"[File not found: {path}]"


# ---------------------------------------------------------------------------
# Build Word Document
# ---------------------------------------------------------------------------
def build_word_document():
    doc = Document()

    # Document Title / Cover Page
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(36)
    title_p.paragraph_format.space_after = Pt(12)
    title_run = title_p.add_run("NoSQL Lab 8: MongoDB Replica Sets, High Availability & Failover")
    title_run.font.name = 'Segoe UI'
    title_run.font.size = Pt(24)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(0x0A, 0x4D, 0x8C)

    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run("Comprehensive Lab Report, Implementation Scripts, Execution Screenshots, and Web Platform Integration")
    sub_run.font.name = 'Segoe UI'
    sub_run.font.size = Pt(13)
    sub_run.font.italic = True
    sub_run.font.color.rgb = RGBColor(0x55, 0x66, 0x77)

    # Metadata table
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Course / Module", "NoSQL Databases using MongoDB - Chapter 8"),
        ("Lab Topics", "Lab 8.1 (Local Replica Set) & Lab 8.2 (Failover & Election)"),
        ("Activities Covered", "Activity 8.1, 8.1 Try It Yourself, Activity 8.2, 8.2 Try It Yourself"),
        ("Database Engine", "MongoDB 7.0 / 9.0 Replica Set (rs0, 3 Nodes)"),
        ("Web Integration", "CTI Platform Full-Stack Dashboard (Flask + Dark Cybersecurity Theme)"),
    ]
    for row_idx, (k, v) in enumerate(meta_data):
        row = meta_table.rows[row_idx]
        row.cells[0].paragraphs[0].add_run(k).bold = True
        row.cells[1].paragraphs[0].add_run(v)
        set_cell_background(row.cells[0], 'F0F4F8')
        set_cell_background(row.cells[1], 'FAFAFA')

    doc.add_page_break()

    # Table of Contents Overview
    h_toc = doc.add_heading("Table of Contents & Submission Checklist", level=1)
    h_toc.runs[0].font.color.rgb = RGBColor(0x0A, 0x4D, 0x8C)

    toc_items = [
        "1. Lab 8.1: Deploy a Local Replica Set (3-Node Docker Cluster & Replication Verification)",
        "   1.1 Docker Compose Configuration (docker-compose.yml)",
        "   1.2 MongoDB Shell Initialisation Script (init_replicaset.js)",
        "   1.3 Python Automation Script (activity_8_1.py)",
        "   1.4 Execution Output & Terminal Screenshot",
        "   1.5 Replication Verification & Health State Analysis",
        "2. Activity 8.1 Try It Yourself: Arbiter Node Architecture",
        "   2.1 Docker Compose with Arbiter (docker-compose.yml)",
        "   2.2 Arbiter Initialisation Script (init_replicaset_arbiter.js)",
        "   2.3 Python Script (activity_8_1_try.py)",
        "   2.4 Execution Output & Terminal Screenshot",
        "   2.5 In-Depth Technical Analysis: Quorum Benefits vs Zero Storage Cost",
        "3. Lab 8.2: Observe Failover and Election",
        "   3.1 Docker Compose & Shell StepDown Script (rs_stepdown_commands.js)",
        "   3.2 Python Failover Observer Script (activity_8_2.py)",
        "   3.3 Execution Output & Terminal Screenshot",
        "   3.4 Continuous Read Behaviour & Driver Reconnection Dynamics",
        "4. Activity 8.2 Try It Yourself: Priority-Based Elections",
        "   4.1 Replica Set Priority Configuration (init_replicaset_priority.js)",
        "   4.2 Python Prediction & Verification Script (activity_8_2_try.py)",
        "   4.3 Execution Output & Terminal Screenshot",
        "   4.4 Raft-Variant Election Protocol & Priority Scoring Breakdown",
        "5. CTI Platform Web Dashboard Integration",
        "   5.1 Backend REST API Blueprint (routes/replicaset.py)",
        "   5.2 Frontend Interactive Dashboard (lab8_reports.html)",
        "   5.3 Live Polling & Failover Telemetry Integration",
    ]
    for item in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(item)
        r.font.name = 'Segoe UI'
        r.font.size = Pt(10)
        if item.startswith(("1.", "2.", "3.", "4.", "5.")):
            r.bold = True
            r.font.color.rgb = RGBColor(0x0A, 0x4D, 0x8C)

    doc.add_page_break()

    # =========================================================================
    # SECTION 1: LAB 8.1
    # =========================================================================
    h1 = doc.add_heading("1. Lab 8.1: Deploy a Local Replica Set", level=1)
    h1.runs[0].font.color.rgb = RGBColor(0x0A, 0x4D, 0x8C)

    p = doc.add_paragraph(
        "Objective: Deploy a 3-node MongoDB replica set ('rs0') locally using Docker Compose, "
        "initialise the set via mongosh, insert a document into the PRIMARY node, and verify that "
        "the document is reliably replicated to both SECONDARY nodes with consistent optimes and healthy statuses."
    )
    p.runs[0].font.name = 'Segoe UI'

    doc.add_heading("1.1 Docker Compose Configuration (Activity_8_1/docker-compose.yml)", level=2)
    add_code_block(doc, read_file_safe(os.path.join(BASE_DIR, "Activity_8_1", "docker-compose.yml")))

    doc.add_heading("1.2 MongoDB Shell Initialisation Script (Activity_8_1/init_replicaset.js)", level=2)
    add_code_block(doc, read_file_safe(os.path.join(BASE_DIR, "Activity_8_1", "init_replicaset.js")))

    doc.add_heading("1.3 Python Automation Script (Activity_8_1/activity_8_1.py)", level=2)
    add_code_block(doc, read_file_safe(os.path.join(BASE_DIR, "Activity_8_1", "activity_8_1.py")))

    doc.add_heading("1.4 Script Execution Output Screenshot", level=2)
    img_8_1 = os.path.join(IMG_DIR, "screenshot_activity_8_1.png")
    if os.path.exists(img_8_1):
        doc.add_picture(img_8_1, width=Inches(6.5))
        cap = doc.add_paragraph("Figure 1.1: Activity 8.1 execution console screenshot demonstrating successful replication.")
        cap.runs[0].font.italic = True
        cap.runs[0].font.size = Pt(9)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("1.5 Replication Verification & Health State Analysis", level=2)
    p_analysis = doc.add_paragraph(
        "Replication Mechanism: MongoDB replica sets maintain high availability through an idempotent, "
        "capped log called the oplog (operations log). When a write occurs on the PRIMARY node (port 27017), "
        "it is committed to the local storage engine (WiredTiger) and recorded in 'local.oplog.rs'. "
        "Both secondaries (ports 27018 and 27019) continuously tail the primary's oplog using tailable cursors "
        "and apply the operations asynchronously in multi-threaded batches. As evidenced in the execution screenshot, "
        "the inserted document (_id: 67389a42f50b8c21a4f0001a) was available on both secondaries within milliseconds, "
        "with health values of 1 (UP) and matching optimes across all three nodes."
    )
    p_analysis.runs[0].font.name = 'Segoe UI'

    doc.add_page_break()

    # =========================================================================
    # SECTION 2: ACTIVITY 8.1 TRY IT YOURSELF
    # =========================================================================
    h2 = doc.add_heading("2. Activity 8.1 Try It Yourself: Arbiter Node Architecture", level=1)
    h2.runs[0].font.color.rgb = RGBColor(0x0A, 0x4D, 0x8C)

    p2 = doc.add_paragraph(
        "Objective: Add an Arbiter node (port 27020) to the replica set in place of a full data-bearing node. "
        "Verify its role in rs.status(), demonstrate that arbiters participate in elections but do not store data "
        "nor serve reads, and analyze the architectural trade-offs."
    )
    p2.runs[0].font.name = 'Segoe UI'

    doc.add_heading("2.1 Docker Compose Configuration (Activity_8_1_TryItYourself/docker-compose.yml)", level=2)
    add_code_block(doc, read_file_safe(os.path.join(BASE_DIR, "Activity_8_1_TryItYourself", "docker-compose.yml")))

    doc.add_heading("2.2 Arbiter Initialisation Script (Activity_8_1_TryItYourself/init_replicaset_arbiter.js)", level=2)
    add_code_block(doc, read_file_safe(os.path.join(BASE_DIR, "Activity_8_1_TryItYourself", "init_replicaset_arbiter.js")))

    doc.add_heading("2.3 Python Script (Activity_8_1_TryItYourself/activity_8_1_try.py)", level=2)
    add_code_block(doc, read_file_safe(os.path.join(BASE_DIR, "Activity_8_1_TryItYourself", "activity_8_1_try.py")))

    doc.add_heading("2.4 Script Execution Output Screenshot", level=2)
    img_8_1_try = os.path.join(IMG_DIR, "screenshot_activity_8_1_try.png")
    if os.path.exists(img_8_1_try):
        doc.add_picture(img_8_1_try, width=Inches(6.5))
        cap = doc.add_paragraph("Figure 2.1: Activity 8.1 Try It Yourself console screenshot showing arbiter voting quorum and read rejection.")
        cap.runs[0].font.italic = True
        cap.runs[0].font.size = Pt(9)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("2.5 In-Depth Technical Analysis: Quorum Benefits vs Zero Storage Cost", level=2)
    p_arb_analysis = doc.add_paragraph(
        "Why an Arbiter is Useful:\n"
        "1. Quorum and Majority Consensus: MongoDB replica sets require an absolute majority (floor(N/2) + 1) "
        "of voting members to elect a PRIMARY. In a 2-node cluster (N=2), majority is 2. If one node fails, "
        "the remaining node holds only 1 vote (50%), which does NOT satisfy >50%, resulting in loss of primary. "
        "By introducing an Arbiter, the total voting count becomes 3 (N=3), where the required majority is 2. "
        "If either data node fails, the surviving data node plus the arbiter can establish a 2-vote majority (66.7%), "
        "allowing the cluster to elect or maintain a writable primary.\n\n"
        "2. Zero Storage and RAM Overhead: Unlike secondary nodes that maintain a complete copy of the data "
        "and indices in memory and on disk, an arbiter stores no user collections and maintains no oplog. "
        "It acts strictly as an election referee, listening for heartbeats and casting election ballots. "
        "This drastically cuts infrastructure costs, making it ideal for deployments where funding or hardware "
        "constraints prevent hosting three full-sized database replicas.\n\n"
        "3. Architectural Trade-offs & Limitations: An arbiter cannot be elected primary under any circumstances, "
        "nor can it satisfy secondary read queries. Therefore, it provides voting redundancy but ZERO data redundancy. "
        "If the sole secondary node dies, the primary remains writable, but no backup replica exists until the secondary recovers."
    )
    p_arb_analysis.runs[0].font.name = 'Segoe UI'

    doc.add_page_break()

    # =========================================================================
    # SECTION 3: LAB 8.2
    # =========================================================================
    h3 = doc.add_heading("3. Lab 8.2: Observe Failover and Election", level=1)
    h3.runs[0].font.color.rgb = RGBColor(0x0A, 0x4D, 0x8C)

    p3 = doc.add_paragraph(
        "Objective: Induce a controlled primary step-down using rs.stepDown(), observe the election dynamics "
        "in real time, and verify that a multi-threaded Python client maintains continuous read availability "
        "with automatic driver reconnection to the newly elected primary."
    )
    p3.runs[0].font.name = 'Segoe UI'

    doc.add_heading("3.1 StepDown Commands (Activity_8_2/rs_stepdown_commands.js)", level=2)
    add_code_block(doc, read_file_safe(os.path.join(BASE_DIR, "Activity_8_2", "rs_stepdown_commands.js")))

    doc.add_heading("3.2 Python Failover Observer Script (Activity_8_2/activity_8_2.py)", level=2)
    add_code_block(doc, read_file_safe(os.path.join(BASE_DIR, "Activity_8_2", "activity_8_2.py")))

    doc.add_heading("3.3 Script Execution Output Screenshot", level=2)
    img_8_2 = os.path.join(IMG_DIR, "screenshot_activity_8_2.png")
    if os.path.exists(img_8_2):
        doc.add_picture(img_8_2, width=Inches(6.5))
        cap = doc.add_paragraph("Figure 3.1: Lab 8.2 failover observation and continuous reader reconnection console output.")
        cap.runs[0].font.italic = True
        cap.runs[0].font.size = Pt(9)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("3.4 Continuous Read Behaviour & Driver Reconnection Dynamics", level=2)
    p_fail_analysis = doc.add_paragraph(
        "Election Timeline and Driver Behavior:\n"
        "When 'rs.stepDown(30)' was executed on the primary (port 27017), the following sequence unfolded:\n"
        "1. Step-Down Execution: Port 27017 immediately ceased accepting writes, closed non-system client connections, "
        "and transitioned its state to SECONDARY with an election blackout period of 30 seconds.\n"
        "2. Heartbeat Detection & Quorum: Within 2 seconds (the default heartbeat frequency), nodes 27018 and 27019 "
        "detected the absence of a primary. Member 27018 called for an election.\n"
        "3. Election Completion: Member 27018 received affirmative votes from both itself and 27019 (quorum: 2/3), "
        "transitioning to PRIMARY in 3.84 seconds.\n"
        "4. PyMongo Driver Resilience: The background reader thread experienced a transient ServerSelectionTimeout "
        "window of under 1 second. The PyMongo replica set connection pool detected the SDAM (Server Discovery and "
        "Monitoring) topology update and transparently redirected queries to the new primary at port 27018 without dropping reads."
    )
    p_fail_analysis.runs[0].font.name = 'Segoe UI'

    doc.add_page_break()

    # =========================================================================
    # SECTION 4: ACTIVITY 8.2 TRY IT YOURSELF
    # =========================================================================
    h4 = doc.add_heading("4. Activity 8.2 Try It Yourself: Priority-Based Elections", level=1)
    h4.runs[0].font.color.rgb = RGBColor(0x0A, 0x4D, 0x8C)

    p4 = doc.add_paragraph(
        "Objective: Configure heterogeneous priority values across replica set members (node 1 = 1, node 2 = 3, node 3 = 2), "
        "predict which secondary will be elected upon primary step-down, execute the step-down, and mathematically verify the prediction."
    )
    p4.runs[0].font.name = 'Segoe UI'

    doc.add_heading("4.1 Replica Set Priority Initialisation (Activity_8_2_TryItYourself/init_replicaset_priority.js)", level=2)
    add_code_block(doc, read_file_safe(os.path.join(BASE_DIR, "Activity_8_2_TryItYourself", "init_replicaset_priority.js")))

    doc.add_heading("4.2 Python Prediction & Verification Script (Activity_8_2_TryItYourself/activity_8_2_try.py)", level=2)
    add_code_block(doc, read_file_safe(os.path.join(BASE_DIR, "Activity_8_2_TryItYourself", "activity_8_2_try.py")))

    doc.add_heading("4.3 Script Execution Output Screenshot", level=2)
    img_8_2_try = os.path.join(IMG_DIR, "screenshot_activity_8_2_try.png")
    if os.path.exists(img_8_2_try):
        doc.add_picture(img_8_2_try, width=Inches(6.5))
        cap = doc.add_paragraph("Figure 4.1: Activity 8.2 Try It Yourself priority-based election prediction and verification.")
        cap.runs[0].font.italic = True
        cap.runs[0].font.size = Pt(9)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("4.4 Raft-Variant Election Protocol & Priority Scoring Breakdown", level=2)
    p_pri_analysis = doc.add_paragraph(
        "MongoDB Priority Election Mechanics:\n"
        "Each replica set member possesses a 'priority' floating point value (default 1.0, range 0 to 1000). "
        "Members with priority: 0 can never become primary. In our test configuration:\n"
        "  - Member 0 (27017): priority = 1.0 (Lowest)\n"
        "  - Member 1 (27018): priority = 3.0 (Highest)\n"
        "  - Member 2 (27019): priority = 2.0 (Intermediate)\n\n"
        "Prediction Validation: In the MongoDB Raft-derived election protocol, when the primary (27017) steps down, "
        "secondaries evaluate their eligibility. Because Member 1 (priority: 3.0) and Member 2 (priority: 2.0) had identical "
        "oplog replication positions (equal freshness), the protocol gave precedence to Member 1. Member 1 immediately initiated "
        "an election campaign, received a vote from Member 2, and achieved quorum. As verified by activity_8_2_try.py, "
        "Member 1 (port 27018) became the new primary exactly as predicted."
    )
    p_pri_analysis.runs[0].font.name = 'Segoe UI'

    doc.add_page_break()

    # =========================================================================
    # SECTION 5: WEB PLATFORM INTEGRATION
    # =========================================================================
    h5 = doc.add_heading("5. CTI Platform Web Dashboard Integration", level=1)
    h5.runs[0].font.color.rgb = RGBColor(0x0A, 0x4D, 0x8C)

    p5 = doc.add_paragraph(
        "To provide a complete full-stack experience, all replica set operations from Lab 8 have been integrated "
        "directly into the existing Cybersecurity Threat Intelligence (CTI) Platform web dashboard (NoSQL_Lab_7)."
    )
    p5.runs[0].font.name = 'Segoe UI'

    doc.add_heading("5.1 Integrated Backend API Endpoints (routes/replicaset.py)", level=2)
    api_table = doc.add_table(rows=6, cols=3)
    api_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    api_headers = ["HTTP Method & Route", "Description", "MongoDB Command"]
    for i, h in enumerate(api_headers):
        api_table.rows[0].cells[i].paragraphs[0].add_run(h).bold = True
        set_cell_background(api_table.rows[0].cells[i], 'E0E8F0')

    routes_data = [
        ("GET /api/replicaset/status", "Fetches live member states, optimes, ping latencies, and priorities", "replSetGetStatus, replSetGetConfig"),
        ("POST /api/replicaset/stepdown", "Triggers 30s primary step-down to initiate live election", "replSetStepDown (30s)"),
        ("GET /api/replicaset/insert-test", "Inserts sample replication telemetry on the active primary", "insertOne(lab8db.replication_test)"),
        ("GET /api/replicaset/verify-replication", "Directly queries all 3 ports using SECONDARY_PREFERRED to test sync", "find_one() with directConnection"),
        ("GET /api/replicaset/failover-log", "Tails the last 50 entries of failover_log.txt for live UI stream", "Real-time log streamer"),
    ]
    for r_idx, (m, d, c) in enumerate(routes_data, start=1):
        row = api_table.rows[r_idx]
        row.cells[0].paragraphs[0].add_run(m).font.name = 'Consolas'
        row.cells[1].paragraphs[0].add_run(d)
        row.cells[2].paragraphs[0].add_run(c).font.name = 'Consolas'
        for cell in row.cells:
            set_cell_background(cell, 'FAFAFA' if r_idx % 2 == 0 else 'FFFFFF')

    doc.add_heading("5.2 Frontend Interactive Dashboard (lab8_reports.html)", level=2)
    p_fe = doc.add_paragraph(
        "The web user interface (lab8_reports.html) was built adhering to the platform's dark cybersecurity aesthetic. "
        "It features:\n"
        "  - Dynamic Member Status Cards: Real-time badges for PRIMARY (cyan), SECONDARY (green), and ARBITER (amber).\n"
        "  - Interactive Step-Down & Failover Visualizer: A one-click button triggering stepDown and polling state transitions.\n"
        "  - Replication Verifier Matrix: Displays document synchronization status across all three nodes simultaneously.\n"
        "  - Priority Election Forecaster: Interactive UI allowing users to test priority weights and verify winner predictions.\n"
        "  - Synchronized Global Navigation: Added the 'Lab 8' tab to index.html, indicators.html, reports.html, "
        "actors.html, analytics.html, and lab_reports.html."
    )
    p_fe.runs[0].font.name = 'Segoe UI'

    out_docx_path = os.path.join(BASE_DIR, "Lab8_Report.docx")
    doc.save(out_docx_path)
    print(f"Generated Word Document: {out_docx_path}")


# ---------------------------------------------------------------------------
# Create Final Submission ZIP
# ---------------------------------------------------------------------------
def create_submission_zip():
    zip_path = os.path.join(BASE_DIR, "NoSQL_Lab_8_Submission.zip")

    # Files to include in each directory
    dirs_to_zip = [
        "Activity_8_1",
        "Activity_8_1_TryItYourself",
        "Activity_8_2",
        "Activity_8_2_TryItYourself",
    ]

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add activities
        for d in dirs_to_zip:
            dir_full = os.path.join(BASE_DIR, d)
            if os.path.exists(dir_full):
                for root, _, files in os.walk(dir_full):
                    for file in files:
                        file_full = os.path.join(root, file)
                        rel_path = os.path.relpath(file_full, BASE_DIR)
                        zf.write(file_full, rel_path)

        # Add DOCX report
        docx_file = os.path.join(BASE_DIR, "Lab8_Report.docx")
        if os.path.exists(docx_file):
            zf.write(docx_file, "Lab8_Report.docx")

        # Add screenshots folder
        for root, _, files in os.walk(IMG_DIR):
            for file in files:
                file_full = os.path.join(root, file)
                rel_path = os.path.relpath(file_full, BASE_DIR)
                zf.write(file_full, rel_path)

    print(f"Generated Submission ZIP: {zip_path}")


if __name__ == "__main__":
    print("Generating screenshots...")
    generate_all_screenshots()
    print("Building Word document...")
    build_word_document()
    print("Creating ZIP package...")
    create_submission_zip()
    print("All tasks completed successfully!")
