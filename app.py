import string
import random
from urllib.parse import urlparse

from flask import Flask, request, redirect, url_for, render_template_string, flash

app = Flask(__name__)
app.secret_key = "dev"  # needed for flash messages

# In-memory store (for demo). For production use a database.
links = {}   # code -> long_url
clicks = {}  # code -> click count

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>URL Shortener</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-4">
  <h1 class="mb-3">URL Shortener</h1>
  <p class="text-muted">Paste a long URL, get a short one. (Demo app)</p>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <div class="alert alert-warning">{{ messages[0] }}</div>
    {% endif %}
  {% endwith %}

  <form class="row g-2 mb-4" method="post" action="{{ url_for('shorten') }}">
    <div class="col-12 col-md-9">
      <input class="form-control" name="url" placeholder="https://example.com/very/long/link" required>
    </div>
    <div class="col-12 col-md-3 d-grid">
      <button class="btn btn-primary" type="submit">Shorten</button>
    </div>
  </form>

  {% if short_url %}
    <div class="alert alert-success">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <strong>Short URL:</strong>
          <a href="{{ short_url }}" target="_blank">{{ short_url }}</a>
        </div>
        <button class="btn btn-sm btn-outline-secondary" onclick="navigator.clipboard.writeText('{{ short_url }}')">Copy</button>
      </div>
    </div>
  {% endif %}

  {% if recent %}
    <h5 class="mt-4">Recent links</h5>
    <div class="list-group">
      {% for code, long_url in recent %}
        <div class="list-group-item d-flex justify-content-between align-items-center">
          <div class="text-truncate" style="max-width: 70%;">
            <a href="{{ request.host_url ~ code }}" target="_blank">{{ request.host_url ~ code }}</a>
            <div class="small text-muted text-truncate">{{ long_url }}</div>
          </div>
          <span class="badge bg-secondary">Clicks: {{ clicks.get(code, 0) }}</span>
        </div>
      {% endfor %}
    </div>
  {% endif %}
</div>
</body>
</html>
"""

def make_code(k: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choices(alphabet, k=k))

def normalize_url(u: str) -> str:
    u = u.strip()
    if not u:
        return ""
    p = urlparse(u)
    if not p.scheme:
        u = "http://" + u
        p = urlparse(u)
    if p.scheme not in ("http", "https") or not p.netloc:
        return ""
    return u

@app.get("/")
def index():
    recent = list(links.items())[-5:][::-1]  # last 5
    return render_template_string(
        TEMPLATE,
        short_url=None,
        recent=recent,
        clicks=clicks,
        request=request
    )

@app.post("/shorten")
def shorten():
    long_url = normalize_url(request.form.get("url", ""))
    if not long_url:
        flash("Invalid URL. Use http(s)://example.com")
        return redirect(url_for("index"))

    # generate unique short code
    for _ in range(12):
        code = make_code(6)
        if code not in links:
            links[code] = long_url
            clicks[code] = 0
            break
    else:
        flash("Try again, code generation failed.")
        return redirect(url_for("index"))

    short_url = request.host_url + code
    recent = list(links.items())[-5:][::-1]
    return render_template_string(
        TEMPLATE,
        short_url=short_url,
        recent=recent,
        clicks=clicks,
        request=request
    )

@app.get("/<code>")
def follow(code: str):
    if code in links:
        clicks[code] = clicks.get(code, 0) + 1
        return redirect(links[code], 301)
    return "Not found", 404

if __name__ == "__main__":
    app.run(debug=True)
