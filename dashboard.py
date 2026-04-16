# JoshDashboard2 legacy HTML dashboard server
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = ROOT / 'processed'
ACTIVITY_CSV = PROCESSED_DIR / 'normalized_activity.csv'
DOCUMENT_CSV = PROCESSED_DIR / 'normalized_documents.csv'
ENTITY_CSV = PROCESSED_DIR / 'normalized_entities.csv'
MANIFEST_PATH = PROCESSED_DIR / 'source-manifest.json'
COVERAGE_PATH = PROCESSED_DIR / 'source_coverage.json'
INSIGHTS_PATH = PROCESSED_DIR / 'insight_cards.json'
REPORT_PATH = PROCESSED_DIR / 'processed_report.json'


def load_json(path):
    if not path.exists():
        return {}
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def load_csv(path, max_rows=200):
    rows = []
    if not path.exists():
        return rows
    with path.open('r', encoding='utf-8', newline='') as f:
        import csv
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            rows.append(row)
    return rows


def build_overview():
    report = load_json(REPORT_PATH)
    manifest = load_json(MANIFEST_PATH)
    coverage = load_json(COVERAGE_PATH)
    activity_count = sum(1 for _ in open(ACTIVITY_CSV, 'r', encoding='utf-8')) - 1 if ACTIVITY_CSV.exists() else 0
    document_count = sum(1 for _ in open(DOCUMENT_CSV, 'r', encoding='utf-8')) - 1 if DOCUMENT_CSV.exists() else 0
    entity_count = sum(1 for _ in open(ENTITY_CSV, 'r', encoding='utf-8')) - 1 if ENTITY_CSV.exists() else 0
    return {
        'report': report,
        'manifest': manifest,
        'coverage': coverage,
        'activity_count': activity_count,
        'document_count': document_count,
        'entity_count': entity_count,
        'insights': load_json(INSIGHTS_PATH)
    }


def build_html():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>JoshDashboard2</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f6f8fb; color: #1b2431; }
    header { background: #1e3a8a; color: white; padding: 24px; }
    header h1 { margin: 0; }
    nav { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
    nav button { border: none; padding: 10px 16px; border-radius: 999px; background: rgba(255,255,255,0.15); color: white; cursor: pointer; }
    nav button.active { background: white; color: #1e3a8a; }
    main { padding: 24px; max-width: 1280px; margin: auto; }
    .section { display: none; }
    .section.active { display: block; }
    .card { background: white; border-radius: 18px; padding: 18px; box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08); margin-bottom: 18px; }
    .card h2 { margin-top: 0; font-size: 1.1rem; }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.95rem; }
    th, td { text-align: left; padding: 10px; border-bottom: 1px solid #e2e8f0; }
    th { background: #f8fafc; }
    .footer { color: #475569; margin-top: 32px; font-size: 0.95rem; }
  </style>
</head>
<body>
  <header>
    <h1>JoshDashboard2</h1>
    <p>Static dashboard server exposing the current profile data.</p>
    <nav>
      <button data-section="overview" class="active">Overview</button>
      <button data-section="coverage">Coverage</button>
      <button data-section="activity">Activity</button>
      <button data-section="documents">Documents</button>
      <button data-section="contacts">Contacts</button>
      <button data-section="insights">Insights</button>
    </nav>
  </header>
  <main>
    <section id="overview" class="section active"></section>
    <section id="coverage" class="section"></section>
    <section id="activity" class="section"></section>
    <section id="documents" class="section"></section>
    <section id="contacts" class="section"></section>
    <section id="insights" class="section"></section>
    <div class="footer">Run <code>python dashboard.py</code> to launch the dashboard, then open <code>/dashboard.html</code>.</div>
  </main>
  <script>
    const buttons = document.querySelectorAll('nav button');
    buttons.forEach(btn => btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.section').forEach(sec => sec.classList.remove('active'));
      document.getElementById(btn.dataset.section).classList.add('active');
    }));

    async function fetchJson(path) {
      const res = await fetch(path);
      return res.json();
    }

    function renderTable(headers, rows) {
      if (!rows || !rows.length) {
        return '<p>No records available.</p>';
      }
      const headerHtml = headers.map(h => `<th>${h}</th>`).join('');
      const rowsHtml = rows.map(row => `<tr>${headers.map(h => `<td>${row[h] ?? ''}</td>`).join('')}</tr>`).join('');
      return `<table><thead><tr>${headerHtml}</tr></thead><tbody>${rowsHtml}</tbody></table>`;
    }

    function renderInsight(card) {
      const rows = card.values.map(item => `<li>${Array.isArray(item) ? item.join(' - ') : JSON.stringify(item)}</li>`).join('');
      return `<div class="card"><h2>${card.name}</h2><ul>${rows}</ul></div>`;
    }

    async function loadDashboard() {
      const overview = await fetchJson('/api/overview');
      const coverage = await fetchJson('/api/coverage');
      const activity = await fetchJson('/api/activity');
      const documents = await fetchJson('/api/documents');
      const contacts = await fetchJson('/api/contacts');
      const insights = await fetchJson('/api/insights');

      document.getElementById('overview').innerHTML = `
        <div class="card"><h2>Overview</h2><p>${overview.report.summary || 'No summary available.'}</p></div>
        <div class="card"><h2>Totals</h2><ul><li>Activity rows: ${overview.activity_count}</li><li>Documents: ${overview.document_count}</li><li>Entities: ${overview.entity_count}</li></ul></div>
        <div class="card"><h2>Import</h2><p>ID: ${overview.report.import_run?.import_run_id || 'none'}</p><p>Source count: ${overview.manifest.sources?.length || 0}</p></div>
      `;

      document.getElementById('coverage').innerHTML = `
        <div class="card"><h2>Source coverage</h2>${renderTable(['name','status','files_discovered','records_extracted','confidence'], coverage)}</div>
      `;

      document.getElementById('activity').innerHTML = `
        <div class="card"><h2>Activity explorer</h2>${renderTable(['timestamp','source','source_type','title','creator','action','source_path'], activity.rows)}</div>
      `;

      document.getElementById('documents').innerHTML = `
        <div class="card"><h2>Documents</h2>${renderTable(['file_name','file_type','size_bytes','source_path'], documents.rows)}</div>
      `;

      document.getElementById('contacts').innerHTML = `
        <div class="card"><h2>Contacts</h2>${renderTable(['title','creator','raw_id','source_path'], contacts.rows)}</div>
      `;

      document.getElementById('insights').innerHTML = insights.length ? insights.map(renderInsight).join('') : '<p>No insights available.</p>';
    }

    loadDashboard();
  </script>
</body>
</html>'''


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ['/', '/dashboard.html']:
            html = build_html()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return

        if parsed.path.startswith('/api/'):
            self.handle_api(parsed.path)
            return

        self.send_response(404)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'Not Found')

    def handle_api(self, path):
        if path == '/api/overview':
            payload = build_overview()
        elif path == '/api/coverage':
            payload = load_json(COVERAGE_PATH)
        elif path == '/api/activity':
            payload = {'rows': load_csv(ACTIVITY_CSV, max_rows=500)}
        elif path == '/api/documents':
            payload = {'rows': load_csv(DOCUMENT_CSV, max_rows=500)}
        elif path == '/api/contacts':
            payload = {'rows': load_csv(ENTITY_CSV, max_rows=500)}
        elif path == '/api/insights':
            payload = load_json(INSIGHTS_PATH)
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode('utf-8'))
            return
        body = json.dumps(payload)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))


def run(port=8765):
    server = HTTPServer(('localhost', port), DashboardHandler)
    print(f'Opening dashboard at http://localhost:{port}/dashboard.html')
    print('Press Ctrl+C to stop')
    server.serve_forever()


if __name__ == '__main__':
    run()
