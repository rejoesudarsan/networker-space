from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/fourthspace-identity/v2-wordmarks"
OUT.mkdir(parents=True, exist_ok=True)
FONT_DIR = ROOT / "tmp/fourthspace-logo"
INK = "#191714"
ENAMEL = "#F7F2E8"
RED = "#C74328"
GREEN = "#174F47"
YELLOW = "#F2B824"


class Face:
    def __init__(self, filename):
        self.font = TTFont(FONT_DIR / filename)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm

    def width(self, text, height, tracking=0):
        scale = height / self.upm
        return sum(self.glyphs[self.cmap[ord(c)]].width * scale for c in text) + max(0,len(text)-1)*tracking*height

    def draw(self, text, x, y, height, color, tracking=0):
        scale = height / self.upm
        cursor = x
        parts = []
        for char in text:
            glyph = self.glyphs[self.cmap[ord(char)]]
            pen = SVGPathPen(self.glyphs)
            glyph.draw(pen)
            parts.append(f'<path transform="translate({cursor:.3f} {y:.3f}) scale({scale:.7f} {-scale:.7f})" d="{pen.getCommands()}"/>')
            cursor += glyph.width * scale + tracking * height
        return f'<g fill="{color}" aria-label="{escape(text)}">' + ''.join(parts) + '</g>'

    def centered(self, text, cx, y, height, color, tracking=0):
        return self.draw(text, cx-self.width(text,height,tracking)/2, y, height, color, tracking)


SHRIKHAND = Face("Shrikhand-Regular.ttf")
ANTON = Face("Anton-Regular.ttf")
BODONI = Face("BodoniModa.ttf")


def document(w,h,body,title,bg=None):
    ground = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title"><title id="title">{escape(title)}</title>{ground}{body}</svg>\n'''


def warm():
    body = SHRIKHAND.centered("fourthspace",600,180,142,RED,-0.018)
    body += f'<path d="M386 246H814" stroke="{INK}" stroke-width="5"/>'
    body += f'<circle cx="600" cy="246" r="10" fill="{YELLOW}" stroke="{INK}" stroke-width="4"/>'
    return document(1200,285,body,"Fourthspace warm expressive wordmark")


def punch():
    top = ANTON.centered("4TH",600,226,260,INK,0.015)
    bottom = ANTON.centered("SPACE",600,380,166,INK,0.075)
    body = top + bottom
    return document(1200,440,body,"Fourthspace condensed 4th Space wordmark")


def house():
    body = f'<path d="M400 54L70 318V686H306V558H494V686H730V318Z" fill="none" stroke="{INK}" stroke-width="28" stroke-linejoin="miter"/>'
    body += ANTON.centered("4TH",400,355,220,INK,0.015)
    body += ANTON.centered("SPACE",400,522,145,INK,0.075)
    return document(800,740,body,"Fourthspace 4th Space house wordmark")


def elegant():
    body = BODONI.centered("Fourthspace",600,170,148,GREEN,-0.025)
    body += f'<path d="M322 242H878" stroke="{GREEN}" stroke-width="2"/>'
    body += ANTON.centered("HSR  /  BENGALURU",600,287,27,GREEN,0.14)
    return document(1200,325,body,"Fourthspace elegant editorial wordmark")


for filename, fn in [("d-warm-expressive.svg",warm),("e-4th-space.svg",punch),("e-4th-space-house.svg",house),("f-editorial.svg",elegant)]:
    (OUT / filename).write_text(fn())

sheet = []
sheet.append(f'<text x="70" y="72" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="{INK}">FOURTHSPACE / WORDMARK STUDIES</text>')
sheet.append(f'<text x="70" y="106" font-family="Arial, sans-serif" font-size="18" fill="{INK}">No symbols. Three different voices.</text>')
rows = [
    (150,340,ENAMEL,"D / WARM + EXPRESSIVE",warm,"Friendly, rounded lettering with a hand-painted Indian signboard spirit."),
    (520,550,YELLOW,"E / TALL + PUNCHY",punch,"A compressed poster wordmark. Direct, urban, impossible to miss."),
    (1100,390,"#E7EEE8","F / EDITORIAL + QUIET",elegant,"High-contrast lettering for a more private, cultured members’ house."),
]
for y,h,bg,label,fn,desc in rows:
    sheet.append(f'<rect x="40" y="{y}" width="1520" height="{h}" fill="{bg}"/>')
    sheet.append(f'<text x="70" y="{y+42}" font-family="Arial, sans-serif" font-size="17" font-weight="700" letter-spacing="2" fill="{INK}">{label}</text>')
    art = fn()
    art_body = art.split('<title id="title">',1)[1].split('</title>',1)[1].rsplit('</svg>',1)[0]
    viewbox = art.split('viewBox="0 0 ',1)[1].split('"',1)[0]
    w,h0 = map(float,viewbox.split())
    target_w = 1320 if label.startswith("E") == False else 700
    scale = min(target_w/w,(h-120)/h0)
    dx = 800-w*scale/2
    dy = y+68+(h-90-h0*scale)/2
    sheet.append(f'<g transform="translate({dx} {dy}) scale({scale})">{art_body}</g>')
    sheet.append(f'<text x="70" y="{y+h-20}" font-family="Arial, sans-serif" font-size="18" fill="{INK}">{escape(desc)}</text>')
(OUT / "fourthspace-wordmarks-v2.svg").write_text(document(1600,1530,''.join(sheet),"Fourthspace wordmark studies, second round", "#D8D4CC"))
print("Generated v2 wordmarks")
