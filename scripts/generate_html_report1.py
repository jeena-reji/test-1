import os
import re
from pathlib import Path
from html import escape

report_dir = Path("reports")
html_file = report_dir / "static_report.html"

def generate_table(title, filepath):
    if not filepath.exists():
        return f"<h2>{title}</h2><p>No report file found.</p>"

    rows = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Attempt to extract structured info: filename, line, severity, message
            match = re.match(r"(.+?):(\d+):(?:(\d+):)?\s*(\w*):?\s*(.*)", line)
            if match:
                file, line_no, col, level, msg = match.groups()
                rows.append((file, line_no or "", level or "info", msg))
            else:
                rows.append(("", "", "", line))

    if not rows:
        return f"<h2>{title}</h2><p>No issues found.</p>"

    table = f"<h2>{title}</h2><table border='1' cellspacing='0' cellpadding='4'><tr><th>File</th><th>Line</th><th>Severity</th><th>Message</th></tr>"
    for row in rows:
        table += "<tr>" + "".join(f"<td>{escape(str(col))}</td>" for col in row) + "</tr>"
    table += "</table>"
    return table


def main():
    sections = []
    file_map = {
        "C (cppcheck)": "cppcheck.txt",
        "Python (flake8)": "flake8.txt",
        "Python (pylint)": "pylint.txt",
        "Java (checkstyle)": "checkstyle.txt",
        "Makefile (checkmake)": "checkmake.txt",
        "Mustache": "mustache.txt",
    }

    for title, filename in file_map.items():
        section = generate_table(title, report_dir / filename)
        sections.append(section)

    with open(html_file, "w", encoding="utf-8") as f:
        f.write("<html><head><title>Static Analysis Report</title></head><body>")
        f.write("<h1>Static Analysis Report</h1>")
        f.write("<hr/>".join(sections))
        f.write("</body></html>")

if __name__ == "__main__":
    main()
