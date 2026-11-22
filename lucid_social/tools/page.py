"""
page.py - the review page for the TESTIDE pre-launch kit (published as an Artifact).
Shows the profile preview, every post with its caption (copy button), hashtags and posting day, the stories,
the reel, the profile kit and the production / compliance notes. Images are JPEG previews of the PNG masters.
usage: python3 page.py PLAN.json IMG_DIR OUT_DIR
"""
import html, json, os, shutil, sys

FDA = ('*These statements have not been evaluated by the Food and Drug Administration. '
       'This product is not intended to diagnose, treat, cure, or prevent any disease.')

CSS = """
<title>TESTIDE Pre-Launch Kit</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Marcellus&family=Inter:wght@400;500;600&family=Share+Tech+Mono&display=swap">
<style>
/* layout: one editorial column; posts as image + copy rows; the brand's own palette */
:root{
  --bg:#FAF8F6; --fg:#101431; --navy:#091A68; --cobalt:#1D46DE; --sand:#AD9368; --gold:#B8860B;
  --muted:#4A4F6E; --line:#E4DED3; --card:#FFFFFF; --chip:#EEF1FD; --band:#1D46DE; --bandfg:#FAF8F6;
  --display:'Marcellus',Georgia,serif; --body:'Inter',system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  --mono:'Share Tech Mono',ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0E1230; --fg:#F2EFEA; --navy:#C9D3FF; --cobalt:#7F9BFF; --sand:#CDB68E; --gold:#F7B524;
  --muted:#A6ABC8; --line:#262B52; --card:#151A3D; --chip:#1E2552; --band:#091A68; --bandfg:#FAF8F6; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0E1230; --fg:#F2EFEA; --navy:#C9D3FF; --cobalt:#7F9BFF; --sand:#CDB68E; --gold:#F7B524;
  --muted:#A6ABC8; --line:#262B52; --card:#151A3D; --chip:#1E2552; --band:#091A68; --bandfg:#FAF8F6; color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font-family:var(--body);font-size:16px;line-height:1.55;margin:0}
.wrap{max-width:1120px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.hero{background:var(--band);color:var(--bandfg);margin-top:calc(-1 * env(safe-area-inset-top,0px));padding-top:calc(env(safe-area-inset-top,0px) + 3.2rem);padding-bottom:3rem}
.hero .wrap{display:grid;gap:1.2rem}
.label{font-family:var(--mono);text-transform:uppercase;letter-spacing:.16em;font-size:.78rem}
.hero h1{font-family:var(--display);font-weight:400;font-size:clamp(2.4rem,6vw,4.4rem);line-height:1.02;margin:0;text-wrap:balance}
.hero p{max-width:62ch;margin:0;font-size:1.08rem;opacity:.95}
.arc{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1px;background:rgba(250,248,246,.25);margin-top:.8rem}
.arc div{background:var(--band);padding:1rem 1rem 1rem 0}
.arc b{display:block;font-family:var(--display);font-weight:400;font-size:1.35rem;margin:.2rem 0}
section{padding-block:3.2rem;border-bottom:1px solid var(--line)}
h2{font-family:var(--display);font-weight:400;font-size:clamp(1.8rem,4vw,2.6rem);margin:.2rem 0 1.2rem;text-wrap:balance}
.intro{max-width:66ch;color:var(--muted);margin:0 0 1.6rem}
.grid2{display:grid;grid-template-columns:minmax(0,420px) minmax(0,1fr);gap:2.4rem;align-items:start}
@media (max-width:820px){.grid2{grid-template-columns:1fr}}
.profile img{width:100%;border:1px solid var(--line);border-radius:18px;display:block}
table{border-collapse:collapse;width:100%;font-size:.95rem}
th,td{text-align:left;padding:.55rem .6rem;border-bottom:1px solid var(--line);vertical-align:top}
th{font-family:var(--mono);text-transform:uppercase;letter-spacing:.12em;font-size:.72rem;color:var(--muted);font-weight:400}
td.day{font-family:var(--mono);white-space:nowrap;font-variant-numeric:tabular-nums}
.tablebox{overflow-x:auto}
.post{display:grid;grid-template-columns:minmax(0,400px) minmax(0,1fr);gap:2rem;padding-block:2rem;border-top:1px solid var(--line)}
.post:first-of-type{border-top:0}
@media (max-width:820px){.post{grid-template-columns:1fr}}
.post img{width:100%;display:block;border-radius:6px;box-shadow:0 1px 0 var(--line)}
.meta{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:.8rem}
.chip{font-family:var(--mono);text-transform:uppercase;letter-spacing:.1em;font-size:.72rem;background:var(--chip);color:var(--navy);padding:.25rem .55rem;border-radius:3px}
.chip.gold{color:var(--gold);background:transparent;border:1px solid var(--gold)}
.post h3{font-family:var(--display);font-weight:400;font-size:1.6rem;line-height:1.15;margin:.2rem 0 .8rem;text-wrap:balance}
.caption{white-space:pre-wrap;background:var(--card);border:1px solid var(--line);border-radius:6px;padding:1rem 1.1rem;font-size:.96rem;max-width:66ch;min-width:0;overflow-wrap:anywhere}
.tags{color:var(--cobalt);font-size:.92rem;margin:.6rem 0 0;overflow-wrap:anywhere}
.note{font-size:.88rem;color:var(--muted);margin-top:.8rem;max-width:66ch}
.row{display:flex;gap:.6rem;align-items:center;margin-top:.8rem;flex-wrap:wrap}
button{font:inherit;font-family:var(--mono);text-transform:uppercase;letter-spacing:.12em;font-size:.75rem;background:transparent;color:var(--fg);border:1px solid var(--fg);padding:.45rem .8rem;border-radius:3px;cursor:pointer}
button:hover{background:var(--fg);color:var(--bg)}
button:focus-visible{outline:2px solid var(--cobalt);outline-offset:2px}
.slides{display:flex;gap:12px;overflow-x:auto;padding-bottom:.6rem;scroll-snap-type:x mandatory}
.slides img{width:min(260px,70vw);flex:none;scroll-snap-align:start;border-radius:6px}
.stories{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1.4rem}
.stories figure{margin:0;min-width:0}
.stories img{width:100%;border-radius:10px;display:block}
figcaption{font-size:.9rem;margin-top:.6rem;min-width:0}
figcaption b{display:block;font-family:var(--mono);font-weight:400;text-transform:uppercase;letter-spacing:.12em;font-size:.72rem;color:var(--muted)}
.reel{display:grid;grid-template-columns:minmax(0,320px) minmax(0,1fr);gap:2rem;align-items:start}
@media (max-width:820px){.reel{grid-template-columns:1fr}}
video{width:100%;border-radius:10px;background:#000;display:block}
.kit{display:flex;flex-wrap:wrap;gap:1.6rem;align-items:flex-start}
.kit .av{width:150px;height:150px;border-radius:50%;object-fit:cover;border:1px solid var(--line)}
.kit .hl{width:110px;text-align:center;font-size:.85rem}
.kit .hl img{width:110px;height:110px;border-radius:50%;object-fit:cover;border:1px solid var(--line);display:block;margin-bottom:.4rem}
.notes{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.6rem}
.notes h4{font-family:var(--display);font-weight:400;font-size:1.25rem;margin:0 0 .4rem}
.notes ul{margin:0;padding-left:1.1rem}
.notes li{margin:.3rem 0}
.fda{font-size:.85rem;color:var(--muted);border-left:3px solid var(--sand);padding-left:.8rem;max-width:70ch}
footer{padding-block:2.4rem;color:var(--muted);font-size:.88rem}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto}}
</style>
"""

JS = """
<script>
document.querySelectorAll('button[data-copy]').forEach(b => b.addEventListener('click', () => {
  const el = document.getElementById(b.dataset.copy);
  const txt = el.innerText;
  const done = () => { const t = b.textContent; b.textContent = 'Copied'; setTimeout(() => b.textContent = t, 1400); };
  try {
    navigator.clipboard.writeText(txt).then(done, () => sel(el));
  } catch (e) { sel(el); }
  function sel(n) { const r = document.createRange(); r.selectNodeContents(n); const s = getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = 'Selected, press copy'; }
}));
</script>
"""


def esc(s):
    return html.escape(s or '')


def build(plan, img_dir, out_dir, extra):
    """extra: dict(handle, notes(list of (title, [items])), reel(bool))"""
    os.makedirs(os.path.join(out_dir, 'img'), exist_ok=True)
    items = plan['items']
    feed = [i for i in items if i['kind'] in ('feed', 'carousel_slide')]
    stories = [i for i in items if i['kind'] == 'story']
    # group carousel slides
    posts, car = [], {}
    for it in feed:
        if it['kind'] == 'carousel_slide':
            base = it['id'].rstrip('abcdefgh')
            if base not in car:
                car[base] = []; posts.append(('carousel', base))
            car[base].append(it)
        else:
            posts.append(('feed', it))
    h = [CSS, "<div class='hero'><div class='wrap'>",
         f"<div class='label'>The Lucid Institute &middot; TESTIDE &middot; pre-launch social, proposed</div>",
         f"<h1>{esc(plan['campaign_name'])}</h1><p>{esc(plan['big_idea'])}</p><div class='arc'>"]
    for a in plan['arc']:
        h.append(f"<div><span class='label'>{esc(a['days'])}</span><b>{esc(a['phase'])}</b>{esc(a['purpose'])}</div>")
    h.append("</div></div></div>")
    # grid + calendar
    h.append("<section><div class='wrap'><div class='label'>The grid</div><h2>How the profile reads on launch day</h2>"
             "<div class='grid2'><div class='profile'><img src='img/PROFILE.jpg' alt='Instagram profile preview with the nine pre-launch posts in a three by three grid'></div><div>"
             "<p class='intro'>Posting order runs from the bottom right of the grid to the top left, so the last post before launch sits first. "
             "Handle, launch date and the waitlist page are placeholders until they are set.</p>"
             "<div class='tablebox'><table><thead><tr><th>Day</th><th>Post</th><th>Format</th><th>Phase</th></tr></thead><tbody>")
    for kind, p in posts:
        it = p if kind == 'feed' else car[p][0]
        fmt = 'Carousel, %d slides' % len(car[p]) if kind == 'carousel' else 'Feed post'
        h.append(f"<tr><td class='day'>{esc(it['day'])}</td><td>{esc(it['id'] if kind == 'feed' else p)} &middot; {esc(strip(it['headline']))}</td><td>{fmt}</td><td>{esc(it['phase'])}</td></tr>")
    for it in stories:
        h.append(f"<tr><td class='day'>{esc(it['day'])}</td><td>{esc(it['id'])} &middot; {esc(strip(it['headline']))}</td><td>Story</td><td>{esc(it['phase'])}</td></tr>")
    if extra.get('reel'):
        h.append(f"<tr><td class='day'>{esc(extra['reel_day'])}</td><td>Reel &middot; 360&deg; reveal</td><td>Reel, 10.5 s</td><td>{esc(extra['reel_phase'])}</td></tr>")
    h.append("</tbody></table></div></div></div></div></section>")
    # feed posts
    h.append("<section><div class='wrap'><div class='label'>Feed</div><h2>Nine posts, in posting order</h2>"
             "<p class='intro'>Each image is 1080 &times; 1350. Captions are ready to paste. Posts that carry a structure/function claim show the FDA line on the image and in the caption.</p>")
    n = 0
    for kind, p in posts:
        n += 1
        if kind == 'feed':
            it = p
            img = f"<img src='img/{it['id']}.jpg' alt='{esc(alt(it))}' loading='lazy'>"
            pid = it['id']
        else:
            it = car[p][0]
            img = "<div class='slides'>" + ''.join(f"<img src='img/{s['id']}.jpg' alt='{esc(alt(s))}' loading='lazy'>" for s in car[p]) + "</div>"
            pid = p
        chips = (f"<span class='chip'>{esc(it['day'])}</span><span class='chip'>{esc(it['phase'])}</span>"
                 f"<span class='chip'>{'Carousel' if kind == 'carousel' else 'Feed'}</span>"
                 + ("<span class='chip gold'>FDA line on image</span>" if any(s.get('disclaimer_on_image') for s in (car[p] if kind == 'carousel' else [it])) else ''))
        tags = ' '.join('#' + t.lstrip('#') for t in it.get('hashtags', []))
        h.append(f"<article class='post'><div>{img}</div><div style='min-width:0'><div class='meta'>{chips}</div>"
                 f"<h3>{esc(pid)} &middot; {esc(strip(it['headline']))}</h3>"
                 f"<div class='caption' id='cap-{pid}'>{esc(it['caption'])}{(chr(10) + chr(10) + esc(tags)) if tags else ''}</div>"
                 f"<div class='row'><button type='button' data-copy='cap-{pid}'>Copy caption</button></div>"
                 f"<div class='note'><b>Claims check:</b> {esc(it.get('claim_risk', ''))}</div></div></article>")
    h.append("</div></section>")
    # stories
    h.append("<section><div class='wrap'><div class='label'>Stories</div><h2>Four stories</h2>"
             "<p class='intro'>1080 &times; 1920. Text stays inside the safe zone; add the sticker named under each one in the Instagram app.</p><div class='stories'>")
    for it in stories:
        h.append(f"<figure><img src='img/{it['id']}.jpg' alt='{esc(alt(it))}' loading='lazy'><figcaption><b>{esc(it['day'])} &middot; {esc(it['id'])}</b>{esc(it['caption'])}</figcaption></figure>")
    h.append("</div></div></section>")
    if extra.get('reel'):
        h.append("<section><div class='wrap'><div class='label'>Reel</div><h2>360&deg; reveal</h2><div class='reel'>"
                 "<video controls muted playsinline loop poster='img/REEL_COVER.jpg' src='media/TESTIDE_teaser_reel.mp4'></video>"
                 f"<div><p class='intro'>{esc(extra['reel_text'])}</p><div class='caption' id='cap-reel'>{esc(extra['reel_caption'])}</div>"
                 "<div class='row'><button type='button' data-copy='cap-reel'>Copy caption</button></div></div></div></div></section>")
    # profile kit
    h.append("<section><div class='wrap'><div class='label'>Profile kit</div><h2>Avatar, highlights, bio</h2><div class='kit'>"
             "<div><img class='av' src='img/AVATAR.jpg' alt='Avatar: the LUCID logo on cobalt'><div class='note'>Avatar</div></div>")
    for k, name in enumerate(plan.get('highlights', [])[:5]):
        h.append(f"<div class='hl'><img src='img/HL{k + 1}.jpg' alt='Highlight cover {esc(name)}'>{esc(name)}</div>")
    h.append(f"</div><div class='caption' id='cap-bio' style='margin-top:1.6rem'>{esc(plan.get('bio', ''))}</div>"
             "<div class='row'><button type='button' data-copy='cap-bio'>Copy bio</button></div></div></section>")
    # notes
    h.append("<section><div class='wrap'><div class='label'>Before posting</div><h2>Notes</h2><div class='notes'>")
    for title, lis in extra['notes']:
        h.append(f"<div><h4>{esc(title)}</h4><ul>" + ''.join(f"<li>{esc(x)}</li>" for x in lis) + "</ul></div>")
    h.append(f"</div><p class='fda' style='margin-top:1.6rem'>{esc(FDA)}</p></div></section>")
    h.append(f"<footer><div class='wrap'>{esc(extra.get('footer', ''))}</div></footer>")
    h.append(JS)
    open(os.path.join(out_dir, 'index.html'), 'w').write('\n'.join(h))


def strip(s):
    return (s or '').replace('*', '').replace('\\n', ' ').replace('\n', ' ')


def alt(it):
    bits = [strip(it.get('eyebrow')), strip(it.get('headline')), strip((it.get('sub') or '').replace('|', ', '))]
    return 'Post: ' + '. '.join(b for b in bits if b)


if __name__ == '__main__':
    plan = json.load(open(sys.argv[1]))
    build(plan, sys.argv[2], sys.argv[3], json.load(open(sys.argv[4])) if len(sys.argv) > 4 else {'notes': []})
