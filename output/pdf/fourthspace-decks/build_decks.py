from pathlib import Path
import json
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
ASSETS = ROOT / 'assets'
FONTS = ASSETS / 'fonts'
HOUSE = PROJECT / 'docs' / 'house-understanding' / 'img'
CONFIG = json.loads((ROOT / 'model.json').read_text())
ASSETS.mkdir(parents=True, exist_ok=True)
FONTS.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720
CREAM = '#F5F1E8'
PAPER = '#FFFCF5'
INK = '#18251F'
GREEN = '#244B3F'
SAGE = '#91A99A'
ORANGE = '#B6532F'
LILAC = '#CDC4E3'
SAND = '#D8C9B4'
MUTED = '#627067'
WHITE = '#FFFFFF'
LINE = '#D6D5CA'


font_files = {
    'Display': Path('/System/Library/Fonts/Supplemental/Georgia.ttf'),
    'DisplayBold': Path('/System/Library/Fonts/Supplemental/Georgia Bold.ttf'),
    'Body': Path('/Users/rejoesudarsan/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts/Ubuntu-R.ttf'),
    'BodyBold': Path('/Users/rejoesudarsan/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts/Ubuntu-B.ttf'),
}
for name, path in font_files.items():
    pdfmetrics.registerFont(TTFont(name, str(path)))


def font(path, size):
    return ImageFont.truetype(str(path), size)


def centered(draw, xy, value, face, fill):
    x, y = xy
    box = draw.textbbox((0, 0), value, font=face)
    draw.text((x - (box[2] - box[0]) / 2, y), value, font=face, fill=fill)


def make_cup():
    path = ASSETS / 'cup-concept.png'
    im = PILImage.new('RGB', (1400, 1100), CREAM)
    d = ImageDraw.Draw(im)
    d.ellipse((260, 920, 1150, 1060), fill=SAND)
    d.rounded_rectangle((335, 855, 1070, 1000), 40, fill=LILAC)
    d.rectangle((335, 805, 1070, 900), fill=LILAC)
    d.ellipse((335, 755, 1070, 885), fill='#DDD6EC')
    d.polygon([(490, 260), (920, 260), (865, 875), (545, 875)], fill='#E8E3D8', outline=INK, width=5)
    d.polygon([(515, 500), (895, 500), (860, 840), (550, 840)], fill='#A86B43')
    d.polygon([(515, 500), (895, 500), (880, 650), (530, 650)], fill='#D9B48D')
    d.rounded_rectangle((455, 215, 955, 290), 25, fill=PAPER, outline=INK, width=5)
    d.rectangle((500, 185, 910, 230), fill=PAPER, outline=INK, width=5)
    d.polygon([(480, 465), (930, 465), (905, 705), (505, 705)], fill=PAPER, outline=INK, width=4)
    centered(d, (705, 500), 'FOURTHSPACE', font(font_files['BodyBold'], 30), INK)
    centered(d, (705, 550), 'YOUR', font(font_files['DisplayBold'], 64), INK)
    centered(d, (705, 620), 'BRAND', font(font_files['DisplayBold'], 64), INK)
    d.text((55, 45), 'CUP / CONCEPT 01', font=font(font_files['BodyBold'], 24), fill=INK)
    im.save(path)
    return path


def make_shelf():
    path = ASSETS / 'shelf-concept.png'
    im = PILImage.new('RGB', (1400, 1100), LILAC)
    d = ImageDraw.Draw(im)
    d.text((60, 48), 'FOURTHSPACE HSR / PARTNER MERCHANDISE', font=font(font_files['BodyBold'], 25), fill=INK)
    d.text((60, 100), 'Illustrative stock and shelf layout', font=font(font_files['Body'], 24), fill=INK)
    d.rectangle((0, 850, 1400, 1100), fill=SAND)
    for y in (440, 820):
        d.rectangle((100, y, 1300, y + 32), fill=INK)
        d.rectangle((140, y + 32, 165, y + 92), fill=INK)
        d.rectangle((1235, y + 32, 1260, y + 92), fill=INK)
    d.rectangle((155, 215, 390, 440), fill=GREEN, outline=INK, width=4)
    centered(d, (272, 300), 'NOTEBOOK', font(font_files['BodyBold'], 25), CREAM)
    d.rounded_rectangle((500, 170, 640, 440), 45, fill=PAPER, outline=INK, width=4)
    d.rectangle((530, 135, 610, 185), fill=INK)
    centered(d, (570, 300), 'BOTTLE', font(font_files['BodyBold'], 22), INK)
    d.polygon([(770, 245), (990, 245), (1030, 440), (730, 440)], fill=ORANGE, outline=INK)
    d.arc((805, 155, 955, 320), 180, 360, fill=INK, width=8)
    centered(d, (880, 330), 'TOTE', font(font_files['BodyBold'], 26), CREAM)
    d.rounded_rectangle((1080, 190, 1260, 440), 18, fill=PAPER, outline=ORANGE, width=5)
    centered(d, (1170, 255), 'YOUR', font(font_files['BodyBold'], 24), INK)
    centered(d, (1170, 300), 'BRAND', font(font_files['BodyBold'], 24), INK)
    centered(d, (1170, 355), 'HERE', font(font_files['BodyBold'], 24), ORANGE)
    d.rounded_rectangle((180, 560, 1220, 810), 24, fill=PAPER, outline=INK, width=4)
    centered(d, (700, 600), 'YOUR BRAND HERE', font(font_files['DisplayBold'], 48), INK)
    centered(d, (700, 680), 'APPROVED SPONSOR STOCK', font(font_files['BodyBold'], 26), ORANGE)
    centered(d, (700, 735), 'One agreed bay / voluntary guest distribution', font(font_files['Body'], 25), INK)
    d.text((60, 1010), 'Concept only. Generic product examples; no brand partnership implied.', font=font(font_files['Body'], 21), fill=INK)
    im.save(path)
    return path


def menu_thumb(im, source, x, y, w=116, h=142):
    cup = PILImage.open(ASSETS / 'cups' / source).convert('RGB')
    scale = max(w / cup.width, h / cup.height)
    cup = cup.resize((round(cup.width * scale), round(cup.height * scale)), PILImage.Resampling.LANCZOS)
    left = (cup.width - w) // 2
    top = (cup.height - h) // 2
    cup = cup.crop((left, top, left + w, top + h))
    mask = PILImage.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), 12, fill=255)
    im.paste(cup, (x, y), mask)


def draw_menu_row(im, d, y, drink, company, description, cup, width, highlight=False):
    fg = '#171717'
    muted = '#666662'
    menu_thumb(im, cup, 64, y + 8)
    name_font = font(font_files['BodyBold'], 34)
    badge_font = font(font_files['BodyBold'], 19)
    d.text((214, y + 20), drink, font=name_font, fill=fg)
    name_width = d.textlength(drink, font=name_font)
    badge = f'By {company}'
    badge_width = d.textlength(badge, font=badge_font)
    badge_x = 214 + name_width + 18
    d.rounded_rectangle((badge_x, y + 23, badge_x + badge_width + 26, y + 59), 18, fill=ORANGE if highlight else '#171717')
    d.text((badge_x + 13, y + 30), badge, font=badge_font, fill=PAPER)
    d.text((214, y + 78), description, font=font(font_files['Body'], 22), fill=muted)
    d.text((width - 125, y + 26), 'TBD', font=font(font_files['BodyBold'], 23), fill=fg)
    d.line((214, y + 132, width - 64, y + 132), fill='#DDDDD8', width=1)


def menu_header(d, width, compact=False):
    d.text((64, 56), 'Partner drinks', font=font(font_files['BodyBold'], 52 if not compact else 48), fill='#171717')
    d.text((66, 128), 'Each one co-built with a partner.', font=font(font_files['Body'], 23), fill='#666662')
    pill = 'YOUR BRAND COULD BE NEXT'
    pill_font = font(font_files['BodyBold'], 17)
    pill_width = d.textlength(pill, font=pill_font)
    d.rounded_rectangle((width - pill_width - 100, 126, width - 56, 164), 19, outline=ORANGE, width=2)
    d.text((width - pill_width - 78, 135), pill, font=pill_font, fill=ORANGE)
    d.text((width - 127, 188), 'PRICE', font=font(font_files['Body'], 14), fill='#858581')


def make_menu():
    path = ASSETS / 'opportunity-menu.png'
    im = PILImage.new('RGB', (1200, 1400), SAND)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 1180, 1380), 34, fill='#F8F8F6')
    menu_header(d, 1200)
    rows = [
        ('Prompt & Pour', 'OpenAI', 'Espresso, tonic and orange / partner story QR', 'openai-cup.png'),
        ('Checkout Cold Brew', 'Razorpay', 'Cold brew, vanilla and orange / partner offer QR', 'razorpay-cup.png'),
        ('Blank Page Matcha', 'Notion', 'Matcha, milk and vanilla / partner story QR', 'notion-cup.png'),
        ('The Delivery', 'Postman', 'Filter coffee, cocoa and sea salt / partner offer QR', 'postman-cup.png'),
        ('Your Signature Drink', 'Your Brand', 'Your recipe, story and QR / one founding category', 'your-brand-cup.png'),
    ]
    for i, (drink, company, description, cup) in enumerate(rows):
        draw_menu_row(im, d, 232 + i * 204, drink, company, description, cup, 1200, i == 4)
    d.text((66, 1290), 'Illustrative co-build concepts. No current partnership or endorsement.', font=font(font_files['Body'], 18), fill='#666662')
    im.save(path)
    return path


def make_menu_cover():
    path = ASSETS / 'partner-menu-cover.png'
    im = PILImage.new('RGB', (1200, 1100), CREAM)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 1180, 1080), 34, fill='#F8F8F6')
    menu_header(d, 1200, True)
    rows = [
        ('Prompt & Pour', 'OpenAI', 'Espresso, tonic and orange / partner story QR', 'openai-cup.png'),
        ('Checkout Cold Brew', 'Razorpay', 'Cold brew, vanilla and orange / partner offer QR', 'razorpay-cup.png'),
        ('Your Signature Drink', 'Your Brand', 'Your recipe, story and QR destination', 'your-brand-cup.png'),
    ]
    for i, (drink, company, description, cup) in enumerate(rows):
        draw_menu_row(im, d, 254 + i * 232, drink, company, description, cup, 1200, i == 2)
    d.text((66, 1005), 'Illustrative co-build concepts / no current partnership implied', font=font(font_files['Body'], 18), fill='#666662')
    im.save(path)
    return path


def make_mild_atta_menu():
    path = ASSETS / 'mild-atta-breakfast-menu.png'
    im = PILImage.new('RGB', (1200, 1100), SAND)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 1180, 1080), 34, fill='#F8F8F6')
    d.text((64, 56), 'Founders’ breakfast', font=font(font_files['BodyBold'], 48), fill='#171717')
    d.text((66, 126), 'A daily product trial, built around Mild Atta.', font=font(font_files['Body'], 23), fill='#666662')
    pill = 'MADE USING MILD ATTA'
    pill_font = font(font_files['BodyBold'], 17)
    pill_width = d.textlength(pill, font=pill_font)
    d.rounded_rectangle((1200 - pill_width - 100, 126, 1144, 164), 19, fill=ORANGE)
    d.text((1200 - pill_width - 78, 135), pill, font=pill_font, fill=PAPER)
    d.text((1073, 188), 'PRICE', font=font(font_files['Body'], 14), fill='#858581')
    rows = [
        ('01', 'The Founders’ Breakfast', 'Atta flatbread, seasonal filling and house chutney'),
        ('02', 'The Roti Roll', 'Atta roti, egg or paneer and house chutney'),
        ('03', 'The Morning Special', 'A rotating breakfast serve and approved recipe QR'),
    ]
    for i, (num, name, description) in enumerate(rows):
        y = 254 + i * 232
        d.rounded_rectangle((64, y + 8, 180, y + 150), 12, fill=SAND if i else ORANGE)
        centered(d, (122, y + 54), num, font(font_files['BodyBold'], 38), INK if i else PAPER)
        name_font = font(font_files['BodyBold'], 34)
        d.text((214, y + 20), name, font=name_font, fill='#171717')
        badge_font = font(font_files['BodyBold'], 19)
        badge = 'Made using Mild Atta'
        badge_width = d.textlength(badge, font=badge_font)
        badge_x = 214 + d.textlength(name, font=name_font) + 18
        d.rounded_rectangle((badge_x, y + 23, badge_x + badge_width + 26, y + 59), 18, fill='#171717')
        d.text((badge_x + 13, y + 30), badge, font=badge_font, fill=PAPER)
        d.text((214, y + 78), description, font=font(font_files['Body'], 22), fill='#666662')
        d.text((1075, y + 26), 'TBD', font=font(font_files['BodyBold'], 23), fill='#171717')
        d.line((214, y + 132, 1136, y + 132), fill='#DDDDD8', width=1)
    d.text((66, 1005), 'Illustrative serves only. Recipes, allergens, claims and prices require approval.', font=font(font_files['Body'], 18), fill='#666662')
    im.save(path)
    return path


CUP = make_cup()
SHELF = make_shelf()
MENU = make_menu()
MENU_COVER = make_menu_cover()
MILD_ATTA_MENU = make_mild_atta_menu()

checks = []
current_deck = ''


def rect(c, x, y, w, h, color, radius=0, stroke=None, width=1):
    c.setFillColor(HexColor(color))
    if stroke:
        c.setStrokeColor(HexColor(stroke))
        c.setLineWidth(width)
    else:
        c.setStrokeColor(HexColor(color))
    if radius:
        c.roundRect(x, H - y - h, w, h, radius, fill=1, stroke=1 if stroke else 0)
    else:
        c.rect(x, H - y - h, w, h, fill=1, stroke=1 if stroke else 0)


def text(c, value, x, y, size=20, face='Body', color=INK):
    if current_deck == 'sponsorship' and face == 'DisplayBold':
        face = 'BodyBold'
    c.setFillColor(HexColor(color))
    c.setFont(face, size)
    c.drawString(x, H - y - size * .82, value)
    checks.append((current_deck, c.getPageNumber(), value, x, y, size, pdfmetrics.stringWidth(value, face, size)))


def para(c, value, x, y, width, size=20, color=INK, face='Body', leading=None, max_lines=None):
    if current_deck == 'sponsorship' and face == 'DisplayBold':
        face = 'BodyBold'
    leading = leading or size * 1.35
    lines = []
    for block in value.split('\n'):
        words = block.split()
        line = ''
        for word in words:
            trial = (line + ' ' + word).strip()
            if line and pdfmetrics.stringWidth(trial, face, size) > width:
                lines.append(line)
                line = word
            else:
                line = trial
        if line:
            lines.append(line)
        if not block:
            lines.append('')
    if max_lines and len(lines) > max_lines:
        raise RuntimeError(f'Copy overflow: {value!r} needs {len(lines)} lines, max {max_lines}')
    for i, line in enumerate(lines):
        text(c, line, x, y + i * leading, size, face, color)
    return y + len(lines) * leading


def heading(c, value, x, y, width, size=58, color=INK, face='DisplayBold'):
    return para(c, value, x, y, width, size, color, face, size * .98)


def image(c, source, x, y, w, h, fit='cover'):
    source = Path(source)
    im = PILImage.open(source)
    iw, ih = im.size
    scale = max(w / iw, h / ih) if fit == 'cover' else min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    c.saveState()
    p = c.beginPath()
    p.rect(x, H - y - h, w, h)
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(ImageReader(im), x + (w - dw) / 2, H - y - h + (h - dh) / 2, dw, dh, mask='auto')
    c.restoreState()


def rule(c, x, y, w, color=LINE, width=1):
    rect(c, x, y, w, width, color)


def pill(c, value, x, y, size=13, fill=INK, color=CREAM, stroke=None):
    width = pdfmetrics.stringWidth(value, 'BodyBold', size) + 30
    rect(c, x, y, width, 34, fill, 17, stroke, 1.5)
    text(c, value, x + 15, y + 9, size, 'BodyBold', color)
    return width


def base(c, deck, page, section, bg=CREAM, dark=False):
    global current_deck
    current_deck = deck
    rect(c, 0, 0, W, H, bg)
    fg = CREAM if dark else INK
    text(c, 'FOURTHSPACE', 48, 30, 16, 'BodyBold', fg)
    text(c, section.upper(), 850, 32, 12, 'BodyBold', fg)
    rule(c, 48, 674, 1184, GREEN if dark else LINE)
    text(c, 'FIRST HOUSE  /  HSR LAYOUT  /  OPENING 30 NOVEMBER 2026', 48, 691, 10, 'BodyBold', fg)
    text(c, f'{page:02d} / 10', 1170, 691, 10, 'BodyBold', fg)


def end(c):
    c.showPage()


def photo_note(c, value='Existing house photograph. Proposed use; final layout and capacity subject to review.', color=MUTED):
    text(c, value, 48, 648, 11, 'Body', color)


def stat(c, value, label, x, y, width=240, color=INK):
    text(c, value, x, y, 54, 'DisplayBold', color)
    para(c, label, x, y + 68, width, 16, color, 'Body', 21)


def benefit_row(c, head, body, x, y, width, color=INK):
    rule(c, x, y, width, SAGE if color == CREAM else LINE)
    text(c, head, x, y + 18, 22, 'DisplayBold', color)
    para(c, body, x, y + 52, width, 16, color, 'Body', 22)


def membership_deck():
    path = ROOT / 'Fourthspace-Founder-Membership.pdf'
    c = canvas.Canvas(str(path), pagesize=(W, H), pageCompression=1)
    c.setTitle('Fourthspace | Founder Membership')
    c.setAuthor('HSR Founders Club')
    c.setSubject('Founder-only membership: INR 2 lakh first year, INR 1 lakh annual renewal')

    base(c, 'membership', 1, 'Founder membership', GREEN, True)
    heading(c, 'A house for\nfounders.\nA year of\nmoving forward.', 48, 112, 610, 62, CREAM)
    para(c, 'Trusted relationships, useful asks and offers, and a house that remembers what you are building.', 52, 405, 510, 22, CREAM)
    text(c, '₹2 LAKH FIRST YEAR  /  ₹1 LAKH ANNUAL RENEWAL', 52, 526, 15, 'BodyBold', CREAM)
    text(c, 'FOUNDERS ONLY  /  OPENS 30 NOVEMBER 2026', 52, 558, 13, 'Body', SAND)
    image(c, HOUSE / 'p11.jpg', 685, 82, 547, 560)
    end(c)

    base(c, 'membership', 2, 'The origin')
    heading(c, 'Before the house,\nthere was a club.', 48, 100, 620, 58)
    para(c, 'HSR Founders Club built a habit of bringing founders together around HSR. Fourthspace turns that history into a physical place for repeated professional encounters.', 50, 260, 520, 21)
    image(c, HOUSE / 'p25.jpg', 690, 86, 280, 330)
    image(c, HOUSE / 'p20.jpg', 982, 86, 250, 330)
    stat(c, '120+', 'events hosted', 62, 474, 240)
    stat(c, '≈5,200', 'reported event attendees', 355, 474, 240)
    stat(c, '3,000+', 'founders in the HSR-area directory', 680, 474, 250)
    stat(c, '7,000', 'newsletter signups', 1000, 474, 210)
    text(c, 'HSR Founders Club figures supplied October 2026. These are not Fourthspace operating results or paid-member counts.', 48, 648, 11, 'Body', MUTED)
    end(c)

    base(c, 'membership', 3, 'The membership', GREEN, True)
    heading(c, 'The room is only\nthe beginning.', 48, 96, 620, 62, CREAM)
    para(c, 'Membership is a repeated practice of asking, offering, meeting and returning—not a desk package.', 52, 254, 610, 22, CREAM)
    rows = [
        ('ASK', 'Say what would move your company forward: a pilot, a hire, a technical answer or a customer conversation.'),
        ('OFFER', 'Make your experience useful to another founder. The house gets stronger when members create value for each other.'),
        ('RETURN', 'Follow up, join the next circle, host what you know, and let relationships develop beyond one introduction.'),
    ]
    y = 342
    for head, body in rows:
        text(c, head, 54, y, 25, 'DisplayBold', SAND)
        para(c, body, 230, y + 2, 880, 20, CREAM, 'Body', 27)
        rule(c, 54, y + 74, 1120, SAGE)
        y += 96
    end(c)

    base(c, 'membership', 4, 'What membership includes')
    heading(c, 'A useful year,\nnot a long perk list.', 48, 96, 570, 52)
    benefits = [
        ('Founder house access', '08:00–23:00, subject to room and program schedules.'),
        ('Four room-hours monthly', 'Bookable meeting space; up to two hours per booking.'),
        ('Asks and offers', 'A living member board for founder needs and help.'),
        ('One introduction request monthly', 'Facilitated with consent from both sides; never a guaranteed outcome.'),
        ('Founder programming', 'Four house-led sessions plus up to four member-hosted slots monthly.'),
        ('Two guest passes monthly', 'For meetings and work; event access is stated separately.'),
    ]
    positions = [(50, 268), (650, 268), (50, 382), (650, 382), (50, 496), (650, 496)]
    for (head, body), (x, y) in zip(benefits, positions):
        benefit_row(c, head, body, x, y, 540)
    text(c, 'Monthly allowances do not roll over. Café F&B is paid separately unless an event says otherwise.', 50, 632, 12, 'Body', MUTED)
    end(c)

    base(c, 'membership', 5, 'The house')
    heading(c, 'Four floors.\nDifferent kinds of work.', 48, 92, 580, 48)
    panels = [
        ('p25.jpg', 'GROUND', 'Public café and garden'),
        ('p20.jpg', 'LOWER', 'Founder work and making'),
        ('p11.jpg', 'FIRST', 'Meetings, learning and events'),
        ('p33.jpg', 'SECOND', 'Quiet rooms and small gatherings'),
    ]
    for i, (photo, floor, use) in enumerate(panels):
        x = 48 + i * 300
        image(c, HOUSE / photo, x, 238, 280, 332)
        text(c, floor, x, 588, 14, 'BodyBold')
        para(c, use, x, 614, 270, 16, INK, 'Body', 20)
    end(c)

    base(c, 'membership', 6, 'A day inside')
    heading(c, 'Work by day.\nMeet after six.', 48, 96, 550, 60)
    timeline = [
        ('08:00', 'The public café opens on the ground floor. Founder work begins below and above.'),
        ('DAY', 'Book a room, join a clinic, post an ask, or make an introduction happen.'),
        ('18:00', 'Work stops. Founder circles, learning, selected public events and shared dinners begin.'),
        ('23:00', 'The house closes. The relationships and follow-ups continue between visits.'),
    ]
    y = 276
    for when, body in timeline:
        text(c, when, 50, y, 17, 'BodyBold', ORANGE)
        para(c, body, 150, y, 455, 18, INK, 'Body', 24)
        y += 82
    image(c, HOUSE / 'p28.jpg', 680, 90, 552, 528)
    photo_note(c)
    end(c)

    base(c, 'membership', 7, 'The opportunity system', GREEN, True)
    heading(c, 'Opportunity needs\na next step.', 48, 96, 600, 60, CREAM)
    steps = [
        ('1', 'TELL THE HOUSE', 'What are you building? What do you need? What can you offer?'),
        ('2', 'MAKE IT VISIBLE', 'Add an ask or offer to the opt-in member system.'),
        ('3', 'ACCEPT A MATCH', 'Both people agree before an introduction is made.'),
        ('4', 'FOLLOW THROUGH', 'Meet, act, and report only the outcome that actually happened.'),
    ]
    y = 286
    for num, head, body in steps:
        text(c, num, 54, y, 40, 'DisplayBold', SAND)
        text(c, head, 120, y + 2, 20, 'BodyBold', CREAM)
        para(c, body, 440, y + 2, 690, 19, CREAM, 'Body', 25)
        y += 82
    text(c, 'One facilitated introduction request per member per month. No funding, hiring, customer or cofounder guarantee.', 52, 636, 12, 'Body', SAND)
    end(c)

    base(c, 'membership', 8, 'Trust and eligibility')
    heading(c, 'Founders are members.\nNot inventory.', 48, 96, 650, 52)
    para(c, 'The value of the house depends on being able to participate without being harvested, pitched or displayed.', 52, 240, 540, 21)
    rules = [
        'Founder status confirmed through application and review.',
        'The member directory is never supplied to sponsors.',
        'Introductions require consent from both people.',
        'No unsolicited pitching, scraping or bulk member messages.',
        'Members can ignore sponsor activity without losing benefits.',
    ]
    y = 342
    for item in rules:
        para(c, item, 54, y, 1090, 20, INK, 'Body', 26)
        rule(c, 54, y + 40, 1110)
        y += 56
    end(c)

    base(c, 'membership', 9, 'The annual membership', LILAC)
    heading(c, '₹2,00,000', 48, 104, 650, 74)
    text(c, 'INCLUDING YOUR FIRST MEMBERSHIP YEAR', 52, 198, 16, 'BodyBold')
    heading(c, '₹1,00,000', 48, 278, 650, 58)
    text(c, 'EACH ANNUAL RENEWAL AFTER THAT', 52, 350, 16, 'BodyBold')
    para(c, 'One membership. Founders only. An initial cohort of up to 25, expanding in reviewed cohorts toward a cap of 100 active members.', 52, 424, 510, 21)
    para(c, 'Included', 730, 112, 390, 26, INK, 'DisplayBold')
    included = 'Founder-house access\nAsk/offer system\nMonthly introduction request\nFour room-hours monthly\nFounder and member-hosted programming\nTwo guest day passes monthly'
    para(c, included, 730, 164, 410, 20, INK, 'Body', 37)
    para(c, 'F&B, additional bookings and separately priced services are not included unless expressly stated.', 730, 442, 400, 18, INK, 'Body', 25)
    text(c, 'Membership terms, cancellation, pause and conduct rules are set out in the signed agreement.', 52, 638, 12, 'Body', INK)
    end(c)

    base(c, 'membership', 10, 'The invitation', GREEN, True)
    heading(c, 'Bring what\nyou’re building.', 48, 110, 580, 66, CREAM)
    para(c, 'Apply for founder membership. We will review fit, show you the house, and explain the current terms before asking for payment.', 52, 300, 500, 22, CREAM)
    text(c, '01  APPLY', 52, 420, 14, 'BodyBold', SAND)
    text(c, '02  FOUNDER REVIEW', 190, 420, 14, 'BodyBold', SAND)
    text(c, '03  VISIT', 414, 420, 14, 'BodyBold', SAND)
    text(c, '04  JOIN', 536, 420, 14, 'BodyBold', SAND)
    para(c, 'HSR Founders Club\nFourthspace\nHSR Layout, Bengaluru\nOpening 30 November 2026', 52, 486, 440, 19, CREAM, 'Body', 29)
    image(c, HOUSE / 'p11.jpg', 690, 82, 542, 560)
    end(c)

    c.save()
    return path


def sponsorship_deck():
    path = ROOT / 'Fourthspace-Founding-Sponsorship.pdf'
    c = canvas.Canvas(str(path), pagesize=(W, H), pageCompression=1)
    c.setTitle('Fourthspace | Founding Brand Sponsorship')
    c.setAuthor('HSR Founders Club')
    c.setSubject('Five founding category partnerships at INR 15 lakh annually')

    base(c, 'sponsorship', 1, 'Founding brand partnerships', GREEN, True)
    heading(c, 'Founding brand\npartnerships at\nFourthspace HSR', 48, 104, 610, 56, CREAM)
    para(c, 'Your signature drink on the menu for 12 months, plus merchandise distribution and four sponsor-led event-space uses.', 52, 314, 510, 22, CREAM)
    pill(c, '₹15 LAKH  /  ONE CATEGORY  /  ONE YEAR', 52, 426, 13, INK, CREAM)
    text(c, 'FIRST HOUSE OPENS 30 NOVEMBER 2026', 52, 482, 13, 'BodyBold', CREAM)
    para(c, 'Five founding category partnerships for brands seeking direct, voluntary engagement with café visitors and the HSR founder community.', 52, 536, 500, 18, CREAM)
    image(c, MENU_COVER, 690, 82, 542, 542, 'contain')
    text(c, 'Illustrative co-build menu. No current brand partnership implied.', 700, 632, 11, 'Body', SAND)
    end(c)

    base(c, 'sponsorship', 2, '01 / Community and fit')
    heading(c, 'An existing founder community.\nA house being built in HSR.', 48, 88, 1120, 48)
    para(c, 'Fourthspace HSR is being built by the team behind HSR Founders Club. The house adds a café, workspaces and event rooms to the existing founder events programme.', 50, 206, 1120, 20)
    stat(c, '120+', 'events hosted', 62, 298, 240)
    stat(c, '≈5,200', 'event attendees', 355, 298, 240)
    stat(c, '3,000+', 'founders in the HSR-area directory', 680, 298, 250)
    stat(c, '7,000', 'newsletter signups', 1000, 298, 210)
    rect(c, 48, 460, 1184, 146, PAPER, 24)
    objectives = [
        ('PRODUCT DISCOVERY', 'Give visitors a drink and QR journey they can choose.'),
        ('VISITOR FEEDBACK', 'Use sponsor-led events for research and customer conversations.'),
        ('OPT-IN ENQUIRIES', 'Measure explicit interest separately from café activity.'),
    ]
    for i, (head, body) in enumerate(objectives):
        x = 72 + i * 392
        text(c, head, x, 486, 13, 'BodyBold', ORANGE)
        para(c, body, x, 522, 330, 17, INK, 'Body', 23)
    text(c, 'HSR Founders Club figures supplied October 2026. Community figures are not Fourthspace operating results.', 48, 640, 11, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 3, '02 / Partner menu')
    heading(c, 'Your drink on the menu.\nFor 12 months.', 48, 88, 580, 46)
    para(c, 'One co-built coffee or mocktail, with your company name, brand story and dedicated QR destination.', 52, 238, 500, 21)
    rows = [
        ('ONE SIGNATURE DRINK', 'Co-built with your team and our F&B team.'),
        ('YOUR COMPANY NAME', 'Shown on the menu as “By [company]”.'),
        ('YOUR AVAILABLE SLOT', 'One of five founding category partnerships.'),
    ]
    y = 390
    for head, body in rows:
        text(c, head, 52, y, 14, 'BodyBold', ORANGE)
        para(c, body, 52, y + 26, 500, 18, INK, 'Body', 24)
        y += 78
    image(c, MENU, 650, 70, 500, 560, 'contain')
    text(c, 'Illustrative concepts only. Recipes, ingredients, prices and service require F&B approval.', 52, 640, 11, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 4, '03 / Co-build process')
    heading(c, 'We build the drink, story\nand QR journey with you.', 48, 88, 760, 46)
    cards = [
        ('01', 'RECIPE CARD', 'Your signature drink', 'Drink name, ingredients and preparation developed with our F&B team.'),
        ('02', 'MENU STORY', 'Co-built with YOUR BRAND', 'Your approved brand story and claims in the Fourthspace menu layout.'),
        ('03', 'QR DESTINATION', 'Your approved landing page', 'A dedicated QR takes interested visitors to your website or offer.'),
    ]
    for i, (num, label, title, body) in enumerate(cards):
        y = 254 + i * 112
        rule(c, 48, y, 660)
        text(c, num, 52, y + 24, 26, 'DisplayBold', ORANGE)
        text(c, label, 120, y + 16, 11, 'BodyBold', MUTED)
        text(c, title, 120, y + 40, 19, 'DisplayBold')
        para(c, body, 410, y + 22, 290, 14, INK, 'Body', 19)
    para(c, 'F&B approves the recipe, price, ingredients, availability and service. You supply the brand story, claims and QR destination; Fourthspace controls the final menu layout.', 52, 616, 680, 14, INK, 'Body', 19)
    image(c, ASSETS / 'cups' / 'your-brand-cup.png', 790, 82, 400, 516, 'contain')
    text(c, 'Cup concept; final packaging requires approval.', 800, 616, 11, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 5, '04 / Merchandise')
    heading(c, 'Merchandise storage\nand distribution.', 48, 88, 600, 48)
    para(c, 'You supply and replenish approved stock. We store it in one agreed bay and offer it voluntarily to walk-in guests matching transparent audience criteria agreed with you.', 52, 250, 520, 20)
    rows = [
        ('YOU SUPPLY', 'Approved stock, replenishment and audience criteria.'),
        ('WE STORE & OFFER', 'One agreed shelf bay and a recorded distribution process.'),
        ('THE GUEST CHOOSES', 'No purchase or contact exchange is required.'),
    ]
    y = 388
    for head, body in rows:
        text(c, head, 52, y, 14, 'BodyBold', ORANGE)
        para(c, body, 280, y, 340, 17, INK, 'Body', 23)
        y += 70
    image(c, SHELF, 690, 82, 542, 542, 'contain')
    text(c, 'Concept only. Distribution is not a retail-sales commitment.', 52, 638, 11, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 6, '05 / Quarterly events')
    heading(c, 'Four sponsor-led event-space uses per year.', 48, 88, 1140, 46)
    para(c, 'One use per calendar quarter. You propose the audience and format for approval; your team curates, funds, staffs and runs the event.', 50, 154, 1120, 20)
    quarters = [
        ('Q1', 'PRODUCT\nDEMONSTRATION'),
        ('Q2', 'CUSTOMER\nROUNDTABLE'),
        ('Q3', 'COMMUNITY\nEVENING'),
        ('Q4', 'PRODUCT\nLAUNCH'),
    ]
    for i, (quarter, format_name) in enumerate(quarters):
        x = 48 + i * 300
        rule(c, x, 254, 270, INK, 2)
        text(c, quarter, x, 278, 38, 'DisplayBold', ORANGE)
        para(c, format_name, x, 354, 250, 24, INK, 'DisplayBold', 29)
        text(c, 'ILLUSTRATIVE FORMAT', x, 432, 11, 'BodyBold', MUTED)
    pill(c, '20% OFF PRE-AGREED EVENT CATERING', 52, 490, 13, INK, CREAM)
    para(c, 'Taxes and service charges are not discounted. Production and dedicated staffing are separately priced. Each schedule confirms dates, guest limit, setup and cancellation terms. Unused quarterly uses expire.', 52, 548, 1120, 17, INK, 'Body', 23)
    text(c, 'Illustrative formats only. No events booked or attendance implied.', 52, 638, 11, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 7, '06 / Annual package', LILAC)
    heading(c, 'The annual partnership.', 48, 88, 940, 48)
    heading(c, '₹15,00,000', 48, 158, 560, 60)
    pill(c, 'ONE CATEGORY  /  12 MONTHS  /  HSR HOUSE', 52, 236, 12, INK, CREAM)
    benefits = [
        ('01 / Signature drink', 'One co-built drink, brand story and menu QR for 12 months.'),
        ('02 / Merchandise', 'One agreed bay and voluntary distribution of sponsor stock.'),
        ('03 / Quarterly events', 'Four sponsor-led uses; 20% off pre-agreed catering.'),
        ('Category exclusivity', 'One written category at the HSR house for the term.'),
        ('Two-week feature', 'One annual feature supporting the drink and QR campaign.'),
        ('Reporting', 'Weekly activity reports and four quarterly reviews.'),
    ]
    positions = [(50, 304), (650, 304), (50, 410), (650, 410), (50, 516), (650, 516)]
    for (head, body), (x, y) in zip(benefits, positions):
        benefit_row(c, head, body, x, y, 540)
    text(c, 'Extra drinks, events, production, dedicated staffing and bespoke activations are separately scoped and priced.', 50, 638, 12, 'Body', INK)
    end(c)

    base(c, 'sponsorship', 8, '07 / Two-week feature')
    heading(c, 'Two weeks focused on\nyour partnership.', 48, 88, 800, 48)
    para(c, 'One annual in-house feature amplifies the same signature drink and QR campaign.', 50, 210, 1120, 20)
    features = [
        ('01 / MENU HIGHLIGHT', 'Your signature drink receives a featured position on the partner menu.'),
        ('02 / PARTNER STORY', 'An approved story card explains the drink and your company.'),
        ('03 / IN-CAFÉ PLACEMENT', 'One agreed placement supports the same campaign in the café.'),
        ('04 / QR MEASUREMENT', 'The feature uses the same QR destination and campaign reporting.'),
    ]
    positions = [(50, 300), (650, 300), (50, 452), (650, 452)]
    for (head, body), (x, y) in zip(features, positions):
        rule(c, x, y, 540, INK, 2)
        text(c, head, x, y + 24, 14, 'BodyBold', ORANGE)
        para(c, body, x, y + 62, 500, 18, INK, 'Body', 24)
    text(c, 'Exact feature dates, placements and creative are confirmed in your annual benefit schedule.', 52, 626, 12, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 9, '08 / Reporting')
    heading(c, 'A weekly report your team can use.', 48, 82, 1100, 46)
    para(c, 'Weekly activity reporting, plus four quarterly reviews of delivery, sponsor-supplied outcomes and next actions.', 50, 148, 1120, 20)
    rect(c, 48, 208, 1184, 378, PAPER, 10, LINE)
    text(c, 'FOURTHSPACE PARTNER ACTIVITY REPORT', 72, 230, 16, 'BodyBold')
    text(c, 'TEMPLATE — NOT OPERATING DATA', 884, 232, 12, 'BodyBold', ORANGE)
    text(c, 'PARTNER / CATEGORY: —     REPORTING WEEK: —', 72, 264, 12, 'Body', MUTED)
    report_sections = [
        ('CAMPAIGN STATUS', 'Menu-live status: —\nFeature activity: —'),
        ('DRINK & QR', 'Verified paid drink orders: —\nQR visits where tracked: —'),
        ('MERCHANDISE & EVENTS', 'Units distributed / remaining: —\nVerified event check-ins: —'),
        ('VALIDATED INTEREST', 'Redemptions: —\nExplicit opt-in enquiries: —'),
        ('SPONSOR-SUPPLIED OUTCOMES', 'Product use or trials: —\nSales attribution: —'),
        ('DATA NOTES', 'Missing data: —\nCorrections: —'),
    ]
    for i, (label, body) in enumerate(report_sections):
        col = i % 3
        row = i // 3
        x = 72 + col * 380
        y = 312 + row * 132
        rule(c, x, y, 350, LINE, 2)
        text(c, label, x, y + 18, 11, 'BodyBold', ORANGE)
        para(c, body, x, y + 50, 330, 15, INK, 'Body', 25)
    text(c, 'Aggregate reporting by default. Individual details require separate consent naming purpose and recipient.', 52, 626, 12, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 10, '09 / Next step', GREEN, True)
    heading(c, 'Five founding\ncategory partners.', 48, 96, 680, 58, CREAM)
    para(c, '₹15,00,000 per category for 12 months at Fourthspace HSR, opening 30 November 2026.', 52, 248, 560, 21, CREAM)
    steps = [
        ('01', 'Confirm your category and objective.'),
        ('02', 'Receive the drink brief, annual benefit schedule and agreement.'),
        ('03', 'Approve the presentation and launch plan.'),
    ]
    y = 350
    for num, body in steps:
        text(c, num, 52, y, 26, 'DisplayBold', SAND)
        para(c, body, 120, y + 2, 520, 18, CREAM, 'Body', 24)
        y += 76
    para(c, 'Next step: request a category-fit conversation with HSR Founders Club.\nFourthspace HSR / HSR Layout, Bengaluru', 52, 586, 600, 16, CREAM, 'Body', 23)
    rect(c, 780, 112, 380, 438, CREAM, 14)
    text(c, '05', 824, 156, 112, 'DisplayBold', GREEN)
    text(c, 'FOUNDING CATEGORIES', 828, 300, 16, 'BodyBold', GREEN)
    rule(c, 828, 344, 280, GREEN, 2)
    text(c, 'YOUR CATEGORY', 828, 380, 18, 'BodyBold', INK)
    text(c, 'YOUR SIGNATURE DRINK', 828, 424, 18, 'BodyBold', INK)
    text(c, 'YOUR 12-MONTH PARTNERSHIP', 828, 468, 18, 'BodyBold', INK)
    end(c)

    c.save()
    return path


def mild_atta_deck():
    path = ROOT / 'Fourthspace-Mild-Atta-Partnership.pdf'
    c = canvas.Canvas(str(path), pagesize=(W, H), pageCompression=1)
    c.setTitle('Fourthspace | Mild Atta Partnership Concept')
    c.setAuthor('HSR Founders Club')
    c.setSubject('Proposed breakfast-led annual partnership for Mild Atta')

    base(c, 'sponsorship', 1, 'Mild Atta partnership concept', GREEN, True)
    heading(c, 'Own the first meal\nof the workday.', 48, 104, 610, 58, CREAM)
    para(c, 'A breakfast-led partnership that turns Mild Atta into a useful daily ritual—not another logo on a menu.', 52, 268, 510, 23, CREAM)
    pill(c, 'MILD ATTA × FOURTHSPACE  /  12 MONTHS', 52, 404, 13, INK, CREAM)
    para(c, 'One signature breakfast, an approved recipe QR, voluntary take-home samples and four quarterly Breakfast & Build sessions.', 52, 480, 500, 19, CREAM, 'Body', 27)
    text(c, 'CONCEPT ONLY  /  PRODUCT, CLAIMS AND FINAL PACKAGE REQUIRE APPROVAL', 52, 610, 11, 'BodyBold', SAND)
    image(c, MILD_ATTA_MENU, 690, 82, 542, 542, 'contain')
    text(c, 'Illustrative proposal. No current partnership implied.', 700, 632, 11, 'Body', SAND)
    end(c)

    base(c, 'sponsorship', 2, '01 / The proposition')
    heading(c, 'A product people can taste.\nNot just a brand they notice.', 48, 88, 1130, 48)
    para(c, 'The partnership is designed around a simple behaviour: try Mild Atta at breakfast, choose to learn more, and decide what happens next.', 50, 210, 1120, 20)
    principles = [
        ('DAILY TRIAL', 'A real breakfast serve creates a more relevant product experience than a conventional sponsorship placement.'),
        ('USEFUL RECALL', 'An approved recipe and take-home pack give visitors something useful after they leave the house.'),
        ('OPT-IN RETURN', 'Recipe visits, enquiries and redemptions are measured separately. Participation never requires contact details.'),
    ]
    for i, (head, body) in enumerate(principles):
        x = 48 + i * 400
        rule(c, x, 330, 350, INK, 2)
        text(c, head, x, 358, 15, 'BodyBold', ORANGE)
        para(c, body, x, 404, 340, 19, INK, 'Body', 27)
    rect(c, 48, 554, 1184, 62, PAPER, 20)
    text(c, 'THE COMMERCIAL IDEA  /  OWN A REPEATABLE MORNING RITUAL, NOT A ONE-OFF ACTIVATION.', 72, 575, 14, 'BodyBold', INK)
    text(c, 'Concept assumes a packaged atta product; Mild Atta supplies final product information and approved claims.', 48, 640, 11, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 3, '02 / Signature breakfast')
    heading(c, 'The Founders’ Breakfast.\nA daily reason to return.', 48, 88, 590, 46)
    para(c, 'One approved breakfast serve, with Mild Atta named on the menu and a dedicated recipe or offer QR.', 52, 238, 500, 21)
    rows = [
        ('ONE SIGNATURE SERVE', 'Developed with Mild Atta and approved by our F&B team.'),
        ('ONE APPROVED STORY', 'Product details and claims supplied and approved by Mild Atta.'),
        ('ONE RECIPE QR', 'A useful destination chosen by the visitor, never a forced lead form.'),
    ]
    y = 390
    for head, body in rows:
        text(c, head, 52, y, 14, 'BodyBold', ORANGE)
        para(c, body, 52, y + 26, 500, 18, INK, 'Body', 24)
        y += 78
    image(c, MILD_ATTA_MENU, 650, 70, 500, 560, 'contain')
    text(c, 'Illustrative serves only. Recipes, allergens, prices and service require F&B approval.', 52, 640, 11, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 4, '03 / Visitor journey')
    heading(c, 'From first bite\nto the next purchase.', 48, 88, 850, 50)
    para(c, 'Every stage has a clear visitor choice and a separate measure. A breakfast order is not a lead; a scan is not a sale.', 50, 224, 1120, 20)
    journey = [
        ('TASTE', 'Order the breakfast', 'Count verified paid serves where the POS identifies the item.'),
        ('SCAN', 'Open the recipe or offer', 'Measure campaign visits where the approved destination supports tracking.'),
        ('CHOOSE', 'Take a sample voluntarily', 'Record packs received, distributed, damaged and remaining.'),
        ('RETURN', 'Redeem or enquire by choice', 'Report validated redemptions and explicit opt-in enquiries separately.'),
    ]
    for i, (label, title, body) in enumerate(journey):
        x = 48 + i * 300
        rule(c, x, 318, 270, INK, 2)
        text(c, label, x, 342, 14, 'BodyBold', ORANGE)
        para(c, title, x, 382, 255, 23, INK, 'DisplayBold', 28)
        para(c, body, x, 456, 250, 16, INK, 'Body', 23)
    text(c, 'Sponsor-side trials, repurchase and sales are reported only when Mild Atta supplies the outcome and counting method.', 48, 638, 11, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 5, '04 / Product and place')
    heading(c, 'A clear ingredient tag.\nNot a branded cup.', 48, 88, 590, 46)
    para(c, 'The same idea appears across the breakfast, menu story and approved take-home pack—using a simple ingredient tag instead of branded drinkware.', 52, 224, 520, 20)
    rows = [
        ('ON THE MENU', 'A named breakfast and a concise approved product story.'),
        ('ON THE SERVE', 'A clear “Made using Mild Atta” tag on the breakfast packaging.'),
        ('TO TAKE HOME', 'One approved sample pack, offered voluntarily with no contact exchange.'),
    ]
    y = 388
    for head, body in rows:
        text(c, head, 52, y, 14, 'BodyBold', ORANGE)
        para(c, body, 280, y, 340, 17, INK, 'Body', 23)
        y += 70
    rect(c, 760, 112, 400, 438, SAND, 24)
    rect(c, 824, 166, 272, 258, PAPER, 18)
    text(c, 'FOURTHSPACE', 850, 192, 12, 'BodyBold', GREEN)
    rule(c, 850, 226, 220, LINE, 2)
    text(c, 'MADE USING', 850, 258, 17, 'BodyBold', ORANGE)
    heading(c, 'MILD ATTA', 850, 302, 220, 36)
    para(c, 'Breakfast serve & take-home pack', 850, 358, 200, 14, INK, 'Body', 19)
    pill(c, 'INGREDIENT TAG', 824, 462, 12, INK, CREAM)
    text(c, 'Menu and packaging tag concepts; final claims and design require approval.', 52, 638, 11, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 6, '05 / Quarterly events')
    heading(c, 'Breakfast & Build.\nFour mornings a year.', 48, 88, 1000, 48)
    para(c, 'One sponsor-led event-space use per quarter. Mild Atta proposes the audience and format; Fourthspace reviews and approves each event.', 50, 220, 1120, 20)
    quarters = [
        ('Q1', 'PANTRY\nRESEARCH'),
        ('Q2', 'FOUNDER\nBREAKFAST'),
        ('Q3', 'RECIPE\nCO-CREATION'),
        ('Q4', 'COMMUNITY\nTABLE'),
    ]
    for i, (quarter, format_name) in enumerate(quarters):
        x = 48 + i * 300
        rule(c, x, 318, 270, INK, 2)
        text(c, quarter, x, 342, 38, 'DisplayBold', ORANGE)
        para(c, format_name, x, 410, 250, 24, INK, 'DisplayBold', 29)
        text(c, 'ILLUSTRATIVE FORMAT', x, 486, 11, 'BodyBold', MUTED)
    pill(c, '20% OFF PRE-AGREED EVENT CATERING', 52, 540, 13, INK, CREAM)
    text(c, 'Event production and dedicated staffing are separately scoped. Unused quarterly uses expire.', 52, 638, 11, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 7, '06 / Annual package', LILAC)
    heading(c, 'The annual partnership.', 48, 88, 940, 48)
    heading(c, '₹15,00,000', 48, 158, 560, 60)
    pill(c, 'PROPOSED CUSTOM PACKAGE  /  12 MONTHS', 52, 236, 12, INK, CREAM)
    benefits = [
        ('01 / Signature breakfast', 'One approved Mild Atta breakfast serve and recipe QR.'),
        ('02 / Take-home samples', 'One agreed bay and voluntary distribution of approved packs.'),
        ('03 / Quarterly breakfasts', 'Four sponsor-led uses; 20% off pre-agreed catering.'),
        ('Category exclusivity', 'Proposed packaged atta category, defined in the agreement.'),
        ('Two-week feature', 'One annual feature supporting the breakfast and recipe QR.'),
        ('Reporting', 'Weekly activity reports and four quarterly reviews.'),
    ]
    positions = [(50, 304), (650, 304), (50, 410), (650, 410), (50, 516), (650, 516)]
    for (head, body), (x, y) in zip(benefits, positions):
        benefit_row(c, head, body, x, y, 540)
    text(c, 'Proposed variation replaces the standard coffee/mocktail benefit; commercial and F&B approval required.', 50, 638, 12, 'Body', INK)
    end(c)

    base(c, 'sponsorship', 8, '07 / Two-week feature')
    heading(c, 'Two weeks focused on\nbetter mornings.', 48, 88, 800, 48)
    para(c, 'One annual in-house feature brings the breakfast, product story, samples and recipe journey together.', 50, 210, 1120, 20)
    features = [
        ('01 / BREAKFAST HIGHLIGHT', 'The Mild Atta serve receives a featured position on the breakfast menu.'),
        ('02 / PRODUCT STORY', 'An approved card explains the product, ingredients and recipe.'),
        ('03 / SAMPLE MOMENT', 'Staff offer the approved take-home pack using transparent criteria.'),
        ('04 / RECIPE MEASUREMENT', 'The feature uses one approved QR destination and campaign report.'),
    ]
    positions = [(50, 300), (650, 300), (50, 452), (650, 452)]
    for (head, body), (x, y) in zip(features, positions):
        rule(c, x, y, 540, INK, 2)
        text(c, head, x, y + 24, 14, 'BodyBold', ORANGE)
        para(c, body, x, y + 62, 500, 18, INK, 'Body', 24)
    text(c, 'Exact feature dates, placements and creative are confirmed in the annual benefit schedule.', 52, 626, 12, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 9, '08 / Reporting')
    heading(c, 'Measure trial.\nNever mistake it for loyalty.', 48, 82, 1000, 46)
    para(c, 'Weekly activity reporting separates café behaviour from sponsor-supplied outcomes and genuine opt-in interest.', 50, 202, 1120, 20)
    rect(c, 48, 264, 1184, 322, PAPER, 24, LINE)
    text(c, 'MILD ATTA PARTNER ACTIVITY REPORT', 72, 286, 16, 'BodyBold')
    text(c, 'TEMPLATE — NOT OPERATING DATA', 884, 288, 12, 'BodyBold', ORANGE)
    report_sections = [
        ('BREAKFAST', 'Paid breakfast orders: —\nMenu-live status: —'),
        ('RECIPE QR', 'Tracked visits: —\nFeature activity: —'),
        ('SAMPLES', 'Packs distributed / remaining: —'),
        ('OPT-IN INTEREST', 'Redemptions: —\nExplicit enquiries: —'),
        ('SPONSOR-SUPPLIED', 'Repurchase outcomes: —\nSales attribution: —'),
        ('DATA NOTES', 'Missing data: —\nCorrections: —'),
    ]
    for i, (label, body) in enumerate(report_sections):
        col = i % 3
        row = i // 3
        x = 72 + col * 380
        y = 334 + row * 116
        rule(c, x, y, 350, LINE, 2)
        text(c, label, x, y + 16, 11, 'BodyBold', ORANGE)
        para(c, body, x, y + 44, 330, 15, INK, 'Body', 23)
    text(c, 'Aggregate reporting by default. No member, attendee or newsletter lists are supplied.', 52, 626, 12, 'Body', MUTED)
    end(c)

    base(c, 'sponsorship', 10, '09 / Recommended next step', GREEN, True)
    heading(c, 'Make Mild Atta\npart of the morning.', 48, 96, 680, 56, CREAM)
    para(c, 'Start with one breakfast pilot, one approved recipe destination and a clear definition of the packaged atta category.', 52, 252, 560, 21, CREAM)
    steps = [
        ('01', 'Confirm the product, category boundary and approved claims.'),
        ('02', 'Prototype the breakfast, service process and take-home pack.'),
        ('03', 'Approve the annual schedule, measurement and agreement.'),
    ]
    y = 374
    for num, body in steps:
        text(c, num, 52, y, 26, 'DisplayBold', SAND)
        para(c, body, 120, y + 2, 520, 18, CREAM, 'Body', 24)
        y += 76
    para(c, 'Recommended: approve a concept and F&B workshop before contracting.\nFourthspace HSR / HSR Layout, Bengaluru', 52, 610, 620, 15, CREAM, 'Body', 22)
    rect(c, 780, 112, 380, 438, CREAM, 24)
    text(c, 'DAILY', 824, 156, 72, 'DisplayBold', GREEN)
    text(c, 'PRODUCT TRIAL', 828, 258, 16, 'BodyBold', GREEN)
    rule(c, 828, 306, 280, GREEN, 2)
    text(c, 'ONE SIGNATURE BREAKFAST', 828, 350, 17, 'BodyBold', INK)
    text(c, 'ONE RECIPE DESTINATION', 828, 400, 17, 'BodyBold', INK)
    text(c, 'FOUR QUARTERLY SESSIONS', 828, 450, 17, 'BodyBold', INK)
    end(c)

    c.save()
    return path


if __name__ == '__main__':
    outputs = [membership_deck(), sponsorship_deck(), mild_atta_deck()]
    for deck, page, line, x, y, size, width in checks:
        if x < 0 or x + width > W + 1 or y < 0 or y + size > H - 8:
            raise RuntimeError(f'Text overflow: {deck} page {page} {line!r} at {x},{y}, width {width}')
    (ROOT / 'layout-check.json').write_text(json.dumps({'decks': 3, 'pages_per_deck': 10, 'text_runs': len(checks), 'overflow': False}, indent=2))
    (ASSETS / 'provenance.json').write_text(json.dumps({
        'concept_assets': [
            {'file': 'cup-concept.png', 'method': 'Original procedural vector-style illustration; no image model or third-party brand asset'},
            {'file': 'shelf-concept.png', 'method': 'Original procedural illustration using generic product examples'},
            {'file': 'opportunity-menu.png', 'method': 'Original illustrative co-build menu composed with generated cup mockups; Corgi Cafe public menu used as layout reference; no current partnership or endorsement'},
            {'file': 'partner-menu-cover.png', 'method': 'Original illustrative co-build menu cover composed with generated cup mockups; Corgi Cafe public menu used as layout reference; no current partnership implied'},
            {'file': 'mild-atta-breakfast-menu.png', 'method': 'Original illustrative breakfast concept for Mild Atta; no brand identity or product claims supplied; recipes, allergens, claims and prices require approval'},
        ],
        'cup_mockups': {
            'generator': 'build_cup_mockups.py / Blender Cycles',
            'files': [f'cups/{name}' for name in ['openai-cup.png', 'razorpay-cup.png', 'notion-cup.png', 'postman-cup.png', 'your-brand-cup.png', 'partner-cup-lineup.png']],
            'status': 'Illustrative packaging concepts using company names without logos; no current partnership or endorsement; final packaging requires approval'
        },
        'photographs': [f'docs/house-understanding/img/{name}' for name in ['p11.jpg', 'p20.jpg', 'p25.jpg', 'p28.jpg', 'p33.jpg']],
        'font_sources': ['System Georgia / Georgia Bold', 'Bundled Poppler Ubuntu-R / Ubuntu-B'],
        'status': 'Sponsorship decks use labelled sales concepts and describe the HSR house as under construction; membership deck uses existing house photographs; Mild Atta proposal is an unconfirmed concept'
    }, indent=2))
    print('\n'.join(str(p) for p in outputs))
    m = CONFIG['membership']
    s = CONFIG['sponsorship']
    print('Recurring revenue checks:')
    print('100 first-year members + 5 sponsors:', m['active_member_cap'] * m['first_year_inr'] + s['launch_category_slots'] * s['annual_fee_inr'])
    print('100 renewing members + 5 sponsors:', m['active_member_cap'] * m['renewal_year_inr'] + s['launch_category_slots'] * s['annual_fee_inr'])
    print('100 first-year members + 20 sponsors:', m['active_member_cap'] * m['first_year_inr'] + s['maximum_future_category_slots'] * s['annual_fee_inr'])
    print('100 renewing members + 20 sponsors:', m['active_member_cap'] * m['renewal_year_inr'] + s['maximum_future_category_slots'] * s['annual_fee_inr'])
