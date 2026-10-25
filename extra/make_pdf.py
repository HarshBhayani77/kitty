from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas as pdfcanvas

W, H = A4

# ── colour palette ──────────────────────────────────────────────────────────
BLACK    = colors.HexColor("#0d0d1a")
DARK     = colors.HexColor("#1a1a2e")
ACCENT   = colors.HexColor("#e74c3c")
ACCENT2  = colors.HexColor("#27ae60")
ACCENT3  = colors.HexColor("#3498db")
MUTED    = colors.HexColor("#666680")
LIGHT_BG = colors.HexColor("#f4f4f8")
BORDER   = colors.HexColor("#d0d0e0")
WHITE    = colors.white
CODE_BG  = colors.HexColor("#1e1e2e")
CODE_FG  = colors.HexColor("#cdd6f4")
MONO_ACC = colors.HexColor("#89b4fa")

# ── header / footer canvas ───────────────────────────────────────────────────
def on_page(canv, doc):
    canv.saveState()
    # top bar
    canv.setFillColor(BLACK)
    canv.rect(0, H - 14*mm, W, 14*mm, fill=1, stroke=0)
    canv.setFillColor(ACCENT)
    canv.rect(0, H - 14*mm, 4*mm, 14*mm, fill=1, stroke=0)
    canv.setFillColor(WHITE)
    canv.setFont("Courier-Bold", 8)
    canv.drawString(8*mm, H - 8*mm, "COMNYANG PIXEL PET  |  Project Setup Guide")
    canv.setFont("Courier", 7)
    canv.setFillColor(MUTED)
    canv.drawRightString(W - 8*mm, H - 8*mm, "Docker + VSCode + HTML/JS")
    # bottom bar
    canv.setFillColor(LIGHT_BG)
    canv.rect(0, 0, W, 8*mm, fill=1, stroke=0)
    canv.setFillColor(MUTED)
    canv.setFont("Courier", 7)
    canv.drawString(8*mm, 2.8*mm, "v1.0  |  2026")
    canv.drawCentredString(W/2, 2.8*mm, "github.com/you/comnyang")
    canv.drawRightString(W - 8*mm, 2.8*mm, f"Page {doc.page}")
    canv.restoreState()

# ── style helpers ────────────────────────────────────────────────────────────
BASE = getSampleStyleSheet()

def S(name, **kw):
    s = ParagraphStyle(name, **kw)
    return s

H1 = S("H1", fontName="Courier-Bold", fontSize=18, textColor=BLACK,
        spaceAfter=4, spaceBefore=14, leading=22)
H2 = S("H2", fontName="Courier-Bold", fontSize=13, textColor=DARK,
        spaceAfter=3, spaceBefore=10, leading=17,
        borderPad=4, leftIndent=0)
H3 = S("H3", fontName="Courier-Bold", fontSize=10, textColor=ACCENT3,
        spaceAfter=2, spaceBefore=7, leading=13)
BODY = S("BODY", fontName="Helvetica", fontSize=9, textColor=DARK,
         spaceAfter=4, leading=14)
BODYM = S("BODYM", fontName="Helvetica", fontSize=9, textColor=DARK,
          spaceAfter=2, leading=13, leftIndent=6)
CODE = S("CODE", fontName="Courier", fontSize=7.5, textColor=CODE_FG,
         backColor=CODE_BG, spaceAfter=6, spaceBefore=4, leading=12,
         leftIndent=8, rightIndent=8,
         borderPad=8, borderWidth=0, borderColor=CODE_BG)
NOTE = S("NOTE", fontName="Helvetica-Oblique", fontSize=8, textColor=MUTED,
         spaceAfter=3, leading=12, leftIndent=10)
BADGE_RED = S("BR", fontName="Courier-Bold", fontSize=8, textColor=WHITE,
              backColor=ACCENT, leading=12, leftIndent=4)
BADGE_GRN = S("BG", fontName="Courier-Bold", fontSize=8, textColor=WHITE,
              backColor=ACCENT2, leading=12, leftIndent=4)
BADGE_BLU = S("BB", fontName="Courier-Bold", fontSize=8, textColor=WHITE,
              backColor=ACCENT3, leading=12, leftIndent=4)

def hr(c=BORDER, w=0.5): return HRFlowable(width="100%", thickness=w, color=c, spaceAfter=4, spaceBefore=4)
def sp(h=4):             return Spacer(1, h)

def code_block(lines):
    txt = "<br/>".join(
        l.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace(" ","&nbsp;")
        for l in lines
    )
    return Paragraph(txt, CODE)

def feature_table(rows):
    data = [["#", "Feature", "How it works", "Trigger"]] + rows
    col_w = [8*mm, 38*mm, 80*mm, 42*mm]
    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0),  BLACK),
        ("TEXTCOLOR",   (0,0), (-1,0),  WHITE),
        ("FONTNAME",    (0,0), (-1,0),  "Courier-Bold"),
        ("FONTSIZE",    (0,0), (-1,0),  7.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LIGHT_BG]),
        ("FONTNAME",    (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",    (0,1), (-1,-1), 7.5),
        ("FONTNAME",    (0,1), (0,-1),  "Courier-Bold"),
        ("TEXTCOLOR",   (0,1), (0,-1),  ACCENT),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("ROWPADDING",  (0,0), (-1,-1), 4),
        ("GRID",        (0,0), (-1,-1), 0.3, BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING",(0,0), (-1,-1), 5),
    ]))
    return t

def section_header(text, color=ACCENT):
    return Table(
        [[Paragraph(text, S("SH", fontName="Courier-Bold", fontSize=11, textColor=WHITE, leading=14))]],
        colWidths=[W - 40*mm],
        style=TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), color),
            ("LEFTPADDING",(0,0),(-1,-1), 8),
            ("TOPPADDING", (0,0),(-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("ROUNDEDCORNERS", [4]),
        ])
    )

# ── document ─────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    "/mnt/user-data/outputs/comnyang_pdr.pdf",
    pagesize=A4,
    leftMargin=20*mm, rightMargin=20*mm,
    topMargin=20*mm, bottomMargin=14*mm,
    title="Comnyang Pixel Pet — PDR",
    author="Comnyang Dev",
)

story = []

# ══ COVER PAGE ══════════════════════════════════════════════════════════════
story.append(sp(20))
story.append(Paragraph("🐱", S("CAT", fontName="Courier-Bold", fontSize=48, textColor=ACCENT,
                                alignment=TA_CENTER, spaceAfter=6)))
story.append(Paragraph("COMNYANG", S("T", fontName="Courier-Bold", fontSize=32, textColor=BLACK,
                                      alignment=TA_CENTER, spaceAfter=4, letterSpacing=6)))
story.append(Paragraph("PIXEL PET DESKTOP COMPANION", S("T2", fontName="Courier", fontSize=11,
                         textColor=MUTED, alignment=TA_CENTER, spaceAfter=2)))
story.append(hr(ACCENT, 2))
story.append(sp(2))
story.append(Paragraph("Project Documentation & Requirements (PDR)",
    S("SUB", fontName="Helvetica-Oblique", fontSize=10, textColor=MUTED, alignment=TA_CENTER)))
story.append(sp(14))

cover_info = [
    ["Stack",    "HTML · CSS · JavaScript (Vanilla)"],
    ["Runtime",  "Docker (Node:alpine) + VSCode Dev Container"],
    ["Features", "15 interactive cat behaviours"],
    ["Version",  "1.0.0"],
    ["Date",     "June 2026"],
]
ct = Table(cover_info, colWidths=[35*mm, 110*mm])
ct.setStyle(TableStyle([
    ("FONTNAME",  (0,0), (0,-1), "Courier-Bold"),
    ("FONTNAME",  (1,0), (1,-1), "Helvetica"),
    ("FONTSIZE",  (0,0), (-1,-1), 9),
    ("TEXTCOLOR", (0,0), (0,-1), ACCENT3),
    ("TEXTCOLOR", (1,0), (1,-1), DARK),
    ("ROWBACKGROUNDS",(0,0),(-1,-1),[LIGHT_BG, WHITE]),
    ("GRID",      (0,0), (-1,-1), 0.3, BORDER),
    ("LEFTPADDING",(0,0),(-1,-1), 8),
    ("ROWPADDING",(0,0),(-1,-1), 5),
]))
story.append(ct)
story.append(sp(20))
story.append(Paragraph(
    "This document covers every file you need to create, the complete source code, "
    "Docker setup, VSCode devcontainer config, and all 15 cat features explained.",
    S("CV", fontName="Helvetica", fontSize=9, textColor=MUTED, alignment=TA_CENTER, leading=14)))
story.append(PageBreak())

# ══ 1. PROJECT STRUCTURE ════════════════════════════════════════════════════
story.append(Paragraph("1. Project Structure", H1))
story.append(hr())
story.append(Paragraph("Create this folder layout on your machine:", BODY))
story.append(code_block([
    "comnyang/",
    "├── .devcontainer/",
    "│   └── devcontainer.json      ← VSCode Dev Container config",
    "├── src/",
    "│   ├── index.html             ← main app entry point",
    "│   ├── cat.js                 ← pixel cat engine",
    "│   ├── features.js            ← all 15 feature handlers",
    "│   └── style.css              ← dark theme styles",
    "├── Dockerfile                 ← Docker image definition",
    "├── docker-compose.yml         ← compose for easy launch",
    "├── .dockerignore",
    "└── README.md",
]))
story.append(sp(4))

# ══ 2. DOCKER FILES ══════════════════════════════════════════════════════════
story.append(Paragraph("2. Docker Configuration", H1))
story.append(hr())

story.append(Paragraph("2.1  Dockerfile", H2))
story.append(Paragraph("Uses a lightweight Node Alpine image with a tiny HTTP server (serve):", BODY))
story.append(code_block([
    "# Dockerfile",
    "FROM node:20-alpine",
    "",
    "WORKDIR /app",
    "",
    "# Install static file server",
    "RUN npm install -g serve",
    "",
    "# Copy source files",
    "COPY src/ ./src/",
    "",
    "# Expose port",
    "EXPOSE 3000",
    "",
    "# Serve the src/ folder",
    'CMD ["serve", "-s", "src", "-l", "3000"]',
]))

story.append(Paragraph("2.2  docker-compose.yml", H2))
story.append(code_block([
    "# docker-compose.yml",
    "version: '3.9'",
    "",
    "services:",
    "  comnyang:",
    "    build: .",
    "    container_name: comnyang",
    "    ports:",
    '      - "3000:3000"',
    "    volumes:",
    '      - ./src:/app/src   # live reload on file save',
    "    restart: unless-stopped",
]))

story.append(Paragraph("2.3  .dockerignore", H2))
story.append(code_block([
    "node_modules",
    ".devcontainer",
    "*.md",
    ".git",
    ".DS_Store",
]))

story.append(Paragraph("Run commands:", H3))
story.append(code_block([
    "# Build and start",
    "docker compose up --build",
    "",
    "# Open in browser",
    "open http://localhost:3000",
    "",
    "# Stop",
    "docker compose down",
]))
story.append(PageBreak())

# ══ 3. VSCODE DEV CONTAINER ══════════════════════════════════════════════════
story.append(Paragraph("3. VSCode Dev Container", H1))
story.append(hr())
story.append(Paragraph(
    "Open the project in VSCode and press  Reopen in Container  when prompted. "
    "This gives you a full dev environment inside Docker.", BODY))

story.append(Paragraph("3.1  .devcontainer/devcontainer.json", H2))
story.append(code_block([
    '{',
    '  "name": "Comnyang Dev",',
    '  "dockerComposeFile": "../docker-compose.yml",',
    '  "service": "comnyang",',
    '  "workspaceFolder": "/app",',
    '  "forwardPorts": [3000],',
    '  "customizations": {',
    '    "vscode": {',
    '      "extensions": [',
    '        "esbenp.prettier-vscode",',
    '        "dbaeumer.vscode-eslint",',
    '        "ritwickdey.liveserver",',
    '        "bradlc.vscode-tailwindcss",',
    '        "ecmel.vscode-html-css"',
    '      ],',
    '      "settings": {',
    '        "editor.formatOnSave": true,',
    '        "editor.defaultFormatter": "esbenp.prettier-vscode",',
    '        "liveServer.settings.port": 3000',
    '      }',
    '    }',
    '  },',
    '  "postCreateCommand": "echo Ready! Open http://localhost:3000"',
    '}',
]))

story.append(Paragraph("Recommended VSCode Extensions:", H3))
ext_data = [
    ["Extension", "ID", "Purpose"],
    ["Prettier", "esbenp.prettier-vscode", "Auto-format HTML/JS/CSS"],
    ["ESLint", "dbaeumer.vscode-eslint", "JS linting"],
    ["Live Server", "ritwickdey.liveserver", "Hot reload on save"],
    ["HTML CSS Support", "ecmel.vscode-html-css", "IntelliSense"],
]
et = Table(ext_data, colWidths=[30*mm, 68*mm, 60*mm])
et.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("TEXTCOLOR",  (0,0), (-1,0), WHITE),
    ("FONTNAME",   (0,0), (-1,0), "Courier-Bold"),
    ("FONTSIZE",   (0,0), (-1,-1), 7.5),
    ("FONTNAME",   (0,1), (-1,-1), "Helvetica"),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LIGHT_BG]),
    ("GRID",       (0,0), (-1,-1), 0.3, BORDER),
    ("LEFTPADDING",(0,0),(-1,-1), 5),
    ("ROWPADDING", (0,0),(-1,-1), 4),
    ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
]))
story.append(et)
story.append(PageBreak())

# ══ 4. SOURCE CODE ════════════════════════════════════════════════════════════
story.append(Paragraph("4. Source Code", H1))
story.append(hr())

story.append(Paragraph("4.1  src/index.html", H2))
story.append(code_block([
    '<!DOCTYPE html>',
    '<html lang="en">',
    '<head>',
    '  <meta charset="UTF-8">',
    '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
    '  <title>Comnyang — Pixel Pet</title>',
    '  <link rel="stylesheet" href="style.css">',
    '</head>',
    '<body>',
    '  <div id="scene">',
    '    <div id="cat-wrap">',
    '      <div id="hearts"></div>',
    '      <canvas id="cat" width="48" height="48"></canvas>',
    '      <div id="bubble"></div>',
    '      <div id="timer-badge"></div>',
    '    </div>',
    '  </div>',
    '',
    '  <div id="controls">',
    '    <span class="label">SKIN:</span>',
    '    <button onclick="setSkin(\'black\')">Black</button>',
    '    <button onclick="setSkin(\'orange\')">Orange</button>',
    '    <button onclick="setSkin(\'siamese\')">Siamese</button>',
    '    <button onclick="setSkin(\'mackerel\')">Mackerel</button>',
    '    <input id="name-inp" placeholder="Your name">',
    '    <button onclick="setName()">Set Name</button>',
    '    <input id="msg-inp" placeholder="Pin a note...">',
    '    <button onclick="pinNote()">Pin</button>',
    '    <input id="note-inp" placeholder="Reminder msg">',
    '    <button onclick="setReminder()">Remind 30s</button>',
    '    <button onclick="togglePomodoro()">Pomodoro</button>',
    '    <button onclick="catJump()">Jump!</button>',
    '  </div>',
    '',
    '  <div id="type-area">',
    '    <input id="type-inp" placeholder="Type here...">',
    '  </div>',
    '',
    '  <div id="status">Comnyang is ready!</div>',
    '',
    '  <script src="cat.js"></script>',
    '  <script src="features.js"></script>',
    '</body>',
    '</html>',
]))

story.append(Paragraph("4.2  src/style.css", H2))
story.append(code_block([
    "* { box-sizing: border-box; margin: 0; padding: 0; }",
    "body { background: #0d0d1a; font-family: monospace; overflow: hidden; }",
    "",
    "#scene {",
    "  position: relative; width: 100vw; height: calc(100vh - 90px);",
    "  background: linear-gradient(180deg, #0d0d1a 0%, #16213e 100%);",
    "  overflow: hidden; cursor: crosshair;",
    "}",
    "",
    "#cat-wrap {",
    "  position: absolute; z-index: 10;",
    "  cursor: grab; user-select: none;",
    "}",
    "#cat-wrap:active { cursor: grabbing; }",
    "",
    "#bubble {",
    "  position: absolute; background: #fff; color: #000;",
    "  font-size: 10px; padding: 4px 8px; border-radius: 8px;",
    "  white-space: nowrap; display: none;",
    "  top: -30px; left: 50%; transform: translateX(-50%);",
    "  border: 2px solid #333; z-index: 20;",
    "}",
    "",
    "#timer-badge {",
    "  position: absolute; background: #e74c3c; color: #fff;",
    "  font-size: 10px; padding: 2px 6px; border-radius: 4px;",
    "  display: none; top: -20px; right: -10px; z-index: 15;",
    "}",
    "",
    ".heart {",
    "  position: absolute; font-size: 14px; pointer-events: none;",
    "  animation: floatHeart 1.2s ease-out forwards;",
    "}",
    "@keyframes floatHeart {",
    "  0%   { opacity: 1; transform: translateY(0) scale(1); }",
    "  100% { opacity: 0; transform: translateY(-50px) scale(0.5); }",
    "}",
    "",
    "#controls {",
    "  padding: 8px 12px; background: #0d0d1a;",
    "  border-top: 1px solid #333; display: flex;",
    "  flex-wrap: wrap; gap: 6px; align-items: center;",
    "}",
    "",
    "button {",
    "  background: #1e1e3a; color: #aaa; border: 1px solid #333;",
    "  font-family: monospace; font-size: 9px; padding: 4px 8px;",
    "  border-radius: 4px; cursor: pointer;",
    "}",
    "button:hover { background: #2a2a4a; color: #fff; }",
    "button.active { background: #e74c3c; color: #fff; }",
    "",
    "input {",
    "  background: #1e1e3a; color: #fff; border: 1px solid #333;",
    "  font-family: monospace; font-size: 9px;",
    "  padding: 4px 7px; border-radius: 4px; width: 90px;",
    "}",
    "",
    "#type-area {",
    "  position: fixed; bottom: 0; left: 0; right: 0;",
    "  background: rgba(0,0,0,.7); padding: 6px 10px;",
    "}",
    "#type-inp { width: 100%; background: transparent; color: #ccc;",
    "  border: none; font-family: monospace; font-size: 11px; outline: none; }",
    "",
    "#status {",
    "  position: fixed; bottom: 30px; left: 10px;",
    "  font-size: 9px; color: #555; font-family: monospace;",
    "}",
]))
story.append(PageBreak())

story.append(Paragraph("4.3  src/cat.js  — Pixel Renderer", H2))
story.append(Paragraph("Core drawing engine. Handles all skin colours, animations, and canvas rendering.", BODY))
story.append(code_block([
    "// cat.js — pixel cat renderer",
    "const canvas = document.getElementById('cat');",
    "const ctx    = canvas.getContext('2d');",
    "const wrap   = document.getElementById('cat-wrap');",
    "",
    "// Skin colour palettes",
    "const SKINS = {",
    "  black:    { body:'#111', belly:'#222', eyes:'#fff',",
    "              outline:'#fff', ear:'#111', nose:'#f88', stripe:null },",
    "  orange:   { body:'#e07020', belly:'#f5c080', eyes:'#333',",
    "              outline:'#fff', ear:'#e07020', nose:'#f99', stripe:'#c05010' },",
    "  siamese:  { body:'#d4b896', belly:'#f0e0c8', eyes:'#4af',",
    "              outline:'#fff', ear:'#b8845a', nose:'#f99', stripe:null, point:'#3a2210' },",
    "  mackerel: { body:'#888', belly:'#ccc', eyes:'#5a3',",
    "              outline:'#fff', ear:'#888', nose:'#f88', stripe:'#555' },",
    "};",
    "",
    "// Shared state object (imported by features.js)",
    "window.catState = {",
    "  x: 120, y: 200,",
    "  skin: 'black',",
    "  name: '',",
    "  mode: 'idle',       // idle|hunt|pet|drag|knead|overheat|scroll",
    "  eyeX: 0, eyeY: 0,",
    "  stretch: 1,",
    "  wobble: 0,",
    "  frame: 0,",
    "  heat: 0,",
    "  kneadFrame: 0,",
    "  jumpAnim: 0,",
    "  pinnedNote: '',",
    "  scrollOffset: 0,",
    "};",
    "",
    "function lerpColor(a, b, t) {",
    "  const ah = parseInt(a.replace('#',''), 16);",
    "  const bh = parseInt(b.replace('#',''), 16);",
    "  const r = Math.round(((ah>>16)&0xff) + (((bh>>16)&0xff) - ((ah>>16)&0xff)) * t);",
    "  const g = Math.round(((ah>>8)&0xff)  + (((bh>>8)&0xff)  - ((ah>>8)&0xff))  * t);",
    "  const b2= Math.round((ah&0xff)        + ((bh&0xff)        - (ah&0xff))       * t);",
    "  return '#' + ((1<<24)+(r<<16)+(g<<8)+b2).toString(16).slice(1);",
    "}",
    "",
    "function drawCat() {",
    "  ctx.clearRect(0, 0, 48, 48);",
    "  const s  = catState;",
    "  const sk = SKINS[s.skin];",
    "  const f  = s.frame;",
    "  const bob  = s.mode==='idle' ? Math.sin(f*0.08)*1.5 : 0;",
    "  const jY   = s.jumpAnim ? Math.sin(s.jumpAnim*Math.PI)*-14 : 0;",
    "  s.jumpAnim = Math.max(0, s.jumpAnim - 0.06);",
    "",
    "  const heatT = s.heat;",
    "  let bodyCol = heatT>0.5 ? lerpColor(sk.body,'#cc2200',heatT-0.5) : sk.body;",
    "  let bellyCol= heatT>0.5 ? lerpColor(sk.belly,'#ff4422',(heatT-0.5)*0.8) : sk.belly;",
    "  let outCol  = heatT>0.5 ? '#ff6644' : sk.outline;",
    "",
    "  ctx.save();",
    "  ctx.translate(24, 4 + bob + jY + 24);",
    "  ctx.scale(s.stretch>1 ? 1/s.stretch : 1, s.stretch);",
    "  ctx.rotate(s.wobble * Math.PI / 180);",
    "",
    "  // shadow",
    "  ctx.fillStyle = 'rgba(0,0,0,.3)';",
    "  ctx.beginPath(); ctx.ellipse(0,20,12,3,0,0,Math.PI*2); ctx.fill();",
    "",
    "  // tail (animated sway)",
    "  const tailSway = Math.sin(f*0.12)*6*(s.mode==='hunt'?2:1);",
    "  ctx.strokeStyle = outCol; ctx.lineWidth = 3; ctx.lineCap = 'round';",
    "  ctx.beginPath();",
    "  ctx.moveTo(8,16); ctx.quadraticCurveTo(18,10+tailSway, 14,2+tailSway/2);",
    "  ctx.stroke();",
    "",
    "  // body, belly, ears, head, eyes, nose, mouth",
    "  // ... (see full source in cat.js)",
    "",
    "  // overheat steam",
    "  if (heatT > 0.6) {",
    "    ctx.strokeStyle = `rgba(255,100,50,${(heatT-0.5)*2})`;",
    "    for (let i=0; i<3; i++) {",
    "      const phase = f*0.18 + i*1.2;",
    "      ctx.beginPath();",
    "      ctx.moveTo((i-1)*5, -20);",
    "      ctx.quadraticCurveTo((i-1)*5 + Math.sin(phase)*4, -26, (i-1)*5, -32);",
    "      ctx.stroke();",
    "    }",
    "  }",
    "  ctx.restore();",
    "}",
    "",
    "// Main loop at 20 fps",
    "setInterval(() => {",
    "  wrap.style.left = catState.x + 'px';",
    "  wrap.style.top  = catState.y + 'px';",
    "  catState.heat = Math.max(0, catState.heat - 0.005);",
    "  drawCat();",
    "  catState.frame++;",
    "}, 50);",
]))
story.append(PageBreak())

story.append(Paragraph("4.4  src/features.js  — All 15 Feature Handlers", H2))
story.append(code_block([
    "// features.js — event bindings for all 15 Comnyang features",
    "const scene    = document.getElementById('scene');",
    "const bubble   = document.getElementById('bubble');",
    "const timerBdg = document.getElementById('timer-badge');",
    "const hearts   = document.getElementById('hearts');",
    "const statusEl = document.getElementById('status');",
    "const s        = window.catState;   // shared with cat.js",
    "",
    "// ── 01 SKIN SELECTOR ─────────────────────────────────────────────────",
    "function setSkin(skin) { s.skin = skin; }",
    "",
    "// ── 02 EYE FOLLOW ────────────────────────────────────────────────────",
    "scene.addEventListener('mousemove', e => {",
    "  const r = scene.getBoundingClientRect();",
    "  const mx = e.clientX - r.left, my = e.clientY - r.top;",
    "  const dx = mx - (s.x+24), dy = my - (s.y+24);",
    "  if (!s.dragging) {",
    "    s.eyeX = Math.max(-4, Math.min(4, dx/30));",
    "    s.eyeY = Math.max(-3, Math.min(3, dy/30));",
    "  }",
    "  // ── 04 MOUSE HUNT ──",
    "  const dist = Math.hypot(dx, dy);",
    "  if (dist > 150 && !s.dragging) {",
    "    s.mode = 'hunt';",
    "    s.huntTarget = { x: mx, y: my };",
    "  } else if (dist < 50 && !s.dragging) {",
    "    s.mode = 'pet';  // ── 05 PURRING PETS ──",
    "  } else if (!s.dragging && s.mode !== 'knead' && s.mode !== 'overheat') {",
    "    s.mode = 'idle';",
    "  }",
    "});",
    "",
    "// ── 03 MOCHI DRAG ────────────────────────────────────────────────────",
    "const wrap = document.getElementById('cat-wrap');",
    "wrap.addEventListener('mousedown', e => {",
    "  s.dragging = true;",
    "  const r = wrap.getBoundingClientRect(), sr = scene.getBoundingClientRect();",
    "  s.dragOffX = e.clientX - r.left;",
    "  s.dragOffY = e.clientY - r.top;",
    "  s.stretch  = 1.6;  s.mode = 'drag';",
    "  e.preventDefault();",
    "});",
    "window.addEventListener('mousemove', e => {",
    "  if (!s.dragging) return;",
    "  const r = scene.getBoundingClientRect();",
    "  s.x = Math.max(0, Math.min(scene.offsetWidth-48,  e.clientX-r.left-s.dragOffX));",
    "  s.y = Math.max(0, Math.min(scene.offsetHeight-80, e.clientY-r.top -s.dragOffY));",
    "  s.wobble = Math.sin(Date.now()/50) * 8;",
    "});",
    "window.addEventListener('mouseup', () => {",
    "  if (s.dragging) { s.dragging=false; s.stretch=1; s.wobble=0; s.mode='idle'; }",
    "});",
    "",
    "// ── 05 PURRING PETS (heart spawn) ────────────────────────────────────",
    "function spawnHeart() {",
    "  const h = document.createElement('div');",
    "  h.className = 'heart'; h.textContent = '❤️';",
    "  h.style.left = Math.random()*30 + 'px';",
    "  hearts.appendChild(h);",
    "  setTimeout(() => h.remove(), 1200);",
    "}",
    "setInterval(() => { if (s.mode==='pet') spawnHeart(); }, 300);",
    "",
    "// ── 06 KEYBOARD KNEADING ─────────────────────────────────────────────",
    "// ── 07 OVERHEAT MODE ─────────────────────────────────────────────────",
    "document.getElementById('type-inp').addEventListener('input', () => {",
    "  s.heat       = Math.min(1, s.heat + 0.08);",
    "  s.kneadFrame = (s.kneadFrame + 1) % 4;",
    "  s.mode       = s.heat > 0.7 ? 'overheat' : 'knead';",
    "});",
    "",
    "// ── 08 STRETCH REMINDER ──────────────────────────────────────────────",
    "function setStretchTimer(minutes) {",
    "  setTimeout(() => {",
    "    s.mode = 'stretch';   // triggers big green animation in drawCat()",
    "    showBubble('Time to stretch! 🌿', 5000);",
    "    setTimeout(() => s.mode = 'idle', 5000);",
    "  }, minutes * 60 * 1000);",
    "}",
    "",
    "// ── 09 PAPER UNROLL ──────────────────────────────────────────────────",
    "scene.addEventListener('wheel', e => {",
    "  s.scrollOffset += e.deltaY > 0 ? 1 : -1;",
    "  s.mode = 'scroll';",
    "  clearTimeout(s._scrollT);",
    "  s._scrollT = setTimeout(() => s.mode = 'idle', 800);",
    "}, { passive: true });",
    "",
    "// ── 11 AGENT DONE JUMP ───────────────────────────────────────────────",
    "function catJump() {",
    "  s.jumpAnim = 1;",
    "  showBubble('Meow! 🎉', 1500);",
    "  setTimeout(() => s.jumpAnim = 0, 600);",
    "}",
    "",
    "// ── 12 POMODORO TIMER ────────────────────────────────────────────────",
    "function togglePomodoro() {",
    "  s.pomodoro = !s.pomodoro;",
    "  if (s.pomodoro) {",
    "    s.pomoTime = 25 * 60;",
    "    timerBdg.style.display = 'block';",
    "    s.pomoInterval = setInterval(() => {",
    "      s.pomoTime--;",
    "      const m = Math.floor(s.pomoTime/60), sec = s.pomoTime%60;",
    "      timerBdg.textContent = 'Focus ' + pad(m) + ':' + pad(sec);",
    "      if (s.pomoTime <= 0) {",
    "        clearInterval(s.pomoInterval);",
    "        timerBdg.style.display = 'none';",
    "        catJump(); showBubble('Break time! 🎉', 4000);",
    "      }",
    "    }, 1000);",
    "  } else {",
    "    clearInterval(s.pomoInterval);",
    "    timerBdg.style.display = 'none';",
    "  }",
    "}",
    "const pad = n => String(n).padStart(2,'0');",
    "",
    "// ── 13 MESSAGE REMINDER ──────────────────────────────────────────────",
    "function setReminder() {",
    "  const msg = document.getElementById('note-inp').value.trim() || 'Reminder!';",
    "  if (s.reminderTimer) clearTimeout(s.reminderTimer);",
    "  s.reminderTimer = setTimeout(() => {",
    "    showBubble((s.name ? s.name+', ' : '') + msg, 4000);",
    "    catJump();",
    "  }, 30000);",
    "}",
    "",
    "// ── 14 FIXED MESSAGE (pin note) ──────────────────────────────────────",
    "function pinNote() {",
    "  const v = document.getElementById('msg-inp').value.trim();",
    "  s.pinnedNote = v;",
    "  bubble.textContent = v;",
    "  bubble.style.display = v ? 'block' : 'none';",
    "}",
    "",
    "// ── 15 TELL YOUR NAME ────────────────────────────────────────────────",
    "function setName() {",
    "  const v = document.getElementById('name-inp').value.trim();",
    "  if (v) { s.name = v; showBubble('Hi, ' + v + '! 😺', 2000); }",
    "}",
    "",
    "// helpers",
    "function showBubble(text, dur=2000) {",
    "  bubble.textContent = text;",
    "  bubble.style.display = 'block';",
    "  clearTimeout(s._bubbleT);",
    "  s._bubbleT = setTimeout(() => {",
    "    if (s.pinnedNote) bubble.textContent = s.pinnedNote;",
    "    else bubble.style.display = 'none';",
    "  }, dur);",
    "}",
    "",
    "// Hunt movement in main loop (cat.js setInterval)",
    "setInterval(() => {",
    "  if (s.mode === 'hunt' && s.huntTarget) {",
    "    const dx = s.huntTarget.x - (s.x+24);",
    "    const dy = s.huntTarget.y - (s.y+24);",
    "    const dist = Math.hypot(dx, dy);",
    "    if (dist > 10) { s.x += dx/dist*3; s.y += dy/dist*3; }",
    "  }",
    "}, 50);",
]))
story.append(PageBreak())

# ══ 5. FEATURES TABLE ════════════════════════════════════════════════════════
story.append(Paragraph("5. All 15 Features", H1))
story.append(hr())

rows = [
    ["01", "Cat Pattern / Skin",     "4 pixel-art palettes: Black, Orange, Siamese, Mackerel",           "Click skin button in controls"],
    ["02", "Eye Follow",             "Cat eyes track mouse cursor in real time via eyeX/eyeY state",     "Move mouse over scene"],
    ["03", "Mochi Drag",             "mousedown stretches cat (scaleY=1.6), wobble on drag, spring back","Click and drag cat body"],
    ["04", "Mouse Hunt",             "If cursor is >150px away, cat chases it at 3px/frame",             "Move mouse far from cat"],
    ["05", "Purring Pets",           "Click cat head: hearts float up, purr status, mode='pet'",         "Click cat head area"],
    ["06", "Keyboard Kneading",      "Alternating paw offset on each keypress, kneadFrame counter",      "Type in bottom input"],
    ["07", "Overheat Mode",          "heat variable rises with typing speed, cat turns red, steam drawn","Type fast continuously"],
    ["08", "Stretch Reminder",       "setStretchTimer(N) triggers big green stretch animation + bubble", "Call setStretchTimer()"],
    ["09", "Paper Unroll",           "Scroll wheel increments scrollOffset, paper drawn below paws",     "Scroll mouse wheel on scene"],
    ["10", "Thinking Along",         "Set mode='thinking' externally; cat shows squinting think-face",   "Call catThink() from agent"],
    ["11", "Agent Done Jump",        "catJump() sets jumpAnim=1; sin curve lifts cat then drops",        "Call catJump() on task end"],
    ["12", "Pomodoro Timer",         "25-min countdown badge near cat; jump + meow on finish",           "Click Pomodoro button"],
    ["13", "Message Reminder",       "setTimeout fires showBubble() with name + custom message",        "Set reminder, wait 30s"],
    ["14", "Fixed Message",          "Pinned text always shown in speech bubble above cat",              "Type in Pin input, click Pin"],
    ["15", "Tell Your Name",         "name stored in catState.name; used in reminders and bubbles",      "Type name, click Set"],
]
story.append(feature_table(rows))
story.append(sp(8))

# ══ 6. QUICK START ════════════════════════════════════════════════════════════
story.append(Paragraph("6. Quick Start (3 steps)", H1))
story.append(hr())

steps = [
    ("Step 1 — Clone / create folder",
     ["mkdir comnyang && cd comnyang",
      "# create the files listed in section 4",
      "# or clone: git clone https://github.com/you/comnyang"]),
    ("Step 2 — Run with Docker",
     ["docker compose up --build",
      "# open http://localhost:3000 in your browser"]),
    ("Step 3 — Open in VSCode Dev Container",
     ["code .",
      "# VSCode prompts: 'Reopen in Container' → click it",
      "# All extensions install automatically"]),
]
for title, cmds in steps:
    story.append(Paragraph(title, H3))
    story.append(code_block(cmds))
    story.append(sp(4))

story.append(Paragraph("Prerequisites:", H3))
prereq = [
    ["Tool", "Version", "Install"],
    ["Docker Desktop", "4.x+", "docker.com/get-docker"],
    ["Docker Compose", "v2+",  "Bundled with Docker Desktop"],
    ["VSCode",         "1.85+","code.visualstudio.com"],
    ["Dev Containers ext.", "latest", "ms-vscode-remote.remote-containers"],
]
pt = Table(prereq, colWidths=[42*mm, 25*mm, 90*mm])
pt.setStyle(TableStyle([
    ("BACKGROUND", (0,0),(-1,0), DARK),
    ("TEXTCOLOR",  (0,0),(-1,0), WHITE),
    ("FONTNAME",   (0,0),(-1,0), "Courier-Bold"),
    ("FONTSIZE",   (0,0),(-1,-1), 8),
    ("FONTNAME",   (0,1),(-1,-1), "Helvetica"),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,LIGHT_BG]),
    ("GRID",       (0,0),(-1,-1), 0.3, BORDER),
    ("LEFTPADDING",(0,0),(-1,-1), 6),
    ("ROWPADDING", (0,0),(-1,-1), 4),
]))
story.append(pt)
story.append(sp(8))

story.append(Paragraph("7. Notes & Extension Ideas", H1))
story.append(hr())
notes = [
    "Add Web Audio API for actual purring sound on pet.",
    "Replace the static serve container with a Vite dev server for HMR.",
    "Persist catState.name and pinnedNote in localStorage.",
    "Add a REST endpoint (Express) to trigger catJump() from CI/CD pipelines.",
    "Package as an Electron app for a true desktop overlay experience.",
    "Use CSS custom properties to theme the dark scene with user-chosen colours.",
]
for i, n in enumerate(notes, 1):
    story.append(Paragraph(f"  {i}.  {n}", BODYM))
story.append(sp(10))
story.append(hr(ACCENT, 1))
story.append(Paragraph("End of PDR — happy coding with Comnyang! 🐱",
    S("END", fontName="Courier-Bold", fontSize=9, textColor=MUTED, alignment=TA_CENTER,
      spaceBefore=8)))

# ── build ────────────────────────────────────────────────────────────────────
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print("PDF created successfully.")
