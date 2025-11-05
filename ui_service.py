"""
ui_service.py

FastAPI microservice for Whatsafe UI:
- Serves an HTML form to upload WhatsApp .txt exports.
- Sends the content to the Detection Service over HTTP.
- Renders the analysis result as an HTML page.
"""

from typing import Dict, Any  # Type hints for clarity

from fastapi import FastAPI, UploadFile, File  # FastAPI web framework + file upload support
from fastapi.responses import HTMLResponse    # For HTML responses
import httpx                                  # HTTP client for calling the detection microservice
import pandas as pd                           # For clean tables


# Create a FastAPI application instance for the UI microservice
app = FastAPI(
    title="Whatsafe UI Service",
    description="Frontend service for Whatsafe - handles file upload and displays results.",
    version="1.0.0",
)


def render_result_html(result: Dict[str, Any]) -> str:
    """
    Build a minimal HTML page to display the analysis result.

    This is intentionally simple and does not use templates,
    but it is enough to demonstrate a clear UI.
    """
    risk = result["risk_signals"]["boycott_risk"]
    label = result["label"]
    per_sender = result["per_sender_stats"]
    target = result["potential_target"]
    target_mentions = result["target_mentions"]

    # Build pandas table for per-sender stats
    df = (
        pd.DataFrame.from_dict(per_sender, orient="index")
        .reset_index()
        .rename(columns={"index": "Sender", "messages": "Messages", "chars": "Chars", "boycott_msgs": "Boycott messages"})
    )
    table_html = df.to_html(index=False, classes="table")

    # Prepare chart data
    senders = list(per_sender.keys())
    msgs = [per_sender[s]["messages"] for s in senders]
    boycott = [per_sender[s]["boycott_msgs"] for s in senders]

    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8' />",
        "<title>WhatSafe - WhatsApp Boycott Detector</title>",
        "<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>",
        "<style>",
        ":root { --bg:#0f172a; --panel:#111827; --muted:#94a3b8; --text:#e5e7eb; --accent:#60a5fa; --accent2:#f59e0b; --ok:#34d399; --warn:#f59e0b; --danger:#ef4444; }",
        "body { margin:0; font-family: Inter, ui-sans-serif, system-ui; background:linear-gradient(180deg,#0b1220,#0b1220 50%,#0a0f1c); color:var(--text); }",
        ".container { max-width:1024px; margin:40px auto; padding:0 20px; }",
        ".card { background:rgba(17,24,39,0.8); backdrop-filter: blur(10px); border:1px solid #243244; border-radius:14px; padding:24px; box-shadow:0 10px 30px rgba(0,0,0,0.3); }",
        ".title { display:flex; align-items:center; gap:12px; margin:0 0 16px 0; }",
        ".badge { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; background:#0b1324; border:1px solid #1f2a44; color:var(--muted); }",
        ".grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:16px; }",
        ".kpi { background:#0b1324; border:1px solid #1f2a44; border-radius:12px; padding:16px; }",
        ".kpi h3 { margin:0 0 8px 0; font-size:13px; color:var(--muted); font-weight:600; }",
        ".kpi .value { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:22px; }",
        ".value.ok{ color:var(--ok);} .value.warn{color:var(--warn);} .value.danger{color:var(--danger);} ",
        ".section { margin-top:24px; }",
        ".section h2 { font-size:16px; color:var(--muted); letter-spacing:.02em; margin:0 0 8px 0; }",
        ".table { width:100%; border-collapse: collapse; }",
        ".table th, .table td { padding:10px 12px; border-bottom:1px solid #1f2a44; }",
        ".table th { text-align:left; color:var(--muted); font-weight:600; background:#0b1324; }",
        ".table tr:hover td { background:rgba(36,50,68,0.25); }",
        ".target-pill { display:inline-block; margin-top:6px; padding:6px 10px; background:#0b1324; border:1px solid #1f2a44; border-radius:999px; }",
        ".footer { margin-top:20px; display:flex; gap:12px; }",
        ".btn { color:var(--text); text-decoration:none; padding:10px 14px; border-radius:10px; border:1px solid #1f2a44; background:#0b1324; }",
        ".btn:hover { background:#0c1530; }",
        "</style>",
        "</head>",
        "<body>",
        "<div class='container'>",
        "  <div class='card'>",
        "    <div class='title'>",
        "      <h1 style='font-size:20px; margin:0;'>WhatSafe - WhatsApp Boycott Detector</h1>",
        "      <span class='badge'>Analysis</span>",
        "    </div>",
        "    <div class='grid'>",
        "      <div class='kpi'>",
        "        <h3>Risk label</h3>",
        f"        <div class='value'>{label}</div>",
        "      </div>",
        "      <div class='kpi'>",
        "        <h3>Risk score</h3>",
        f"        <div class='value {'danger' if risk>=0.75 else 'warn' if risk>=0.5 else 'ok'}'>{risk}</div>",
        "      </div>",
        "      <div class='kpi'>",
        "        <h3>Total messages</h3>",
        f"        <div class='value'>{int(result['risk_signals']['total_messages'])}</div>",
        "      </div>",
        "      <div class='kpi'>",
        "        <h3>Boycott messages</h3>",
        f"        <div class='value'>{int(result['risk_signals']['boycott_messages'])}</div>",
        "      </div>",
        "    </div>",
        "    <div class='grid section'>",
        "      <div class='kpi'>",
        "        <h3>Messages per sender</h3>",
        "        <canvas id='msgsChart' height='160'></canvas>",
        "      </div>",
        "      <div class='kpi'>",
        "        <h3>Boycott msgs per sender</h3>",
        "        <canvas id='boycottChart' height='160'></canvas>",
        "      </div>",
        "    </div>",
        "    <div class='section'>",
        "      <h2>Per-sender statistics</h2>",
        table_html,
        "    </div>",
        "    <div class='section'>",
        "      <h2>Potential target</h2>",
    ]

    # Mentions and target section

    # Show potential target if available
    if target is None:
        html_parts.append("<p>No clear target detected.</p>")
    else:
        html_parts.append(f"<p>Candidate name/word: <span class='target-pill'><strong>{target}</strong></span></p>")

    html_parts.append("<h3>Top mentions in boycott-related messages</h3>")

    # Show top mentions in boycott-related context
    if not target_mentions:
        html_parts.append("<p>No boycott-related messages found.</p>")
    else:
        html_parts.append("<ul>")
        for word, count in target_mentions:
            html_parts.append(f"<li>{word}: {count}</li>")
        html_parts.append("</ul>")

    html_parts.append("<div class='footer'>")
    html_parts.append("  <a class='btn' href='/'>Analyze another file</a>")
    html_parts.append("</div>")

    # Charts script
    html_parts.append("<script>")
    html_parts.append(f"const senders = {senders!r};")
    html_parts.append(f"const msgs = {msgs!r};")
    html_parts.append(f"const boycott = {boycott!r};")
    html_parts.append("const ctx1 = document.getElementById('msgsChart').getContext('2d');")
    html_parts.append("new Chart(ctx1, { type:'bar', data:{ labels: senders, datasets:[{ label:'Messages', data: msgs, backgroundColor: 'rgba(96,165,250,0.6)', borderColor:'#60a5fa', borderWidth:1 }] }, options:{ plugins:{legend:{labels:{color:'#e5e7eb'}}}, scales:{ x:{ ticks:{color:'#94a3b8'}}, y:{ ticks:{color:'#94a3b8'}, beginAtZero:true } } } });")
    html_parts.append("const ctx2 = document.getElementById('boycottChart').getContext('2d');")
    html_parts.append("new Chart(ctx2, { type:'bar', data:{ labels: senders, datasets:[{ label:'Boycott msgs', data: boycott, backgroundColor: 'rgba(239,68,68,0.6)', borderColor:'#ef4444', borderWidth:1 }] }, options:{ plugins:{legend:{labels:{color:'#e5e7eb'}}}, scales:{ x:{ ticks:{color:'#94a3b8'}}, y:{ ticks:{color:'#94a3b8'}, beginAtZero:true } } } });")
    html_parts.append("</script>")

    html_parts.append("</div>")  # container end
    html_parts.append("</body></html>")

    # Join all parts into a single HTML string
    return "".join(html_parts)


@app.get("/", response_class=HTMLResponse)
async def upload_form() -> str:
    """
    Serve a simple HTML page with a form to upload a WhatsApp .txt export.

    This is the main entry point for end-users via a web browser.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>WhatSafe - WhatsApp Boycott Detector</title>
        <style>
            :root { --bg:#0f172a; --panel:#111827; --muted:#94a3b8; --text:#e5e7eb; }
            body { margin:0; font-family: Inter, ui-sans-serif, system-ui; background:#0b1220; color:var(--text); overflow-x:hidden; }
            /* Animated background */
            .bg { position: fixed; inset: 0; z-index: 0; pointer-events:none;
                 background:
                   radial-gradient(1200px 600px at 10% -20%, rgba(59,130,246,0.20), transparent 60%),
                   radial-gradient(800px 400px at 90% 0%, rgba(236,72,153,0.18), transparent 60%),
                   radial-gradient(900px 500px at 40% 120%, rgba(34,197,94,0.16), transparent 60%),
                   linear-gradient(180deg, #0b1220 0%, #0a0f1c 100%);
                 filter: saturate(120%);
                 animation: bgShift 18s ease-in-out infinite alternate; }
            @keyframes bgShift {
              0% { background-position: 0px 0px, 0px 0px, 0px 0px, 0 0; }
              50% { background-position: 30px -20px, -40px 10px, 20px -30px, 0 0; }
              100% { background-position: -50px 30px, 60px -10px, -30px 40px, 0 0; }
            }
            /* Floating orbs */
            .orb { position: fixed; width: 240px; height: 240px; border-radius: 50%;
                   filter: blur(30px); opacity: .35; mix-blend-mode: screen; z-index: 0; pointer-events:none; }
            .orb.o1 { background: #60a5fa; top: 10%; left: -60px; animation: float1 22s ease-in-out infinite; }
            .orb.o2 { background: #f59e0b; bottom: 8%; right: -40px; animation: float2 26s ease-in-out infinite; }
            .orb.o3 { background: #34d399; top: 55%; left: 60%; animation: float3 24s ease-in-out infinite; }
            @keyframes float1 { 0%{transform:translate(0,0)} 50%{transform:translate(40px,20px)} 100%{transform:translate(-10px,-10px)} }
            @keyframes float2 { 0%{transform:translate(0,0)} 50%{transform:translate(-30px,-25px)} 100%{transform:translate(10px,5px)} }
            @keyframes float3 { 0%{transform:translate(0,0)} 50%{transform:translate(25px,-35px)} 100%{transform:translate(-15px,15px)} }
            .container { max-width:720px; margin:60px auto; padding:0 20px; }
            .card { background:rgba(17,24,39,0.8); border:1px solid #243244; border-radius:14px; padding:28px; box-shadow:0 10px 30px rgba(0,0,0,0.3); }
            h1 { margin:0 0 8px 0; font-size:22px; }
            p.desc { margin:0 0 18px 0; color:var(--muted); }
            .controls { display:flex; gap:12px; align-items:center; }
            input[type=file] { flex:1; padding:10px; background:#0b1324; border:1px solid #1f2a44; border-radius:10px; color:var(--text); }
            button { padding:10px 16px; border-radius:10px; background:#0b1324; border:1px solid #1f2a44; color:var(--text); cursor:pointer; }
            button:hover { background:#0c1530; }
        </style>
    </head>
    <body>
        <div class="bg"></div>
        <div class="orb o1"></div>
        <div class="orb o2"></div>
        <div class="orb o3"></div>
        <div class="container" style="position:relative; z-index:1;">
          <div class="card">
            <h1>WhatSafe - WhatsApp Boycott Detector</h1>
            <p class="desc">Upload a WhatsApp <strong>.txt</strong> export file to analyze the group.</p>
            <div class="desc" style="margin:10px 0 18px 0;">
              <strong>How to export a group chat (without media):</strong>
              <ol style="margin:8px 0 0 18px;">
                <li>Open WhatsApp and go to the group chat.</li>
                <li>Tap the group name (top) to open Group Info.</li>
                <li>Choose <em>Export Chat</em> (iOS) or <em>More &gt; Export chat</em> (Android).</li>
                <li>Select <em>Without Media</em>.</li>
                <li>Save/share the exported <code>.txt</code> file to your computer.</li>
                <li>Return here and upload that <code>.txt</code> file.</li>
              </ol>
            </div>
            <form action="/analyze" method="post" enctype="multipart/form-data">
                <div class="controls">
                  <input type="file" name="file" accept=".txt" required />
                  <button type="submit">Analyze</button>
                </div>
            </form>
          </div>
        </div>
    </body>
    </html>
    """


@app.post("/analyze", response_class=HTMLResponse)
async def analyze_file_html(file: UploadFile = File(...)) -> HTMLResponse:
    """
    Receive an uploaded file from the user, send its text content to the
    Detection Service over HTTP, and render the result as an HTML page.

    Note:
        The UI service does not run detection logic directly.
        It acts as a client of the Detection Service.
    """
    # Read the uploaded file into memory (bytes)
    content_bytes = await file.read()

    # Decode the bytes into a string using UTF-8 encoding
    text_content = content_bytes.decode("utf-8", errors="ignore")

    # Call the Detection Service over HTTP (microservice architecture)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/api/analyze-text",  # Detection Service URL
                json={"content": text_content},            # JSON payload
                timeout=20.0,
            )
            response.raise_for_status()
        # Convert the JSON response into a Python dictionary
        result: Dict[str, Any] = response.json()
    except httpx.RequestError as exc:
        error_html = (
            "<h1>Detection Service Unavailable</h1>"
            f"<p>Could not reach detection service: {exc}</p>"
            "<p>Ensure it is running on http://localhost:8001</p>"
        )
        return HTMLResponse(content=error_html, status_code=503)
    except httpx.HTTPStatusError as exc:
        error_html = (
            "<h1>Detection Service Error</h1>"
            f"<p>Service returned error: {exc.response.status_code}</p>"
            f"<pre>{exc.response.text}</pre>"
        )
        return HTMLResponse(content=error_html, status_code=502)

    # Render HTML using the analysis result
    html = render_result_html(result)
    return HTMLResponse(content=html)


if __name__ == "__main__":
    # Allow running this microservice with:
    #   python ui_service.py
    import uvicorn  # ASGI server for running FastAPI apps

    print("Starting Whatsafe UI Service on http://0.0.0.0:8002 …")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,   # UI service listens on port 8002 to avoid conflicts
        reload=False,
        log_level="info",
    )
