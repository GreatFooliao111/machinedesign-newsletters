#!/usr/bin/env python3
"""
MachineDesign.ir - Newsletter Sync & Multi-Dimensional Categorization Tool
Synchronizes newsletters from content repo to this repository, organizes them by
Reference / Category / Date, and automatically regenerates index.json & README.md.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent
NEWSLETTERS_DIR = REPO_ROOT / "newsletters"
INDEX_FILE = REPO_ROOT / "index.json"
TAXONOMY_FILE = REPO_ROOT / "taxonomy.json"
README_FILE = REPO_ROOT / "README.md"

def load_json(path, default=None):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def rebuild_index():
    taxonomy = load_json(TAXONOMY_FILE, {"references": {}, "categories": {}})
    entries = []

    # Scan newsletters/<ref>/<category>/<folder>
    if not NEWSLETTERS_DIR.exists():
        return entries

    for ref_dir in NEWSLETTERS_DIR.iterdir():
        if not ref_dir.is_dir():
            continue
        ref_slug = ref_dir.name
        ref_info = taxonomy.get("references", {}).get(ref_slug, {})
        ref_name = ref_info.get("name", ref_slug)

        for cat_dir in ref_dir.iterdir():
            if not cat_dir.is_dir():
                continue
            cat_slug = cat_dir.name
            cat_info = taxonomy.get("categories", {}).get(cat_slug, {})
            cat_title_fa = cat_info.get("title_fa", cat_slug)

            for item_dir in cat_dir.iterdir():
                if not item_dir.is_dir():
                    continue

                meta_path = item_dir / "metadata.json"
                art_path = item_dir / "article.md"
                images_dir = item_dir / "images"

                meta = load_json(meta_path, {}) if meta_path.exists() else {}
                title_fa = meta.get("project_name", item_dir.name)
                # extract title from article if possible
                if art_path.exists():
                    try:
                        with open(art_path, "r", encoding="utf-8") as af:
                            for line in af:
                                if line.startswith("# "):
                                    title_fa = line.replace("# ", "").strip()
                                    break
                    except Exception:
                        pass

                date_str = meta.get("date", item_dir.name.split("_")[0])
                sponsors = meta.get("email_metadata", {}).get("sponsors") or [meta.get("email_metadata", {}).get("sponsor")]
                sponsors = [s for s in sponsors if s]

                images = list(images_dir.glob("*.*")) if images_dir.exists() else []
                lead_img = None
                for img in sorted(images):
                    lead_img = f"newsletters/{ref_slug}/{cat_slug}/{item_dir.name}/images/{img.name}"
                    break

                entries.append({
                    "id": item_dir.name,
                    "date": date_str,
                    "reference": ref_slug,
                    "reference_name": ref_name,
                    "category": cat_slug,
                    "category_title_fa": cat_title_fa,
                    "title_fa": title_fa,
                    "sponsors": sponsors,
                    "folder_path": f"newsletters/{ref_slug}/{cat_slug}/{item_dir.name}",
                    "article_md": f"newsletters/{ref_slug}/{cat_slug}/{item_dir.name}/article.md",
                    "metadata_json": f"newsletters/{ref_slug}/{cat_slug}/{item_dir.name}/metadata.json",
                    "image_count": len(images),
                    "lead_image": lead_img,
                    "pillars": meta.get("engineering_pillars", [])
                })

    # Sort descending by date
    entries.sort(key=lambda x: x["date"], reverse=True)
    save_json(INDEX_FILE, entries)
    return entries

def generate_readme(entries):
    taxonomy = load_json(TAXONOMY_FILE, {"references": {}, "categories": {}})

    # Generate Markdown
    md = []
    md.append("# 🏭 آرشیو و کالبدشکافی مهندسی خبرنامه‌های صنعتی جهان (MachineDesign Newsletters Vault)")
    md.append("")
    md.append("[![MachineDesign.ir](https://img.shields.io/badge/MachineDesign.ir-Engineering%20Intelligence-%238ce70c?style=for-the-badge&logo=probot&logoColor=black)](https://machinedesign.ir)")
    md.append("[![Total Articles](https://img.shields.io/badge/Articles-" + str(len(entries)) + "-blue?style=for-the-badge)](#۱-جدول-ایندکس-زمانی-timeline-index)")
    md.append("[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](./LICENSE)")
    md.append("")
    md.append("> این ریپازیتوری پایگاه داده رسمی آرشیو، طبقه‌بندی چندبعدی (**تاریخ**، **موضوع** و **مرجع**)، ترجمه فنی بومی و کالبدشکافی مهندسی مقالات و خبرنامه‌های تخصصی ماشین‌آلات صنعتی جهان متعلق به **دپارتمان تحقیق و توسعه ماشین دیزاین (`MachineDesign.ir`)** است.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 📌 راهنمای دسترسی سه‌بعدی به محتوا (Multi-Dimensional Navigation)")
    md.append("1. [📅 جدول ایندکس زمانی (Timeline Index by Date)](#۱-جدول-ایندکس-زمانی-timeline-index)")
    md.append("2. [⚙️ طبقه‌بندی بر اساس موضوع و حوزه مهندسی (Category / Topic)](#۲-طبقه‌بندی-بر-اساس-موضوع-و-حوزه-مهندسی-category--topic)")
    md.append("3. [🌐 طبقه‌بندی بر اساس مرجع و ناشر بین‌المللی (Reference / Publisher)](#۳-طبقه‌بندی-بر-اساس-مرجع-و-ناشر-بین‌المللی-reference--publisher)")
    md.append("4. [🏗️ پیوند با ۶ ستون خدمات ماشین دیزاین](#۴-پیوند-با-۶-ستون-خدمات-ماشین-دیزاین)")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## ۱. جدول ایندکس زمانی (Timeline Index)")
    md.append("")
    md.append("| تاریخ انتشار | عنوان و کالبدشکافی مهندسی (فارسی) | مرجع و ناشر | دسته‌بندی موضوعی | اسپانسر / فناور | مطالعه مقاله |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :---: |")

    for e in entries:
        sponsors_str = "، ".join(e["sponsors"]) if e["sponsors"] else "—"
        md.append(f"| **{e['date']}** | [{e['title_fa']}]({e['article_md']}) | `{e['reference_name']}` | **{e['category_title_fa']}** | {sponsors_str} | [📖 مطالعه مقاله]({e['article_md']}) |")

    md.append("")
    md.append("---")
    md.append("")
    md.append("## ۲. طبقه‌بندی بر اساس موضوع و حوزه مهندسی (Category / Topic)")
    md.append("")

    # Group by category
    cats = {}
    for e in entries:
        cats.setdefault(e["category"], []).append(e)

    for cat_slug, cat_entries in sorted(cats.items()):
        cat_info = taxonomy.get("categories", {}).get(cat_slug, {})
        title_fa = cat_info.get("title_fa", cat_slug)
        title_en = cat_info.get("title_en", cat_slug)
        pillar = cat_info.get("pillar", "Machine Design")

        md.append(f"### 🔹 {title_fa} (`{cat_slug}`)")
        md.append(f"**حوزه تخصصی انگلیسی:** *{title_en}* | **ستون مرتبط:** `{pillar}`")
        md.append("")
        for item in cat_entries:
            md.append(f"* **[{item['date']}]** [{item['title_fa']}]({item['article_md']}) — *مرجع: {item['reference_name']}*")
        md.append("")

    md.append("---")
    md.append("")
    md.append("## ۳. طبقه‌بندی بر اساس مرجع و ناشر بین‌المللی (Reference / Publisher)")
    md.append("")

    # Group by reference
    refs = {}
    for e in entries:
        refs.setdefault(e["reference"], []).append(e)

    for ref_slug, ref_entries in sorted(refs.items()):
        ref_info = taxonomy.get("references", {}).get(ref_slug, {})
        ref_name = ref_info.get("name", ref_slug)
        ref_url = ref_info.get("website", "")
        ref_country = ref_info.get("country", "")
        ref_type = ref_info.get("type", "")

        md.append(f"### 🌐 [{ref_name}]({ref_url}) (`{ref_slug}`)")
        md.append(f"**کشور / منطقه:** {ref_country} | **ماهیت مرجع:** {ref_type}")
        md.append("")
        for item in ref_entries:
            md.append(f"* **[{item['date']}]** [{item['title_fa']}]({item['article_md']}) — *موضوع: {item['category_title_fa']}*")
        md.append("")

    md.append("---")
    md.append("")
    md.append("## ۴. پیوند با ۶ ستون خدمات ماشین دیزاین")
    md.append("""
کلیه مقالات و تحلیل‌های ترجمه‌شده در این ریپازیتوری در راستای ارتقای ۶ ستون اصلی خدمات **ماشین دیزاین (`MachineDesign.ir`)** تدوین و بومی‌سازی می‌شوند:
1. **طراحی ماشین‌آلات و خطوط تولید:** صنایع غذایی، بسته‌بندی، مکانیزم‌های صنعتی، DFMA، مهندسی معکوس و استانداردسازی قطعات (DIN/ISO/JIS).
2. **مشاوره فنی و حل مسئله کارخانه‌ها:** رفع توقف خط، عیب‌یابی ارتعاشات، یاتاقان‌ها، اتصالات ایمن و بهینه‌سازی فرآیند ساخت.
3. **مشاوره سازمانی و تحقیق و توسعه (R&D):** ساخت پروتوتایپ، اجرای DFMEA و امکان‌سنجی سلول‌های پیشرفته مکانیزه.
4. **آموزش و منتورشیپ فردی:** سالیدورک پیشرفته، شبیه‌سازی اجزای محدود FEA با Ansys و تلرانس‌گذاری ابعادی هندسی (GD&T).
5. **آموزش سازمانی کارخانه‌ها:** ارتقای تیم‌های فنی در محل کارگاه، نقشه‌خوانی صنعتی و استانداردسازی مونتاژ.
6. **مشاوره و کارشناسی خرید ماشین‌آلات:** ارزیابی فنی دستگاه‌های وارداتی از چین و دبی، راستی‌آزمایی کاتالوگ‌ها و تدوین RFQ.

---

### 💻 همگام‌سازی و افزودن خبرنامه جدید
جهت اسکن پوشه خبرنامه‌ها و بازسازی خودکار ایندکس‌ها:
```bash
python sync_newsletter.py
```
""")

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

if __name__ == "__main__":
    print("[*] Rebuilding newsletter index...")
    items = rebuild_index()
    print(f"[+] Found {len(items)} newsletters.")
    print("[*] Generating README.md catalog...")
    generate_readme(items)
    print("[+] Done.")
