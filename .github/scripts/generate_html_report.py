import os
import re
from pathlib import Path
from html import escape

REPORT_DIR = Path("reports")
HTML_OUT = REPORT_DIR / "staticcheck.html"

def parse_lines(path):
    with open(path) as f:
        return [line.strip("\n") for line in f.readlines()]

def make_html_table(title, headers, rows):
    html = f"<h2>{escape(title)}</h2><table><tr>"
    html += "".join(f"<th>{escape(h)}</th>" for h in headers)
    html += "</tr>"
    for row in rows:
        html += "<tr>" + "".join(f"<td><pre>{escape(str(cell))}</pre></td>" for cell in row) + "</tr>"
    html += "</table>"
    return html

def parse_generic(file):
    lines = parse_lines(file)
    return [["", l] for l in lines]

def parse_checkmake(file):
    rows = []
    lines = parse_lines(file)
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            cols = lines[i].split(maxsplit=3)
            rule = cols[0] if cols else ""
            desc = cols[1] if len(cols) > 1 else ""
            fname = cols[2] if len(cols) > 2 else ""
            lineno = cols[3] if len(cols) > 3 else ""
            msg = lines[i + 1]
            rows.append([rule, desc, fname, lineno, msg])
    return rows

def parse_clang_tidy(file):
    lines = parse_lines(file)
    rows = []
    buffer = []
    for line in lines:
        if re.match(r"^.*:\d+:\d+: ", line):
            if buffer:
                rows.append(["\n".join(buffer)])
                buffer = []
        buffer.append(line)
    if buffer:
        rows.append(["\n".join(buffer)])
    return rows

def parse_cppcheck(file):
    return parse_clang_tidy(file)

def parse_checkstyle(file):
    lines = parse_lines(file)
    rows = [line.split(":", 3) for line in lines if ":" in line]
    return rows

def parse_flake8(file):
    lines = parse_lines(file)
    return [line.split(":", 3) for line in lines if ":" in line]

def parse_pylint(file):
    lines = parse_lines(file)
    return parse_clang_tidy(file)

def parse_mustache(file):
    return [["", l] for l in parse_lines(file)]

PARSERS = {
    "checkmake.txt": lambda f: parse_checkmake(f),
    "clang-tidy.txt": parse_clang_tidy,
    "cppcheck.txt": parse_cppcheck,
    "checkstyle.txt": parse_checkstyle,
    "flake8.txt": parse_flake8,
    "pylint.txt": parse_pylint,
    "mustache.txt": parse_mustache,
}

def main():
    with open(HTML_OUT, "w") as out:
        out.write("<html><head><style>")
        out.write("""
        body { font-family: Arial; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        pre { white-space: pre-wrap; margin: 0; }
        """)
        out.write("</style></head><body><h1>Static Analysis Report</h1>")

        for file in sorted(REPORT_DIR.glob("*.txt")):
            parser = PARSERS.get(file.name, parse_generic)
            try:
                rows = parser(file)
                headers = ["File", "Line", "Message"] if file.name not in PARSERS else ["Message"] * len(rows[0])
                out.write(make_html_table(file.name, headers, rows))
            except Exception as e:
                out.write(f"<h2>{file.name}</h2><p>Error parsing: {e}</p>")

        out.write("</body></html>")

if __name__ == "__main__":
    main()
