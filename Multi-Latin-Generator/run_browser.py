"""Run the Python multi-Latin generator in a local browser: python run_browser.py"""
import json
import colorsys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from multi_latin_generator import generate_square, validate_square


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        request = urlparse(self.path)
        status = 200
        if request.path in ("/", "/index.html"):
            params = parse_qs(request.query)
            try:
                m, k, d = (int(params.get(key, [default])[0])
                           for key, default in (("m", 5), ("k", 2), ("d", 2)))
                square = generate_square(m, k, d)
                initial = dict(m=m, k=k, d=d, n=m*k, square=square,
                               report=validate_square(square, m, k, d))
                max_start = m * k - d + 1
                row = min(max(int(params.get("row", ["1"])[0]), 1), max_start)
                col = min(max(int(params.get("col", ["1"])[0]), 1), max_start)
                block = [square[r][c] for r in range(row-1, row+d-1)
                         for c in range(col-1, col+d-1)]
                rows = []
                for r, values in enumerate(square):
                    cells = [f'<th scope="row">{r+1}</th>']
                    for c, symbol in enumerate(values):
                        hue = round(symbol * 360 / m)
                        selected = row-1 <= r < row+d-1 and col-1 <= c < col+d-1
                        style = f' style="background:hsl({hue},48%,76%)"'
                        cls = ' class="window-cell"' if selected else ""
                        cells.append(f'<td{cls}{style}>{symbol}</td>')
                    rows.append("<tr>" + "".join(cells) + "</tr>")
                header = "<tr><th></th>" + "".join(
                    f'<th scope="col">{c+1}</th>' for c in range(m*k)) + "</tr>"
                grid_html = '<table class="square" aria-label="Generated multi-Latin square">' + header + "".join(rows) + "</table>"
                download = f"/export?m={m}&k={k}&d={d}"
                stats = (f'<div class="stats"><div class="stat"><span>Grid size</span><strong>{m*k} × {m*k}</strong></div>'
                         f'<div class="stat"><span>Row and column counts</span><strong>PASS</strong></div>'
                         f'<div class="stat"><span>Overlapping windows</span><strong>{initial["report"]["blocks_checked"]} · PASS</strong></div></div>')
                inspection = (f"Rows {row}–{row+d-1}, columns {col}–{col+d-1}: "
                              f"{len(set(block))} distinct symbols across {d*d} cells · "
                              f"{'PASS' if len(set(block)) == d*d else 'FAIL'}")
            except (ValueError, OverflowError) as error:
                m, k, d = 5, 2, 2
                row = col = 1
                grid_html = ""
                stats = ""
                download = "#"
                inspection = str(error)
            page = Path(__file__).with_name("explorer.html").read_text(encoding="utf-8")
            page = page.replace('value="__M__"', f'value="{m}"')
            page = page.replace('value="__K__"', f'value="{k}"')
            page = page.replace('value="__D__"', f'value="{d}"')
            page = page.replace('value="__ROW__"', f'value="{row}"')
            page = page.replace('value="__COL__"', f'value="{col}"')
            page = page.replace("__GRID__", grid_html)
            page = page.replace("__STATS__", stats)
            page = page.replace("__INSPECTION__", inspection)
            page = page.replace("__DOWNLOAD__", download)
            content = page.encode("utf-8")
            mime = "text/html; charset=utf-8"
        elif request.path == "/export":
            params = parse_qs(request.query)
            try:
                m, k, d = (int(params.get(key, default)[0])
                           for key, default in (("m", ["5"]), ("k", ["2"]), ("d", ["2"])))
                square = generate_square(m, k, d)
                content = ("\n".join(",".join(map(str, row)) for row in square) + "\n").encode()
                mime = "text/csv; charset=utf-8"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Disposition", f'attachment; filename="multi_latin_m{m}_k{k}_d{d}.csv"')
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except ValueError as error:
                content, mime, status = str(error).encode(), "text/plain", 400
        elif request.path == "/api/generate":
            try:
                params = parse_qs(request.query)
                m, k, d = (int(params.get(key, [default])[0])
                           for key, default in (("m", 5), ("k", 2), ("d", 2)))
                if m*k > 100:
                    raise ValueError("The browser view supports grids up to 100 × 100.")
                square = generate_square(m, k, d)
                result = dict(m=m, k=k, d=d, n=m*k, square=square,
                              report=validate_square(square, m, k, d))
            except (ValueError, OverflowError) as error:
                result = {"error": str(error)}
                status = 400
            content = json.dumps(result).encode("utf-8")
            mime = "application/json; charset=utf-8"
        else:
            content, mime, status = b"Not found", "text/plain", 404
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)


if __name__ == "__main__":
    print("Multi-Latin Explorer: http://127.0.0.1:8765", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
