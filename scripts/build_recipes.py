#!/usr/bin/env python3
"""Uygulamanın tarif havuzundan İngilizce tarif sayfaları üretir.

Kaynak: uygulama deposu (uguryesilbas-ui/pisirsem) backend/data + backend/services/i18n.py.
Uygulamadaki İngilizce çeviriyi birebir kullanır; ayrı bir çeviri yoktur.

Çıktı (bu depoda):
  en/recipes/index.html          — tüm tarifler, kategoriye göre
  en/recipes/<id>.html           — her tarif için bir sayfa (schema.org Recipe ile)
  en/recipes/recipes.json        — pin aracı için tarif verisi
  sitemap.xml, robots.txt

Görseller: assets/recipes/<id>.jpg|.jpeg|.webp|.png varsa sayfaya ve şemaya eklenir.
Görsel ekledikten sonra script'i yeniden çalıştırmak yeterli.

Kullanım:
  python3 scripts/build_recipes.py /yol/pisirsem/backend
"""
import html
import json
import re
import sys
from pathlib import Path

SITE = "https://www.pisirsem.com.tr"  # alan adı www adresine yönlendiriyor
PLAY = "https://play.google.com/store/apps/details?id=com.pisirsem.app"
WEB = Path(__file__).resolve().parent.parent
OUT = WEB / "en" / "recipes"
IMG_DIR = WEB / "assets" / "recipes"
IMG_EXT = (".jpg", ".jpeg", ".webp", ".png")

# Kategori sırası ve kısa açıklamaları (dizin sayfası için)
CATEGORY_ORDER = [
    "Kahvaltı", "Çorba", "Sebze Yemekleri", "Et/Kıyma Yemekleri", "Tavuk Yemekleri",
    "Balık/Deniz Ürünleri", "Bakliyat", "Makarna/Pilav", "Salata/Meze",
    "Pratik/Ekonomik", "Tatlı/Atıştırmalık", "Sporcu Öğünü",
]


def esc(s):
    return html.escape(str(s or ""), quote=True)


def slug_category(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def iso_minutes(m):
    m = int(m or 0)
    if m <= 0:
        return None
    h, mm = divmod(m, 60)
    return "PT" + (f"{h}H" if h else "") + (f"{mm}M" if mm else "")


def human_minutes(m):
    m = int(m or 0)
    h, mm = divmod(m, 60)
    if h and mm:
        return f"{h} hr {mm} min"
    return f"{h} hr" if h else f"{mm} min"


def find_image(rid):
    for ext in IMG_EXT:
        p = IMG_DIR / f"{rid}{ext}"
        if p.exists():
            return f"/assets/recipes/{rid}{ext}"
    return None


def load(backend):
    sys.path.insert(0, str(backend))
    from services import i18n  # noqa: E402  (uygulamanın kendi çeviri kodu)

    tr = json.loads((backend / "data" / "recipes_tr.json").read_text(encoding="utf-8"))
    out = []
    for r in tr:
        en = i18n.recipe_en(r["id"])
        if not en:
            continue
        times = r.get("times") or {}
        prep, cook, rest = int(times.get("hazirlik") or 0), int(times.get("pisirme") or 0), int(times.get("bekleme") or 0)
        soak = times.get("islatma")
        ings = []
        for name in r["ingredients"]:
            amount = i18n.translate_amount((r.get("ingredient_amounts") or {}).get(name)) or ""
            ings.append({"name": i18n.ingredient_en(name), "amount": amount})
        out.append({
            "id": r["id"],
            "title": en["title"],
            "category": i18n.category_en(r["category"]),
            "category_tr": r["category"],
            "difficulty": i18n.difficulty_en(r.get("difficulty") or ""),
            "servings": r.get("servings") or 4,
            "serving_note": i18n.serving_note_en(r.get("serving_note")) or "",
            "prep": prep, "cook": cook, "rest": rest,
            "total": prep + cook + rest,
            "soak": (i18n.times_en(times) or {}).get("islatma") if soak else None,
            "ingredients": ings,
            "steps": list(en["steps"]),
            "tags_tr": r.get("tags") or [],
            "image": find_image(r["id"]),
        })
    return out


def description(r):
    names = ", ".join(i["name"] for i in r["ingredients"][:4])
    t = human_minutes(r["total"])
    soak = " (plus overnight soaking)" if r["soak"] else ""
    return f"{r['title']}: an easy Turkish home-cooking recipe ready in {t}{soak}. With {names}. Simple step-by-step instructions, serves {r['servings']}."


CSS = """:root{--orange:#F26430;--ink:#2A1B10;--muted:#6E5A49;--cream:#FFF8EC;--cream2:#FBF3E4;--line:#EEDFCB}*{box-sizing:border-box}body{margin:0;background:var(--cream2);color:var(--ink);font-family:Manrope,system-ui,sans-serif;line-height:1.6}a{color:inherit;text-decoration:none}.wrap{width:min(860px,calc(100% - 32px));margin:auto}.nav{position:sticky;top:0;z-index:50;background:#fbf3e4e8;backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}.navin{height:68px;display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:19px}.logo{width:40px;height:40px;border-radius:12px;object-fit:cover}.play{display:inline-flex;align-items:center;gap:8px;background:#17110d;color:#fff;border-radius:14px;padding:10px 15px;font-weight:800;font-size:14px}h1,h2{font-family:'Playfair Display',Georgia,serif;line-height:1.08}h1{font-size:clamp(34px,5.5vw,52px);letter-spacing:-.02em;margin:10px 0 12px}h2{font-size:28px;margin:34px 0 12px}.crumb{font-size:13px;color:var(--muted);margin-top:26px}.crumb a{color:var(--orange);font-weight:700}.lead{color:var(--muted);font-size:17px;margin:0 0 18px}.hero{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:24px;box-shadow:0 20px 50px #4b301b22;display:block;margin:18px 0}.meta{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}.chip{background:#fff;border:1px solid var(--line);border-radius:999px;padding:7px 13px;font-size:13px;font-weight:700}.box{background:#fff;border:1px solid var(--line);border-radius:22px;padding:20px 22px;box-shadow:0 12px 30px #4b301b0c}.ings{list-style:none;padding:0;margin:0}.ings li{display:flex;justify-content:space-between;gap:16px;padding:9px 0;border-bottom:1px dashed var(--line)}.ings li:last-child{border:0}.ings b{font-weight:700}.ings span{color:var(--muted);text-align:right}.steps{counter-reset:s;list-style:none;padding:0;margin:0}.steps li{counter-increment:s;position:relative;padding:4px 0 16px 50px}.steps li:before{content:counter(s);position:absolute;left:0;top:2px;width:34px;height:34px;border-radius:50%;background:var(--orange);color:#fff;display:grid;place-items:center;font-weight:800}.note{font-size:13px;color:var(--muted);margin-top:10px}.cta{margin:40px 0;background:linear-gradient(135deg,#f26430,#e34f1d);color:#fff;border-radius:26px;padding:30px;text-align:center}.cta h2{margin:0 0 8px;color:#fff}.cta p{margin:0 0 18px;color:#fff0e9}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}.card{display:block;background:#fff;border:1px solid var(--line);border-radius:18px;overflow:hidden}.card img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block}.card div{padding:12px 14px}.card b{display:block;line-height:1.25}.card small{color:var(--muted)}.cats{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 4px}.cats a{background:#fff;border:1px solid var(--line);border-radius:999px;padding:6px 12px;font-size:13px;font-weight:700}footer{background:#211610;color:#d8c8bb;padding:30px 0;margin-top:50px;font-size:13px}footer a{color:#ff9b6f;font-weight:700;margin-right:16px}@media(max-width:560px){.navin .play span{display:none}.box{padding:16px}}"""


def page(title, desc, canonical, body, extra_head=""):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#F26430"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow"><link rel="canonical" href="{esc(canonical)}"><meta property="og:type" content="article"><meta property="og:site_name" content="Pişirsem"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canonical)}">{extra_head}<link rel="icon" href="/assets/pisirsem-logo-official.png"><link rel="stylesheet" href="/assets/fonts/fonts.css"><style>{CSS}</style></head><body><header class="nav"><div class="wrap navin"><a class="brand" href="/en/"><img class="logo" src="/assets/pisirsem-logo-official.png" alt="Pişirsem logo">Pişirsem</a><a class="play" href="{PLAY}" target="_blank" rel="noopener">▶ <span>Get the app</span></a></div></header><main class="wrap">{body}</main><footer><div class="wrap"><a href="/en/recipes/">All recipes</a><a href="/en/">Pişirsem app</a><a href="/en/privacy-policy.html">Privacy</a><a href="/en/contact.html">Contact</a><div style="margin-top:12px">© 2026 Pişirsem</div></div></footer></body></html>"""


def cta():
    return f"""<section class="cta"><h2>Can't decide what to cook tomorrow?</h2><p>Pişirsem picks one easy Turkish meal for you, based on what's in your kitchen and how much time you have.</p><a class="play" href="{PLAY}" target="_blank" rel="noopener">▶ Get it on Google Play</a></section>"""


def card(r):
    img = f'<img src="{esc(r["image"])}" alt="{esc(r["title"])}" loading="lazy">' if r["image"] else ""
    return f'<a class="card" href="/en/recipes/{esc(r["id"])}.html">{img}<div><b>{esc(r["title"])}</b><small>{esc(human_minutes(r["total"]))} · {esc(r["difficulty"])}</small></div></a>'


def recipe_page(r, by_cat):
    url = f"{SITE}/en/recipes/{r['id']}.html"
    title = f"{r['title']} Recipe – Easy Turkish Home Cooking"
    desc = description(r)
    ld = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": r["title"],
        "description": desc,
        "recipeCuisine": "Turkish",
        "recipeCategory": r["category"],
        "keywords": f"{r['title']}, Turkish recipe, easy Turkish food, {r['category'].lower()}",
        "recipeYield": f"{r['servings']} servings",
        "recipeIngredient": [f"{i['amount']} {i['name']}".strip() for i in r["ingredients"]],
        "recipeInstructions": [{"@type": "HowToStep", "text": s} for s in r["steps"]],
        "author": {"@type": "Organization", "name": "Pişirsem", "url": f"{SITE}/en/"},
    }
    for k, v in (("prepTime", r["prep"]), ("cookTime", r["cook"]), ("totalTime", r["total"])):
        if iso_minutes(v):
            ld[k] = iso_minutes(v)
    extra = ""
    if r["image"]:
        ld["image"] = [SITE + r["image"]]
        extra = f'<meta property="og:image" content="{esc(SITE + r["image"])}">'
    extra += '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"

    chips = [f"⏱️ {human_minutes(r['total'])}"]
    if r["soak"]:
        chips.append(f"💧 Soak {r['soak']}")
    chips += [f"👩‍🍳 {r['difficulty']}", f"🍽️ {r['serving_note'] or str(r['servings']) + ' servings'}", f"📂 {r['category']}"]
    times = " · ".join(f"{n}: {human_minutes(v)}" for n, v in (("Prep", r["prep"]), ("Cook", r["cook"]), ("Rest", r["rest"])) if v)
    ings = "".join(f"<li><b>{esc(i['name'])}</b><span>{esc(i['amount'])}</span></li>" for i in r["ingredients"])
    cup_note = '<p class="note">1 cup = 200 ml (a Turkish water glass). tbsp = tablespoon, tsp = teaspoon.</p>' if any("cup" in i["amount"] for i in r["ingredients"]) else ""
    steps = "".join(f"<li>{esc(s)}</li>" for s in r["steps"])
    related = [x for x in by_cat.get(r["category"], []) if x["id"] != r["id"]][:6]
    img = f'<img class="hero" src="{esc(r["image"])}" alt="{esc(r["title"])}">' if r["image"] else ""
    body = f"""<div class="crumb"><a href="/en/recipes/">Turkish recipes</a> › <a href="/en/recipes/#{slug_category(r['category'])}">{esc(r['category'])}</a></div>
<article><h1>{esc(r['title'])}</h1><p class="lead">{esc(desc)}</p>{img}
<div class="meta">{''.join(f'<span class="chip">{esc(c)}</span>' for c in chips)}</div>
{f'<p class="note">{esc(times)}</p>' if times else ''}
<h2>Ingredients</h2><div class="box"><ul class="ings">{ings}</ul>{cup_note}</div>
<h2>Instructions</h2><div class="box"><ol class="steps">{steps}</ol></div></article>
{cta()}
{f'<h2>More {esc(r["category"].lower())}</h2><div class="grid">{"".join(card(x) for x in related)}</div>' if related else ''}"""
    return page(title, desc, url, body, extra)


def index_page(recipes, by_cat):
    url = f"{SITE}/en/recipes/"
    title = "Easy Turkish Recipes – Home Cooking, Step by Step"
    desc = f"{len(recipes)} easy Turkish home-cooking recipes: breakfast, soups, vegetable dishes, meat, chicken, pulses, desserts and more. Simple ingredients, clear steps."
    cats = [c for c in by_cat]
    nav = '<div class="cats">' + "".join(f'<a href="#{slug_category(c)}">{esc(c)}</a>' for c in cats) + "</div>"
    sections = "".join(
        f'<h2 id="{slug_category(c)}">{esc(c)}</h2><div class="grid">{"".join(card(r) for r in by_cat[c])}</div>' for c in cats
    )
    body = f"""<h1 style="margin-top:30px">Easy Turkish recipes</h1><p class="lead">{esc(desc)}</p>{nav}{sections}{cta()}"""
    return page(title, desc, url, body)


def main():
    if len(sys.argv) < 2:
        sys.exit("Kullanım: python3 scripts/build_recipes.py /yol/pisirsem/backend")
    backend = Path(sys.argv[1]).resolve()
    recipes = load(backend)
    order = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    recipes.sort(key=lambda r: (order.get(r["category_tr"], 99), r["title"]))
    by_cat = {}
    for r in recipes:
        by_cat.setdefault(r["category"], []).append(r)

    OUT.mkdir(parents=True, exist_ok=True)
    keep = {f"{r['id']}.html" for r in recipes} | {"index.html", "recipes.json"}
    for old in OUT.iterdir():  # havuzdan çıkan tariflerin sayfalarını kaldır
        if old.name not in keep:
            old.unlink()
    for r in recipes:
        (OUT / f"{r['id']}.html").write_text(recipe_page(r, by_cat), encoding="utf-8")
    (OUT / "index.html").write_text(index_page(recipes, by_cat), encoding="utf-8")
    pin_data = [{k: r[k] for k in ("id", "title", "category", "difficulty", "servings", "total", "soak", "image")}
                | {"ingredients": [i["name"] for i in r["ingredients"]], "tags_tr": r["tags_tr"]} for r in recipes]
    (OUT / "recipes.json").write_text(json.dumps(pin_data, ensure_ascii=False, indent=1), encoding="utf-8")

    pages = ["/", "/en/", "/en/recipes/", "/iletisim.html", "/en/contact.html"] + [f"/en/recipes/{r['id']}.html" for r in recipes]
    sm = "".join(f"<url><loc>{SITE}{p}</loc></url>" for p in pages)
    (WEB / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n', encoding="utf-8")
    (WEB / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    with_img = sum(1 for r in recipes if r["image"])
    print(f"{len(recipes)} tarif sayfası üretildi ({with_img} tanesinde görsel var).")


if __name__ == "__main__":
    main()
