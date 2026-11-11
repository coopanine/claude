"""sub-pixel registration of a built label.pdf against the designers' screenshot (shot.png)"""
import numpy as np, pymupdf, sys
from PIL import Image
from labelkit import PAGE_MM, PT
SX=7.4795; SY=7.4586; X0=191.01; Y0=93.5      # screenshot: px per mm and index coords of label origin
K=8
shot=np.array(Image.open('shot.png').convert('L')).astype(float)
def hires(pdf, i0, j0, nx, ny, pad=3):
    """render pdf so that hi-res block [K*k, K*k+K) corresponds to screenshot pixel (i0+k); includes pad screenshot px around"""
    l=(i0-pad-0.5-X0)/SX; t=(j0-pad-0.5-Y0)/SY
    r=l+(nx+2*pad)/SX; b=t+(ny+2*pad)/SY
    pl,ptp,pr,pb=PAGE_MM
    doc=pymupdf.open(pdf); pg=doc[0]
    clip=pymupdf.Rect((l-pl)*PT,(t-ptp)*PT,(r-pl)*PT,(b-ptp)*PT)
    zx=K*SX/PT; zy=K*SY/PT
    pix=pg.get_pixmap(matrix=pymupdf.Matrix(zx,zy),clip=clip,alpha=False,colorspace=pymupdf.csGRAY)
    a=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width).astype(float)
    return a
def reg(pdf, roi_mm, search=2.0, verbose=False):
    l,t,r,b=roi_mm
    i0=int(round(l*SX+X0)); i1=int(round(r*SX+X0)); j0=int(round(t*SY+Y0)); j1=int(round(b*SY+Y0))
    nx=i1-i0; ny=j1-j0; pad=int(np.ceil(search))+1
    H=hires(pdf,i0,j0,nx,ny,pad)
    target=shot[j0:j1,i0:i1]
    best=None; S=int(search*K)
    # normalise contrast: fit target ~ a*render+b
    for dy in range(-S,S+1):
        for dx in range(-S,S+1):
            y0=pad*K-dy; x0=pad*K-dx
            sub=H[y0:y0+ny*K, x0:x0+nx*K]
            if sub.shape!=(ny*K,nx*K): continue
            ds=sub.reshape(ny,K,nx,K).mean(axis=(1,3))
            A=np.vstack([ds.ravel(),np.ones(ds.size)]).T
            coef,res,_,_=np.linalg.lstsq(A,target.ravel(),rcond=None)
            err=float(((A@coef-target.ravel())**2).mean())
            if best is None or err<best[0]: best=(err,dx,dy)
    err,dx,dy=best
    # parabolic refinement skipped; resolution 1/8 px
    return {'dx_mm':dx/(K*SX),'dy_mm':dy/(K*SY),'rmse':err**0.5,'dx_px':dx/K,'dy_px':dy/K}
if __name__=='__main__':
    pdf=sys.argv[1]
    rois={'control facts title rows':(6.5,59.8,48,72.0),'control facts mid rows':(6.5,92,47.5,111.5),'control DV footnote':(6.5,127.2,30,130.8),
          'facts box bottom edge':(8,130.9,46,132.1),
          'other ingredients (2 lines)':(6.6,132.7,41,138.9),'distributed line 1':(6.6,140.3,39.5,143.05),'distributed line 2':(6.6,142.95,33.5,145.6),
          'control testide':(66,33,124,46),'control statue':(73,68,117,128),'control protocol title':(142,61,178,66)}
    for name,roi in rois.items():
        print(f"{name:32s}", {k:round(v,4) for k,v in reg(pdf,roi).items()})
