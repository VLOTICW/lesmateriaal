"""Bouwt de site uit de map inhoud/ naar de map _site/.

Structuur:  inhoud/<vak>/<klas>/<bestand>
            inhoud/<vak>/<klas>/<groep>/<bestand>        -> groep wordt een tussenkop
            inhoud/<vak>/<klas>/<map met index.html>/     -> één item (pagina met eigen bestanden)

Lokaal testen:  python build.py   en dan _site/index.html openen.
"""

import html
import re
import shutil
import subprocess
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent
INHOUD = ROOT / "inhoud"
SITE = ROOT / "_site"
NIEUW_DAGEN = 14          # zo lang krijgt een bestand het label "nieuw"
RECENT_AANTAL = 8         # aantal items in "Recent toegevoegd" op de startpagina
NEGEER = {".gitkeep", ".DS_Store", "Thumbs.db", "desktop.ini"}

config = tomllib.loads((ROOT / "site.toml").read_text(encoding="utf-8"))
VAKKEN = config["vakken"]
KLASSEN = config["klassen"]


# ---------- hulpfuncties ----------

def leesbare_naam(naam: str) -> str:
    """'03-wet-van-ohm' -> 'Wet van ohm' (volgnummer vooraan wordt weggelaten)."""
    naam = re.sub(r"^\d+[\s._-]+", "", naam)
    naam = naam.replace("_", " ").replace("-", " ").strip()
    return naam[:1].upper() + naam[1:] if naam else naam


def html_titel(pad: Path) -> str | None:
    try:
        tekst = pad.read_text(encoding="utf-8", errors="ignore")[:20000]
    except OSError:
        return None
    m = re.search(r"<title[^>]*>(.*?)</title>", tekst, re.I | re.S)
    if not m:
        return None
    return html.unescape(m.group(1)).strip() or None


def toegevoegd_op(pad: Path) -> float:
    """Tijdstip van de eerste commit van dit bestand (of de wijzigingstijd als fallback)."""
    try:
        uit = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%at", "--", str(pad)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
        if uit:
            return float(uit[-1])
    except (OSError, subprocess.CalledProcessError):
        pass
    return pad.stat().st_mtime


def soort(pad: Path) -> str:
    if pad.is_dir():
        return "web"
    ext = pad.suffix.lower().lstrip(".")
    return {"html": "web", "htm": "web"}.get(ext, ext or "bestand")


def item(pad: Path) -> dict:
    is_map = pad.is_dir()
    doel = pad / "index.html" if is_map else pad
    titel = None
    if doel.suffix.lower() in (".html", ".htm"):
        titel = html_titel(doel)
    if not titel:
        titel = leesbare_naam(pad.name if is_map else pad.stem)
    rel = pad.relative_to(INHOUD).as_posix() + ("/" if is_map else "")
    return {
        "titel": titel,
        "url": rel,
        "soort": soort(pad),
        "sorteer": pad.name.lower(),
        "tijd": toegevoegd_op(doel),
    }


def verzamel(map_: Path) -> tuple[list, dict]:
    """Geeft (losse items, {groepnaam: items}) voor een klasmap."""
    losse, groepen = [], {}
    if not map_.exists():
        return losse, groepen
    for p in sorted(map_.iterdir(), key=lambda x: x.name.lower()):
        if p.name in NEGEER or p.name.startswith("."):
            continue
        if p.is_dir() and not (p / "index.html").exists():
            sub = [item(q) for q in sorted(p.iterdir(), key=lambda x: x.name.lower())
                   if q.name not in NEGEER and not q.name.startswith(".")]
            if sub:
                groepen[leesbare_naam(p.name)] = sub
        else:
            losse.append(item(p))
    return losse, groepen


# ---------- HTML ----------

CSS = """
:root{--bg:#f6f5f2;--kaart:#fff;--tekst:#1d1d1b;--zacht:#6b6a66;--lijn:#e3e1dc;
--accent:#1f5f8b;--k5:#1f5f8b;--k6:#8b3a1f;--nieuw:#2e7d32}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--kaart:#20201e;--tekst:#ecebe7;
--zacht:#a3a19b;--lijn:#34332f;--accent:#7fb3d9;--k5:#7fb3d9;--k6:#e0a07f;--nieuw:#81c784}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tekst);
font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:inherit}
.wrap{max-width:1100px;margin:0 auto;padding:0 16px}
header{border-bottom:1px solid var(--lijn);background:var(--kaart)}
header .wrap{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;padding-top:18px;padding-bottom:14px}
header .merk{font-weight:700;font-size:1.15rem;text-decoration:none}
header .sub{color:var(--zacht);font-size:.9rem}
nav{display:flex;gap:4px;flex-wrap:wrap;margin-left:auto}
nav a{text-decoration:none;padding:4px 10px;border-radius:6px;font-size:.92rem;color:var(--zacht)}
nav a:hover{background:var(--bg);color:var(--tekst)}
nav a.actief{background:var(--bg);color:var(--tekst);font-weight:600}
main{padding:28px 0 60px}
h1{font-size:1.7rem;margin:0 0 6px}
.intro{color:var(--zacht);margin:0 0 24px}
.tegels{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
.tegel{background:var(--kaart);border:1px solid var(--lijn);border-radius:10px;padding:18px}
.tegel h2{margin:0 0 10px;font-size:1.15rem}
.tegel h2 a{text-decoration:none}
.tegel h2 a:hover{text-decoration:underline}
.klaslinks{display:flex;gap:8px;flex-wrap:wrap}
.klaslink{text-decoration:none;font-size:.9rem;padding:4px 10px;border-radius:6px;border:1px solid var(--lijn)}
.klaslink:hover{border-color:var(--tekst)}
.klaslink small{color:var(--zacht)}
.kolommen{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start}
@media (max-width:760px){.kolommen{grid-template-columns:1fr}}
section.klas{background:var(--kaart);border:1px solid var(--lijn);border-radius:10px;
padding:16px 18px;border-top:4px solid var(--kk);scroll-margin-top:16px}
section.klas h2{margin:0 0 8px;font-size:1.2rem;color:var(--kk)}
section.klas:target{box-shadow:0 0 0 2px var(--kk)}
h3{font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;color:var(--zacht);margin:18px 0 4px}
ul.lijst{list-style:none;margin:0;padding:0}
ul.lijst li{border-top:1px solid var(--lijn)}
ul.lijst li:first-child{border-top:0}
ul.lijst a{display:flex;align-items:center;gap:10px;padding:8px 2px;text-decoration:none}
ul.lijst a:hover .t{text-decoration:underline}
.t{flex:1;min-width:0}
.badge{font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.04em;
padding:2px 6px;border-radius:4px;border:1px solid var(--lijn);color:var(--zacht);white-space:nowrap}
.nieuw{color:var(--nieuw);border-color:var(--nieuw)}
.leeg{color:var(--zacht);font-style:italic;margin:6px 0}
.meta{color:var(--zacht);font-size:.85rem}
.recent{margin-top:32px}
.recent h2{font-size:1.15rem;margin:0 0 8px}
.recent .kaart{background:var(--kaart);border:1px solid var(--lijn);border-radius:10px;padding:6px 18px}
footer{color:var(--zacht);font-size:.85rem;padding:20px 0;border-top:1px solid var(--lijn)}
"""


def e(s: str) -> str:
    return html.escape(s, quote=True)


def pagina(titel: str, inhoud: str, prefix: str, actief: str | None = None) -> str:
    nav = "".join(
        f'<a href="{prefix}{v}/"{" class=actief" if v == actief else ""}>{e(n)}</a>'
        for v, n in VAKKEN.items()
    )
    bijgewerkt = time.strftime("%d/%m/%Y")
    return f"""<!doctype html>
<html lang="nl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titel)}</title><style>{CSS}</style></head>
<body><header><div class="wrap">
<a class="merk" href="{prefix}">{e(config["titel"])}</a>
<span class="sub">{e(config.get("ondertitel", ""))}</span>
<nav>{nav}</nav></div></header>
<main><div class="wrap">{inhoud}</div></main>
<footer><div class="wrap">Bijgewerkt op {bijgewerkt}</div></footer>
</body></html>"""


def lijst(items: list, prefix: str, nu: float) -> str:
    rijen = []
    for it in items:
        nieuw = nu - it["tijd"] < NIEUW_DAGEN * 86400
        rijen.append(
            f'<li><a href="{prefix}{e(it["url"])}"><span class="t">{e(it["titel"])}</span>'
            + ('<span class="badge nieuw">nieuw</span>' if nieuw else "")
            + f'<span class="badge">{e(it["soort"])}</span></a></li>'
        )
    return f'<ul class="lijst">{"".join(rijen)}</ul>'


def bouw():
    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(INHOUD, SITE, ignore=shutil.ignore_patterns(*NEGEER))
    (SITE / ".nojekyll").touch()
    nu = time.time()

    alle = []
    tellingen = {}
    for vak, vaknaam in VAKKEN.items():
        kolommen = []
        for klas, klasnaam in KLASSEN.items():
            losse, groepen = verzamel(INHOUD / vak / klas)
            n = len(losse) + sum(len(g) for g in groepen.values())
            tellingen[(vak, klas)] = n
            for it in losse + [x for g in groepen.values() for x in g]:
                alle.append({**it, "vak": vaknaam, "klas": klasnaam})
            delen = []
            if losse:
                delen.append(lijst(losse, "../", nu))
            for gnaam, gitems in groepen.items():
                delen.append(f"<h3>{e(gnaam)}</h3>" + lijst(gitems, "../", nu))
            if not delen:
                delen.append('<p class="leeg">Nog geen materiaal.</p>')
            kleur = "var(--k5)" if klas.startswith("5") else "var(--k6)"
            kolommen.append(
                f'<section class="klas" id="{klas}" style="--kk:{kleur}">'
                f"<h2>{e(klasnaam)}</h2>{''.join(delen)}</section>"
            )
        inhoud = (
            f"<h1>{e(vaknaam)}</h1>"
            f'<p class="intro">Materiaal voor {" en ".join(e(k) for k in KLASSEN.values())}.</p>'
            f'<div class="kolommen">{"".join(kolommen)}</div>'
        )
        (SITE / vak).mkdir(parents=True, exist_ok=True)
        (SITE / vak / "index.html").write_text(
            pagina(f"{vaknaam} — {config['titel']}", inhoud, "../", vak), encoding="utf-8"
        )

    # startpagina
    tegels = []
    for vak, vaknaam in VAKKEN.items():
        links = "".join(
            f'<a class="klaslink" href="{vak}/#{klas}">{e(kn)} <small>({tellingen[(vak, klas)]})</small></a>'
            for klas, kn in KLASSEN.items()
        )
        tegels.append(
            f'<div class="tegel"><h2><a href="{vak}/">{e(vaknaam)}</a></h2>'
            f'<div class="klaslinks">{links}</div></div>'
        )
    recent = sorted(alle, key=lambda x: x["tijd"], reverse=True)[:RECENT_AANTAL]
    recent_html = ""
    if recent:
        rijen = "".join(
            f'<li><a href="{e(it["url"])}"><span class="t">{e(it["titel"])}'
            f'<br><span class="meta">{e(it["vak"])} · {e(it["klas"])} · '
            f'{time.strftime("%d/%m/%Y", time.localtime(it["tijd"]))}</span></span>'
            f'<span class="badge">{e(it["soort"])}</span></a></li>'
            for it in recent
        )
        recent_html = (f'<div class="recent"><h2>Recent toegevoegd</h2>'
                       f'<div class="kaart"><ul class="lijst">{rijen}</ul></div></div>')
    inhoud = (
        f"<h1>{e(config['titel'])}</h1>"
        f'<p class="intro">Kies een vak.</p>'
        f'<div class="tegels">{"".join(tegels)}</div>{recent_html}'
    )
    (SITE / "index.html").write_text(pagina(config["titel"], inhoud, ""), encoding="utf-8")
    print(f"Site gebouwd in {SITE} ({len(alle)} items)")


if __name__ == "__main__":
    bouw()
