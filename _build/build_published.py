"""Published Features: articles about AFT published elsewhere (AwareNow), shown as the original magazine pages
plus a readable text version. Output: <site>/published-features/ and one page per feature."""
import json, os, sys, html, shutil
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import nav as NAVMOD
SITE = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
AWN = os.environ.get('AWN', HERE)  # folder holding new page images (feature 'folder' is relative to it)
FEATURES = json.load(open(os.path.join(HERE, 'awarenow-features.json')))
FONT = '<link rel="stylesheet" href="https://use.typekit.net/scq8iav.css"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&display=swap">'
CSS = '''
.pf-hero{background:#111;color:#fff}.pf-hero .wrap{padding-block:clamp(28px,4vw,52px);display:grid;gap:12px}
.pf-hero .src{font-weight:600;font-size:1rem;letter-spacing:.06em;text-transform:uppercase;color:#f8a6cf}
.pf-hero h1{margin:0;font-size:clamp(2.4rem,5.4vw,4.6rem);line-height:.92;font-weight:700;max-width:20ch}
.pf-hero .kick{font-size:1.25rem;font-weight:600;color:#ddd}
.pf-hero .acts{display:flex;gap:12px;flex-wrap:wrap;margin-top:8px}
.pf-hero .acts a{font-weight:700;text-decoration:none;padding:10px 16px;border-radius:2px;border:1px solid #fff;color:#fff}
.pf-hero .acts a.p{background:var(--grad);color:#000;border-color:transparent}
.mag{background:#2b2b2b;padding:clamp(18px,3vw,40px) 0}
.spreads{display:grid;gap:clamp(14px,2vw,26px);max-width:1500px;margin:0 auto;padding:0 20px}
.spread{display:grid;grid-template-columns:1fr 1fr;box-shadow:0 12px 30px rgba(0,0,0,.45)}
.spread a{display:block;background:#fff;line-height:0}
.spread img{width:100%;height:auto;display:block}
.spread a:first-child{box-shadow:inset -14px 0 18px -14px rgba(0,0,0,.35)}
.pgno{color:#aaa;font-size:.9rem;text-align:center;margin-top:-6px}
@media (max-width:820px){.spread{grid-template-columns:1fr;box-shadow:none;gap:14px}.spread a{box-shadow:0 8px 20px rgba(0,0,0,.4)!important}}
.lb{position:fixed;inset:0;background:rgba(0,0,0,.92);display:none;z-index:100;overflow:auto;cursor:zoom-out}
.lb.on{display:block}.lb img{display:block;margin:20px auto;max-width:min(1133px,96vw);width:100%;height:auto}
.lb button{position:fixed;top:12px;right:14px;font:700 1.1rem var(--head);padding:8px 14px;border:0;border-radius:2px;background:#fff;cursor:pointer}
.txt{max-width:760px;margin:0 auto;padding:40px 20px 0;scroll-margin-top:80px}
.txt h2{font-size:2.2rem;line-height:.95;margin:0 0 6px}
.txt .lede{font-size:1.45rem;line-height:1.15;font-weight:600;margin:16px 0 24px}
.txt p{margin:0 0 18px;font-size:23px;line-height:1.18}
.txt p b{font-weight:700}
.txt .q b{color:var(--pink-ink)}
.txt .pre{white-space:pre-line}
.txt .caps{font-size:1rem;color:var(--mute);border-left:4px solid var(--line);padding-left:14px}
.txt .credit{font-size:1rem;color:var(--mute);border-top:1px solid var(--line);padding-top:14px;margin-top:30px}
.pfl{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:26px;padding-block:32px}
.pfc{text-decoration:none;display:grid;gap:10px}
.pfc .ph{aspect-ratio:1133/1467;overflow:hidden;background:#eee;box-shadow:0 8px 20px rgba(0,0,0,.15)}
.pfc .ph img{width:100%;height:100%;object-fit:cover}
.pfc small{color:var(--mute);font-weight:600;font-size:.95rem}
.pfc b{font-size:1.5rem;line-height:1}.pfc:hover b{color:var(--pink-ink)}
'''

def page(title, body, desc):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc[:160])}">
{FONT}<link rel="stylesheet" href="/blog/blog.css"><link rel="stylesheet" href="/published-features/pf.css"></head><body>
<header class="top"><div class="wrap"><a href="/" aria-label="Artists for Trauma home"><img src="/images/art_full.png" alt="Artists for Trauma"></a>
<nav class="main" aria-label="Main">{NAVMOD.nav_html()}</nav></div></header>
{body}
<footer><div class="wrap"><span>© Artists for Trauma · Powered by human spirit™</span><a href="/">artistsfortrauma.org</a></div></footer>
{NAVMOD.JS}</body></html>
'''

def para(p, f):
    import re
    m = re.match(r'^([A-ZÉ]{2,12}):\s*', p)
    if m:
        who = m.group(1); first = re.split(r'[,& ]', f['by'])
        is_q = who in ('ALLIÉ', 'ALLIE', 'EDDIE') or (who == 'LAURA' and 'Laura Sharpe' in f['by'] and f['people'] != 'Laura Sharpe') or (who == 'AARON' and 'Laquita' in f['people'])
        name = 'Allié' if who in ('ALLIÉ', 'ALLIE') else who.title()
        return f'<p{" class=\"q\"" if is_q else ""}><b>{html.escape(name)}:</b> {html.escape(p[m.end():])}</p>'
    return f'<p{" class=\"pre\"" if chr(10) in p else ""}>{html.escape(p)}</p>'

base = f'{SITE}/published-features'
os.makedirs(base, exist_ok=True)
open(f'{base}/pf.css', 'w').write(CSS)
cards = []
for f in FEATURES:
    d = f'{base}/{f["slug"]}'; os.makedirs(f'{d}/pages', exist_ok=True)
    for n in f['pages']:
        if os.path.exists(f'{d}/pages/p{n:03d}.jpg'): continue  # already published
        Image.open(f'{AWN}/{f["folder"]}/p{n:03d}.jpg').convert('RGB').save(f'{d}/pages/p{n:03d}.jpg', 'JPEG', quality=86, optimize=True, progressive=True)
    ISSUE = {'pub': 'AwareNow', 'issue': f"{f['issue']} · Issue {f['num']}" if f.get('num') else f['issue'], 'date': f['date'], 'url': f['url']}
    pairs = [f['pages'][i:i+2] for i in range(0, len(f['pages']), 2)]
    spreads = ''.join('<div class="spread">' + ''.join(f'<a href="pages/p{n:03d}.jpg" data-lb><img src="pages/p{n:03d}.jpg" alt="{html.escape(ISSUE["pub"])} page {n}" loading="{"eager" if i==0 else "lazy"}" width="1133" height="1467"></a>' for n in pr) + '</div>' for i, pr in enumerate(pairs))
    t = {'intro': f['intro'], 'body': f['body']}
    body = ''.join(para(p, f) for p in t['body'])
    extra = ''.join(f'<p class="caps"><b>{html.escape(h)}:</b> {html.escape(x)}</p>' for h, x in f['extra'])
    art = f'''<section class="pf-hero"><div class="wrap"><a class="crumb" href="/published-features/" style="color:#fff">← Published Features</a>
<div class="src">{ISSUE["pub"]} · {ISSUE["issue"]} · {ISSUE["date"]}</div>
<h1>{html.escape(f["title"])}</h1><div class="kick">{html.escape(f["kicker"])}</div>
<div class="acts"><a class="p" href="#read">Read the text</a><a href="{ISSUE["url"]}" target="_blank" rel="noopener">View the full issue ↗</a></div></div></section>
<section class="mag" aria-label="Magazine pages"><div class="spreads">{spreads}</div><p class="pgno">Pages {f["pages"][0]}–{f["pages"][-1]} as published. Click a page to enlarge.</p></section>
<article class="txt" id="read"><h2>{html.escape(f["title"])}</h2><div class="kick" style="color:var(--mute);font-weight:600">{html.escape(f["by"])}</div>
<p class="lede">{html.escape(t["intro"])}</p>{body}{extra}
<p class="credit">Originally published in {ISSUE["pub"]}, {ISSUE["issue"]} ({ISSUE["date"]}), by Awareness Ties. Republished with permission. {html.escape(f["credit"])}</p></article>
<div class="lb" id="lb" role="dialog" aria-label="Enlarged page"><button type="button">Close</button><img alt=""></div>
<script>(function(){{var lb=document.getElementById('lb'),im=lb.querySelector('img');document.querySelectorAll('[data-lb]').forEach(function(a){{a.addEventListener('click',function(e){{e.preventDefault();im.src=a.getAttribute('href');lb.classList.add('on');lb.scrollTop=0}})}});lb.addEventListener('click',function(){{lb.classList.remove('on')}});document.addEventListener('keydown',function(e){{if(e.key==='Escape')lb.classList.remove('on')}})}})();</script>'''
    open(f'{d}/index.html', 'w').write(page(f'{f["title"]} · Published Features · Artists for Trauma', art, t['intro']))
    cards.append((f.get('sort') or f['num'], f'<a class="pfc" href="/published-features/{f["slug"]}/"><div class="ph"><img src="/published-features/{f["slug"]}/pages/p{f["thumb"]:03d}.jpg" alt="" loading="lazy"></div><small>{ISSUE["pub"]} · {ISSUE["issue"]} · {ISSUE["date"]}</small><b>{html.escape(f["title"])}</b><small>{html.escape(f["people"])}</small></a>'))
idx = f'''<section class="band"><div class="wrap"><h1><span>Published</span> Features</h1>
<p>Stories about Artists for Trauma, our Fellow Travelers and collaborators, as published in AwareNow magazine from 2021, including Laura Sharpe’s column ‘Fellow Travelers’.</p></div></section>
<div class="wrap"><div class="pfl">{''.join(c for _, c in sorted(cards, key=lambda x: -x[0]))}</div></div>'''
open(f'{base}/index.html', 'w').write(page('Published Features · Artists for Trauma', idx, 'Stories about Artists for Trauma published in AwareNow and other magazines.'))
print('built', len(FEATURES), 'features')
