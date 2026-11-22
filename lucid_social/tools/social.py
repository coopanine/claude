"""
social.py - TESTIDE pre-launch social assets: HTML templates in the Lucid brand system, rendered with Chromium.

Brand system (Lucid brand book, Figma "V2 [09.09.2026]"):
  palette  cream #FAF8F6, cobalt #1D46DE, navy #091A68, ink #101431, sand #AD9368, gold #F7B524
  type     Ashcroft (licensed, Peregrin Studio) for display + body, italics for emphasis;
           Mono45 Headline (Adobe Fonts) for small caps labels -> stand-in here: Share Tech Mono (SIL OFL)
  marks    LUCID logo, statue engraving, statue-head line icon (vectors from the brand file), final tube renders

usage: python3 social.py PLAN.json OUT_DIR      (PLAN = the final plan from the strategy workflow)
Fonts are not in the repo (Ashcroft is licensed): point LUCID_FONTS at a folder with Ashcroft-*.woff2 and
share-tech-mono-latin-400-normal.woff2.
"""
import html, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
ASSETS = os.path.join(ROOT, 'assets')
SCRATCH = '/tmp/claude-0/-home-user-claude/86cbe00f-c61a-5cb5-8dc6-e187390f6093/scratchpad'
FONTS = os.environ.get('LUCID_FONTS', os.path.join(SCRATCH, 'brandfonts', 'woff2'))
MONO = os.environ.get('LUCID_MONO', os.path.join(
    SCRATCH, 'fontx', 'mono', 'fontsource-share-tech-mono-5.3.0', 'package', 'files', 'share-tech-mono-latin-400-normal.woff2'))

C = dict(cream='#FAF8F6', cobalt='#1D46DE', navy='#091A68', ink='#101431', sand='#AD9368', gold='#F7B524')
# per background: text, accent (rules, numerals), statue tone, statue opacity
THEME = {
    'cream':  dict(fg=C['navy'],  accent=C['cobalt'], soft=C['sand'],  statue=C['cobalt'], st_op=1.0),
    'cobalt': dict(fg=C['cream'], accent=C['gold'],   soft='#B9C6F4', statue=C['navy'],   st_op=0.55),
    'navy':   dict(fg=C['cream'], accent=C['gold'],   soft='#8E9AC8', statue=C['cobalt'], st_op=0.85),
    'ink':    dict(fg=C['cream'], accent=C['gold'],   soft='#8C8FA8', statue=C['cobalt'], st_op=0.75),
    'sand':   dict(fg=C['ink'],   accent=C['cream'],  soft='#EFE6D6', statue=C['navy'],   st_op=0.35),
}
SIZE = {'feed': (1080, 1350), 'carousel_slide': (1080, 1350), 'story': (1080, 1920), 'avatar': (1080, 1080),
        'highlight': (1080, 1920)}
WEIGHTS = [('ExtraLight', 200), ('Light', 300), ('Regular', 400), ('Medium', 500), ('SemiBold', 600), ('Bold', 700),
           ('Extrabold', 800), ('Black', 900)]
FDA = ('*These statements have not been evaluated by the Food and Drug Administration. '
       'This product is not intended to diagnose, treat, cure, or prevent any disease.')


def _svg(name):
    s = open(os.path.join(ASSETS, 'vector', name)).read()
    return re.sub(r'<svg ', '<svg preserveAspectRatio="xMidYMid meet" ', s, count=1)


def font_css():
    out = []
    for n, w in WEIGHTS:
        out.append(f"@font-face{{font-family:Ashcroft;font-weight:{w};font-style:normal;src:url('file://{FONTS}/Ashcroft-{n}.woff2')}}")
        it = 'Italic' if n == 'Regular' else n + 'Italic'
        out.append(f"@font-face{{font-family:Ashcroft;font-weight:{w};font-style:italic;src:url('file://{FONTS}/Ashcroft-{it}.woff2')}}")
    out.append(f"@font-face{{font-family:Mono;src:url('file://{MONO}')}}")
    return '\n'.join(out)


def rich(s):
    """*word* -> italic; \\n -> line break; escapes the rest; TESTIDE set like the wordmark (SemiBold, tracked)"""
    s = html.escape(s or '')
    s = re.sub(r'\bTESTIDE\b', "<span style='font-weight:600;letter-spacing:.05em'>TESTIDE</span>", s)
    s = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', s)
    s = s.replace('®', "<span class='reg'>®</span>")
    return s.replace('\\n', '<br>').replace('\n', '<br>')


BASE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:%(w)dpx;height:%(h)dpx;overflow:hidden}
body{background:%(bg)s;color:%(fg)s;font-family:Ashcroft,serif;-webkit-font-smoothing:antialiased;position:relative;
     font-feature-settings:"kern" 1,"liga" 1,"lnum" 1}
em{font-style:italic}
.mono{font-family:Mono,monospace;text-transform:uppercase;letter-spacing:.2em;font-size:27px;line-height:1.35}
.grain{position:absolute;inset:0;pointer-events:none;opacity:%(grain).3f;mix-blend-mode:%(blend)s;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 1 0'/></filter><rect width='400' height='400' filter='url(%%23n)'/></svg>")}
.frame{position:absolute;left:%(pad)dpx;right:%(pad)dpx;top:%(top)dpx;bottom:%(bot)dpx;display:flex;flex-direction:column}
.top,.bottom{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;flex:none}
.bottom{align-items:flex-end}
.mid{flex:1;display:flex;flex-direction:column;justify-content:center;min-height:0}
.center{align-items:center;text-align:center}
.h{font-weight:400;line-height:1.0;letter-spacing:-.012em;text-wrap:balance}
.h div,.bal{text-wrap:balance}
.rule{height:2px;background:%(accent)s;width:100%%}
.fit{overflow:hidden}
.reg{font-size:.42em;vertical-align:.95em;margin-left:.04em;letter-spacing:0}
.svgbox svg{width:100%%;height:100%%;display:block}
.statue{position:absolute;color:%(statue)s;opacity:%(st_op).2f}
.fda{font-family:Mono,monospace;font-size:15px;line-height:1.35;letter-spacing:.04em;text-transform:none;opacity:.85}
"""

FIT_JS = """
<script>
document.fonts.ready.then(()=>{
  for (const el of document.querySelectorAll('[data-fit]')) {
    let fs = parseFloat(getComputedStyle(el).fontSize), min = parseFloat(el.dataset.min || 24);
    const box = el.parentElement;
    const over = () => el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1 ||
                       (el.dataset.maxh && el.getBoundingClientRect().height > parseFloat(el.dataset.maxh));
    while (over() && fs > min) { fs -= 2; el.style.fontSize = fs + 'px'; }
  }
  document.body.setAttribute('data-ready', '1');
});
</script>"""


def page(fmt, bg, body, grain=None):
    w, h = SIZE[fmt]
    t = THEME[bg]
    story = fmt in ('story', 'highlight')
    pad = 84
    top, bot = (250, 250) if story else (78, 70)
    if fmt == 'avatar':
        top = bot = 78
    css = BASE_CSS % dict(w=w, h=h, bg=C[bg], fg=t['fg'], accent=t['accent'], statue=t['statue'], st_op=t['st_op'],
                          pad=pad, top=top, bot=bot, grain=(0.10 if bg in ('cream', 'sand') else 0.16) if grain is None else grain,
                          blend='multiply' if bg in ('cream', 'sand') else 'soft-light')
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{font_css()}\n{css}</style></head>"
            f"<body>{body}<div class='grain'></div>{FIT_JS}</body></html>")


# ------------------------------------------------------------------ layouts
def _top(it, t):
    eb = html.escape(it.get('eyebrow') or '')
    return f"<div class='top mono' style='color:{t['fg']}'><span>{eb}</span><span style='color:{t['accent']}'>{html.escape(it.get('corner', '') or '')}</span></div>"


def _bottom(it, t, fda=False):
    ft = html.escape(it.get('footer') or '')
    disc = f"<div class='fda' style='margin-top:18px;max-width:880px'>{html.escape(FDA)}</div>" if fda else ''
    right = html.escape(it.get('footer_right') or '')
    return (f"<div style='flex:none'><div class='bottom mono' style='color:{t['fg']}'><span>{ft}</span><span>{right}</span></div>{disc}</div>")


def L_type_hero(it, fmt, bg):
    t = THEME[bg]
    hs = 132 if fmt != 'story' else 150
    sub = f"<div class='fit' style='margin-top:46px;height:auto'><div style='font-size:44px;line-height:1.22;font-style:italic;color:{t['fg']};opacity:.92'>{rich(it.get('sub'))}</div></div>" if it.get('sub') else ''
    mid = (f"<div class='mid center'><div class='fit' style='width:100%;height:{'760' if fmt != 'story' else '980'}px;display:flex;flex-direction:column;justify-content:center'>"
           f"<div class='h' data-fit data-min='60' style='font-size:{hs}px;height:100%;display:flex;flex-direction:column;justify-content:center'><div>{rich(it.get('headline'))}</div>{sub}</div></div></div>")
    return page(fmt, bg, f"<div class='frame'>{_top(it, t)}{mid}{_bottom(it, t, it.get('disclaimer_on_image'))}</div>")


def L_statue_type(it, fmt, bg):
    t = THEME[bg]
    w, h = SIZE[fmt]
    sh = int(h * (0.93 if fmt != 'story' else 0.80))
    sw = int(sh * 536.984 / 763)
    statue = (f"<div class='statue svgbox' style='height:{sh}px;width:{sw}px;right:{-int(sw * 0.16)}px;bottom:0'>{_svg('statue.svg')}</div>")
    head = (f"<div class='fit' style='width:640px;height:{'620' if fmt != 'story' else '760'}px'>"
            f"<div class='h' data-fit data-min='56' style='font-size:112px;height:100%'>{rich(it.get('headline'))}</div></div>")
    sub = f"<div style='font-size:38px;line-height:1.25;font-style:italic;max-width:560px;margin-top:34px'>{rich(it.get('sub'))}</div>" if it.get('sub') else ''
    mid = f"<div class='mid' style='justify-content:flex-start;padding-top:70px'>{head}{sub}</div>"
    return page(fmt, bg, f"{statue}<div class='frame'>{_top(it, t)}{mid}{_bottom(it, t, it.get('disclaimer_on_image'))}</div>")


def L_logo_reveal(it, fmt, bg):
    t = THEME[bg]
    lw = 600 if fmt != 'story' else 680
    logo_col = C['gold'] if bg in ('navy', 'ink') else (C['cream'] if bg == 'cobalt' else C['cobalt'] if bg == 'cream' else C['navy'])
    head = f"<div class='h' style='font-size:{it.get('hsize', 54)}px;margin-top:70px;font-style:normal'>{rich(it.get('headline'))}</div>" if it.get('headline') else ''
    sub = f"<div class='bal' style='font-size:{it.get('ssize', 34)}px;font-style:italic;margin-top:22px;opacity:.9;line-height:1.25'>{rich(it.get('sub'))}</div>" if it.get('sub') else ''
    mid = f"<div class='mid center'><div class='svgbox' style='width:{lw}px;height:{int(lw * 248.455 / 460)}px;color:{logo_col}'>{_svg('lucid_logo.svg')}</div>{head}{sub}</div>"
    return page(fmt, bg, f"<div class='frame'>{_top(it, t)}{mid}{_bottom(it, t, it.get('disclaimer_on_image'))}</div>")


def L_product_hero(it, fmt, bg):
    t = THEME[bg]
    view = it.get('view', 'front')
    img = os.path.join(ASSETS, 'renders', f'tube_{view}.png')
    shadow_col = 'rgba(0,0,20,.45)' if bg in ('navy', 'ink', 'cobalt') else 'rgba(16,20,49,.28)'
    tube = (f"<div style='flex:1;min-height:0;display:flex;justify-content:center;align-items:flex-end;position:relative'>"
            f"<div style='position:relative;height:100%;aspect-ratio:724/1787'>"
            f"<div style='position:absolute;left:-14%;right:-14%;bottom:-22px;height:64px;border-radius:50%;"
            f"background:radial-gradient(ellipse at center,{shadow_col} 0%,rgba(0,0,0,0) 70%)'></div>"
            f"<img src='file://{img}' style='position:relative;height:100%;width:100%;display:block'></div></div>")
    head = (f"<div class='h' style='flex:none;font-size:{it.get('hsize', 78)}px;text-align:center;margin:26px 0 40px'>{rich(it.get('headline'))}</div>"
            if it.get('headline') else "<div style='height:30px;flex:none'></div>")
    sub = (f"<div class='bal' style='flex:none;font-size:36px;font-style:italic;text-align:center;margin-top:40px;line-height:1.2'>{rich(it.get('sub'))}</div>"
           if it.get('sub') else '')
    mid = f"<div class='mid' style='justify-content:flex-start'>{head}{tube}{sub}</div>"
    return page(fmt, bg, f"<div class='frame'>{_top(it, t)}{mid}{_bottom(it, t, it.get('disclaimer_on_image'))}</div>")


def L_list_type(it, fmt, bg):
    t = THEME[bg]
    lines = [x.strip() for x in (it.get('sub') or '').split('|') if x.strip()]
    rows = ''.join(f"<div style='font-style:{'italic' if k % 2 else 'normal'};'>{rich(x)}</div>" for k, x in enumerate(lines))
    head = f"<div class='mono' style='color:{t['accent']};margin-bottom:44px'>{html.escape(it.get('headline') or '')}</div>" if it.get('headline') else ''
    box_h = 900 if fmt != 'story' else 1100
    mid = (f"<div class='mid center'>{head}<div class='fit' style='width:100%;height:{box_h}px;display:flex;align-items:center;justify-content:center'>"
           f"<div data-fit data-min='36' style='font-size:84px;line-height:1.16;letter-spacing:-.01em;height:100%;width:100%;display:flex;flex-direction:column;justify-content:center'>{rows}</div></div></div>")
    return page(fmt, bg, f"<div class='frame'>{_top(it, t)}{mid}{_bottom(it, t, it.get('disclaimer_on_image'))}</div>")


def L_numerals(it, fmt, bg):
    t = THEME[bg]
    lines = [x.strip() for x in (it.get('sub') or '').split('|') if x.strip()]
    nums = ['I', 'II', 'III', 'IV', 'V']
    rows = ''.join(
        f"<div style='display:flex;align-items:baseline;gap:44px;padding:30px 0;border-top:2px solid {t['accent']}{'' if k else ''}'>"
        f"<div style='width:{230 if fmt == 'story' else 190}px;flex:none;font-size:{160 if fmt == 'story' else 128}px;line-height:.9;font-weight:500;color:{t['accent']}'>{nums[k]}</div>"
        f"<div style='font-size:{74 if fmt == 'story' else 58}px;line-height:1.1'>{rich(x)}</div></div>" for k, x in enumerate(lines))
    head = f"<div class='h' style='font-size:92px;margin-bottom:48px'>{rich(it.get('headline'))}</div>" if it.get('headline') else ''
    mid = f"<div class='mid'>{head}<div style='border-bottom:2px solid {t['accent']}'>{rows}</div></div>"
    return page(fmt, bg, f"<div class='frame'>{_top(it, t)}{mid}{_bottom(it, t, it.get('disclaimer_on_image'))}</div>")


def L_ingredient_card(it, fmt, bg):
    t = THEME[bg]
    parts = [x.strip() for x in (it.get('sub') or '').split('|')]
    latin = parts[0] if parts else ''
    facts = parts[1:]
    fact_rows = ''.join(f"<div class='mono' style='padding:20px 0;border-top:2px solid {t['accent']};font-size:26px'>{rich(x)}</div>" for x in facts if x)
    w, h = SIZE[fmt]
    sh = int(h * 0.66); sw = int(sh * 536.984 / 763)
    statue = f"<div class='statue svgbox' style='height:{sh}px;width:{sw}px;right:{-int(sw * 0.28)}px;top:{int(h * 0.08)}px;opacity:{THEME[bg]['st_op'] * 0.5:.2f}'>{_svg('statue.svg')}</div>"
    name = it.get('headline') or ''
    fs = it.get('hsize') or (150 if len(name) <= 12 else 120 if len(name) <= 18 else 96)
    mid = (f"<div class='mid' style='justify-content:flex-end;padding-bottom:24px'>"
           f"<div class='h' style='font-size:{fs}px;font-weight:500;max-width:880px'>{rich(name)}</div>"
           f"<div style='font-size:48px;font-style:italic;margin:22px 0 54px'>{rich(latin)}</div>"
           f"<div style='border-bottom:2px solid {t['accent']}'>{fact_rows}</div></div>")
    return page(fmt, bg, f"{statue}<div class='frame'>{_top(it, t)}{mid}{_bottom(it, t, it.get('disclaimer_on_image'))}</div>")


def L_quote_split(it, fmt, bg):
    t = THEME[bg]
    w, h = SIZE[fmt]
    other = {'cream': 'cobalt', 'cobalt': 'cream', 'navy': 'cream', 'ink': 'sand', 'sand': 'ink'}[bg]
    t2 = THEME[other]
    a = rich(it.get('headline')); b = rich(it.get('sub'))
    pad = 84
    half = h // 2
    top_pad, bot_pad = (250, 250) if fmt == 'story' else (78, 70)
    body = (f"<div style='position:absolute;left:0;right:0;top:0;height:{half}px;background:{C[bg]}'></div>"
            f"<div style='position:absolute;left:0;right:0;top:{half}px;bottom:0;background:{C[other]}'></div>"
            f"<div style='position:absolute;left:{pad}px;right:{pad}px;top:{top_pad}px;color:{t['fg']}' class='mono'>{html.escape(it.get('eyebrow') or '')}</div>"
            f"<div style='position:absolute;left:{pad}px;right:{pad}px;top:{top_pad + 60}px;height:{half - top_pad - 60 - 60}px;display:flex;align-items:flex-end;color:{t['fg']}'>"
            f"<div class='h' style='font-size:{it.get('hsize', 100)}px;max-width:900px'>{a}</div></div>"
            f"<div style='position:absolute;left:{pad}px;right:{pad}px;top:{half + 60}px;height:{half - bot_pad - 60 - 60}px;display:flex;align-items:flex-start;justify-content:flex-end;text-align:right;color:{t2['fg']}'>"
            f"<div class='h' style='font-size:{it.get('hsize', 100)}px;max-width:900px'>{b}</div></div>"
            f"<div style='position:absolute;left:{pad}px;right:{pad}px;bottom:{bot_pad}px;color:{t2['fg']};display:flex;justify-content:space-between' class='mono'>"
            f"<span>{html.escape(it.get('footer') or '')}</span><span>{html.escape(it.get('footer_right') or '')}</span></div>")
    if it.get('disclaimer_on_image'):
        body += f"<div class='fda' style='position:absolute;left:{pad}px;right:{pad}px;bottom:{bot_pad - 50}px;color:{t2['fg']}'>{html.escape(FDA)}</div>"
    return page(fmt, bg, body)


def L_cta_waitlist(it, fmt, bg):
    t = THEME[bg]
    url = it.get('url') or 'luciddaily.com'
    head = f"<div class='h' style='font-size:{110 if fmt != 'story' else 120}px'>{rich(it.get('headline'))}</div>"
    sub = f"<div class='bal' style='font-size:{52 if fmt == 'story' else 40}px;font-style:italic;margin-top:40px;line-height:1.25'>{rich(it.get('sub'))}</div>" if it.get('sub') else ''
    btn = (f"<div style='margin-top:70px;display:inline-flex;align-self:center;border:2px solid {t['accent']};padding:26px 46px'>"
           f"<span class='mono' style='font-size:34px;letter-spacing:.18em;color:{t['fg']}'>{html.escape(url)}</span></div>")
    icon = f"<div class='svgbox' style='width:150px;height:181px;color:{t['accent']};margin:0 auto 60px'>{_svg('head_icon.svg')}</div>"
    mid = f"<div class='mid center'>{icon}{head}{sub}{btn}</div>"
    return page(fmt, bg, f"<div class='frame'>{_top(it, t)}{mid}{_bottom(it, t, it.get('disclaimer_on_image'))}</div>")


def L_head_icon(it, fmt, bg):
    t = THEME[bg]
    iw = 430 if fmt != 'story' else 480
    head = f"<div class='h' style='font-size:84px;margin-top:70px'>{rich(it.get('headline'))}</div>" if it.get('headline') else ''
    sub = f"<div style='font-size:38px;font-style:italic;margin-top:24px'>{rich(it.get('sub'))}</div>" if it.get('sub') else ''
    icol = C['gold'] if bg in ('navy', 'ink', 'cobalt') else t['accent']
    mid = f"<div class='mid center'><div class='svgbox' style='width:{iw}px;height:{int(iw * 338.27 / 281.093)}px;color:{icol}'>{_svg('head_icon.svg')}</div>{head}{sub}</div>"
    return page(fmt, bg, f"<div class='frame'>{_top(it, t)}{mid}{_bottom(it, t, it.get('disclaimer_on_image'))}</div>")


def L_avatar(it, fmt, bg):
    col = C['cream'] if bg in ('cobalt', 'navy', 'ink') else C['cobalt']
    return page('avatar', bg, f"<div style='position:absolute;inset:0;display:flex;align-items:center;justify-content:center'>"
                              f"<div class='svgbox' style='width:600px;height:{int(600 * 248.455 / 460)}px;color:{col}'>{_svg('lucid_logo.svg')}</div></div>", grain=0.0)


def L_highlight(it, fmt, bg):
    col = C['gold'] if bg in ('navy', 'ink') else C['cream']
    label = html.escape(it.get('headline') or '')
    if label == 'ICON':
        label = f"<div class='svgbox' style='width:250px;height:301px;color:{col}'>{_svg('head_icon.svg')}</div>"
    return page('highlight', bg, f"<div style='position:absolute;left:0;right:0;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center'>"
                                 f"<div style='width:520px;height:520px;border-radius:50%;border:3px solid {col};display:flex;align-items:center;justify-content:center;color:{col}'>"
                                 f"<div style='font-family:Ashcroft;font-size:{it.get('size', 150)}px;font-weight:500;letter-spacing:.02em'>{label}</div></div></div>", grain=0.0)


def L_reel_bg(it, fmt, bg):
    t = THEME[bg]
    return page('story', bg, f"<div class='frame'>{_top(it, t)}<div class='mid'></div>{_bottom(it, t, False)}</div>")


LAYOUTS = {k[2:]: v for k, v in globals().items() if k.startswith('L_')}


def render_items(items, out_dir):
    """items: dicts with id, kind, layout, background + text fields. Writes HTML + PNG for each."""
    os.makedirs(out_dir, exist_ok=True)
    hdir = os.path.join(out_dir, '_html'); os.makedirs(hdir, exist_ok=True)
    jobs = []
    for it in items:
        fmt = it['kind']
        doc = LAYOUTS[it['layout']](it, fmt, it['background'])
        hp = os.path.join(hdir, f"{it['id']}.html")
        open(hp, 'w').write(doc)
        w, h = SIZE['avatar' if it['layout'] == 'avatar' else 'highlight' if it['layout'] == 'highlight' else fmt]
        jobs.append({'html': hp, 'png': os.path.join(out_dir, f"{it['id']}.png"), 'w': w, 'h': h})
    man = os.path.join(hdir, 'manifest.json'); json.dump(jobs, open(man, 'w'))
    subprocess.run(['node', os.path.join(HERE, 'shoot.js'), man], check=True)
    return jobs


if __name__ == '__main__':
    plan = json.load(open(sys.argv[1]))
    items = plan['items'] if isinstance(plan, dict) else plan
    render_items(items, sys.argv[2])
