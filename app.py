import os
import requests
from flask import Flask, request, Response, stream_with_context

app = Flask(__name__)

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
LAPTOP_URL = os.environ.get("LAPTOP_URL", "").rstrip("/")
TIMEOUT = 5

SKIP_HEADERS = {
    "content-encoding",
    "content-length",
    "transfer-encoding",
    "connection",
    "host"
}

# ─────────────────────────────────────────
# SERVER DOWN PAGE
# ─────────────────────────────────────────
DOWN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ACE AI — Offline</title>
<style>
body{
background:#0d1117;
color:white;
font-family:Arial;
display:flex;
justify-content:center;
align-items:center;
height:100vh;
text-align:center;
}
.box{
background:#161b22;
padding:40px;
border-radius:12px;
box-shadow:0 0 40px rgba(255,0,0,0.2);
}
h1{color:#ff4d4d;}
button{
padding:10px 20px;
background:#00ffae;
border:none;
border-radius:6px;
cursor:pointer;
font-weight:bold;
}
</style>
</head>
<body>
<div class="box">
<h1>Server Temporarily Down</h1>
<p>The AI engine is currently offline.</p>
<p>Please check back shortly.</p>
<button onclick="location.reload()">Retry</button>
</div>
</body>
</html>
"""

# ─────────────────────────────────────────
# HEALTH CHECK FUNCTION
# ─────────────────────────────────────────
def laptop_alive():
    if not LAPTOP_URL:
        return False
    try:
        r = requests.get(f"{LAPTOP_URL}/health", timeout=3)
        return r.status_code == 200
    except:
        return False

# ─────────────────────────────────────────
# PROXY
# ─────────────────────────────────────────
@app.route("/", defaults={"path": ""}, methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
@app.route("/<path:path>", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
def proxy(path):

    if not laptop_alive():
        return Response(DOWN_HTML, status=503, mimetype="text/html")

    target = f"{LAPTOP_URL}/{path}"
    headers = {k: v for k, v in request.headers if k.lower() not in SKIP_HEADERS}

    try:
        resp = requests.request(
            method=request.method,
            url=target,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            timeout=TIMEOUT,
            stream=True,
        )
    except:
        return Response(DOWN_HTML, status=503, mimetype="text/html")

    response_headers = {
        k: v for k, v in resp.headers.items()
        if k.lower() not in SKIP_HEADERS
    }

    return Response(
        stream_with_context(resp.iter_content(chunk_size=8192)),
        status=resp.status_code,
        headers=response_headers,
    )

# ─────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
