"""Independent checks on the OUTPUT pdf (re-parsed from scratch), against the source proof."""
import sys, collections, pikepdf
from interp import walk
from labelkit import PT, X0, YTOP, PAGE_MM, ELEMENTS, Source
out_path=sys.argv[1]
src=Source('src.pdf')
pdf=pikepdf.open(out_path); page=pdf.pages[0]
ops=list(pikepdf.parse_content_stream(page)); objs=walk(ops)
ox=X0+PAGE_MM[0]*PT; oy=YTOP-PAGE_MM[3]*PT
def mm(b):  # output page pt -> label mm
    return ((b[0]+ox-X0)/PT,(YTOP-(b[3]+oy))/PT,(b[2]+ox-X0)/PT,(YTOP-(b[1]+oy))/PT)
for o in objs:
    if 'bbox' in o: o['mm']=mm(o['bbox'])
ok=True
def check(name,cond,detail=''):
    global ok
    print(('PASS ' if cond else 'FAIL ')+name+(' | '+detail if detail else ''))
    ok = ok and cond
# ---- 1. resources / colours
cs=page.Resources.ColorSpace
names={k:str(v[1]) for k,v in cs.items()}
check('spot colours intact', set(names.values())=={'/PANTONE 2728 C','/PANTONE 2758 C','/PANTONE 1255 C','/Cut','/Crease'}, str(names))
check('no images / foreign fonts left', '/XObject' not in page.Resources and list(page.Resources.Font.keys())==['/C0_0'], str(list(page.Resources.get('/Font',{}).keys())))
check('Illustrator private data removed', '/PieceInfo' not in page and '/Thumb' not in page)
check('layers', [str(o.Name) for o in pdf.Root.OCProperties.OCGs]==['Artwork','FOIL','Dielnie','DIEMSION'], str([str(o.Name) for o in pdf.Root.OCProperties.OCGs]))
mb=[float(x) for x in page.MediaBox]
check('page is 1:1 (229 x 177 mm)', abs(mb[2]/PT-229)<0.01 and abs(mb[3]/PT-177)<0.01, f"{mb[2]/PT:.2f} x {mb[3]/PT:.2f} mm")
# ---- 2. dieline + dimension layers identical to source (inside label region)
def sig(o):
    return (o['op'], o.get('stroke_cs'), tuple(o.get('stroke') or ()), round(o.get('lw',0),3), tuple(round(v,2) for v in o['mm']))
def layer_objs(objlist, layer):
    return sorted(sig(o) for o in objlist if o.get('layer')==layer and o['op'] in ('S','f','B') and o['mm'][1]>-14.5 and o['mm'][3]<161)
for lay,nm in (('/MC2','Dieline'),('/MC3','Dimension marks')):
    a=layer_objs(src.objs,lay); b=layer_objs(objs,lay)
    check(f'{nm} layer identical to factory proof ({len(a)} objects)', a==b, '' if a==b else f'src {len(a)} out {len(b)}')
# dimension labels
def texts(objlist): return sorted((o['layer'],tuple(o['strs'])) for o in objlist if o['op']=='TEXT' and o['layer']=='/MC3')
ta=[s for l,ss in texts(src.objs) for s in ss]; tb=[s for l,ss in texts(objs) for s in ss]
check('dimension labels kept (8.5MM, 8.5MM, 45MM, 95MM, 8MM)', len(tb)==5 and all(t in ta for t in tb), f'{len(tb)} labels')
# dashed cap line untouched
da=sorted(tuple(round(v,3) for v in src.objs[i]['mm']) for i in (9,10,11))
db=sorted(tuple(round(v,3) for v in o['mm']) for o in objs if o['op']=='f' and o.get('fill_cs')=='DeviceCMYK' and o['mm'][3]-o['mm'][1]<0.5)
check('dashed cap line untouched', da==db)
# ---- 3. artwork completeness: same number of art objects per colour inside the label
def art_count(objlist):
    c=collections.Counter()
    for o in objlist:
        if o.get('layer') in('/MC0','/MC1') and o['op'] in('f','S') and -4<o['mm'][0] and o['mm'][2]<192 and 0<o['mm'][1] and o['mm'][3]<157:
            c[(o['op'],o.get('fill_cs') if o['op']=='f' else o.get('stroke_cs'))]+=1
    return c
ca=art_count(src.objs); cb=art_count(objs)
check('every artwork object present, none added', ca==cb, str(dict(cb)))
npa=sum(1 for o in src.ops if str(o.operator) in('m','l','c','v','y','re','h'))
# ---- 4. outlines unchanged (each art object = same path, uniformly scaled): compare op counts + aspect ratio
art_src=[o for o in src.objs if o.get('layer') in('/MC0','/MC1') and o['op'] in('f','S') and -4<o['mm'][0] and o['mm'][2]<192 and 0<o['mm'][1] and o['mm'][3]<157]
art_out=[o for o in objs if o.get('layer') in('/MC0','/MC1') and o['op'] in('f','S') and -4<o['mm'][0] and o['mm'][2]<192 and 0<o['mm'][1] and o['mm'][3]<157]
bad=0; boxes={44,411,412,413,16}
for a,b in zip(art_src,art_out):
    if a['npts']!=b['npts'] or a['nsub']!=b['nsub']: bad+=1; continue
    if a['id'] in boxes: continue
    wa,ha=a['mm'][2]-a['mm'][0],a['mm'][3]-a['mm'][1]; wb,hb=b['mm'][2]-b['mm'][0],b['mm'][3]-b['mm'][1]
    if wa>0.3 and ha>0.3 and abs((wb/wa)/(hb/ha)-1)>0.002: bad+=1
check('all glyph/art outlines are the originals (only moved or uniformly scaled)', bad==0 and len(art_src)==len(art_out), f'{len(art_out)} objects, {bad} mismatches')
# ---- 5. key alignments measured on the output
def bb(idx): 
    ms=[art_out[i]['mm'] for i in idx]; return (min(m[0] for m in ms),min(m[1] for m in ms),max(m[2] for m in ms),max(m[3] for m in ms))
pos={o['id']:k for k,o in enumerate(art_src)}
def E(name): return [pos[i] for i in ELEMENTS[name]]
def baseline(idx):
    vals=[art_out[i]['mm'][3] for i in idx]; best=max(vals,key=lambda v:sum(1 for w in vals if abs(w-v)<=0.03))
    g=[w for w in vals if abs(w-best)<=0.03]; return sum(g)/len(g)
half=lambda pt: pt/PT/2
CR_MID=53.5; CR_BOT=148.1495; CH=half(0.709)
facts=bb(E('facts_box')); pbox=bb(E('p_box')); frame=bb(E('powered_frame')); st=bb(E('statue')); logo=bb(E('logo')); te=bb(E('testide')); tg=bb(E('tagline'))
mi=baseline(E('dist2')); bt=baseline(E('btext'))
check('bottom text baseline = "Miami, FL..." baseline', abs(mi-bt)<0.005, f'{bt:.3f} vs {mi:.3f} mm')
t1=facts[1]-half(1.0); t2=pbox[1]-half(0.98); t3=frame[1]
check('three columns share one top line (outer edges)', max(t1,t2,t3)-min(t1,t2,t3)<0.01, f'facts {t1:.3f} / powered {t3:.3f} / protocol {t2:.3f}')
m_top=(pbox[1]-half(0.98))-(CR_MID+CH); m_bot=(CR_BOT-CH)-(pbox[3]+half(0.98))
check('Protocol box centred between the crease lines', abs(m_top-m_bot)<0.005, f'top {m_top:.3f} / bottom {m_bot:.3f} mm')
axis=(st[0]+st[2])/2
cx=lambda b:(b[0]+b[2])/2
ru=bb(E('rule')); btb=bb(E('btext'))
check('front elements on one centre axis', all(abs(cx(b)-axis)<0.005 for b in (logo,te,tg,frame,ru,btb)), ' '.join(f'{cx(b):.3f}' for b in (logo,te,tg,frame,st,ru,btb)))
check('rule and bottom text same width, flush', abs(ru[0]-btb[0])<0.005 and abs(ru[2]-btb[2])<0.005, f'rule {ru[0]:.3f}-{ru[2]:.3f} text {btb[0]:.3f}-{btb[2]:.3f}')
ws_a=te[1]-29.033; ws_b=(CR_MID-CH)-tg[3]
check('TESTIDE + tagline centred between cap line and crease', abs(ws_a-ws_b)<0.005, f'{ws_a:.3f} above / {ws_b:.3f} below (logo top margin {logo[1]-(8.4999+CH):.3f})')
# protocol rhythm from output
def row(name): 
    idx=E(name); b=bb(idx); return b, baseline(idx)
title=row('p_title'); dr=row('p_dir'); wn=row('p_warn'); sg=row('p_stor'); stx=row('p_stor_text'); fda=bb(E('p_fda_box')); upc=bb(E('upc'))
steps=E('p_steps'); l2=[i for i in steps if (art_out[i]['mm'][1]+art_out[i]['mm'][3])/2 > (bb(steps)[1]+bb(steps)[3])/2]
body4=[pos[i] for i in range(174,192)]
def flat_top(name):
    idx=E(name); vals=[art_out[i]['mm'][1] for i in idx]; best=max(vals,key=lambda v:sum(1 for w in vals if abs(w-v)<=0.03)); g=[w for w in vals if abs(w-best)<=0.03]; return sum(g)/len(g)
fh=half(0.471); ph=half(0.98)
gaps={'box->title':flat_top('p_title')-(pbox[1]+ph),'title->DIRECTIONS':flat_top('p_dir')-title[1],'steps->WARNING':flat_top('p_warn')-baseline(l2),
      'body->STORAGE':flat_top('p_stor')-baseline(body4),'storage->FDA box':(fda[1]-fh)-stx[1],'FDA box->UPC':upc[1]-(fda[3]+fh),'UPC->box':(pbox[3]-ph)-upc[3]}
vals=list(gaps.values())
check('Protocol: seven structural gaps equal', max(vals)-min(vals)<0.01, '  '.join(f'{k} {v:.3f}' for k,v in gaps.items()))
h1=bb(E('p_body'))[1]-wn[1]; h2=stx[0][1]-sg[1]
check('Protocol: heading->text gap equal for WARNING and STORAGE', abs(h1-h2)<0.005, f'{h1:.3f} / {h2:.3f}')
ncols=sorted([art_out[pos[i]]['mm'] for i in ELEMENTS['p_num']],key=lambda m:m[0])
c2=(ncols[1][0]+ncols[2][2])/2; c1=(ncols[0][0]+ncols[0][2])/2; c3=(ncols[3][0]+ncols[5][2])/2
check('Protocol: step II on the panel axis, I and III equidistant', abs(c2-cx(pbox))<0.005 and abs((c2-c1)-(c3-c2))<0.005, f'I {c1:.3f}  II {c2:.3f}  III {c3:.3f}  (axis {cx(pbox):.3f})')
# safety: nothing crosses a crease / leaves the label
allb=[b['mm'] for a,b in zip(art_src,art_out) if a['id'] not in (9,10,11)]
body=[m for m in allb if m[1]>CR_MID]; lid=[m for m in allb if m[3]<CR_MID]
check('no artwork touches a crease or the overlap', len(body)+len(lid)==len(allb) and min(m[1] for m in body)>CR_MID+2 and max(m[3] for m in body)<CR_BOT-2 and max(m[3] for m in lid)<CR_MID-2 and min(m[1] for m in lid)>8.5+2 and max(m[2] for m in allb)<188-2 and min(m[0] for m in allb)>2,
      f'min clearances: body top {min(m[1] for m in body)-CR_MID:.2f}, body bottom {CR_BOT-max(m[3] for m in body):.2f}, lid bottom {CR_MID-max(m[3] for m in lid):.2f}, right {188-max(m[2] for m in allb):.2f}, left {min(m[0] for m in allb):.2f} mm')
print('\nALL CHECKS PASSED' if ok else '\nSOME CHECKS FAILED')
