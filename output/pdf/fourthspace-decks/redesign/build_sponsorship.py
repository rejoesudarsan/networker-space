from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from PIL import Image

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
FONTS = ASSETS / 'fonts'
OUT = ROOT / 'Fourthspace-Founding-Sponsorship-Redesigned.pdf'
for name, file in [('Display','Newsreader-Medium.ttf'), ('DisplayBold','Newsreader-Bold.ttf'), ('Body','Schibsted-Regular.ttf'), ('Bold','Schibsted-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS/file)))
pdfmetrics.registerFont(TTFont('Symbols', str(FONTS/'SymbolFallback.ttf')))
W,H=1440,810
PAPER,GREEN,INK,RUST,MUTED,LINE='#F6F0E5','#193E32','#192B24','#A4482C','#5B665E','#D6CDBE'
C=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
C.setTitle('Fourthspace | Founding Brand Partnerships')
C.setAuthor('Fourthspace / HSR Founders Club')
C.setSubject('Founding category sponsorship proposal, November 2026')
page=0
boxes=[]

def rect(x,y,w,h,color):
    C.setFillColor(HexColor(color)); C.rect(x,H-y-h,w,h,stroke=0,fill=1)

def line(x,y,w,color=LINE):
    C.setStrokeColor(HexColor(color)); C.setLineWidth(.8); C.line(x,H-y,x+w,H-y)

def txt(s,x,y,size=22,font='Body',color=INK):
    C.setFillColor(HexColor(color))
    cursor=x
    runs=[]
    for char in s:
        face=font if ord(char) in pdfmetrics.getFont(font).face.charToGlyph else 'Symbols'
        assert ord(char) in pdfmetrics.getFont(face).face.charToGlyph, char
        if runs and runs[-1][0]==face:
            runs[-1][1]+=char
        else:
            runs.append([face,char])
    for face,run in runs:
        C.setFont(face,size); C.drawString(cursor,H-y-size,run)
        cursor+=pdfmetrics.stringWidth(run,face,size)
    boxes.append({'page':page,'text':s,'x':x,'y':y,'w':cursor-x,'h':size*1.2})

def para(s,x,y,w,size=22,font='Body',color=INK,leading=None):
    style=ParagraphStyle('p',fontName=font,fontSize=size,leading=leading or size*1.35,textColor=HexColor(color))
    p=Paragraph(escape(s).replace('\n','<br/>'),style)
    _,h=p.wrap(w,1000); p.drawOn(C,x,H-y-h)
    boxes.append({'page':page,'text':s,'x':x,'y':y,'w':w,'h':h})
    return y+h

def head(s,x=64,y=112,w=1200,size=70,color=INK):
    return para(s,x,y,w,size,'Display',color,size*1.01)

def photo(name,x,y,w,h,fit='cover'):
    src=ASSETS/name
    im=Image.open(src); iw,ih=im.size
    scale=min(w/iw,h/ih) if fit=='contain' else max(w/iw,h/ih)
    dw,dh=iw*scale,ih*scale
    C.saveState(); path=C.beginPath(); path.rect(x,H-y-h,w,h); C.clipPath(path,stroke=0)
    C.drawImage(ImageReader(im),x+(w-dw)/2,H-y-h+(h-dh)/2,dw,dh,mask='auto'); C.restoreState()

def start(bg=PAPER,dark=False):
    global page
    page+=1; rect(0,0,W,H,bg)
    fg=PAPER if dark else GREEN
    txt('FOURTHSPACE',64,34,18,'Bold',fg)
    txt('FOUNDING BRAND PARTNERSHIPS',1010,38,12,'Bold',fg)

def foot(note='',dark=False):
    fg='#D6DFD3' if dark else MUTED
    if note: para(note,64,709,1312,13,'Body',fg,17)
    line(64,760,1312,'#547264' if dark else LINE)
    txt('HSR LAYOUT, BENGALURU',64,775,10,'Bold',fg)
    txt('PROPOSAL / NOVEMBER 2026',590,775,10,'Body',fg)
    txt(f'{page:02d} / 11',1323,775,10,'Body',fg)
    C.showPage()

# 1. Invitation: the product itself carries the cover.
start(GREEN,True)
photo('signature-drink.png',716,96,660,593)
head('Make your brand\npart of the\neveryday.',64,124,620,76,PAPER)
para('One signature drink. A year on the menu.\nA place in the Fourthspace story.',68,390,575,24,color=PAPER)
line(68,502,560,'#547264')
txt('₹15 lakh',68,527,42,'Display',PAPER)
txt('ONE CATEGORY / 12 MONTHS',68,588,15,'Bold',PAPER)
para('Five founding category partnerships.\nPlanned opening: 30 November 2026.',68,635,590,17,color='#D6DFD3')
foot('AI-generated signature-drink concept. Final recipe, menu, packaging and branding require approval.',True)

# 2. Ground the audience without pretending these are venue forecasts.
start()
head('The community came first.')
para('Fourthspace is being built by the team behind HSR Founders Club.\nThe house gives that existing founder programme a place to return to.',66,215,1240,25)
stats=[('120+','events hosted'),('≈5,200','reported event attendees'),('3,000+','founders in the HSR-area directory'),('7,000','newsletter signups')]
for i,(value,label) in enumerate(stats):
    x=64+i*336; line(x,332,300); txt(value,x,355,61,'Display',GREEN); para(label,x,436,285,20)
rect(64,543,1312,116,GREEN)
para('The opportunity',90,567,280,24,'Display',PAPER)
para('A drink people can discover, events they can choose to attend,\nand an invitation to learn more about your brand.',405,569,900,22,color=PAPER)
foot('HSR Founders Club figures supplied October 2026; definitions differ. These are not Fourthspace operating results, guaranteed reach or sponsor contact lists.')

# 3. Show the particular place using the baked model.
start()
head('A house with room for connection.',size=65)
para('Café visits, courtyard conversations and sponsor-led gatherings.',66,201,1230,24)
for i,(name,title,body) in enumerate([
    ('cafe','The café','Where the signature drink meets the everyday visit.'),
    ('court','The courtyard','A setting for conversations around the house.'),
    ('event','The event space','For the audience and format you bring.')]):
    x=64+i*448
    photo(f'blender/{name}-baked.png',x,286,416,286,'contain')
    txt(title,x,594,30,'Display',GREEN)
    para(body,x,638,400,18)
foot('Blender views from the repository’s baked room models. Proposed fit-outs; final layout, room allocation and capacity remain subject to review.')

# 4. Make the single serve, not a logo wall, the main product.
start()
photo('branded-cup.png',64,108,684,565,'contain')
head('One drink.\nYour story.\nAll year.',804,116,565,72)
para('Co-create a coffee or mocktail with our F&B team. Its name and story bring your brand onto the Fourthspace menu for 12 months.',808,370,535,23)
line(808,521,530)
txt('The First Pour',808,547,34,'Display',RUST)
para('By your brand / iced coffee concept\nYour approved story + a menu QR to your offer.',808,600,530,21)
foot('Illustrative name, recipe and AI-generated cup concept. Final packaging is subject to approval. One coffee or mocktail is included; recipe, price, availability and service require F&B approval.')

# 5. Responsibilities and guest journey together.
start()
head('Built with you. Chosen by the guest.')
para('We connect the drink, the story and the next step.',66,210,1200,25)
steps=[('01','Create the drink','Our F&B team develops the recipe with you. Taste, ingredients, pricing and service are agreed before launch.'),('02','Tell your story','You provide the brand story and approved claims. Fourthspace shapes them into the house menu.'),('03','Invite a next step','An interested visitor follows the menu QR to your website or offer. Any enquiry is their choice.')]
for i,(n,title,body) in enumerate(steps):
    x=64+i*448; line(x,326,406,GREEN); txt(n,x,347,22,'Bold',RUST)
    txt(title,x,401,34,'Display',GREEN); para(body,x,466,385,23)
para('The journey: discover the drink  /  read the story  /  choose to explore',64,651,1300,22,'Bold',GREEN)
foot('The sponsor supplies the approved destination. A drink order or QR visit is activity, not a guaranteed lead or sale.')

# 6. A modest, tangible distribution offer.
start()
head('Something useful\nto take away.',64,123,580,70)
para('One agreed bay for sponsor-supplied merchandise, offered voluntarily to visitors matching transparent audience criteria agreed with you.',68,303,540,23)
rows=[('You supply','Approved stock and replenishment.'),('We store & offer','An agreed bay and recorded distribution.'),('The guest chooses','No purchase or contact exchange required.')]
for i,(a,b) in enumerate(rows):
    y=463+i*70; txt(a,68,y,20,'Bold',RUST); para(b,68,y+29,550,18)
photo('merchandise.png',668,110,708,566)
foot('AI-generated merchandise-bay concept. Stock is supplied by the sponsor; distribution is not a retail-sales commitment.')

# 7. Venue plus a concrete example, with entitlement intact.
start()
head('Bring your audience into the house.',size=65)
photo('blender/event-baked.png',64,242,720,413,'contain')
txt('4',842,226,104,'Display',GREEN)
para('sponsor-led event-space uses\none per calendar quarter',949,255,420,24)
line(842,362,534)
txt('Make the format yours.',842,389,32,'Display',GREEN)
para('A product demo. A customer roundtable.\nA community evening. A launch.',842,439,520,22)
txt('20% off pre-agreed catering',842,526,23,'Bold',RUST)
para('Your team curates, funds, staffs and runs the event. Fourthspace provides the agreed space and operating support.',842,576,520,20)
foot('Proposed event-space fit-out. Illustrative formats; no bookings implied. Dates, guest cap, setup and cancellation agreed per event. Unused quarterly uses expire. Production and dedicated staff cost extra; taxes and service charges are not discounted.')

# 8. Show what the two-week support means without broadening it.
start(GREEN,True)
head('A fortnight\nin the spotlight.',64,127,650,75,PAPER)
para('One annual two-week feature draws attention to the same signature drink and QR journey.',68,326,560,25,color=PAPER)
photo('signature-drink.png',728,109,648,564)
for i,s in enumerate(['Featured position on the partner menu','An approved drink and partner story card','One agreed in-café placement']):
    y=470+i*64; line(68,y-13,570,'#547264'); para(s,68,y,570,21,color=PAPER)
foot('AI-generated concept. Exact dates, creative and placements are agreed in the annual benefit schedule.',True)

# 9. The buying decision gets a readable, complete commercial page.
start()
head('The annual partnership.',size=68)
txt('₹15,00,000',64,228,76,'Display',GREEN)
para('One defined category.\n12 months. Fourthspace HSR.',68,337,470,24)
para('Category exclusivity is recorded in writing for the contracted term at the HSR house.',68,464,440,21)
para('Five founding category partnerships\nin the launch plan.',68,585,440,21,'Bold',RUST)
benefits=[('Signature drink','One co-created serve, brand story and menu QR for 12 months.'),('Merchandise','One agreed bay; voluntary distribution of sponsor-supplied stock.'),('Quarterly events','Four sponsor-led space uses; 20% off pre-agreed catering.'),('Two-week feature','One annual spotlight for the signature drink and QR campaign.'),('Reporting','Weekly activity reports and four quarterly partnership reviews.')]
for i,(title,body) in enumerate(benefits):
    y=229+i*88; line(590,y-12,786); txt(title,590,y,23,'Bold',GREEN); para(body,839,y,529,19)
foot('Extra drinks, events, production, dedicated staffing and bespoke activations are separately scoped and priced. The term starts when agreed core benefits become available; opening-delay terms are recorded in the agreement.')

# 10. Measurement separates activity from outcomes; no fake numbers.
start()
head('Know what happened. Learn what worked.',size=64)
para('Weekly activity reports. Four quarterly partnership reviews.',66,207,1260,25)
data=[('Delivery','Menu-live status, feature dates and benefits delivered.'),('Participation','Verified paid drink orders, tracked QR visits, merchandise units and event check-ins.'),('Voluntary interest','Validated offer redemptions and explicit opt-in enquiries.'),('Business outcomes','Trials, usage or sales only when supplied by the sponsor, with attribution notes.')]
for i,(label,body) in enumerate(data):
    y=305+i*76; line(64,y-12,1312); txt(label,64,y,26,'Display',GREEN); para(body,407,y+2,947,21)
rect(64,640,1312,48,GREEN)
txt('Orders ≠ unique guests. QR visits ≠ leads. Report missing data and corrections explicitly.',85,651,19,'Body',PAPER)
foot('Aggregate reporting by default. Individual details require separate consent naming purpose and recipient. Member, attendee and newsletter contact lists are not included.')

# 11. A specific next action, no invented contacts or availability claim.
start(GREEN,True)
head('Let’s find your\nplace on the menu.',64,120,880,80,PAPER)
para('Start with your category, your audience\nand what you want them to discover.',68,326,740,26,color=PAPER)
line(68,442,1308,'#547264')
for i,(a,b) in enumerate([('Confirm the fit','Agree your category, objective and intended audience.'),('Shape the partnership','Receive the drink brief, annual benefit schedule and agreement.'),('Approve the launch','Confirm creative, responsibilities, timing and opening-delay terms.')]):
    x=68+i*448; txt(a,x,476,31,'Display',PAPER); para(b,x,535,390,21,color='#D6DFD3')
txt('Request a category-fit conversation with HSR Founders Club.',68,654,22,'Bold',PAPER)
foot('Planned opening: 30 November 2026. Five founding categories in the launch plan; category availability and final terms confirmed in writing.',True)

C.save()
bad=[b for b in boxes if b['x']<0 or b['y']<0 or b['x']+b['w']>W+1 or b['y']+b['h']>H]
(ROOT/'layout-check.json').write_text(json.dumps({'pages':page,'text_boxes':len(boxes),'out_of_bounds':bad},indent=2))
assert not bad, bad
print(OUT)
