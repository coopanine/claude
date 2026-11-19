import numpy as np, pymupdf as fitz
from scipy import ndimage
PT = 72/25.4; Z = 60
def raster(pdf, x0, y0, x1, y1):
    pg = fitz.open(pdf)[0]
    rr = fitz.Rect((x0+27)*PT, (y0+15.5)*PT, (x1+27)*PT, (y1+15.5)*PT)
    pix = pg.get_pixmap(matrix=fitz.Matrix(Z, Z), clip=rr, colorspace=fitz.csGRAY)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width) < 128
def stroke(mask):
    dt = ndimage.distance_transform_edt(mask); mx = ndimage.maximum_filter(dt, size=5)
    ridge = (dt == mx) & (dt > 2)
    return 2 * np.median(dt[ridge]) / (Z * PT), mask.sum() / (Z * PT) ** 2
