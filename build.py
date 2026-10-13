#!/usr/bin/env python3
"""Builds the static site from src/ into public/.

Usage:  python3 build.py

Content lives in src/pages/<lang>/<slug>.html. Each file starts with a JSON
meta block wrapped in <!--meta ... --> followed by the page body HTML.
Site-wide settings (Telegram, author, URL) are in src/config.json.
Cases (screenshots + short story) are in src/cases.json; a page shows the
cases whose "topic" matches the page's "topic".
"""
import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "public"
LANGS = ["en", "uk", "ru"]
DEFAULT_LANG = "en"

CONFIG = json.loads((SRC / "config.json").read_text(encoding="utf-8"))
CASES = json.loads((SRC / "cases.json").read_text(encoding="utf-8"))
SITE = CONFIG["site_url"].rstrip("/")

T = {
    "en": {
        "lang_name": "English", "locale": "en_US",
        "nav_guides": "Guides", "nav_how": "How I work", "nav_contact": "Contact",
        "home": "Home", "guides": "Guides",
        "by": "Written by", "updated": "Updated",
        "cta_title": "Merchant Center suspended or Shopping ads stuck?",
        "cta_text": "Send me a screenshot of the notice in Merchant Center or Google Ads. I'll tell you what most likely triggered it and what to fix before you request a review. The first look is free.",
        "cta_button": "Message me on Telegram",
        "author_bio": "Google Ads specialist since 2018: Search, Shopping, Performance Max, GDN, conversion tracking with GTM. Since 2024 I've been working closely with Merchant Center suspensions and feed problems for ecommerce stores.",
        "related": "Related guides",
        "cases": "Real cases",
        "case_cause": "Cause", "case_fix": "What I changed", "case_result": "Result",
        "footer_note": "Independent specialist. Not affiliated with Google. Nobody can guarantee reinstatement: Google makes the final decision on every review.",
        "privacy": "This site has no forms, no cookies and no analytics that identify you. If you write to me on Telegram, I see only what you send.",
        "months": ["January","February","March","April","May","June","July","August","September","October","November","December"],
        "notfound_title": "Page not found", "notfound_text": "This page doesn't exist or has moved.", "notfound_link": "Go to the guides",
    },
    "uk": {
        "lang_name": "Українська", "locale": "uk_UA",
        "nav_guides": "Інструкції", "nav_how": "Як я працюю", "nav_contact": "Контакт",
        "home": "Головна", "guides": "Інструкції",
        "by": "Автор", "updated": "Оновлено",
        "cta_title": "Merchant Center заблоковано або товарна реклама не крутиться?",
        "cta_text": "Надішліть мені скриншот повідомлення з Merchant Center або Google Ads. Скажу, що найімовірніше стало причиною і що виправити до запиту на перевірку. Перший погляд безкоштовний.",
        "cta_button": "Написати в Telegram",
        "author_bio": "Працюю з Google Ads з 2018 року: пошук, Shopping, Performance Max, КМС, налаштування конверсій через GTM. З 2024 року щільно займаюся блокуваннями Merchant Center і проблемами фідів інтернет-магазинів.",
        "related": "Схожі інструкції",
        "cases": "Реальні кейси",
        "case_cause": "Причина", "case_fix": "Що я змінив", "case_result": "Результат",
        "footer_note": "Незалежний спеціаліст, не пов'язаний з Google. Розблокування не може гарантувати ніхто: остаточне рішення щодо кожної перевірки ухвалює Google.",
        "privacy": "На сайті немає форм, cookies і аналітики, що вас ідентифікує. Якщо ви пишете мені в Telegram, я бачу лише те, що ви надіслали.",
        "months": ["січня","лютого","березня","квітня","травня","червня","липня","серпня","вересня","жовтня","листопада","грудня"],
        "notfound_title": "Сторінку не знайдено", "notfound_text": "Такої сторінки немає або її перенесено.", "notfound_link": "До інструкцій",
    },
    "ru": {
        "lang_name": "Русский", "locale": "ru_RU",
        "nav_guides": "Инструкции", "nav_how": "Как я работаю", "nav_contact": "Контакт",
        "home": "Главная", "guides": "Инструкции",
        "by": "Автор", "updated": "Обновлено",
        "cta_title": "Merchant Center заблокирован или торговая реклама не крутится?",
        "cta_text": "Пришлите мне скриншот уведомления из Merchant Center или Google Ads. Скажу, что скорее всего стало причиной и что исправить до запроса на проверку. Первый взгляд бесплатный.",
        "cta_button": "Написать в Telegram",
        "author_bio": "Работаю с Google Ads с 2018 года: поиск, Shopping, Performance Max, КМС, настройка конверсий через GTM. С 2024 года плотно занимаюсь блокировками Merchant Center и проблемами фидов интернет-магазинов.",
        "related": "Похожие инструкции",
        "cases": "Реальные кейсы",
        "case_cause": "Причина", "case_fix": "Что я изменил", "case_result": "Результат",
        "footer_note": "Независимый специалист, не связан с Google. Разблокировку не может гарантировать никто: окончательное решение по каждой проверке принимает Google.",
        "privacy": "На сайте нет форм, cookies и аналитики, которая вас идентифицирует. Если вы пишете мне в Telegram, я вижу только то, что вы прислали.",
        "months": ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"],
        "notfound_title": "Страница не найдена", "notfound_text": "Такой страницы нет или она перенесена.", "notfound_link": "К инструкциям",
    },
}
HREFLANG = {"en": "en", "uk": "uk", "ru": "ru"}


def url_path(lang, slug):
    """Public path for a page. slug 'index' is the language home."""
    prefix = "" if lang == DEFAULT_LANG else f"/{lang}"
    if slug == "index":
        return f"{prefix}/"
    return f"{prefix}/{slug}"


def out_file(lang, slug):
    base = OUT if lang == DEFAULT_LANG else OUT / lang
    return base / ("index.html" if slug == "index" else f"{slug}.html")


def fmt_date(iso, lang):
    d = date.fromisoformat(iso)
    m = T[lang]["months"][d.month - 1]
    return f"{m} {d.day}, {d.year}" if lang == "en" else f"{d.day} {m} {d.year}"


def load_pages():
    pages = {}
    for lang in LANGS:
        for f in sorted((SRC / "pages" / lang).rglob("*.html")):
            slug = f.relative_to(SRC / "pages" / lang).with_suffix("").as_posix()
            raw = f.read_text(encoding="utf-8")
            m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*(.*)", raw, re.S)
            if not m:
                raise SystemExit(f"No meta block in {f}")
            meta = json.loads(m.group(1))
            pages[(lang, slug)] = {"meta": meta, "body": m.group(2), "lang": lang, "slug": slug}
    return pages


def tg_url():
    handle = CONFIG["telegram"].lstrip("@")
    return f"https://t.me/{handle}"


def lang_switch(lang, slug, pages):
    items = []
    for l in LANGS:
        if (l, slug) not in pages:
            continue
        label = {"en": "EN", "uk": "UA", "ru": "RU"}[l]
        cur = ' aria-current="true"' if l == lang else ""
        items.append(f'<a href="{url_path(l, slug)}" hreflang="{HREFLANG[l]}" lang="{l}"{cur}>{label}</a>')
    return '<nav class="langs" aria-label="Language">' + "".join(items) + "</nav>"


def hreflang_links(slug, pages):
    out = []
    for l in LANGS:
        if (l, slug) in pages:
            out.append(f'<link rel="alternate" hreflang="{HREFLANG[l]}" href="{SITE}{url_path(l, slug)}">')
    if (DEFAULT_LANG, slug) in pages:
        out.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}{url_path(DEFAULT_LANG, slug)}">')
    return "\n".join(out)


def author_name(lang):
    return CONFIG["author"]["name"][lang]


def cases_html(lang, topic):
    items = [c for c in CASES if topic and c.get("topic") == topic and lang in c.get("text", {})]
    if not items:
        return ""
    t = T[lang]
    parts = [f'<section class="cases"><h2>{t["cases"]}</h2>']
    for c in items:
        x = c["text"][lang]
        imgs = "".join(
            f'<figure><img src="/img/cases/{escape(i["file"])}" alt="{escape(i["alt"][lang])}" loading="lazy" width="{i.get("w", 1200)}" height="{i.get("h", 800)}"><figcaption>{escape(i["alt"][lang])}</figcaption></figure>'
            for i in c.get("images", [])
        )
        parts.append(
            f'<article class="case"><h3>{escape(x["title"])}</h3>'
            f'<dl><dt>{t["case_cause"]}</dt><dd>{escape(x["cause"])}</dd>'
            f'<dt>{t["case_fix"]}</dt><dd>{escape(x["fix"])}</dd>'
            f'<dt>{t["case_result"]}</dt><dd>{escape(x["result"])}</dd></dl>{imgs}</article>'
        )
    parts.append("</section>")
    return "".join(parts)


def cta_html(lang):
    t = T[lang]
    return (
        f'<aside class="cta" id="contact"><h2>{t["cta_title"]}</h2><p>{t["cta_text"]}</p>'
        f'<a class="btn" href="{tg_url()}" rel="noopener">{t["cta_button"]}</a></aside>'
    )


def author_html(lang):
    t = T[lang]
    a = CONFIG["author"]
    photo = (
        f'<img class="avatar" src="{a["photo"]}" alt="{escape(author_name(lang))}" width="96" height="96">'
        if a.get("photo") else f'<span class="avatar" aria-hidden="true">{author_name(lang)[0]}</span>'
    )
    return (
        f'<aside class="author">{photo}<div><p class="author-name">{t["by"]}: {escape(author_name(lang))}</p>'
        f'<p>{t["author_bio"]}</p></div></aside>'
    )


def related_html(lang, rel, pages):
    if not rel:
        return ""
    t = T[lang]
    lis = "".join(
        f'<li><a href="{url_path(lang, s)}">{escape(pages[(lang, s)]["meta"]["h1"])}</a></li>'
        for s in rel if (lang, s) in pages
    )
    return f'<nav class="related" aria-label="{t["related"]}"><h2>{t["related"]}</h2><ul>{lis}</ul></nav>'


def schema(page, pages):
    lang, slug, meta = page["lang"], page["slug"], page["meta"]
    url = SITE + url_path(lang, slug)
    person = {
        "@type": "Person", "@id": f"{SITE}/#author", "name": CONFIG["author"]["name"]["en"],
        "jobTitle": "Google Ads specialist", "url": f"{SITE}/",
        "knowsAbout": ["Google Merchant Center", "Google Ads", "Performance Max", "Conversion tracking"],
    }
    if CONFIG["author"].get("same_as"):
        person["sameAs"] = CONFIG["author"]["same_as"]
    graph = [person, {
        "@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/", "name": CONFIG["brand"],
        "inLanguage": LANGS,
    }]
    if slug == "index":
        graph.append({
            "@type": "ProfessionalService", "@id": f"{SITE}/#service", "name": CONFIG["brand"],
            "url": f"{SITE}/", "description": meta["description"], "founder": {"@id": f"{SITE}/#author"},
            "areaServed": "Worldwide", "serviceType": "Google Merchant Center suspension review and Google Ads troubleshooting",
        })
    else:
        t = T[lang]
        graph.append({
            "@type": "Article", "headline": meta["h1"], "description": meta["description"],
            "inLanguage": lang, "datePublished": meta.get("published", meta["updated"]),
            "dateModified": meta["updated"], "author": {"@id": f"{SITE}/#author"},
            "publisher": {"@id": f"{SITE}/#author"}, "mainEntityOfPage": url,
        })
        graph.append({
            "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": t["home"], "item": SITE + url_path(lang, "index")},
                {"@type": "ListItem", "position": 2, "name": meta["h1"], "item": url},
            ],
        })
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


def render(page, pages):
    lang, slug, meta, body = page["lang"], page["slug"], page["meta"], page["body"]
    t = T[lang]
    url = SITE + url_path(lang, slug)
    is_home = slug == "index"
    home = url_path(lang, "index")
    body = body.replace("{{TELEGRAM_URL}}", tg_url()).replace("{{AUTHOR}}", author_html(lang))

    if is_home:
        main = body
    else:
        crumbs = f'<nav class="crumbs" aria-label="Breadcrumb"><a href="{home}">{t["home"]}</a> / <a href="{home}#guides">{t["guides"]}</a></nav>'
        byline = f'<p class="byline">{t["by"]}: {escape(author_name(lang))}. {t["updated"]}: <time datetime="{meta["updated"]}">{fmt_date(meta["updated"], lang)}</time></p>'
        main = (
            f'<article class="doc">{crumbs}<h1>{escape(meta["h1"])}</h1>{byline}'
            f'<p class="lead">{meta["lead"]}</p>{body}</article>'
            f'{cases_html(lang, meta.get("topic"))}{cta_html(lang)}{author_html(lang)}'
            f'{related_html(lang, meta.get("related", []), pages)}'
        )

    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(meta["title"])}</title>
<meta name="description" content="{escape(meta["description"])}">
<link rel="canonical" href="{url}">
{hreflang_links(slug, pages)}
<meta property="og:type" content="{"website" if is_home else "article"}">
<meta property="og:title" content="{escape(meta["title"])}">
<meta property="og:description" content="{escape(meta["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="{t["locale"]}">
<meta property="og:site_name" content="{CONFIG["brand"]}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700&family=Literata:opsz,wght@7..72,400;7..72,600&display=swap">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{schema(page, pages)}</script>
</head>
<body class="{"home" if is_home else "article"}">
<header class="top">
<a class="brand" href="{home}">{CONFIG["brand"]}</a>
<nav class="menu" aria-label="Main"><a href="{home}#guides">{t["nav_guides"]}</a><a href="{home}#how">{t["nav_how"]}</a><a href="{tg_url()}" rel="noopener">{t["nav_contact"]}</a></nav>
{lang_switch(lang, slug, pages)}
</header>
<main>
{main}
</main>
<footer class="foot">
<p>{t["footer_note"]}</p>
<p>{t["privacy"]}</p>
<p>&copy; {date.today().year} {CONFIG["brand"]} · {escape(author_name(lang))}</p>
</footer>
</body>
</html>
"""


def render_404():
    blocks = "".join(
        f'<section lang="{l}"><h2>{T[l]["notfound_title"]}</h2><p>{T[l]["notfound_text"]} <a href="{url_path(l, "index")}#guides">{T[l]["notfound_link"]}</a></p></section>'
        for l in LANGS
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>404 | {CONFIG["brand"]}</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/style.css"></head>
<body class="home"><header class="top"><a class="brand" href="/">{CONFIG["brand"]}</a></header>
<main class="nf"><p class="nf-code">404</p>{blocks}</main></body></html>
"""


def sitemap(pages):
    rows = []
    for (lang, slug), p in sorted(pages.items(), key=lambda kv: (kv[0][1], LANGS.index(kv[0][0]))):
        alts = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{HREFLANG[l]}" href="{SITE}{url_path(l, slug)}"/>'
            for l in LANGS if (l, slug) in pages
        )
        rows.append(
            f"  <url>\n    <loc>{SITE}{url_path(lang, slug)}</loc>\n    <lastmod>{p['meta']['updated']}</lastmod>{alts}\n  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(rows) + "\n</urlset>\n"
    )


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC / "static", OUT)
    pages = load_pages()
    for page in pages.values():
        f = out_file(page["lang"], page["slug"])
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(render(page, pages), encoding="utf-8")
    (OUT / "404.html").write_text(render_404(), encoding="utf-8")
    (OUT / "sitemap.xml").write_text(sitemap(pages), encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    if "@" in CONFIG["telegram"] or not CONFIG["telegram"] or CONFIG["telegram"] == "CHANGE_ME":
        print("WARNING: set your Telegram username in src/config.json")
    print(f"Built {len(pages)} pages into {OUT}")


if __name__ == "__main__":
    main()
