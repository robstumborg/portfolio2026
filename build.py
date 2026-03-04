#!/usr/bin/env python3
"""
build script for portfolio site.

reads structured data from data/ and content strings from data/content/,
then renders everything into dist/:
  - dist/index.html          (portfolio site with english baked in)
  - dist/locales/en.json     (runtime i18n strings)
  - dist/locales/es.json     (runtime i18n strings)
  - dist/css/                (copied from css/)
  - dist/js/                 (copied from js/)
  - dist/resume_<lang>.tex   (latex resume, if template exists)

usage:
  python build.py
"""

import json
import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

HTML_TAG_RE = re.compile(r"<(?:strong|em|br|span|a)\b")

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CONTENT_DIR = DATA_DIR / "content"
TEMPLATES_DIR = ROOT / "templates"
DIST_DIR = ROOT / "dist"

SUPPORTED_LANGS = ["en", "es"]

# static asset directories to copy into dist/
STATIC_DIRS = ["css", "js", "img"]


def load_json(path: Path) -> dict | list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_data() -> dict:
    """load all structured data files."""
    return {
        "skills": load_json(DATA_DIR / "skills.json"),
        "projects": load_json(DATA_DIR / "projects.json"),
        "experience": load_json(DATA_DIR / "experience.json"),
    }


def load_content(lang: str) -> dict:
    """load content strings for a given language."""
    data = load_json(CONTENT_DIR / f"{lang}.json")
    assert isinstance(data, dict)
    return data


def has_html(value: str) -> bool:
    """check if a content string contains html markup."""
    return bool(HTML_TAG_RE.search(value))


def collect_numbered_keys(content: dict, prefix: str) -> list[dict]:
    """find all numbered keys matching prefix.1, prefix.2, ... in content.

    returns a sorted list of dicts with 'index' (int) and 'is_html' (bool).
    """
    entries = []
    for key, value in content.items():
        if key.startswith(prefix) and key[len(prefix):].isdigit():
            entries.append({
                "index": int(key[len(prefix):]),
                "is_html": has_html(value),
            })
    entries.sort(key=lambda e: e["index"])
    return entries


def collect_desc_paragraphs(content: dict, prefix: str) -> list[dict]:
    """find all paragraph keys matching prefix.p1, prefix.p2, ... in content.

    returns a sorted list of dicts with 'index' (int) and 'is_html' (bool).
    """
    p_prefix = prefix + "p"
    entries = []
    for key, value in content.items():
        if key.startswith(p_prefix) and key[len(p_prefix):].isdigit():
            entries.append({
                "index": int(key[len(p_prefix):]),
                "is_html": has_html(value),
            })
    entries.sort(key=lambda e: e["index"])
    return entries


def enrich_data(data: dict, content: dict) -> dict:
    """scan content keys to compute paragraph/highlight lists for each entry."""
    for proj in data["projects"]:
        pid = proj["id"]
        if proj.get("featured"):
            proj["desc_paras"] = collect_desc_paragraphs(
                content, f"project.{pid}.desc."
            )
        # non-featured projects use a single desc key, no paragraphs to enumerate

    for exp in data["experience"]:
        eid = exp["id"]
        exp["highlight_list"] = collect_numbered_keys(
            content, f"exp.{eid}.highlight."
        )

    return data


def build_html(env: Environment, data: dict, content: dict) -> str:
    """render index.html from template + data + english content."""
    template = env.get_template("index.html.j2")
    return template.render(t=content, **data)


def build_locales(langs: list[str]) -> None:
    """copy content files to dist/locales/ for runtime i18n."""
    locales_dir = DIST_DIR / "locales"
    locales_dir.mkdir(parents=True, exist_ok=True)
    for lang in langs:
        src = CONTENT_DIR / f"{lang}.json"
        dst = locales_dir / f"{lang}.json"
        shutil.copy2(src, dst)
        print(f"  dist/locales/{lang}.json")


def build_resume(env: Environment, data: dict, langs: list[str]) -> None:
    """render latex resume for each language, if template exists."""
    try:
        template = env.get_template("resume.tex.j2")
    except Exception:
        print("  templates/resume.tex.j2 not found, skipping resume generation")
        return

    for lang in langs:
        content = load_content(lang)
        output = template.render(t=content, lang=lang, **data)
        out_path = DIST_DIR / f"resume_{lang}.tex"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"  dist/resume_{lang}.tex")


def copy_static() -> None:
    """copy static asset directories into dist/."""
    for dirname in STATIC_DIRS:
        src = ROOT / dirname
        dst = DIST_DIR / dirname
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  dist/{dirname}/")


def main():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
        lstrip_blocks=False,
        trim_blocks=False,
    )

    data = load_data()
    en_content = load_content("en")
    data = enrich_data(data, en_content)

    # clean and recreate dist/
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()

    print("building portfolio site...")

    # 1. render index.html with english content baked in
    html = build_html(env, data, en_content)
    out_path = DIST_DIR / "index.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  dist/index.html")

    # 2. copy locale files for runtime i18n
    build_locales(SUPPORTED_LANGS)

    # 3. copy static assets
    copy_static()

    # 4. render latex resumes (if template exists)
    build_resume(env, data, SUPPORTED_LANGS)

    print("finished")


if __name__ == "__main__":
    main()
