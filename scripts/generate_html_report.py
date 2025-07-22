import os
import re
import xml.etree.ElementTree as ET

os.makedirs("reports", exist_ok=True)

html = ['<html><head><style>']
html.append("""
body { font-family: Arial; padding: 20px; }
h2 { border-bottom: 2px solid #444; margin-top: 30px; }
table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
th, td { border: 1px solid #ccc; padding: 8px; font-size: 14px; }
th { background: #f4f4f4; text-align: left; }
tr:nth-child(even) { background: #f9f9f9; }
</style></head><body>
<h1>Static Code Analysis Report</h1>
""")

def table_header():
    return "<tr><th>File</th><th>Line</th><th>Type</th><th>Message</th><th>Tool</th></tr>"

def parse_cppcheck(file):
    html.append("<h2>C/C++ (cppcheck)</h2><table>" + table_header())
    try:
        tree = ET.parse(file)
        for error in tree.findall(".//error"):
            msg = error.attrib.get('msg')
            severity = error.attrib.get('severity')
            for loc in error.findall('location'):
                file = loc.attrib.get('file')
                line = loc.attrib.get('line')
                html.append(f"<tr><td>{file}</td><td>{line}</td><td>{severity}</td><td>{msg}</td><td>cppcheck</td></tr>")
    except:
        html.append("<tr><td colspan='5'>Failed to parse cppcheck.xml</td></tr>")
    html.append("</table>")

def parse_flake8(file):
    html.append("<h2>Python (flake8)</h2><table>" + table_header())
    with open(file) as f:
        for line in f:
            parts = line.strip().split("::")
            if len(parts) == 4:
                file, line, code, msg = parts
                html.append(f"<tr><td>{file}</td><td>{line}</td><td>{code}</td><td>{msg}</td><td>flake8</td></tr>")
    html.append("</table>")

def parse_pylint(file):
    html.append("<h2>Python (pylint)</h2><table>" + table_header())
    with open(file) as f:
        for line in f:
            match = re.match(r"(.*?):(\d+):\s\[(.*?)\]\s(.*)", line)
            if match:
                file, line, code, msg = match.groups()
                html.append(f"<tr><td>{file}</td><td>{line}</td><td>{code}</td><td>{msg}</td><td>pylint</td></tr>")
    html.append("</table>")

def parse_checkstyle(file):
    html.append("<h2>Java (checkstyle)</h2><table>" + table_header())
    try:
        tree = ET.parse(file)
        for f in tree.findall(".//file"):
            filename = f.attrib.get('name')
            for err in f.findall('error'):
                line = err.attrib.get('line')
                severity = err.attrib.get('severity')
                msg = err.attrib.get('message')
                html.append(f"<tr><td>{filename}</td><td>{line}</td><td>{severity}</td><td>{msg}</td><td>checkstyle</td></tr>")
    except:
        html.append("<tr><td colspan='5'>Failed to parse checkstyle.xml</td></tr>")
    html.append("</table>")

def parse_checkmake(file):
    html.append("<h2>Makefile (checkmake)</h2><table>" + table_header())
    with open(file) as f:
        for line in f:
            match = re.match(r"(.*?):(\d+):(.*)", line)
            if match:
                file, line, msg = match.groups()
                html.append(f"<tr><td>{file}</td><td>{line}</td><td>warning</td><td>{msg.strip()}</td><td>checkmake</td></tr>")
    html.append("</table>")

def parse_staticcheck(file):
    html.append("<h2>Go (staticcheck)</h2><table>" + table_header())
    with open(file) as f:
        for line in f:
            match = re.match(r"(.*?):(\d+):(\d+):\s+(.*)", line)
            if match:
                file, line, _, msg = match.groups()
                html.append(f"<tr><td>{file}</td><td>{line}</td><td>issue</td><td>{msg}</td><td>staticcheck</td></tr>")
    html.append("</table>")

# Call parsers
parse_cppcheck("reports/json/cppcheck.xml")
parse_flake8("reports/json/flake8.txt")
parse_pylint("reports/json/pylint.txt")
parse_checkstyle("reports/json/checkstyle.xml")
parse_checkmake("reports/json/checkmake.txt")
parse_staticcheck("reports/json/staticcheck.txt")

html.append("</body></html>")

with open("reports/structured-report.html", "w") as f:
    f.write("\n".join(html))
