"""Convert the old artistsfortrauma.org pages + calendar events into the new design.

python3 build_pages.py urls            -> writes /home/claude/pagesrc/image-urls.txt (images to download)
python3 build_pages.py build <site>    -> writes pages at their old paths, /calendar/<slug>/, and /site-archive/
"""
import json, glob, re, os, sys, html, shutil, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import nav as NAVMOD
NAV = NAVMOD.nav_html()
from bs4 import BeautifulSoup, Comment
from PIL import Image, ImageOps

SRC = '/home/claude/pagesrc'
OLD = 'artistsfortrauma.org'
MODE = sys.argv[1]
SITE = sys.argv[2] if len(sys.argv) > 2 else '/home/claude/artists-for-trauma'

pages = sum((json.load(open(f)) for f in sorted(glob.glob(f'{SRC}/json/pages-*.json'))), [])
events = json.load(open(f'{SRC}/json/events.json'))['events']

SKIP_PATHS = {'/past-events/'}            # old "Blogs" page -> /blog/ (redirect)
RENAME = {'/': '/old-home/'}              # old homepage kept for reference
BOILER = (r'^@artistsfortrauma on Instagram', r'^Testimonials\s*“Seeing this transformative')

def path_of(link):
    p = urllib.parse.unquote(urllib.parse.urlparse(link).path) or '/'
    if not p.endswith('/'): p += '/'
    return RENAME.get(p, p)

def img_src(t):
    for k in ('data-src', 'data-lazy-src', 'data-original', 'src'):
        v = t.get(k)
        if v and not v.startswith('data:'): return v
    return None

def norm(u):
    return urllib.parse.urljoin(f'https://{OLD}/', u.split('?')[0])

def clean(node, collect=None):
    for t in node.find_all(['script', 'style', 'noscript', 'form', 'input', 'button', 'select', 'textarea', 'iframe', 'svg']):
        if t.name == 'iframe' and re.search(r'(youtube|vimeo)\.', t.get('src', '') or t.get('data-src', '')):
            continue
        t.decompose()
    for c in node.find_all(string=lambda x: isinstance(x, Comment)): c.extract()
    for sel in ['#sb_instagram', '.sbi', '.sb_instagram_header', '.q_slider', '.rev_slider_wrapper', '.title_outer', '.ftg-filters', '.loading-bar']:
        for t in node.select(sel): t.decompose()
    for row in node.select('.vc_row, .wpb_row'):
        if not row.parent: continue
        txt = re.sub(r'\s+', ' ', row.get_text(' ', strip=True))
        if any(re.search(b, txt) for b in BOILER): row.decompose()
    # images
    for im in node.find_all('img'):
        u = img_src(im)
        if not u or '/plugins/' in u or 'AFT-banner2-background' in u or 'placeholder' in u:
            im.decompose(); continue
        u = norm(u)
        if collect is not None: collect.add(u); collect.add(re.sub(r'-\d+x\d+(\.\w+)$', r'\1', u))
        im.attrs = {'src': u, 'alt': im.get('alt', '')}
    for t in node.find_all(True):
        if t.name == 'img': continue
        keep = {'a': ['href'], 'iframe': ['src', 'data-src']}.get(t.name, [])
        t.attrs = {k: v for k, v in t.attrs.items() if k in keep}
    return node

# ---------- media ----------
MEDIA = f'{SRC}/media'
def local(u):
    pth = urllib.parse.urlparse(u).path
    if '/wp-content/uploads/' not in pth: return None
    rel = urllib.parse.unquote(pth.split('/wp-content/uploads/')[-1])
    orig = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', rel)
    for cand in (orig, rel):
        for base in (MEDIA, '/home/claude/blogsrc/media'):
            if os.path.isfile(f'{base}/{cand}'): return f'{base}/{cand}', cand
    return None

MK = BeautifulSoup('', 'html.parser')
done = {}
def publish(u):
    l = local(u)
    if not l: return None
    src, rel = l
    if rel in done: return done[rel]
    out_rel = rel
    if rel.lower().endswith('.png') and os.path.getsize(src) > 600_000: out_rel = rel[:-4] + '.jpg'
    dst = f'{SITE}/media/{out_rel}'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst):
        try:
            im = ImageOps.exif_transpose(Image.open(src)); im.thumbnail((1600, 1600), Image.LANCZOS)
            if out_rel.lower().endswith(('.jpg', '.jpeg')):
                if im.mode in ('RGBA', 'LA', 'P'):
                    im = im.convert('RGBA'); bg = Image.new('RGB', im.size, 'white'); bg.paste(im, mask=im.split()[-1]); im = bg
                im.convert('RGB').save(dst, 'JPEG', quality=82, optimize=True, progressive=True)
            else: im.save(dst, optimize=True)
        except Exception: shutil.copyfile(src, dst)
    done[rel] = '/media/' + urllib.parse.quote(out_rel); return done[rel]

page_paths = {path_of(p['link']) for p in pages}
def finish(node):
    for im in node.find_all('img'):
        s = publish(im['src'])
        if not s: im.decompose(); continue
        im['src'] = s; im['loading'] = 'lazy'
        pa = im.find_parent('a')
        if pa and re.search(r'\.(jpe?g|png|gif)$', pa.get('href', ''), re.I): pa.unwrap()
    for a in node.find_all('a'):
        h = a.get('href', '')
        u = urllib.parse.urlparse(h)
        if u.netloc.replace('www.', '') == OLD:
            p = urllib.parse.unquote(u.path) or '/'
            if '/wp-content/uploads/' in p:
                s = publish(norm(h)); a['href'] = s or h; continue
            if not p.endswith('/'): p += '/'
            a['href'] = {'/past-events/': '/blog/', '/': '/'}.get(p, RENAME.get(p, p)) + (('#' + u.fragment) if u.fragment else '')
        elif u.netloc:
            a['target'] = '_blank'; a['rel'] = 'noopener'
    for f in node.find_all('iframe'):
        src = (f.get('src') or f.get('data-src') or '').replace('http://', 'https://')
        if src.startswith('//'): src = 'https:' + src
        f.attrs = {'src': src, 'allowfullscreen': '', 'title': 'Video', 'loading': 'lazy'}
        w = MK.new_tag('div', attrs={'class': 'embed'})
        if w is not None: f.wrap(w)
    # logos that link to partner pages -> compact tiles
    for im in node.find_all('img'):
        a = im.find_parent('a')
        if a and not a.get('href', '').startswith('/media/') and len(a.get_text(strip=True)) < 3:
            a['class'] = 'logo'
    # flatten page-builder wrappers
    for t in node.find_all(['div', 'section', 'span', 'font', 'center']):
        if t.get('class') in (['embed'], ['logos']) or t is node: continue
        t.unwrap()
    for t in node.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'strong', 'b', 'em', 'a', 'ul']):
        if not t.get_text(strip=True) and not t.find(['img', 'iframe']): t.decompose()
    for h in node.find_all('h1'): h.name = 'h2'
    for h in node.find_all(['h5', 'h6']): h.name = 'h4'
    out = node.decode_contents() if node.name not in (None, '[document]') else str(node)
    out = re.sub(r'\n\s*\n+', '\n', out)
    out = re.sub(r'((?:<a class="logo"[^>]*>\s*<img[^>]*/?>\s*</a>\s*){2,})', lambda m: '<div class="logos">' + m.group(1) + '</div>', out)
    out = re.sub(r'(<br/?>\s*){2,}', '<br/>', out)
    return out

def text(h): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()

if MODE == 'urls':
    urls = set()
    for f in glob.glob(f'{SRC}/html/*.html'):
        s = BeautifulSoup(open(f).read(), 'html.parser'); c = s.select_one('.content')
        if c: clean(c, urls)
    for e in events:
        if e.get('image') and e['image'].get('url'): urls.add(e['image']['url'])
        s = BeautifulSoup(e.get('description') or '', 'html.parser'); clean(s, urls)
    urls = {u for u in urls if '/wp-content/uploads/' in u}
    open(f'{SRC}/image-urls.txt', 'w').write('\n'.join(sorted(urls)))
    print(len(urls), 'image urls')
    sys.exit()

# ---------- build ----------
sys.path.insert(0, '/home/claude/aft/tools')
CSS_EXTRA = '''
.post.wide{max-width:900px}
.body .gal{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin:20px 0}
.body .gal img{margin:0;aspect-ratio:1;object-fit:cover;width:100%}
.archnote{background:#f3f3ee;padding:12px 16px;font-size:1rem;color:#444;margin-bottom:24px;border-left:4px solid var(--pink)}
.arch table{width:100%;border-collapse:collapse;font-size:1.05rem}
.arch th,.arch td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line);vertical-align:top}
.arch th{font-size:.9rem;text-transform:uppercase;letter-spacing:.06em;color:var(--mute)}
.arch td a{font-weight:700;text-decoration:none}.arch td a:hover{color:var(--pink-ink)}
.arch h2{font-size:2rem;margin:40px 0 8px;border-top:4px solid #000;padding-top:14px}
.arch .k{color:var(--mute);font-size:.95rem}
@media (max-width:760px){.arch th:nth-child(2),.arch td:nth-child(2),.arch th:nth-child(4),.arch td:nth-child(4){display:none}}
.body .logos{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:14px;margin:14px 0 30px}
.body a.logo{display:flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:2px;padding:14px;aspect-ratio:3/2;background:#fff}
.body a.logo:hover{border-color:var(--pink)}
.body a.logo img{margin:0;max-height:100%;width:auto;max-width:100%;object-fit:contain}
'''
FONT = '<link rel="stylesheet" href="https://use.typekit.net/scq8iav.css"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&display=swap">'
def page(title, body, desc='', noindex=False):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc[:160])}">{'<meta name="robots" content="noindex">' if noindex else ''}
{FONT}<link rel="stylesheet" href="/blog/blog.css"><link rel="stylesheet" href="/media/pages.css"></head><body>
<header class="top"><div class="wrap"><a href="/" aria-label="Artists for Trauma home"><img src="/images/art_full.png" alt="Artists for Trauma"></a>
<nav class="main" aria-label="Main">{NAV}</nav></div></header>
{body}
<footer><div class="wrap"><span>© Artists for Trauma · Powered by human spirit™</span><a href="/">artistsfortrauma.org</a></div></footer>
{NAVMOD.JS}</body></html>
'''
os.makedirs(f'{SITE}/media', exist_ok=True)
open(f'{SITE}/media/pages.css', 'w').write(CSS_EXTRA)

KIND = {}  # rough grouping for the review list
partner_kids = set()
rows = []
for p in pages:
    path = path_of(p['link'])
    if path in SKIP_PATHS: continue
    f = f'{SRC}/html/' + ((path.strip('/').replace('/', '__')) if p['link'].rstrip('/') != f'https://{OLD}' else 'home') + '.html'
    if not os.path.exists(f): f = f'{SRC}/html/home.html' if path == '/old-home/' else f
    s = BeautifulSoup(open(f).read(), 'html.parser'); c = s.select_one('.content')
    if not c: continue
    clean(c)
    back = c.find(string=re.compile(r'<<\s*Back to Partners'))
    is_partner = bool(back)
    if back: back.parent.decompose() if back.parent and back.parent.name == 'a' else back.extract()
    body = finish(c)
    title = html.unescape(p['title']['rendered']).strip()
    # drop a leading repeat of the title
    body = re.sub(r'^\s*<h[1-4]>\s*' + re.escape(html.escape(title, quote=False)) + r'\s*</h[1-4]>', '', body)
    words = len(text(body).split())
    nimg = body.count('<img')
    kind = 'Partner pages' if is_partner else ('Old / test pages' if re.search(r'test|old|mpr3|-3/$', path) or path == '/old-home/' else 'Main pages')
    crumb = '<a class="crumb" href="/partners/">← Partners</a>' if is_partner else '<a class="crumb" href="/site-archive/">← All imported pages</a>'
    art = f'''<main class="post wide">{crumb}<h1>{html.escape(title)}</h1>
<div class="archnote">Imported from the old artistsfortrauma.org (page first published {p["date"][:10]}). Under review before launch.</div>
<div class="body">{body}</div></main>'''
    out = f'{SITE}{path}index.html'
    if path == '/' or os.path.exists(out) and path in ('/blog/',): continue
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write(page(f'{title} · Artists for Trauma', art, text(body)[:200], noindex=True))
    rows.append((kind, title, path, p['date'][:10], words, nimg))

# calendar events
for e in events:
    path = path_of(e['url'])
    title = html.unescape(e['title'])
    s = BeautifulSoup(e.get('description') or '', 'html.parser'); clean(s)
    img = ''
    if e.get('image') and e['image'].get('url'):
        pi = publish(norm(e['image']['url']))
        if pi: img = f'<img src="{pi}" alt="" loading="lazy">'
    body = finish(s)
    v = e.get('venue') or {}
    venue = ', '.join(x for x in [v.get('venue'), v.get('city'), v.get('state') or v.get('province')] if x) if isinstance(v, dict) else ''
    when = e['start_date'][:10] + (f" – {e['end_date'][:10]}" if e.get('end_date') and e['end_date'][:10] != e['start_date'][:10] else '')
    art = f'''<main class="post wide"><a class="crumb" href="/site-archive/#events">← Past events</a><h1>{html.escape(title)}</h1>
<div class="meta"><span>{when}</span>{(' · ' + html.escape(venue)) if venue else ''}</div>
<div class="body">{img}{body}</div></main>'''
    out = f'{SITE}{path}index.html'; os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write(page(f'{title} · Artists for Trauma', art, text(body)[:200], noindex=True))
    rows.append(('Calendar events', title, path, e['start_date'][:10], len(text(body).split()), body.count('<img') + (1 if img else 0)))

# events listing (old menu: Get Involved -> Upcoming Events -> /calendar)
ev = sorted([r for r in rows if r[0] == 'Calendar events'], key=lambda r: r[3], reverse=True)
evhtml = ''.join(f'<a class="item" href="{html.escape(r[2])}"><div class="th none"></div><div><small>{r[3]}</small><b>{html.escape(r[1])}</b></div></a>' for r in ev)
ecal = f'''<section class="band"><div class="wrap"><h1><span>Events</span></h1><p>Past Artists for Trauma events from the old calendar, newest first. For recent and upcoming events see the <a href="/blog/?c=Events">Blog</a> and <a href="/digital-flyers-for-our-events/">Digital Flyers</a>.</p></div></section>
<div class="wrap"><div class="list" style="margin-top:28px">{evhtml}</div></div>'''
os.makedirs(f'{SITE}/calendar', exist_ok=True)
open(f'{SITE}/calendar/index.html', 'w').write(page('Events · Artists for Trauma', ecal, 'Past Artists for Trauma events.', noindex=True))

# review list
order = ['Main pages', 'Partner pages', 'Calendar events', 'Old / test pages']
secs = ''
for k in order:
    R = sorted([r for r in rows if r[0] == k], key=lambda r: (r[3] if k == 'Calendar events' else r[1].lower()), reverse=(k == 'Calendar events'))
    if not R: continue
    anchor = 'events' if k == 'Calendar events' else re.sub(r'\W+', '-', k.lower()).strip('-')
    secs += f'<h2 id="{anchor}">{k} <span class="k">({len(R)})</span></h2><table><tr><th>Page</th><th>Address</th><th>{"Event date" if k=="Calendar events" else "First published"}</th><th>Words</th><th>Photos</th></tr>'
    secs += ''.join(f'<tr><td><a href="{html.escape(r[2])}">{html.escape(r[1])}</a></td><td class="k">{html.escape(r[2])}</td><td class="k">{r[3]}</td><td class="k">{r[4]}</td><td class="k">{r[5]}</td></tr>' for r in R) + '</table>'
idx = f'''<section class="band"><div class="wrap"><h1><span>Imported</span> pages</h1>
<p>Every page from the old artistsfortrauma.org, converted to the new design for review. {len(rows)} pages in all. The blog posts are in the <a href="/blog/">Blog archive</a>.</p></div></section>
<div class="wrap arch">{secs}</div>'''
os.makedirs(f'{SITE}/site-archive', exist_ok=True)
open(f'{SITE}/site-archive/index.html', 'w').write(page('Imported pages · Artists for Trauma', idx, noindex=True))
print(len(rows), 'pages written;', len(done), 'media;', {k: sum(r[0] == k for r in rows) for k in order})
