from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/fourthspace-identity"
FONT = TTFont(ROOT / "tmp/fourthspace-logo/Bungee-Regular.ttf")
GLYPHS = FONT.getGlyphSet()
CMAP = FONT.getBestCmap()
UPM = FONT["head"].unitsPerEm
COLORS = {"marigold":"#EBA21C", "sindoor":"#C2361E", "peacock":"#0B5E57", "indigo":"#24306E", "enamel":"#F4EEE1", "ink":"#16130F"}


def wordmark(text, x, y, height, color, tracking=0.01):
    scale = height / UPM
    cursor = x
    parts = []
    for char in text:
        glyph_name = CMAP[ord(char)]
        glyph = GLYPHS[glyph_name]
        pen = SVGPathPen(GLYPHS)
        glyph.draw(pen)
        parts.append(f'<path transform="translate({cursor:.2f} {y:.2f}) scale({scale:.6f} {-scale:.6f})" d="{pen.getCommands()}"/>')
        cursor += glyph.width * scale + height * tracking
    return f'<g fill="{color}" aria-label="{escape(text)}">' + "".join(parts) + '</g>', cursor - x


def mark_a(x, y, size=240, mono=None):
    s = size / 240
    shapes = [
        ("M104 0H12Q0 0 0 12V104H40V48Q40 40 48 40H104Z", "marigold"),
        ("M136 0H228Q240 0 240 12V104H200V48Q200 40 192 40H136Z", "sindoor"),
        ("M0 136V228Q0 240 12 240H104V200H48Q40 200 40 192V136Z", "peacock"),
        ("M240 136V228Q240 240 228 240H136V200H192Q200 200 200 192V136Z", "indigo"),
    ]
    return f'<g transform="translate({x} {y}) scale({s})">' + ''.join(f'<path d="{d}" fill="{mono or COLORS[c]}"/>' for d,c in shapes) + '</g>'


def mark_b(x, y, size=240, mono=None):
    s = size / 240
    shapes = [
        ("M0 0H240V48H0Z", "marigold"),
        ("M48 48H192V104H48Z", "sindoor"),
        ("M0 48H48V240H0Z M48 192H96V240H48Z", "peacock"),
        ("M192 48H240V240H192Z M144 192H192V240H144Z", "indigo"),
    ]
    return f'<g transform="translate({x} {y}) scale({s})">' + ''.join(f'<path d="{d}" fill="{mono or COLORS[c]}"/>' for d,c in shapes) + '</g>'


def mark_c(x, y, size=240, mono=None):
    s = size / 240
    shapes = [
        ("M24 0H216V40H128V56H104V40H24Z", "marigold"),
        ("M8 64H200V104H128V120H104V104H8Z", "sindoor"),
        ("M24 128H216V168H128V184H104V168H24Z", "peacock"),
        ("M8 192H200V240H8Z M104 240V208H128V240Z", "indigo"),
    ]
    return f'<g transform="translate({x} {y}) scale({s})" fill-rule="evenodd">' + ''.join(f'<path d="{d}" fill="{mono or COLORS[c]}"/>' for d,c in shapes) + '</g>'


def svg_document(width, height, body, title, bg=None):
    background = f'<rect width="{width}" height="{height}" fill="{bg}"/>' if bg else ''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">Fourthspace logo concept with a four-part spatial symbol and outlined Bungee wordmark.</desc>
{background}{body}
</svg>\n'''


def lockup(mark, name, mono=None, stacked=False):
    if stacked:
        body = mark(280, 30, 240, mono)
        wm, _ = wordmark("FOURTHSPACE", 58, 390, 70, mono or COLORS["ink"], 0.005)
        body += wm
        return svg_document(800, 440, body, f"Fourthspace {name} stacked logo")
    body = mark(24, 20, 200, mono)
    wm, _ = wordmark("FOURTHSPACE", 268, 166, 96, mono or COLORS["ink"], 0.005)
    body += wm
    return svg_document(1450, 240, body, f"Fourthspace {name} horizontal logo")


for letter, mark, name in [("a",mark_a,"four-corners"),("b",mark_b,"open-threshold"),("c",mark_c,"four-floors")]:
    (OUT / f"concept-{letter}-{name}.svg").write_text(lockup(mark, name))
    (OUT / f"concept-{letter}-{name}-mono.svg").write_text(lockup(mark, name, COLORS["ink"]))

sheet = []
sheet.append(wordmark("FOURTHSPACE", 72, 126, 72, COLORS["ink"])[0])
sheet.append(f'<text x="74" y="178" fill="{COLORS["peacock"]}" font-family="Arial, sans-serif" font-size="24" font-weight="700" letter-spacing="2">FOUR SPACES. ONE OPEN HOUSE.</text>')
rows = [
    ("A", "FOUR CORNERS", "Four rooms make a meeting place. Open on every side.", mark_a),
    ("B", "OPEN THRESHOLD", "A house plan with a clear way in. Hospitality built into the mark.", mark_b),
    ("C", "FOUR FLOORS", "Four distinct levels, connected by one continuous opening.", mark_c),
]
for i,(letter,name,desc,mark) in enumerate(rows):
    y = 230 + i*340
    sheet.append(f'<rect x="48" y="{y}" width="1504" height="300" rx="12" fill="{COLORS["enamel"]}" stroke="{COLORS["ink"]}" stroke-width="3"/>')
    sheet.append(mark(92,y+42,216))
    sheet.append(f'<text x="370" y="{y+72}" fill="{COLORS["sindoor"]}" font-family="Arial, sans-serif" font-size="22" font-weight="800" letter-spacing="2">{letter} / {name}</text>')
    sheet.append(wordmark("FOURTHSPACE", 368, y+176, 82, COLORS["ink"], 0.005)[0])
    sheet.append(f'<text x="370" y="{y+226}" fill="{COLORS["ink"]}" font-family="Arial, sans-serif" font-size="23">{escape(desc)}</text>')
sheet.append(f'<rect x="48" y="1260" width="1504" height="220" rx="12" fill="{COLORS["indigo"]}"/>')
sheet.append(mark_a(92,1300,140,COLORS["enamel"]))
sheet.append(wordmark("FOURTHSPACE", 286, 1404, 82, COLORS["enamel"], 0.005)[0])
sheet.append(f'<text x="1190" y="1388" fill="{COLORS["marigold"]}" font-family="Arial, sans-serif" font-size="20" font-weight="700">ONE-COLOUR TEST</text>')
(OUT / "fourthspace-logo-concepts.svg").write_text(svg_document(1600,1530,''.join(sheet),"Fourthspace logo concept sheet", "#EBA21C"))

body = mark_a(24,20,200) + wordmark("FOURTHSPACE",268,166,96,COLORS["ink"],0.005)[0]
(OUT / "fourthspace-logo-primary.svg").write_text(svg_document(1450,240,body,"Fourthspace primary logo concept"))
(OUT / "fourthspace-symbol.svg").write_text(svg_document(288,288,mark_a(24,24,240),"Fourthspace symbol concept"))
print("Generated", len(list(OUT.glob('*.svg'))), "SVG files")
