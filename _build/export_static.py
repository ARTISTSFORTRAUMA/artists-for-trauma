import json, re, sys, base64, os, hashlib
src, outdir = sys.argv[1], sys.argv[2]
d = json.load(open('/home/claude/aft/sc/imgs_d.json'))
t = open(src).read()
os.makedirs(outdir + '/images', exist_ok=True)
written = {}
def img(k):
    if k in written: return written[k]
    uri = d[k]; head, b64 = uri.split(',', 1)
    ext = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp', 'image/svg+xml': 'svg', 'image/gif': 'gif'}[head[5:].split(';')[0]]
    p = f'images/{k}.{ext}'
    open(f'{outdir}/{p}', 'wb').write(base64.b64decode(b64))
    written[k] = p; return p
keys = ['photo','film','serve','dance','yoga2','calm','pottery','drawing','writing','music','taichi','more','e2','lfa_fight','lm_tape','ch_young','f_kent'] + re.findall(r"'([fv]_\w+)'\]", t) + re.findall(r"IMG\.(\w+)", t)
t = re.sub(r'\{\{(\w+)\}\}', lambda m: img(m.group(1)), t)
t = t.replace('__IMGS__', json.dumps({k: img(k) for k in dict.fromkeys(keys) if k in d}))
# inline data URIs remaining in the template (logos etc.) -> files
def dat(m):
    uri = m.group(0); head, b64 = uri.split(',', 1); mime = head[5:].split(';')[0]
    ext = {'image/jpeg':'jpg','image/png':'png','image/webp':'webp','image/svg+xml':'svg','image/gif':'gif'}.get(mime)
    if not ext or ';base64' not in head: return uri
    h = hashlib.sha1(b64.encode()).hexdigest()[:10]; p = f'images/asset-{h}.{ext}'
    if not os.path.exists(f'{outdir}/{p}'): open(f'{outdir}/{p}', 'wb').write(base64.b64decode(b64))
    return p
t = re.sub(r'data:image/[a-z+]+;base64,[A-Za-z0-9+/=]+', dat, t)
doc = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n' + t + '\n</html>\n'
open(f'{outdir}/index.html', 'w').write(doc)
print(outdir, len(doc)//1024, 'KB html,', len(os.listdir(outdir + '/images')), 'images')
