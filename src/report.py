"""
src/report.py
Generates a self-contained HTML test report from a SuiteResult.
No external dependencies — pure Python + inline CSS/JS.
"""

import json
import os
from src.runner import SuiteResult


CATEGORY_ICONS = {
    "ping": "📡",
    "http": "🌐",
    "dns":  "🔍",
    "port": "🔌",
}

STATUS_COLOUR = {
    "PASS":  ("#22c55e", "#052e16"),
    "FAIL":  ("#ef4444", "#2d0707"),
    "ERROR": ("#f59e0b", "#2d1a00"),
}


def _badge(status: str) -> str:
    fg, bg = STATUS_COLOUR.get(status, ("#94a3b8", "#1e293b"))
    return (f'<span style="background:{bg};color:{fg};border:1px solid {fg};'
            f'padding:2px 10px;border-radius:9999px;font-size:0.75rem;'
            f'font-weight:700;letter-spacing:0.05em;">{status}</span>')


def generate_html_report(suite: SuiteResult, out_dir: str = "reports") -> str:
    os.makedirs(out_dir, exist_ok=True)

    # Build per-category section HTML
    category_sections = ""
    for cat, results in suite.by_category().items():
        p = sum(1 for r in results if r.passed)
        icon = CATEGORY_ICONS.get(cat, "🔧")
        rows = ""
        for r in results:
            det_html = ""
            if r.details:
                det_html = (
                    '<div class="details"><pre>'
                    + json.dumps(r.details, indent=2)
                    + '</pre></div>'
                )
            rows += f"""
            <tr class="result-row {'pass-row' if r.passed else 'fail-row'}">
              <td>{r.test_name}</td>
              <td class="mono">{r.target}</td>
              <td>{_badge(r.status)}</td>
              <td class="mono">{r.duration_ms}ms</td>
              <td>{r.message}{det_html}</td>
            </tr>"""

        category_sections += f"""
        <section class="category">
          <h2>{icon} {cat.upper()} <span class="cat-score">{p}/{len(results)}</span></h2>
          <table>
            <thead>
              <tr><th>Test</th><th>Target</th><th>Status</th><th>Duration</th><th>Message</th></tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </section>"""

    # Summary bar
    s = suite
    summary_cards = ""
    for label, value, colour in [
        ("Total Tests", s.total,     "#60a5fa"),
        ("Passed",      s.passed,    "#22c55e"),
        ("Failed",      s.failed,    "#ef4444"),
        ("Pass Rate",   f"{s.pass_rate}%", "#a78bfa"),
    ]:
        summary_cards += f"""
        <div class="card">
          <div class="card-value" style="color:{colour}">{value}</div>
          <div class="card-label">{label}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{s.suite_name} — Test Report</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #0a0e1a;
    color: #cbd5e1;
    min-height: 100vh;
    padding: 2rem;
  }}
  header {{
    border-bottom: 1px solid #1e293b;
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
  }}
  header h1 {{ font-size: 1.6rem; color: #f1f5f9; font-weight: 700; }}
  header p  {{ color: #64748b; font-size: 0.85rem; margin-top: .3rem; }}
  .summary  {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2.5rem; }}
  .card {{
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1.2rem 2rem;
    min-width: 130px;
    text-align: center;
  }}
  .card-value {{ font-size: 2rem; font-weight: 800; }}
  .card-label {{ font-size: 0.78rem; color: #64748b; margin-top: .2rem; text-transform: uppercase; letter-spacing: .06em; }}
  .category   {{ margin-bottom: 2.5rem; }}
  .category h2 {{
    font-size: 1rem;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: .5rem;
  }}
  .cat-score {{
    background: #1e293b;
    color: #60a5fa;
    border-radius: 9999px;
    padding: 2px 10px;
    font-size: .8rem;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: .85rem;
    background: #111827;
    border-radius: 10px;
    overflow: hidden;
  }}
  thead tr {{ background: #0f172a; }}
  th {{
    text-align: left;
    padding: .7rem 1rem;
    color: #475569;
    font-weight: 600;
    text-transform: uppercase;
    font-size: .72rem;
    letter-spacing: .05em;
    border-bottom: 1px solid #1e293b;
  }}
  td {{
    padding: .65rem 1rem;
    border-bottom: 1px solid #1e293b;
    vertical-align: top;
  }}
  tr:last-child td {{ border-bottom: none; }}
  .pass-row:hover {{ background: #0f2010; }}
  .fail-row:hover {{ background: #1f0a0a; }}
  .mono {{ font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: .8rem; color: #94a3b8; }}
  .details {{ margin-top: .5rem; }}
  .details pre {{
    background: #0a0e1a;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: .6rem .8rem;
    font-size: .72rem;
    color: #64748b;
    white-space: pre-wrap;
    max-height: 180px;
    overflow-y: auto;
  }}
  footer {{ margin-top: 3rem; text-align: center; color: #334155; font-size: .78rem; }}
</style>
</head>
<body>
<header>
  <h1>🛰 {s.suite_name}</h1>
  <p>Started: {s.started_at} &nbsp;|&nbsp; Finished: {s.finished_at}</p>
</header>

<div class="summary">{summary_cards}</div>

{category_sections}

<footer>Generated by NetworkTestFramework · {s.finished_at}</footer>
</body>
</html>"""

    filename = "test_report.html"
    path     = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML report saved → {path}")
    return path
