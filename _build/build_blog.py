"""Build the Artists for Trauma blog archive from the old WordPress export.

Input:  /home/claude/blogsrc/json/*.json and /home/claude/blogsrc/media/ (downloaded originals)
Output: <site>/blog/index.html, <site>/YYYY/MM/<slug>/index.html (same paths as the old site),
        <site>/blog/media/... (web-sized copies of every photo the posts use)
"""
import json, glob, re, os, sys, html, shutil, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import nav as NAVMOD
NAV = NAVMOD.nav_html()
from bs4 import BeautifulSoup, Comment, Doctype
from PIL import Image, ImageOps

SRC = '/home/claude/blogsrc'
SITE = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/artists-for-trauma'
OLD = 'artistsfortrauma.org'

posts = sum((json.load(open(f)) for f in sorted(glob.glob(f'{SRC}/json/posts-*.json'))), [])
posts.sort(key=lambda p: p['date'], reverse=True)
cats = {c['id']: html.unescape(c['name']) for c in json.load(open(f'{SRC}/json/categories.json'))}
# merge the two near-duplicate event categories
cats = {k: ('Events' if v == 'Event' else v) for k, v in cats.items()}

def local_src(u):
    """Downloaded file for a URL, or None."""
    u = urllib.parse.urljoin(f'https://{OLD}/', u.split('?')[0])
    pth = urllib.parse.urlparse(u).path
    rel = urllib.parse.unquote(pth.split('/wp-content/uploads/')[-1]) if '/wp-content/uploads/' in pth else None
    if not rel: return None
    orig = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', rel)
    for cand in (orig, rel):
        if os.path.isfile(f'{SRC}/media/{cand}'): return cand
    return None

done = {}
def publish_media(rel):
    """Copy a downloaded file into the site at web size; return its site path."""
    if rel in done: return done[rel]
    src = f'{SRC}/media/{rel}'
    ext = rel.rsplit('.', 1)[-1].lower()
    out_rel = rel
    if ext in ('png',) and os.path.getsize(src) > 600_000:
        out_rel = rel.rsplit('.', 1)[0] + '.jpg'
    dst = f'{SITE}/blog/media/{out_rel}'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if ext in ('jpg', 'jpeg', 'png', 'webp') and not os.path.exists(dst):
        try:
            im = Image.open(src); im = ImageOps.exif_transpose(im)
            im.thumbnail((1600, 1600), Image.LANCZOS)
            if out_rel.lower().endswith(('.jpg', '.jpeg')):
                if im.mode in ('RGBA', 'LA', 'P'):
                    bg = Image.new('RGB', im.size, 'white'); im = im.convert('RGBA'); bg.paste(im, mask=im.split()[-1]); im = bg
                im.convert('RGB').save(dst, 'JPEG', quality=82, optimize=True, progressive=True)
            else:
                im.save(dst, optimize=True)
        except Exception:
            shutil.copyfile(src, dst)
    elif not os.path.exists(dst):
        shutil.copyfile(src, dst)
    done[rel] = '/blog/media/' + urllib.parse.quote(out_rel)
    return done[rel]

KEEP = {'a': ['href'], 'img': ['src', 'alt'], 'iframe': ['src', 'title', 'allowfullscreen'], 'video': ['controls', 'src'], 'source': ['src', 'type'], 'td': ['colspan'], 'th': ['colspan']}
DROP = {'script', 'style', 'noscript', 'form', 'input', 'button', 'head', 'meta', 'link', 'title'}
UNWRAP = {'html', 'body', 'span', 'font', 'center', 'o:p', 'section', 'article'}

def clean(content):
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.I)
    content = re.sub(r'\[/?[a-z_]+[^\]]*\]', '', content)  # leftover WordPress shortcodes
    s = BeautifulSoup(content, 'html.parser')
    for c in s.find_all(string=lambda t: isinstance(t, (Comment, Doctype))): c.extract()
    for t in s.find_all(list(DROP)): t.decompose()
    for t in s.find_all(list(UNWRAP)): t.unwrap()
    for t in s.find_all(True):
        keep = KEEP.get(t.name, [])
        t.attrs = {k: v for k, v in t.attrs.items() if k in keep}
    imgs = 0
    for img in s.find_all('img'):
        rel = local_src(img.get('src', ''))
        if not rel: img.decompose(); continue
        img['src'] = publish_media(rel); img['loading'] = 'lazy'; imgs += 1
        par = img.parent
        if par and par.name == 'a':  # links that just open the same image
            href = par.get('href', '')
            if local_src(href) or re.search(r'\.(jpe?g|png|gif)$', href, re.I): par.unwrap()
    for a in s.find_all('a'):
        href = a.get('href', '')
        rel = local_src(href)
        if rel: a['href'] = publish_media(rel); continue
        u = urllib.parse.urlparse(href)
        if u.netloc.replace('www.', '') == OLD and re.match(r'^/\d{4}/\d{2}/', u.path):
            a['href'] = u.path  # internal post link stays on the new site
        elif u.netloc and u.netloc.replace('www.', '') != OLD:
            a['target'] = '_blank'; a['rel'] = 'noopener'
    for f in s.find_all('iframe'):
        src = f.get('src', '').replace('http://', 'https://')
        if not re.search(r'(youtube|vimeo|facebook|google)\.', src): f.decompose(); continue
        f['src'] = src; f['allowfullscreen'] = ''; f['title'] = f.get('title') or 'Video'
        w = s.new_tag('div', attrs={'class': 'embed'}); f.wrap(w)
    for b in s.find_all('br'):  # collapse runs of <br>
        while b.next_sibling and getattr(b.next_sibling, 'name', None) == 'br': b.next_sibling.decompose()
    for t in s.find_all(['p', 'div', 'strong', 'b', 'em', 'i', 'h1', 'h2', 'h4', 'blockquote', 'li']):
        if not t.get_text(strip=True) and not t.find(['img', 'iframe', 'video']): t.decompose()
    for bq in s.find_all('blockquote'):
        if bq.find(['img','iframe']) or len(bq.find_all(['p','div'])) > 2: bq.unwrap()
    for h in s.find_all('h1'): h.name = 'h2'
    for d in s.find_all('div'):
        if d.get('class') != ['embed']: d.name = 'p' if not d.find(['p', 'div', 'ul', 'ol', 'blockquote', 'iframe', 'img']) else 'div'
    out = str(s)
    out = re.sub(r'(\s*<br/?>\s*)+(</p>)', r'\2', out)
    out = re.sub(r'(<p>)(\s*<br/?>\s*)+', r'\1', out)
    out = re.sub(r'\n{3,}', '\n\n', out)
    return out.strip(), imgs

def text(h): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()

FONT = '<link rel="stylesheet" href="https://use.typekit.net/scq8iav.css"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&display=swap">'
CSS = '''
:root{--pink:#f567af;--pink-ink:#c93683;--grad:linear-gradient(115deg,#ffeb68 0%,#fed438 42%,#f3a538 100%);--fg:#000;--mute:#555;--line:#d9d9d9;--head:"gotham-condensed","Barlow Condensed","Arial Narrow",sans-serif}
*{box-sizing:border-box}html{font-size:18px}body{margin:0;background:#fff;color:var(--fg);font-family:var(--head);font-weight:500;font-size:22px;line-height:1.2}
a{color:inherit}img{max-width:100%;height:auto;display:block}
.wrap{max-width:1240px;margin:0 auto;padding:0 20px}
.top{border-bottom:1px solid var(--line);background:#fff;position:sticky;top:0;z-index:5}
.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-block:12px}
.top nav.main a.n{font-size:1.05rem}
.top img{height:44px;width:auto}
.top nav{display:flex;gap:20px;align-items:center;flex-wrap:nowrap;white-space:nowrap}
.top nav a{text-decoration:none;font-weight:600;font-size:1.05rem}.top nav a:hover{color:var(--pink-ink)}
.top nav a.on{color:var(--pink-ink);box-shadow:inset 0 -3px 0 currentColor}
.btn{display:inline-flex;align-items:center;padding:10px 18px;background:var(--grad);color:#000;text-decoration:none;font-weight:700;border-radius:2px}
.band{background:var(--grad)}.band .wrap{padding-block:clamp(28px,4vw,48px)}
.band h1{margin:0;font-size:clamp(2.6rem,6vw,5rem);line-height:.9;font-weight:700}.band h1 span{color:var(--pink)}
.band p{margin:12px 0 0;font-size:1.25rem;max-width:62ch}
.tools{display:grid;gap:14px;padding-block:28px 8px}
.tools input{font:inherit;font-size:1.1rem;padding:12px 14px;border:1px solid #000;border-radius:2px;width:100%;max-width:520px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chips button{font:700 1rem var(--head);padding:8px 12px;border:0;border-radius:2px;background:#f3f3ee;cursor:pointer}
.chips button[aria-pressed=true]{background:#000;color:#fff}
.count{color:var(--mute);font-size:1rem}
.yr{display:grid;grid-template-columns:120px 1fr;gap:20px;border-top:4px solid #000;padding-top:16px;margin-top:36px}
.yr>h2{margin:0;font-size:2.6rem;line-height:.9;color:var(--pink-ink)}
.list{display:grid;gap:0}
.item{display:grid;grid-template-columns:150px 1fr;gap:18px;padding:16px 0;border-bottom:1px solid var(--line);text-decoration:none}
.item:first-child{padding-top:0}
.item .th{aspect-ratio:4/3;background:#f3f3ee;overflow:hidden;border-radius:2px}
.item .th img{width:100%;height:100%;object-fit:cover;object-position:50% 25%}
.item .th.none{background:var(--grad)}
.item small{display:block;color:var(--mute);font-size:.95rem;font-weight:600;letter-spacing:.02em}
.item b{display:block;font-size:1.45rem;line-height:1;margin:4px 0 6px}
.item:hover b{color:var(--pink-ink)}
.item p{margin:0;font-size:1.05rem;color:#333}
.empty{padding:40px 0;color:var(--mute)}
footer{margin-top:72px;background:var(--grad);padding-block:36px}footer .wrap{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-size:1rem}
@media (max-width:760px){.yr{grid-template-columns:1fr;gap:10px}.yr>h2{font-size:2rem}.item{grid-template-columns:96px 1fr;gap:12px}.item b{font-size:1.2rem}.item p{display:none}.top img{height:28px}.top nav{gap:12px}.top .btn{padding:8px 12px;font-size:.95rem}.top .wrap{gap:10px}.top nav .hide{display:none}}
/* post */
.post{max-width:760px;margin:0 auto;padding:36px 20px 0}
.crumb{font-weight:600;font-size:1rem;text-decoration:none}.crumb:hover{color:var(--pink-ink)}
.post h1{font-size:clamp(2.4rem,5vw,3.8rem);line-height:.92;margin:18px 0 10px;font-weight:700}
.meta{color:var(--mute);font-size:1.05rem;font-weight:600;display:flex;gap:10px;flex-wrap:wrap;border-bottom:4px solid var(--pink);padding-bottom:14px;margin-bottom:26px}
.meta a{text-decoration:none;color:var(--pink-ink)}
.body{font-size:24px;line-height:1.15}
.body p,.body ul,.body ol,.body blockquote{margin:0 0 20px}
.body h2,.body h3,.body h4{font-size:1.6rem;line-height:1;margin:30px 0 12px;font-weight:700}
.body img{margin:24px auto;border-radius:2px}
.body blockquote{border-left:4px solid #000;padding-left:18px;font-weight:600}
.body a{color:var(--pink-ink)}
.body .embed{position:relative;aspect-ratio:16/9;margin:24px 0}.body .embed iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.body video{width:100%}
.pn{display:grid;grid-template-columns:1fr 1fr;gap:20px;border-top:1px solid var(--line);margin-top:40px;padding-top:18px}
.pn a{text-decoration:none;font-weight:700;font-size:1.15rem;line-height:1}.pn a:hover{color:var(--pink-ink)}
.pn small{display:block;color:var(--mute);font-weight:600;font-size:.9rem;margin-bottom:4px}
.pn .nx{text-align:right}
.note{margin-top:28px;font-size:1rem;color:var(--mute)}
'''

def page(title, body, desc=''):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc[:160])}">
{FONT}<link rel="stylesheet" href="/blog/blog.css"></head><body>
<header class="top"><div class="wrap"><a href="/" aria-label="Artists for Trauma home"><img src="/images/art_full.png" alt="Artists for Trauma"></a>
<nav class="main" aria-label="Main">{NAV}</nav></div></header>
{body}
<footer><div class="wrap"><span>© Artists for Trauma · Powered by human spirit™</span><a href="/">artistsfortrauma.org</a></div></footer>
{NAVMOD.JS}</body></html>
'''

items = []
os.makedirs(f'{SITE}/blog', exist_ok=True)
open(f'{SITE}/blog/blog.css', 'w').write(CSS + NAVMOD.CSS)
missing_imgs = 0
for i, p in enumerate(posts):
    title = html.unescape(p['title']['rendered']).strip() or 'Untitled'
    path = urllib.parse.unquote(urllib.parse.urlparse(p['link']).path)  # /2012/07/lauras-message/
    body, nimg = clean(p['content']['rendered'])
    date = p['date'][:10]
    y, m, d = date.split('-')
    nice = f"{['January','February','March','April','May','June','July','August','September','October','November','December'][int(m)-1]} {int(d)}, {y}"
    pc = sorted({cats.get(c, '') for c in p['categories']} - {'', 'Uncategorized'})
    thumb = None
    fm = (p.get('_embedded') or {}).get('wp:featuredmedia') or []
    if fm and isinstance(fm[0], dict) and fm[0].get('source_url'):
        rel = local_src(fm[0]['source_url']); thumb = publish_media(rel) if rel else None
    if not thumb:
        mm = re.search(r'<img[^>]+src="([^"]+)"', body); thumb = mm.group(1) if mm else None
    excerpt = text(body)[:220]
    items.append({'t': title, 'u': path, 'd': date, 'n': nice, 'c': pc, 'i': thumb, 'x': excerpt})
newer = {}; older = {}
for i, it in enumerate(items):
    newer[it['u']] = items[i-1] if i > 0 else None
    older[it['u']] = items[i+1] if i + 1 < len(items) else None
for p, it in zip(posts, items):
    body, _ = clean(p['content']['rendered'])
    catlinks = ' · '.join(f'<a href="/blog/?c={urllib.parse.quote(c)}">{html.escape(c)}</a>' for c in it['c'])
    nw, od = newer[it['u']], older[it['u']]
    pn = '<nav class="pn">' + (f'<a href="{od["u"]}"><small>← Older</small>{html.escape(od["t"])}</a>' if od else '<span></span>') + (f'<a class="nx" href="{nw["u"]}"><small>Newer →</small>{html.escape(nw["t"])}</a>' if nw else '<span></span>') + '</nav>'
    art = f'''<main class="post"><a class="crumb" href="/blog/">← Blog archive</a>
<h1>{html.escape(it["t"])}</h1><div class="meta"><time datetime="{it["d"]}">{it["n"]}</time>{(' · ' + catlinks) if catlinks else ''}</div>
<div class="body">{body}</div>{pn}</main>'''
    out = f'{SITE}{it["u"]}index.html'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write(page(f'{it["t"]} · Artists for Trauma', art, it['x']))

allcats = sorted({c for it in items for c in it['c']}, key=lambda c: -sum(c in it['c'] for it in items))
first, last = items[-1]['d'][:4], items[0]['d'][:4]
idx = f'''<section class="band"><div class="wrap"><h1><span>Blog</span> archive</h1>
<p>{len(items)} posts from {first} to {last}: events, workshops, news and stories from the Artists for Trauma community.</p></div></section>
<div class="wrap"><div class="tools"><input id="q" type="search" placeholder="Search the archive" aria-label="Search the archive">
<div class="chips" id="chips"><button aria-pressed="true" data-c="">All</button>{''.join(f'<button aria-pressed="false" data-c="{html.escape(c)}">{html.escape(c)}</button>' for c in allcats)}</div>
<div class="count" id="count"></div></div><div id="out"></div></div>
<script>
const P={json.dumps(items)};
const out=document.getElementById('out'),q=document.getElementById('q'),cnt=document.getElementById('count'),chips=[...document.querySelectorAll('#chips button')];
let cat=new URLSearchParams(location.search).get('c')||'';
const esc=s=>s.replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[c]);
function draw(){{const t=q.value.trim().toLowerCase();chips.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.c===cat)));
const L=P.filter(p=>(!cat||p.c.includes(cat))&&(!t||(p.t+' '+p.x).toLowerCase().includes(t)));
cnt.textContent=L.length+(L.length===1?' post':' posts');
const by={{}};L.forEach(p=>(by[p.d.slice(0,4)]=by[p.d.slice(0,4)]||[]).push(p));
out.innerHTML=Object.keys(by).sort().reverse().map(y=>'<section class="yr"><h2>'+y+'</h2><div class="list">'+by[y].map(p=>'<a class="item" href="'+encodeURI(p.u)+'"><div class="th'+(p.i?'':' none')+'">'+(p.i?'<img loading="lazy" src="'+p.i+'" alt="">':'')+'</div><div><small>'+p.n+(p.c.length?' · '+esc(p.c.join(', ')):'')+'</small><b>'+esc(p.t)+'</b><p>'+esc(p.x.slice(0,180))+(p.x.length>180?'…':'')+'</p></div></a>').join('')+'</div></section>').join('')||'<p class="empty">No posts match.</p>';}}
chips.forEach(b=>b.onclick=()=>{{cat=b.dataset.c;history.replaceState(null,'',cat?'?c='+encodeURIComponent(cat):location.pathname);draw()}});
q.oninput=draw;draw();
</script>'''
open(f'{SITE}/blog/index.html', 'w').write(page('Blog archive · Artists for Trauma', idx, f'{len(items)} posts from the Artists for Trauma blog, {first} to {last}.'))
print(len(items), 'posts;', len(done), 'media files;', 'categories:', allcats)
