"""
Build docs/bot_workflow.pdf from the three Mermaid diagrams.

Strategy
--------
1. Send each diagram to the public mermaid.ink renderer and fetch a PNG.
2. Inline the PNGs (base64) into a landscape-A4 HTML page so the PDF has no
   external dependencies and no JS-rendering race conditions.
3. Print the HTML to PDF using headless Microsoft Edge.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import textwrap
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(HERE, "bot_workflow.html")
PDF_PATH = os.path.join(HERE, "bot_workflow.pdf")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# ---------------------------------------------------------------------------
# 1. Diagrams
# ---------------------------------------------------------------------------

DIAGRAM_1 = textwrap.dedent("""\
    flowchart LR
        Start([Bot started]) --> Init[INIT<br/>Login &amp; connect to Pioneer]
        Init -- success --> GetData[GET_DATA<br/>Fetch next patient from API]
        Init -- system error<br/>retry up to N --> Init

        GetData -- no records --> Wait[Wait 30s] --> GetData
        GetData -- patient received --> Process[PROCESS patient<br/>see Diagram 2]

        Process -- all Rx saved --> Success([API: pms_synced])
        Process -- nothing to do --> Skipped([API: skipped])
        Process -- business rule failure --> BizErr([API: failed])
        Process -- system / UI failure --> SysErr([API: failed<br/>retry or END])

        Success --> GetData
        Skipped --> GetData
        BizErr --> GetData
        SysErr --> GetData

        style Success fill:#d4edda,stroke:#28a745,color:#0f5132
        style Skipped fill:#fff3cd,stroke:#ffc107,color:#664d03
        style BizErr fill:#f8d7da,stroke:#dc3545,color:#842029
        style SysErr fill:#f8d7da,stroke:#dc3545,color:#842029
""")

DIAGRAM_2 = textwrap.dedent("""\
    flowchart TD
        Start([Process patient]) --> PickIns[Use the patient's<br/>primary insurance from API]
        PickIns --> OpenFirst[Open first Rx<br/>search in Rx Profile, click Edit]
        OpenFirst --> Popups1[Handle priority &amp; other popups]
        Popups1 --> PreCheck{Dispense Primary combo<br/>already shows this<br/>cardholder ID?}

        PreCheck -- YES --> SkipAll[Cancel first Rx without save<br/>SKIP all remaining Rx<br/>API: pms_synced]
        SkipAll --> Done([Patient done])

        PreCheck -- NO --> EditPatient[Open Edit Patient<br/>pencil icon]
        EditPatient --> Grid{Cardholder ID in<br/>Pay Methods grid?}

        Grid -- YES EXISTS --> CaptureExisting[Capture payer name<br/>from matching row]
        Grid -- NO ADD --> Binocular[Binocular advanced search<br/>BIN + PCN<br/>PCN blank = BIN only<br/>pick first row without PCN]

        Binocular --> SearchResult{Plan returned?}
        SearchResult -- NO --> CancelChain[Cancel Search<br/>Cancel Pay Method<br/>Cancel Edit Patient<br/>API: failed]
        CancelChain --> BizFail([Patient failed])

        SearchResult -- YES --> CaptureNew[Select row<br/>capture Display Name<br/>fill cardholder, group, billing<br/>save Edit Patient]

        CaptureExisting --> SetPri[Set Primary on Dispense<br/>verify, type P+first word + Tab,<br/>re-verify up to 3x]
        CaptureNew --> SetPri

        SetPri --> Verified{Cardholder digits<br/>now in Primary?}
        Verified -- NO --> RxFail[Cancel this Rx<br/>screenshot saved<br/>raise business error]
        Verified -- YES --> PickRph[Select RPh<br/>Stephanie Erwin]
        PickRph --> Save[Save &amp; Continue<br/>see Diagram 3]

        Save -- saved OK --> NextLoop{More Rx for<br/>this patient?}
        Save -- non-bypassable error --> RxFail

        RxFail --> NextLoop

        NextLoop -- NO --> Done
        NextLoop -- YES --> NextRx[Open next Rx]
        NextRx --> SetPri2[Set Primary using the<br/>SAME captured plan name]
        SetPri2 --> Verified2{Cardholder digits<br/>in Primary?}
        Verified2 -- NO --> RxFail2[Cancel this Rx<br/>continue to next]
        Verified2 -- YES --> PickRph2[Select RPh]
        PickRph2 --> Save2[Save &amp; Continue]
        Save2 --> NextLoop
        RxFail2 --> NextLoop

        style SkipAll fill:#d4edda,stroke:#28a745,color:#0f5132
        style Done fill:#d4edda,stroke:#28a745,color:#0f5132
        style BizFail fill:#f8d7da,stroke:#dc3545,color:#842029
        style CancelChain fill:#f8d7da,stroke:#dc3545,color:#842029
        style RxFail fill:#f8d7da,stroke:#dc3545,color:#842029
        style RxFail2 fill:#fff3cd,stroke:#ffc107,color:#664d03
""")

DIAGRAM_3 = textwrap.dedent("""\
    flowchart LR
        Start([Click Save &amp; Continue]) --> EqRx[Equivalent Rx popup<br/>click Fill Anyway]
        EqRx --> EW{Error / Warning<br/>List appeared?}

        EW -- No / bypassable --> Alerts[Alerts popup<br/>fill captcha if shown<br/>Save &amp; Continue]
        EW -- Yes,<br/>non-bypassable --> Classify{Error type?}

        Classify -- third party<br/>setup error --> FixSec[Apply Pioneer<br/>recommended fix]
        Classify -- DAW error --> FixDaw[Toggle DAW<br/>checkbox]
        Classify -- Other --> Fatal[Screenshot saved<br/>Cancel Rx]

        FixSec --> Retry[Save &amp; Continue<br/>again]
        FixDaw --> Retry
        Retry --> EW2{Still<br/>non-bypassable?}
        EW2 -- Yes --> Fatal
        EW2 -- No --> Alerts

        Alerts --> Pending[Equivalent Pending Rx<br/>click Ignore and Continue]
        Pending --> RxDone([Rx saved<br/>successfully])

        Fatal --> RxSkipped([Rx skipped<br/>moves to next Rx])

        style RxDone fill:#d4edda,stroke:#28a745,color:#0f5132
        style RxSkipped fill:#fff3cd,stroke:#ffc107,color:#664d03
        style Fatal fill:#f8d7da,stroke:#dc3545,color:#842029
""")


# ---------------------------------------------------------------------------
# 2. Mermaid.ink renderer
# ---------------------------------------------------------------------------

def fetch_diagram_png(source: str, retries: int = 3) -> bytes:
    """Render a Mermaid diagram via mermaid.ink and return PNG bytes."""
    payload = {
        "code": source.strip(),
        "mermaid": {"theme": "default"},
    }
    b64 = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    url = f"https://mermaid.ink/img/{b64}?type=png&bgColor=FFFFFF"
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (PioneerInsuranceBot/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status}")
                return resp.read()
        except Exception as e:  # noqa: BLE001 — retry on any transient error
            last_err = e
            print(f"  attempt {attempt} failed: {e}")
    raise RuntimeError(f"mermaid.ink fetch failed: {last_err}") from last_err


def png_to_data_uri(png_bytes: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")


# ---------------------------------------------------------------------------
# 3. HTML assembly
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Pioneer Insurance Bot — Workflow</title>
<style>
  @page {
    size: A4 landscape;
    margin: 12mm 14mm;
  }
  * { box-sizing: border-box; }
  body {
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    color: #1f2937;
    margin: 0;
    padding: 0;
    background: #ffffff;
    line-height: 1.5;
  }
  header {
    padding: 18px 28px;
    background: linear-gradient(135deg, #0f4c81 0%, #1e6fb8 100%);
    color: #ffffff;
  }
  header h1 { margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 0.3px; }
  header p { margin: 4px 0 0 0; font-size: 13px; opacity: 0.92; }

  main { padding: 18px 28px 28px 28px; }
  h2 {
    color: #0f4c81;
    font-size: 18px;
    margin: 4px 0 8px 0;
    padding-bottom: 6px;
    border-bottom: 2px solid #dbeafe;
  }
  h2 .badge {
    display: inline-block;
    background: #0f4c81;
    color: #ffffff;
    font-size: 11px;
    padding: 2px 9px;
    margin-right: 8px;
    border-radius: 999px;
    vertical-align: middle;
  }
  h3 { color: #1e3a8a; font-size: 14px; margin: 14px 0 4px 0; }
  p, li { font-size: 12.5px; }
  ul { padding-left: 20px; margin: 4px 0 10px 0; }
  ul li { margin-bottom: 3px; }

  .narrative {
    background: #f0f7ff;
    border: 1px solid #bfdbfe;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 8px 0;
    font-size: 12.5px;
  }
  .narrative ol { padding-left: 18px; margin: 4px 0; }
  .narrative ol li { margin-bottom: 4px; }

  table {
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0 12px 0;
    font-size: 12px;
  }
  table th, table td {
    border: 1px solid #d1d5db;
    padding: 6px 10px;
    text-align: left;
    vertical-align: top;
  }
  table th { background: #f1f5f9; color: #0f4c81; font-weight: 600; }

  .legend {
    background: #f8fafc;
    border-left: 4px solid #0f4c81;
    padding: 8px 14px;
    margin: 10px 0;
    border-radius: 4px;
    font-size: 12px;
  }
  .legend strong { color: #0f4c81; }

  /*
   * Each diagram lives in its own full-page section. The image is given an
   * explicit max-height in millimetres (NOT a percentage) so it always fits
   * within the landscape-A4 printable area regardless of how flex shakes
   * out in the print pipeline.
   *
   * Landscape A4 = 297mm wide, 210mm tall. With 12mm top/bottom @page
   * margins the printable area is 186mm tall. Subtracting heading + intro
   * paragraph + frame chrome leaves ~155mm safely available for the image.
   */
  .page { page-break-after: always; }
  .page:last-child { page-break-after: auto; }

  .diagram-page main { padding-bottom: 6mm; }
  .diagram-page h2 { margin-top: 0; }
  .diagram-page p { margin: 4px 0 8px 0; font-size: 12px; }
  .diagram-page .diagram-frame {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 4mm;
    background: #ffffff;
    text-align: center;
    margin-top: 4mm;
  }
  .diagram-page .diagram-frame img {
    display: block;
    margin: 0 auto;
    /* Hard caps so the image always fits the landscape-A4 page. */
    max-width: 260mm;
    max-height: 155mm;
    width: auto;
    height: auto;
  }

  .footer {
    margin-top: 18px;
    padding-top: 8px;
    border-top: 1px solid #e5e7eb;
    color: #6b7280;
    font-size: 10.5px;
    text-align: center;
  }

  code {
    background: #f1f5f9;
    color: #0f172a;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 11.5px;
    font-family: "Consolas", "Courier New", monospace;
  }
</style>
</head>
<body>

<div class="page">
<header>
  <h1>Pioneer Insurance Bot — Workflow</h1>
  <p>End-to-end automation for adding / verifying patient insurance and saving prescriptions in Pioneer</p>
</header>
<main>
<div class="narrative">
  <strong>What this bot does, in one paragraph.</strong>
  The bot logs into Pioneer, fetches the next patient from the CloudRx API, and for each prescription either confirms the correct insurance is already configured or adds/selects it before saving the Rx. It handles every standard Pioneer popup along the way and auto-recovers from the two most common save-time errors. Each patient ends with exactly one API status update — <code>pms_synced</code>, <code>skipped</code>, or <code>failed</code>.
</div>

<h3>How to read this document</h3>
<ul>
  <li><strong>Diagram 1</strong> — the bot's state machine (the outer loop that drives everything).</li>
  <li><strong>Diagram 2</strong> — how a single patient is processed end-to-end.</li>
  <li><strong>Diagram 3</strong> — the post-save popup &amp; recovery flow that runs after every Save &amp; Continue.</li>
</ul>

<h3>Color key (used in every diagram)</h3>
<table>
  <tr><th style="width:30%">Color</th><th>Meaning</th></tr>
  <tr><td style="background:#d4edda;color:#0f5132;font-weight:600">Green</td><td>Success outcome — patient/Rx is done, API marked <code>pms_synced</code>.</td></tr>
  <tr><td style="background:#fff3cd;color:#664d03;font-weight:600">Yellow</td><td>Soft skip — a single Rx was bypassed, but the rest of the patient continues.</td></tr>
  <tr><td style="background:#f8d7da;color:#842029;font-weight:600">Red</td><td>Hard failure — patient marked <code>failed</code> in the API.</td></tr>
</table>
</main>
</div>

<div class="page diagram-page">
<main>
<h2><span class="badge">Diagram 1</span>Top-level state machine</h2>
<p>The bot runs as a long-lived state machine — <strong>INIT → GET_DATA → PROCESS → END</strong>. On success the cycle returns to <code>GET_DATA</code> for the next patient. The bot runs 24×7.</p>
<div class="diagram-frame"><img src="{IMG_1}" alt="Top-level state machine"></div>
</main>
</div>

<div class="page diagram-page">
<main>
<h2><span class="badge">Diagram 2</span>Per-patient: insurance &amp; Rx workflow</h2>
<p>For each patient, the bot opens the first prescription and follows this decision tree. If the patient is already fully configured (cardholder ID already on the Primary insurance field), the bot does nothing and skips every remaining Rx for that patient.</p>
<div class="diagram-frame"><img src="{IMG_2}" alt="Per-patient workflow"></div>
</main>
</div>

<div class="page">
<main>
<h2>Decision points (Diagram 2) explained</h2>
<table>
<thead><tr><th style="width:30%">Decision</th><th>Plain English</th></tr></thead>
<tbody>
<tr><td><strong>Dispense pre-check</strong></td><td>"Is this patient's correct insurance already showing as Primary on the prescription?" If yes, the bot does nothing — the patient is already fully configured.</td></tr>
<tr><td><strong>Pay Methods grid check</strong></td><td>"Is the right insurance card already in the patient's profile?" If yes, no add is needed — the bot just selects it as Primary.</td></tr>
<tr><td><strong>Binocular advanced search</strong></td><td>When the insurance is missing, the bot uses Pioneer's magnifying-glass icon to look up plans by BIN/PCN — exactly like a pharmacist would.</td></tr>
<tr><td><strong>"(P) + first word" shortcut</strong></td><td>Pioneer's typing shortcut to switch the Primary combo. Using the first word of the plan name (e.g. <code>(P)BCBS</code>) is needed when the patient has multiple Primary plans on file.</td></tr>
<tr><td><strong>Verification</strong></td><td>After every Primary selection the bot re-reads the field and confirms the patient's cardholder ID is in it. If not, the Rx is cancelled rather than saved against the wrong insurance.</td></tr>
</tbody>
</table>
</main>
</div>

<div class="page diagram-page">
<main>
<h2><span class="badge">Diagram 3</span>Save &amp; Continue — post-save recovery flow</h2>
<p>Every <strong>Save &amp; Continue</strong> click goes through the same checked sequence of popups. Two common non-bypassable errors are auto-fixed and retried; anything else cancels that one prescription and moves on.</p>
<div class="diagram-frame"><img src="{IMG_3}" alt="Save and Continue recovery"></div>
</main>
</div>

<div class="page">
<main>
<h2>Summary for stakeholders</h2>
<div class="narrative">
<ol>
<li><strong>Pre-check</strong> — if the patient's correct insurance is already selected on the Dispense tab, the bot does nothing and marks the patient <code>pms_synced</code>.</li>
<li><strong>Profile check</strong> — otherwise it opens the patient's profile and either picks up the existing insurance card or adds a new one via the binocular search (BIN + PCN).</li>
<li><strong>Primary selection</strong> — the bot selects the matching plan as Primary on the prescription, verifies it took, and only then runs Save &amp; Continue.</li>
<li><strong>Save recovery</strong> — the save flow handles every popup. For non-bypassable errors it auto-fixes the two common ones (third-party-setup-only and DAW) and re-saves. Other non-bypassable errors cancel that single prescription.</li>
<li><strong>All other Rx</strong> — every subsequent prescription for the same patient runs the same Primary verification using the plan name captured during step 2/3.</li>
<li><strong>One API call</strong> — the portal is updated exactly once per patient with <code>pms_synced</code>, <code>failed</code>, or <code>skipped</code>.</li>
</ol>
</div>

<div class="legend">
<strong>What the bot auto-recovers from during save:</strong>
<ul>
<li><strong>Third-party setup errors</strong> — bot applies the Pioneer-recommended fix and re-saves.</li>
<li><strong>DAW (Dispense As Written) errors</strong> — bot toggles the DAW checkbox and re-saves.</li>
</ul>
Any other non-bypassable error is treated as a real issue: the bot saves a screenshot, cancels that single prescription, and moves on.
</div>

<div class="footer">
Pioneer Insurance Bot &middot; CloudRx Automation &middot; Generated for stakeholder review
</div>
</main>
</div>

</body>
</html>
"""


def build_html(img1_uri: str, img2_uri: str, img3_uri: str) -> str:
    return (
        HTML_TEMPLATE
        .replace("{IMG_1}", img1_uri)
        .replace("{IMG_2}", img2_uri)
        .replace("{IMG_3}", img3_uri)
    )


# ---------------------------------------------------------------------------
# 4. Edge headless print
# ---------------------------------------------------------------------------

def print_to_pdf(html_path: str, pdf_path: str) -> None:
    if not os.path.isfile(EDGE_PATH):
        raise RuntimeError(f"Edge not found at {EDGE_PATH}")
    file_url = "file:///" + html_path.replace("\\", "/")
    print(f"  HTML : {html_path}")
    print(f"  PDF  : {pdf_path}")
    cmd = [
        EDGE_PATH,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        file_url,
    ]
    subprocess.run(cmd, check=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    diagrams = [
        ("Diagram 1 — state machine", DIAGRAM_1),
        ("Diagram 2 — per-patient workflow", DIAGRAM_2),
        ("Diagram 3 — Save & Continue recovery", DIAGRAM_3),
    ]
    data_uris: list[str] = []
    for name, src in diagrams:
        print(f"Rendering: {name}")
        png_bytes = fetch_diagram_png(src)
        print(f"  got {len(png_bytes)} bytes")
        data_uris.append(png_to_data_uri(png_bytes))

    print("Assembling HTML...")
    html = build_html(*data_uris)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print("Printing PDF...")
    print_to_pdf(HTML_PATH, PDF_PATH)

    print(f"\nDone. PDF: {PDF_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
