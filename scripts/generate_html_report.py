import os
import pandas as pd
import xml.etree.ElementTree as ET
from glob import glob

def parse_cppcheck(xml_file):
    rows = []
    tree = ET.parse(xml_file)
    root = tree.getroot()
    for error in root.findall('errors/error'):
        for location in error.findall('location'):
            rows.append({
                "Tool": "cppcheck",
                "File": location.attrib.get("file"),
                "Line": location.attrib.get("line"),
                "Severity": error.attrib.get("severity"),
                "Message": error.attrib.get("msg"),
                "Id": error.attrib.get("id"),
            })
    return rows

def parse_golangci(xml_file):
    rows = []
    tree = ET.parse(xml_file)
    root = tree.getroot()
    for err in root.findall('file/error'):
        rows.append({
            "Tool": "golangci-lint",
            "File": err.attrib.get("file"),
            "Line": err.attrib.get("line"),
            "Severity": "warning",
            "Message": err.attrib.get("message"),
        })
    return rows

def parse_clang_tidy():
    rows = []
    for fname in glob("clang_tidy_*.txt"):
        with open(fname) as f:
            for line in f:
                parts = line.strip().split(":", 3)
                if len(parts) >= 4:
                    file, line_no, col, msg = parts
                    rows.append({
                        "Tool": "clang-tidy",
                        "File": file,
                        "Line": line_no,
                        "Severity": "warning",
                        "Message": msg.strip(),
                    })
    return rows

all_rows = []

if os.path.exists("cppcheck.xml"):
    all_rows.extend(parse_cppcheck("cppcheck.xml"))

if os.path.exists("golint.xml"):
    all_rows.extend(parse_golangci("golint.xml"))

all_rows.extend(parse_clang_tidy())

df = pd.DataFrame(all_rows)
df = df.fillna("")

html_content = df.to_html(index=False, border=1, justify="center")

with open("lint-report.html", "w") as f:
    f.write("<h2>Code Lint Report</h2>")
    f.write(html_content)
