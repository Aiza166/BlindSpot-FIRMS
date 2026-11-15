"""Split docs/SUBMISSION.md into one paste-ready block per Space Apps form field.

The form editor is rich text, not Markdown, so tables become plain lines,
bold and code marks are removed, and each image becomes an upload note.
No wording or number is changed. Run again after `make story`:

    python scripts/form_fields.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "SUBMISSION.md"
OUT = ROOT / "docs" / "FORM_PASTE.md"

# (form field name in the 2026 guide, SUBMISSION.md sections that fill it)
FIELDS = [
    ("Project Name", ["Project name"]),
    ("High-Level Project Summary", ["High-level summary"]),
    ("Link to Project Demo", ["Link to Project Demo"]),
    ("Link to Final Project", ["Link to Final Project"]),
    ("Detailed Project Description", ["Detailed description"]),
    ("Use of Super Intelligence (SI)", ["Use of Super Intelligence (SI)"]),
    ("NASA Data", ["NASA data used"]),
    (
        "Space Agency Partner Data and Other References",
        ["Space agency partner data and other references", "References"],
    ),
]


def sections(text: str) -> dict[str, str]:
    """Map each `## ` heading to its body."""
    parts = re.split(r"^## (.+)$", text, flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts), 2)}


def plain(body: str) -> str:
    out: list[str] = []
    for line in body.splitlines():
        image = re.match(r"!\[(.*)\]\((.+)\)", line)
        if image:
            out.append(f"[UPLOAD IMAGE HERE: docs/{image[2]} | caption: {image[1]}]")
            continue
        if re.match(r"^\|[\s:|-]+\|$", line):  # table rule row
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            line = " | ".join(cells)
        line = re.sub(r"^### (.+)$", lambda m: m[1].upper(), line)
        line = line.replace("**", "").replace("`", "")
        out.append(line)
    return "\n".join(out).strip()


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    found = sections(text)
    lead = re.search(r"^\*\*(.+)\*\*$", text, flags=re.M)
    blocks = [
        "# Form paste sheet",
        "",
        "Made by `scripts/form_fields.py` from `docs/SUBMISSION.md`. Do not edit by hand.",
        "One block per form field, in form order. Copy the text inside each fence.",
        "",
    ]
    for field, names in FIELDS:
        body = "\n\n".join(plain(found[n]) for n in names)
        if field == "High-Level Project Summary" and lead:
            body = f"{lead[1]}\n\n{body}"
        words = len(re.sub(r"\[UPLOAD IMAGE HERE[^\]]*\]", "", body).split())
        blocks += [f"## {field}", "", f"{words} words", "", "````text", body, "````", ""]
    OUT.write_text("\n".join(blocks), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
