"""Build a Template #1 feature article: python3 build_feature.py <source.html> <images.json|img-dir> <slug> <repo>
Photos in the source are {{name}} placeholders. Images are written to /features/<slug>/img/<name>.(jpg|png)."""
import sys, os, re, json, base64, io
from PIL import Image
src, imgs, slug, repo = sys.argv[1:5]
html = open(src).read()
out = f'{repo}/features/{slug}'; os.makedirs(f'{out}/img', exist_ok=True)
names = sorted(set(re.findall(r'\{\{([a-z0-9_]+)\}\}', html)))
data = json.load(open(imgs)) if imgs.endswith('.json') and os.path.exists(imgs) else {}
paths = {}
for n in names:
    have = [f for f in os.listdir(f'{out}/img') if os.path.splitext(f)[0] == n]
    if have: paths[n] = have[0]; continue          # keep an image already placed (e.g. a high-res replacement)
    b = base64.b64decode(data[n].split(',', 1)[1]); im = Image.open(io.BytesIO(b))
    ext = 'png' if im.mode in ('RGBA', 'LA', 'P') else 'jpg'
    open(f'{out}/img/{n}.{ext}', 'wb').write(b); paths[n] = f'{n}.{ext}'
for n in names:
    html = html.replace('{{' + n + '}}', f'/features/{slug}/img/{paths[n]}')
# live-site wiring
if '<html' not in html.lower():  # the template source is a fragment: wrap it as a full page
    title = re.search(r'<title>(.*?)</title>', html).group(1)
    name = title.split(' · ')[0]
    html = re.sub(r'<title>.*?</title>\s*', '', html, count=1)
    html = re.sub(r'<meta name="claude:[^>]*>\s*', '', html)
    i = html.index('<header>')
    html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{name} · Features · Artists for Trauma</title>\n' + html[:i] + '</head>\n<body>\n' + html[i:] + '\n</body>\n</html>\n')
html = html.replace('<link rel="preconnect" href="https://fonts.googleapis.com">', '<link rel="stylesheet" href="https://use.typekit.net/scq8iav.css">\n<link rel="preconnect" href="https://fonts.googleapis.com">', 1)
nav = {'Home': '/', 'Programs': '/#programs', 'Features': '/#features', 'Videos': '/#videos', 'About': '/#about', 'Events': '/#events'}
for k, v in nav.items():
    html = re.sub(rf'<a class="n( on)?" href="#top">{k}</a>', lambda m, v=v, k=k: f'<a class="n{m.group(1) or ""}" href="{v}">{k}</a>', html)
html = html.replace('href="#top">See all features', 'href="/#features">See all features')
html = html.replace('<a href="#top" aria-label="Artists for Trauma home">', '<a href="/" aria-label="Artists for Trauma home">')
html = html.replace('<a href="#top">Home</a> / <a href="#top">Features</a>', '<a href="/">Home</a> / <a href="/#features">Features</a>')
html = re.sub(r'<a class="btn" href="#top"', '<a class="btn" href="https://www.zeffy.com/"', html)
more = {'Ford Austin': 'ford-austin', 'Chelsie Hill': 'chelsie-hill', 'Onofre Banderas': 'onofre-banderas', 'Aaron Baker': 'aaron-baker', 'Lilian Raven': 'lilian-raven', 'Fiona Dowdee': 'fiona-dowdee', 'Risky': 'risky', 'Dr. Thomas K. Duncan': 'thomas-duncan'}
for n, s in more.items():
    html = html.replace(f'<a href="#top" aria-label="{n}">', f'<a href="/#feature-{s}" aria-label="{n}">')
html = html.replace('<img src="/features/', '<img loading="lazy" src="/features/').replace('<img loading="lazy" src="/features/' + slug + '/img/' + paths.get('hero', 'x'), '<img src="/features/' + slug + '/img/' + paths.get('hero', 'x'), 1)
html = html.replace('</body>', '<script src="/features/tune.js" defer></script>\n</body>', 1) if 'tune.js' not in html else html
open(f'{out}/index.html', 'w').write(html)
print('built', f'/features/{slug}/', len(names), 'images')
