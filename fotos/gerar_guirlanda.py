"""Gera uma foto de guirlanda de Natal (1080x1440) sobre fundo azul com bokeh."""
import math, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

random.seed(7); np.random.seed(7)
W, H = 1080, 1440
S = 2                      # supersampling
w, h = W * S, H * S
CX, CY, R = 540 * S, 845 * S, 280 * S   # centro e raio médio da guirlanda
TH = 115 * S                            # espessura

def clamp(v): return max(0, min(255, int(v)))

# ---------- fundo: parede azul + luz quente desfocada ----------
y = np.linspace(0, 1, h)[:, None]; x = np.linspace(0, 1, w)[None, :]
top = np.array([22, 40, 62]); bot = np.array([38, 62, 88])
bg = top + (bot - top) * y[..., None]
d = np.sqrt((x - 0.55) ** 2 + ((y - 0.55) * 1.2) ** 2)
bg = bg * (1.15 - 0.55 * d[..., None])
bg += np.random.normal(0, 3, (h, w, 1))
base = Image.fromarray(np.clip(bg, 0, 255).astype("uint8"), "RGB")

bok = Image.new("RGBA", (w, h), (0, 0, 0, 0)); bd = ImageDraw.Draw(bok)
for _ in range(70):
    bx = random.uniform(0, w); by = random.uniform(0, h * 0.75)
    r = random.uniform(18, 60) * S
    c = random.choice([(255, 196, 110), (255, 170, 80), (255, 225, 160), (180, 210, 255)])
    bd.ellipse([bx - r, by - r, bx + r, by + r], fill=c + (random.randint(40, 110),))
bok = bok.filter(ImageFilter.GaussianBlur(14 * S))
base = Image.alpha_composite(base.convert("RGBA"), bok)

# ---------- sombra da guirlanda ----------
sh = Image.new("L", (w, h), 0); sd = ImageDraw.Draw(sh)
ro, ri = R + TH * 0.75, R - TH * 0.75
off = 40 * S
sd.ellipse([CX - ro, CY - ro + off, CX + ro, CY + ro + off], fill=170)
sd.ellipse([CX - ri, CY - ri + off, CX + ri, CY + ri + off], fill=0)
sh = sh.filter(ImageFilter.GaussianBlur(45 * S))
base = Image.composite(Image.new("RGBA", (w, h), (5, 12, 20, 255)), base, sh)

# ---------- galhos de pinheiro ----------
LIGHT = np.array([-0.55, -0.83])   # luz vindo de cima/esquerda

def sprig(dr, ang, radial, length, depth):
    """Desenha um raminho com agulhas."""
    px = CX + math.cos(ang) * (R + radial); py = CY + math.sin(ang) * (R + radial)
    # direção: tangente com variação
    t = ang + math.pi / 2 * random.choice([1, -1]) + random.uniform(-0.9, 0.9)
    dx, dy = math.cos(t), math.sin(t)
    # luz: normal "para fora" da superfície do toro
    nrm = np.array([math.cos(ang), math.sin(ang)]) * (radial / (TH * 0.8))
    lum = 0.55 + 0.45 * float(np.dot(nrm, LIGHT)) + depth * 0.35
    lum = max(0.25, min(1.25, lum))
    n = int(length / (5 * S))
    stem_w = max(1, int(1.6 * S))
    for i in range(n):
        f = i / max(1, n - 1)
        sx = px + dx * length * f; sy = py + dy * length * f
        nl = (13 - 5 * f) * S * random.uniform(0.8, 1.15)
        for side in (1, -1):
            a = t + side * random.uniform(0.75, 1.15) + side * 0.25 * f
            ex = sx + math.cos(a) * nl; ey = sy + math.sin(a) * nl
            g = random.uniform(0.75, 1.15) * lum
            tip = f > 0.8
            col = (clamp((22 + (30 if tip else 0)) * g), clamp((62 + (40 if tip else 0)) * g),
                   clamp((40 + (12 if tip else 0)) * g), 255)
            dr.line([sx, sy, ex, ey], fill=col, width=max(1, int(2.3 * S)))
    dr.line([px, py, px + dx * length, py + dy * length], fill=(60, 45, 30, 255), width=stem_w)

layers = []
for depth, count, blur in ((0.0, 1900, 1.4), (0.25, 1700, 0.6), (0.5, 1300, 0)):
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    for _ in range(count):
        ang = random.uniform(0, 2 * math.pi)
        radial = random.gauss(0, TH * 0.32) * (1 - depth * 0.3)
        sprig(dr, ang, radial, random.uniform(40, 85) * S, depth)
    if blur: lay = lay.filter(ImageFilter.GaussianBlur(blur * S))
    base = Image.alpha_composite(base, lay)

# ---------- enfeites ----------
deco = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dd = ImageDraw.Draw(deco)

def sphere(cx, cy, r, color, spec=1.0):
    """Esfera com sombreado radial e brilho especular."""
    steps = int(r)
    for k in range(steps, 0, -1):
        f = k / steps
        sx = cx - r * 0.35 * (1 - f); sy = cy - r * 0.35 * (1 - f)
        c = tuple(clamp(cc * (0.35 + 0.85 * (1 - f) ** 0.7)) for cc in color)
        dd.ellipse([sx - r * f, sy - r * f, sx + r * f, sy + r * f], fill=c + (255,))
    hr = r * 0.28
    dd.ellipse([cx - r * 0.45 - hr, cy - r * 0.45 - hr * 0.7, cx - r * 0.45 + hr, cy - r * 0.45 + hr * 0.7],
               fill=(255, 255, 240, int(200 * spec)))

def pinecone(cx, cy, size, ang):
    pc = Image.new("RGBA", (int(size * 2.4), int(size * 2.4)), (0, 0, 0, 0)); pd = ImageDraw.Draw(pc)
    c = size * 1.2
    for row in range(9):
        yy = c - size * 0.85 + row * size * 0.2
        ww = size * 0.55 * math.sin(math.pi * (row + 1) / 10)
        for k in range(-2, 3):
            xx = c + k * ww * 0.42
            g = 0.6 + 0.4 * (1 - row / 9)
            pd.ellipse([xx - ww * 0.28, yy - size * 0.13, xx + ww * 0.28, yy + size * 0.13],
                       fill=(clamp(120 * g), clamp(78 * g), clamp(45 * g), 255),
                       outline=(clamp(55 * g), clamp(32 * g), 18, 255), width=max(1, S))
    pc = pc.rotate(math.degrees(ang), resample=Image.BICUBIC)
    deco.alpha_composite(pc, (int(cx - pc.width / 2), int(cy - pc.height / 2)))

def berries(cx, cy, n=5):
    for _ in range(n):
        bx = cx + random.uniform(-18, 18) * S; by = cy + random.uniform(-18, 18) * S
        sphere(bx, by, random.uniform(7, 10) * S, (210, 25, 30), 0.9)

pts = sorted(random.sample(range(0, 360, 10), 30))
for i, deg in enumerate(pts):
    a = math.radians(deg + random.uniform(-4, 4))
    rr = R + random.uniform(-0.45, 0.45) * TH
    x0, y0 = CX + math.cos(a) * rr, CY + math.sin(a) * rr
    kind = i % 3
    if kind == 0:
        pinecone(x0, y0, random.uniform(34, 44) * S, a + math.pi / 2 + random.uniform(-0.5, 0.5))
    elif kind == 1:
        berries(x0, y0, random.randint(4, 7))
    else:
        sphere(x0, y0, random.uniform(20, 28) * S, random.choice([(230, 180, 70), (200, 30, 40), (235, 230, 220)]))

# laço vermelho de veludo (posição ~ 8h)
ba = math.radians(135); bx, by = CX + math.cos(ba) * R, CY + math.sin(ba) * R
bow = Image.new("RGBA", (w, h), (0, 0, 0, 0)); bw = ImageDraw.Draw(bow)
def loop(sgn):
    # alça: elipses concêntricas do escuro (borda) ao claro (topo)
    for k in range(30, 0, -1):
        f = k / 30
        cx0 = bx + sgn * 62 * S; cy0 = by - 8 * S - (1 - f) * 10 * S
        rx, ry = 62 * S * f, 40 * S * f
        c = (clamp(95 + 120 * (1 - f) ** 0.6), clamp(6 + 30 * (1 - f) ** 2), clamp(16 + 28 * (1 - f) ** 2), 255)
        bw.ellipse([cx0 - rx, cy0 - ry, cx0 + rx, cy0 + ry], fill=c)
    # dobra interna escura
    bw.ellipse([bx + sgn * 30 * S - 18 * S, by - 14 * S, bx + sgn * 30 * S + 18 * S, by + 10 * S], fill=(80, 4, 12, 255))
for sgn in (-1, 1):
    for k in range(12, 0, -1):
        f = k / 12; c = (clamp(110 + 70 * (1 - f)), 10, 22, 255)
        bw.polygon([(bx + sgn * 6 * S, by), (bx + sgn * (18 + 30 * f) * S, by + 120 * S),
                    (bx + sgn * (52 + 10 * f) * S, by + 108 * S)], fill=c)
for sgn in (-1, 1): loop(sgn)
for k in range(14, 0, -1):
    f = k / 14; c = (clamp(120 + 90 * (1 - f)), clamp(10 + 25 * (1 - f)), 24, 255)
    bw.ellipse([bx - 22 * S * f, by - 22 * S * f - 4 * S, bx + 22 * S * f, by + 20 * S * f - 4 * S], fill=c)
bow = bow.filter(ImageFilter.GaussianBlur(1.0 * S))
deco = Image.alpha_composite(deco, bow)
dsh = deco.split()[3].filter(ImageFilter.GaussianBlur(8 * S))
shadow = Image.new("RGBA", (w, h), (0, 10, 0, 0)); shadow.putalpha(dsh.point(lambda v: v * 0.6))
base = Image.alpha_composite(base, shadow.transform((w, h), Image.AFFINE, (1, 0, -6 * S, 0, 1, -10 * S)))
base = Image.alpha_composite(base, deco)

# luzinhas (pisca-pisca) sobre a guirlanda
glow = Image.new("RGBA", (w, h), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
core = Image.new("RGBA", (w, h), (0, 0, 0, 0)); cd = ImageDraw.Draw(core)
for k in range(46):
    a = 2 * math.pi * k / 46 + random.uniform(-0.05, 0.05)
    rr = R + math.sin(k * 1.7) * TH * 0.4
    lx, ly = CX + math.cos(a) * rr, CY + math.sin(a) * rr
    gd.ellipse([lx - 22 * S, ly - 22 * S, lx + 22 * S, ly + 22 * S], fill=(255, 190, 90, 120))
    cd.ellipse([lx - 4 * S, ly - 4 * S, lx + 4 * S, ly + 4 * S], fill=(255, 245, 210, 255))
base = Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(12 * S)))
base = Image.alpha_composite(base, core.filter(ImageFilter.GaussianBlur(1.2 * S)))

out = base.convert("RGB").resize((W, H), Image.LANCZOS)
out = out.filter(ImageFilter.UnsharpMask(radius=1.2, percent=40, threshold=2))
out.save(sys.argv[1] if len(sys.argv) > 1 else "guirlanda.jpg", quality=92)
