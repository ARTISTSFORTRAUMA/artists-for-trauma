"""Shared main menu for the Artists for Trauma site, laid out like the old artistsfortrauma.org menu."""

MENU = [
    ('Home', '/', None),
    ('About', '/about/', [('About', '/about/'), ("Laura's Story", '/lauras-story/'), ('Team', '/team/')]),
    ('Features', '/#features', None),
    ('Partners', '/partners/', None),
    ('Press/Media', '/published-features/', [('Published Features', '/published-features/'), ('LYB 2021', '/lyb-2021/'), ('Videos', '/videos/'), ('Media/Press', '/mediapress/')]),
    ('Get Involved', '/become-a-student-artist/', [('Become a Student Artist', '/become-a-student-artist/'), ('Become a Volunteer', '/become-a-volunteer-artist/'),
                       ('Events', '/calendar/'), ('Blogs', '/blog/'), ('Workshops', '/workshops/')]),
    ('Contact', '/contact/', None),
    ('Digital Flyers', '/digital-flyers-for-our-events/', None),
    ('Athletes for Trauma', 'https://athletes-for-trauma.netlify.app/', None),
]

def nav_html(home_prefix=''):
    """home_prefix: '' on inner pages; on the homepage '/#x' links become '#x'."""
    out = []
    for i, (label, href, kids) in enumerate(MENU):
        h = href[1:] if (home_prefix == 'home' and href.startswith('/#')) else href
        if home_prefix == 'home' and href == '/': h = '#top'
        if kids:
            items = ''.join(f'<a href="{k}">{t}</a>' for t, k in kids)
            out.append(f'<div class="dd"><a class="n" href="{h}" aria-haspopup="true">{label}<i aria-hidden="true">▾</i></a><div class="ddm">{items}</div></div>')
        else:
            out.append(f'<a class="n" href="{h}">{label}</a>')
    give = '#give' if home_prefix == 'home' else '/#give'
    return ('<button class="menubtn" aria-expanded="false" aria-controls="mainmenu">Menu</button>'
            '<div class="menu" id="mainmenu">' + ''.join(out) + '</div>'
            f'<a class="btn" href="{give}">Give with Zeffy</a>')

CSS = '''
/* main menu, old-site layout */
nav.main{display:flex;align-items:center;gap:14px}
nav.main .menu{display:flex;align-items:center;gap:clamp(12px,1.3vw,20px)}
nav.main a.n{display:inline-flex !important;align-items:center;gap:4px;text-decoration:none;font-family:var(--head);font-weight:600;font-size:1.12rem;white-space:nowrap;color:inherit}
nav.main a.n i{font-style:normal;font-size:.7em;opacity:.7}
nav.main a.n:hover,nav.main .dd:hover>a.n{color:var(--pink-ink)}
nav.main .dd{position:relative}
nav.main .ddm{display:none;position:absolute;top:100%;left:-12px;min-width:230px;background:#fff;border:1px solid #d9d9d9;border-top:3px solid var(--pink);box-shadow:0 10px 24px rgba(0,0,0,.12);padding:6px 0;z-index:50}
nav.main .dd:hover .ddm,nav.main .dd:focus-within .ddm{display:block}
nav.main .ddm a{display:block;padding:9px 16px;text-decoration:none;font-family:var(--head);font-weight:600;font-size:1.05rem;color:#000;white-space:nowrap}
nav.main .ddm a:hover{background:#f3f3ee;color:var(--pink-ink)}
nav.main .menubtn{display:none;font:700 1.05rem var(--head);padding:9px 14px;border:2px solid #000;background:#fff;border-radius:2px;cursor:pointer}
@media (max-width:1180px){
  nav.main .menubtn{display:inline-flex}
  nav.main .menu{display:none;position:absolute;left:0;right:0;top:100%;background:#fff;border-top:1px solid #d9d9d9;box-shadow:0 14px 28px rgba(0,0,0,.14);flex-direction:column;align-items:stretch;gap:0;padding:8px 20px 18px;max-height:80vh;overflow:auto;z-index:60}
  nav.main.open .menu{display:flex}
  nav.main .menu a.n{padding:12px 0;border-bottom:1px solid #eee;font-size:1.25rem;box-shadow:none !important}
  nav.main .dd{border-bottom:1px solid #eee}nav.main .dd>a.n{border-bottom:0;width:100%}
  nav.main .dd .ddm{display:block;position:static;border:0;box-shadow:none;padding:0 0 8px 14px;min-width:0}
  nav.main .dd .ddm a{padding:8px 0;font-size:1.1rem;color:#444}
  nav.main a.n i{display:none}
}
'''

JS = '''<script>(function(){var n=document.querySelector('nav.main'),b=n&&n.querySelector('.menubtn');if(!b)return;
b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o);b.textContent=o?'Close':'Menu'});
n.querySelectorAll('.menu a').forEach(function(a){a.addEventListener('click',function(){n.classList.remove('open');b.setAttribute('aria-expanded','false');b.textContent='Menu'})});})();</script>'''
