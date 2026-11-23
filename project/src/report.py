"""Standalone HTML report (open in a browser and print to PDF; works for any script)."""
import html
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from i18n import tr  # noqa: E402

COLORS = {"high": "#C0392B", "inconclusive": "#D68910", "low": "#1E8449"}


def build_report_html(result, inputs, lang="en"):
    e = html.escape
    rows = "".join(f"<tr><td>{e(str(k))}</td><td>{e('-' if v is None else str(v))}</td></tr>"
                   for k, v in inputs.items())
    facts = "".join(f"<li>{e(f['sentence'])}</li>" for f in result["factors"])
    warns = "".join(f"<li>{e(w)}</li>" for w in result["warnings"])
    col = COLORS[result["band"]]
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<title>{e(tr(lang, 'report_title'))}</title>
<style>body{{font-family:Arial,'Noto Sans Devanagari',sans-serif;max-width:760px;margin:2rem auto;color:#222}}
h1{{color:#0B2545}} .band{{background:{col};color:#fff;padding:.6rem 1rem;border-radius:8px;display:inline-block}}
table{{border-collapse:collapse}} td{{border:1px solid #ccc;padding:.3rem .7rem}}
.disc{{background:#FDEDEC;border-left:4px solid #C0392B;padding:.7rem;margin:1rem 0}}</style></head><body>
<h1>{e(tr(lang, 'report_title'))}</h1><p>{date.today().isoformat()}</p>
<div class="disc">{e(tr(lang, 'disclaimer'))}</div>
<h2>{e(tr(lang, 'risk_estimate'))}: {result['probability']*100:.0f}%</h2>
<p class="band">{e(result['band_label'])}</p><p>{e(result['guidance'])}</p>
<h3>{e(tr(lang, 'factors'))}</h3><ul>{facts}</ul>{('<ul>'+warns+'</ul>') if warns else ''}
<h3>{e(tr(lang, 'inputs'))}</h3><table>{rows}</table>
<h3>{e(tr(lang, 'about'))}</h3><p>{e(tr(lang, 'about_text'))}</p></body></html>"""
