"""Minimal PDF content-stream interpreter: lists every painted object with page-space bbox + state."""
import pikepdf, json, sys
from decimal import Decimal

def mat_mul(m, n):
    # PDF row-vector convention: result = m x n
    a,b,c,d,e,f = m; A,B,C,D,E,F = n
    return (a*A+b*C, a*B+b*D, c*A+d*C, c*B+d*D, e*A+f*C+E, e*B+f*D+F)
def apply(m, x, y):
    a,b,c,d,e,f = m
    return (a*x+c*y+e, b*x+d*y+f)

def walk(ops):
    """Yield dicts for each painted object."""
    I=(1.0,0.0,0.0,1.0,0.0,0.0)
    gs={'ctm':I,'fill_cs':'DeviceGray','fill':(0.0,),'stroke_cs':'DeviceGray','stroke':(0.0,),'lw':1.0,'dash':None,'gsname':None,'cap':0,'join':0}
    stack=[]; layer=None; layers=[]
    pts=[]; path_start=None; cur=None; nsub=0; has_re=False; pending_clip=None
    out=[]
    text_obj=None
    for i,o in enumerate(ops):
        op=str(o.operator); a=o.operands
        if op=='q': stack.append(dict(gs))
        elif op=='Q': gs=stack.pop()
        elif op=='cm':
            m=tuple(float(x) for x in a); gs['ctm']=mat_mul(m, gs['ctm'])
        elif op=='BDC': layers.append(str(a[1]) if len(a)>1 else str(a[0])); layer=layers[-1]
        elif op=='BMC': layers.append(str(a[0])); layer=layers[-1]
        elif op=='EMC': layers.pop(); layer=layers[-1] if layers else None
        elif op=='w': gs['lw']=float(a[0])
        elif op=='J': gs['cap']=int(a[0])
        elif op=='j': gs['join']=int(a[0])
        elif op=='d': gs['dash']=([float(x) for x in a[0]], float(a[1]))
        elif op=='gs': gs['gsname']=str(a[0])
        elif op=='cs': gs['fill_cs']=str(a[0])
        elif op=='CS': gs['stroke_cs']=str(a[0])
        elif op in('sc','scn'): gs['fill']=tuple(float(x) for x in a if not isinstance(x,pikepdf.Name))
        elif op in('SC','SCN'): gs['stroke']=tuple(float(x) for x in a if not isinstance(x,pikepdf.Name))
        elif op=='g': gs['fill_cs']='DeviceGray'; gs['fill']=(float(a[0]),)
        elif op=='G': gs['stroke_cs']='DeviceGray'; gs['stroke']=(float(a[0]),)
        elif op=='rg': gs['fill_cs']='DeviceRGB'; gs['fill']=tuple(float(x) for x in a)
        elif op=='RG': gs['stroke_cs']='DeviceRGB'; gs['stroke']=tuple(float(x) for x in a)
        elif op=='k': gs['fill_cs']='DeviceCMYK'; gs['fill']=tuple(float(x) for x in a)
        elif op=='K': gs['stroke_cs']='DeviceCMYK'; gs['stroke']=tuple(float(x) for x in a)
        elif op in('m','l'):
            if path_start is None: path_start=i
            x,y=float(a[0]),float(a[1]); pts.append(apply(gs['ctm'],x,y)); cur=(x,y)
            if op=='m': nsub+=1
        elif op=='c':
            if path_start is None: path_start=i
            for j in (0,2,4): pts.append(apply(gs['ctm'],float(a[j]),float(a[j+1])))
            cur=(float(a[4]),float(a[5]))
        elif op in('v','y'):
            if path_start is None: path_start=i
            for j in (0,2): pts.append(apply(gs['ctm'],float(a[j]),float(a[j+1])))
            cur=(float(a[2]),float(a[3]))
        elif op=='re':
            if path_start is None: path_start=i
            x,y,w,h=[float(v) for v in a]; has_re=True; nsub+=1
            for (px,py) in ((x,y),(x+w,y),(x+w,y+h),(x,y+h)): pts.append(apply(gs['ctm'],px,py))
        elif op=='h': pass
        elif op in('W','W*'): pending_clip=op
        elif op in('f','F','f*','S','s','B','B*','b','b*','n'):
            if pts:
                xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
                rec={'start':path_start,'end':i,'op':op,'clip':pending_clip,'bbox':(min(xs),min(ys),max(xs),max(ys)),'layer':layer,
                     'fill_cs':gs['fill_cs'],'fill':gs['fill'],'stroke_cs':gs['stroke_cs'],'stroke':gs['stroke'],'lw':gs['lw'],'dash':gs['dash'],
                     'ctm':gs['ctm'],'nsub':nsub,'has_re':has_re,'npts':len(pts),'depth':len(stack),'gs':gs['gsname'],'cap':gs['cap'],'join':gs['join']}
                out.append(rec)
            pts=[]; path_start=None; nsub=0; has_re=False; pending_clip=None
        elif op=='Do':
            m=gs['ctm']; c=[apply(m,x,y) for x,y in ((0,0),(1,0),(1,1),(0,1))]
            xs=[p[0] for p in c]; ys=[p[1] for p in c]
            out.append({'start':i,'end':i,'op':'Do','name':str(a[0]),'bbox':(min(xs),min(ys),max(xs),max(ys)),'layer':layer,'ctm':m,'depth':len(stack)})
        elif op=='BT': text_obj={'start':i,'layer':layer,'strs':[],'tm':None,'font':None,'ctm':gs['ctm'],'fill_cs':gs['fill_cs'],'fill':gs['fill']}
        elif op=='ET':
            text_obj['end']=i; text_obj['op']='TEXT'; out.append(text_obj); text_obj=None
        elif op=='Tf' and text_obj is not None: text_obj['font']=(str(a[0]),float(a[1]))
        elif op=='Tm' and text_obj is not None:
            if text_obj['tm'] is None: text_obj['tm']=tuple(float(x) for x in a)
        elif op in('Tj','TJ') and text_obj is not None:
            if op=='Tj': text_obj['strs'].append(bytes(a[0]))
            else: text_obj['strs'].append(b''.join(bytes(x) for x in a[0] if isinstance(x,pikepdf.String)))
    return out

if __name__=='__main__':
    pdf=pikepdf.open(sys.argv[1]); p=pdf.pages[0]
    ops=pikepdf.parse_content_stream(p)
    objs=walk(ops)
    import collections
    print('objects',len(objs))
    by=collections.Counter((o['layer'],o['op'],o.get('fill_cs'),o.get('fill'),o.get('stroke_cs') if o['op'] in('S','s','B') else None, o.get('stroke') if o['op'] in('S','s','B') else None) for o in objs)
    for k,v in sorted(by.items(), key=lambda kv:str(kv[0])): print(v,k)
