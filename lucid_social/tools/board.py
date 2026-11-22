"""
board.py - Instagram profile preview (how the 3x3 grid reads after the last pre-launch post) + JPEG previews.
usage: python3 board.py PLAN.json IMG_DIR OUT_PNG
"""
import html, json, os, subprocess, sys
from PIL import Image
import social


def feed_order(items):
    """feed posts in posting order (carousel = its first slide), newest first for the grid"""
    seen, posts = set(), []
    for it in items:
        if it['kind'] == 'feed':
            posts.append(it['id'])
        elif it['kind'] == 'carousel_slide':
            base = it['id'].rstrip('abcdefgh')
            if base not in seen:
                seen.add(base); posts.append(it['id'])
    return list(reversed(posts))


def profile_html(plan, img_dir, handle='thelucidinstitute'):
    items = plan['items']
    grid = feed_order(items)[:9]
    hl = plan.get('highlights', [])[:5]
    cells = ''.join(f"<div class='cell' style=\"background-image:url('file://{img_dir}/{i}.png')\"></div>" for i in grid)
    hls = ''.join(f"<div class='hl'><div class='hlc' style=\"background-image:url('file://{img_dir}/HL{k + 1}.png')\"></div>"
                  f"<div class='hln'>{html.escape(h)}</div></div>" for k, h in enumerate(hl))
    bio = html.escape(plan.get('bio', '')).replace('\n', '<br>')
    css = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;background:#fff;color:#000;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.bar{height:120px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:40px;border-bottom:1px solid #eee}
.head{display:flex;align-items:center;gap:60px;padding:36px 40px 10px}
.av{width:230px;height:230px;border-radius:50%;background-size:cover;background-position:center;flex:none;border:1px solid #ddd}
.stats{display:flex;gap:70px;font-size:34px;text-align:center}.stats b{display:block;font-size:40px}
.name{padding:18px 40px 0;font-weight:700;font-size:34px}
.bio{padding:6px 40px 0;font-size:32px;line-height:1.32;white-space:normal}
.link{padding:6px 40px 0;font-size:32px;color:#00376b;font-weight:600}
.hls{display:flex;gap:44px;padding:34px 40px 30px}
.hl{width:150px;text-align:center}.hlc{width:150px;height:150px;border-radius:50%;border:2px solid #ddd;background-size:cover;background-position:center;margin-bottom:10px}
.hln{font-size:24px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tabs{height:90px;border-top:1px solid #eee;display:flex;align-items:center;justify-content:center;font-size:28px;letter-spacing:.12em;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:3px}
.cell{aspect-ratio:3/4;background-size:cover;background-position:center}
"""
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>"
            f"<div class='bar'>{html.escape(handle)}</div>"
            f"<div class='head'><div class='av' style=\"background-image:url('file://{img_dir}/AVATAR.png')\"></div>"
            f"<div class='stats'><div><b>9</b>posts</div><div><b>&ndash;</b>followers</div><div><b>&ndash;</b>following</div></div></div>"
            f"<div class='name'>The Lucid Institute</div><div class='bio'>{bio}</div><div class='link'>luciddaily.com</div>"
            f"<div class='hls'>{hls}</div><div class='tabs'>POSTS</div><div class='grid'>{cells}</div>"
            f"<script>document.fonts.ready.then(()=>document.body.setAttribute('data-ready','1'))</script></body></html>")


def render_profile(plan, img_dir, out_png, handle='thelucidinstitute'):
    hdir = os.path.join(img_dir, '_html'); os.makedirs(hdir, exist_ok=True)
    hp = os.path.join(hdir, 'profile.html')
    open(hp, 'w').write(profile_html(plan, img_dir, handle))
    # height: header ~ 1060 + 3 rows of 3:4 cells (359 x 479)
    man = os.path.join(hdir, 'profile.json')
    json.dump([{'html': hp, 'png': out_png, 'w': 1080, 'h': 1090 + 3 * 482}], open(man, 'w'))
    subprocess.run(['node', os.path.join(social.HERE, 'shoot.js'), man], check=True)


def jpegs(img_dir, out_dir, quality=88, max_w=1080):
    os.makedirs(out_dir, exist_ok=True)
    for f in sorted(os.listdir(img_dir)):
        if f.endswith('.png'):
            im = Image.open(os.path.join(img_dir, f)).convert('RGB')
            if im.width > max_w:
                im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
            im.save(os.path.join(out_dir, f[:-4] + '.jpg'), quality=quality, optimize=True, progressive=True)


if __name__ == '__main__':
    plan = json.load(open(sys.argv[1]))
    render_profile(plan, os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]))
