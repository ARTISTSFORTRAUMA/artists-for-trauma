"""Apply tune-panel photo adjustments to an image file (same maths as tune.js).
python3 tone.py <image.jpg> br ct hl sh sa wa   (each -100..100)"""
import sys, numpy as np
from PIL import Image, ImageCms
def curve(x, br, ct, hl, sh):
    x = x * 2 ** (br / 100)
    x = (x - .5) * (1 + ct / 100) + .5
    x = x + (sh / 100) * .4 * (1 - np.clip(x, 0, 1)) ** 3
    x = x + (hl / 100) * .4 * np.clip(x, 0, 1) ** 3
    return np.clip(x, 0, 1)
def apply(path, br, ct, hl, sh, sa, wa):
    im = Image.open(path); alpha = im.getchannel('A') if 'A' in im.getbands() else None; icc = im.info.get('icc_profile'); a = np.asarray(im.convert('RGB')).astype(np.float64) / 255
    lut = curve(np.arange(256) / 255, br, ct, hl, sh)           # 256-entry table, interpolated like SVG feFuncX type=table
    idx = a * 255; lo = np.floor(idx).astype(int); hi = np.minimum(lo + 1, 255); f = idx - lo
    a = lut[lo] * (1 - f) + lut[hi] * f
    s = 1 + sa / 100                                            # SVG feColorMatrix type=saturate
    M = np.array([[.213 + .787 * s, .715 - .715 * s, .072 - .072 * s],
                  [.213 - .213 * s, .715 + .285 * s, .072 - .072 * s],
                  [.213 - .213 * s, .715 - .715 * s, .072 + .928 * s]])
    a = np.clip(a @ M.T, 0, 1)
    w = wa / 100 * .1; a[..., 0] *= 1 + w; a[..., 2] *= 1 - w
    out = Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8))
    if alpha is not None:                                       # cut-outs keep their transparency
        out.putalpha(alpha); out.save(path, 'WEBP' if path.lower().endswith('.webp') else 'PNG', quality=88, method=6); return
    out.save(path, 'JPEG', quality=86, optimize=True, progressive=True, icc_profile=icc or ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
if __name__ == '__main__':
    apply(sys.argv[1], *[float(v) for v in sys.argv[2:8]])
