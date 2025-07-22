import os
import re
from pathlib import Path
from html import escape

REPORT_DIR = Path("reports")
HTML_OUT = REPORT_DIR / "staticcheck.html"

def parse_lines(path):
    with open(path) as f:
        return [line.strip("\n") for line in f.readlines()]

def make_html_table(title, headers, rows, description=""):
    html = f"<h2><b>{escape(title)}</b></h2>"
    if description:
        html += f"<p><i>{escape(description)}</i></p>"
    html += "<table><tr>"
    html += "".join(f"<th>{escape(h)}</th>" for h in headers)
    html += "</tr>"
    for row in rows:
        html += "<tr>" + "".join(f"<td><pre>{escape(str(cell))}</pre></td>" for cell in row) + "</tr>"
    html += "</table>"
    return html

def parse_generic(file):
    return [["", l] for l in parse_lines(file)]

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
    structured_rows = []
    fallback_rows = []

    for line in lines:
        match = re.match(r"^(.*?):(\d+):(\d+): (.*)", line)
        if match:
            f, l, c, msg = match.groups()
            structured_rows.append([f, l, c, msg])
        else:
            fallback_rows.append(line)

    return structured_rows if structured_rows else [["", msg] for msg in fallback_rows if msg.strip()]

def parse_cppcheck(file):
    return parse_clang_tidy(file)

def parse_checkstyle(file):
    lines = parse_lines(file)
    return [line.split(":", 3) for line in lines if ":" in line]

def parse_flake8(file):
    lines = parse_lines(file)
    structured_rows = []
    fallback_rows = []

    for line in lines:
        parts = line.split(":", 3)
        if len(parts) == 4:
            structured_rows.append(parts)
        else:
            fallback_rows.append(line)

    return structured_rows if structured_rows else [["", msg] for msg in fallback_rows if msg.strip()]

def parse_pylint(file):
    lines = parse_lines(file)
    structured_rows = []
    fallback_rows = []

    for line in lines:
        if "Your code has been rated at" in line:
            fallback_rows.append(f"<b>{escape(line)}</b>")
        else:
            match = re.match(r"^(.*?):(\d+):(\d+): (.*)", line)
            if match:
                structured_rows.append(list(match.groups()))
            else:
                fallback_rows.append(line)

    return structured_rows if structured_rows else [["", msg] for msg in fallback_rows if msg.strip()]

def parse_staticcheck(file):
    lines = parse_lines(file)
    structured_rows = []
    fallback_rows = []

    for line in lines:
        match = re.match(r"^(.*?):(\d+):(\d+): (.*)", line)
        if match:
            structured_rows.append(list(match.groups()))
        else:
            fallback_rows.append(escape(line))

    return structured_rows, fallback_rows


def parse_mustache(file):
    return [["", l] for l in parse_lines(file)]

# Tool-specific configurations
PARSERS = {
    "checkmake.txt": parse_checkmake,
    "clang-tidy.txt": parse_clang_tidy,
    "cppcheck.txt": parse_cppcheck,
    "checkstyle.txt": parse_checkstyle,
    "flake8.txt": parse_flake8,
    "pylint.txt": parse_pylint,
    "mustache.txt": parse_mustache,
    "staticcheck.txt": parse_staticcheck,
}

TOOL_HEADERS = {
    "checkmake.txt": ["Rule", "Desc", "File", "Line", "Message"],
    "clang-tidy.txt": ["File", "Line", "Column", "Message"],
    "cppcheck.txt": ["File", "Line", "Column", "Message"],
    "checkstyle.txt": ["File", "Line", "Column", "Message"],
    "flake8.txt": ["File", "Line", "Column", "Message"],
    "pylint.txt": ["File", "Line", "Column", "Message"],
    "mustache.txt": ["", "Message"]
    "staticcheck.txt": ["File", "Line", "Column", "Message"],
}

TOOL_DESCRIPTIONS = {
    "clang-tidy.txt": "Clang-Tidy: Advanced C/C++ static analysis using Clang compiler internals.",
    "cppcheck.txt": "Cppcheck: Detects bugs, memory issues, and undefined behavior in C/C++.",
    "checkmake.txt": "Checkmake: Analyzes Makefiles for common issues.",
    "checkstyle.txt": "Checkstyle: Code style and formatting violations in Java.",
    "flake8.txt": "Flake8: Python code linting and style checker.",
    "pylint.txt": "Pylint: Deep static analysis for Python with code ratings.",
    "mustache.txt": "Mustache: Checks Mustache templates (if applicable).",
    "staticcheck.txt": "Staticcheck: Advanced Go static analysis (like lint, vet, etc).",
}

def main():
    # Define logical tool groupings
    tool_groups = {
        "Python": ["flake8.txt", "pylint.txt"],
        "C/C++": ["clang-tidy.txt", "cppcheck.txt"],
        "Makefile": ["checkmake.txt"],
        "Go": ["staticcheck.txt"],
        "Java": ["checkstyle.txt"],
        "Mustache": ["mustache.txt"],
    }

    with open(HTML_OUT, "w") as out:
        out.write("<html><head><style>")
        out.write("""
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top; }
        th { background-color: #f2f2f2; }
        h1 { font-size: 28px; }
        h2 { font-size: 22px; margin-top: 40px; }
        pre { white-space: pre-wrap; margin: 0; font-family: Consolas, monospace; }
        b { color: #333; }
        """)
        out.write("</style></head><body><h1><b>Static Analysis Report</b></h1>")

        for group_title, filenames in tool_groups.items():
            out.write(f"<h2><b>{escape(group_title)}</b></h2>")
            for fname in filenames:
                file_path = REPORT_DIR / fname
                if not file_path.exists():
                    continue
                parser = PARSERS.get(fname, parse_generic)
                headers = TOOL_HEADERS.get(fname, ["Message"])
                desc = TOOL_DESCRIPTIONS.get(fname, "")
                try:
                    rows = parser(file_path)
                    out.write(make_html_table(fname, headers, rows, description=desc))
                except Exception as e:
                    out.write(f"<h3>{fname}</h3><p><b>Error parsing:</b> {e}</p>")

        out.write("</body></html>")

if __name__ == "__main__":
    main()
