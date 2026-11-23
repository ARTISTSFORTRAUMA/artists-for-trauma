"""Apply pasted Tune-panel settings (opening box + photos) to a feature source file.
Usage: python3 apply_settings.py <source.html> <settings.txt>
Text-block moves are applied by hand (they are matched by their opening words)."""
import re, sys
src, txt = sys.argv[1], open(sys.argv[2]).read()
s = open(src).read()
VARS = {'Space above profile line':'--gap-top','Space under profile line':'--gap-eyebrow','Name size':'--name-size',
        'Name line spacing':'--name-lh','Name letter spacing':'--name-ls','Space under name':'--gap-name',
        'Title size':'--deck-size','Title line spacing':'--deck-lh','Space between title lines':'--deck-gap','Space above credits':'--gap-deck'}
for label, var in VARS.items():
    m = re.search(r'^' + re.escape(label) + r': (\S+)', txt, re.M)
    if m and var + ':' in s:
        s = re.sub(re.escape(var) + r':[^;}]+', var + ':' + m.group(1), s, count=1)
for m in re.finditer(r'Photo (\w+)\.\w+: zoom ([\d.]+), left/right ([\d.]+)%, up/down ([\d.]+)%(?:, move up/down (-?\d+)px)?(?:, move left/right (-?\d+)px)?', txt):
    k, z, x, y = m.group(1), m.group(2), m.group(3), m.group(4)
    my, mx = int(m.group(5) or 0), int(m.group(6) or 0)
    t = (f'translate({mx}px, {my}px) ' if (mx or my) else '') + f'scale({z})'
    im = re.search(r'<img src="\{\{' + k + r'\}\}"[^>]*?>', s)
    if not im: print('not found', k); continue
    tag = im.group(0)
    st = re.search(r' style="([^"]*)"', tag)
    keep = ';'.join(p for p in (st.group(1).split(';') if st else []) if p and not p.strip().startswith(('object-position','transform-origin','transform')))
    tag = re.sub(r' style="[^"]*"', '', tag)[:-1] + f' style="{keep + ";" if keep else ""}object-position:{x}% {y}%;transform-origin:{x}% {y}%;transform:{t}">'
    s = s[:im.start()] + tag + s[im.end():]
    print('photo', k, t)
open(src, 'w').write(s)
