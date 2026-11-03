"""Editable source for Katte's sponsor-specific PDF proposal. No PowerPoint required."""
from pathlib import Path
import json, shutil, textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
CONFIG = json.loads((ROOT / 'sponsor.json').read_text())
W,H = 1280,720
INK='#18251F'; CREAM='#F8F5ED'; LILAC='#CDC3EB'; ORANGE='#B65025'; GREY='#657067'; LINE='#DCDDD5'
for name, file in [('Body','Arial.ttf'),('Bold','Arial Bold.ttf'),('Display','Arial Black.ttf')]:
    pdfmetrics.registerFont(TTFont(name, '/System/Library/Fonts/Supplemental/'+file))
pdfmetrics.registerFont(TTFont('Unicode','/Users/rejoesudarsan/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts/Ubuntu-R.ttf'))
OUT=ROOT/'Katte-OpenAI-Annual-Drink-Partnership.pdf'
c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
c.setTitle('Katte | Proposed OpenAI Specialty Drink Partnership')
c.setAuthor('Katte')
c.setSubject('One co-created specialty drink. Twelve months. INR 15,00,000 annual sponsorship.')
checks=[]

def rect(x,y,w,h,color,r=0):
    c.setFillColor(HexColor(color)); c.setStrokeColor(HexColor(color))
    if r: c.roundRect(x,H-y-h,w,h,r,fill=1,stroke=0)
    else: c.rect(x,H-y-h,w,h,fill=1,stroke=0)
def text(s,x,y,size=22,font='Body',color=INK):
    s=s.replace('OpenAI',CONFIG['sponsor']).replace('OPENAI',CONFIG['sponsor'].upper())
    c.setFillColor(HexColor(color)); c.setFont(font,size)
    for i,line in enumerate(s.split('\n')):
        tw=pdfmetrics.stringWidth(line,font,size)
        checks.append((c.getPageNumber(),line,x,y+i*size*1.12,tw))
        c.drawString(x,H-y-size*.83-i*size*1.12,line)
def para(s,x,y,width,size=22,color=INK,font='Body',leading=None):
    leading=leading or size*1.36
    words=s.split(); lines=[]; cur=''
    for word in words:
        test=(cur+' '+word).strip()
        if pdfmetrics.stringWidth(test,font,size)>width and cur: lines.append(cur);cur=word
        else:cur=test
    if cur:lines.append(cur)
    for i,line in enumerate(lines):text(line,x,y+i*leading,size,font,color)
    return y+len(lines)*leading
def rule(x,y,w,color=LINE):rect(x,y,w,1,color)
def image(name,x,y,w,h,fit='cover',radius=0):
    p=ASSETS/name
    im=Image.open(p); iw,ih=im.size
    scale=max(w/iw,h/ih) if fit=='cover' else min(w/iw,h/ih)
    dw,dh=iw*scale,ih*scale
    c.saveState()
    path=c.beginPath(); path.roundRect(x,H-y-h,w,h,radius) if radius else path.rect(x,H-y-h,w,h)
    c.clipPath(path,stroke=0,fill=0)
    c.drawImage(ImageReader(im),x+(w-dw)/2,H-y-h+(h-dh)/2,dw,dh,mask='auto')
    c.restoreState()
def brand(x,y,height=30):
    p=ASSETS/'openai-wordmark.png'
    if p.exists():
        im=Image.open(p); w=height*im.width/im.height
        c.drawImage(ImageReader(im),x,H-y-height,w,height,mask='auto')
    else:raise RuntimeError('Official OpenAI wordmark asset is required')
def pill(s,x,y,w,color=ORANGE,fg='#FFFFFF',size=14):
    rect(x,y,w,34,color,17);text(s,x+16,y+9,size,'Bold',fg)
def base(n,label,bg=CREAM,dark=False):
    rect(0,0,W,H,bg);fg=CREAM if dark else INK
    text('katte',48,25,34,'Display',fg)
    text(label.upper(),208,38,12,'Bold',fg)
    text('HSR LAYOUT / BENGALURU',1000,38,12,'Bold',fg)
    rule(48,675,1184,'#526056' if dark else LINE)
    text('PROPOSED PARTNERSHIP  /  OPENAI',48,692,10,'Bold',fg)
    text(f'{n:02d} / 10',1172,692,10,'Bold',fg)
def end():c.showPage()
def arrow(x,y,color=INK):
    c.setStrokeColor(HexColor(color));c.setLineWidth(2)
    c.line(x,H-y,x+28,H-y);c.line(x+20,H-y+7,x+28,H-y);c.line(x+20,H-y-7,x+28,H-y)

# 01 — clear invitation; actual sponsor logo is independent of concept photography.
base(1,'Annual specialty drink sponsorship')
text('A signature drink.\nA year of\nyour brand.',48,108,56,'Display')
para('An invitation to OpenAI to co-create a specialty drink at Katte.',50,314,530,24)
rect(48,394,530,229,LILAC,28)
text('katte',78,426,41,'Display')
text('×',235,434,30,'Body');brand(285,433,35)
text('ONE DRINK  /  TWELVE MONTHS',78,503,15,'Bold')
text('₹15,00,000',78,539,40,'Unicode')
text('Annual sponsorship',320,552,17,'Body')
image('openai-coffee.png',637,95,595,546,'contain',28)
text('AI-generated concept. Proposed branding; subject to approval.',670,647,11,'Body',GREY)
end()

# 02 — sponsor relevance, framed as intended audience and campaign objectives.
base(2,'The opportunity')
text('Meet people\nin the middle\nof an idea.',48,111,64,'Display')
para('Katte is being shaped as a place for founders and builders to return, exchange ideas and spend time together.',50,368,510,24)
pill('INTENDED AUDIENCE',50,526,188)
text('Founders · Operators · Builders',50,580,23,'Bold')
rect(657,103,575,526,LILAC,28)
text('Why OpenAI',692,139,36,'Display')
items=[('01','Familiarity','A recognisable drink creates another opportunity to encounter the brand.'),('02','Useful discovery','An optional prompt guide connects the coffee moment to a practical task.'),('03','A next step','An opt-in link lets an interested guest continue to an approved OpenAI destination.')]
for i,(num,title,body) in enumerate(items):
    yy=210+i*130;text(num,692,yy,16,'Bold',ORANGE);text(title,744,yy-3,24,'Bold');para(body,744,yy+34,438,19)
text('Campaign objectives; audience size and outcomes are not claimed.',50,643,12,'Body',GREY)
end()

# 03 — one product, one specific recipe proposal.
base(3,'The signature concept')
image('openai-coffee.png',48,99,537,548,'contain',26)
pill('PROPOSED FOR OPENAI',655,111,218)
text(CONFIG['drink_name'],652,176,58,'Display')
text('Jaggery iced filter coffee',655,259,27,'Bold')
para('A familiar Bengaluru coffee ritual, served cold with a mellow jaggery finish.',655,315,520,25)
rule(655,424,528)
text('THE RECIPE DIRECTION',655,448,13,'Bold',ORANGE)
para('Filter coffee · milk · jaggery · ice',655,478,530,23)
para('Developed through tasting with the sponsor. Final recipe, portion and retail price agreed before launch.',655,542,520,18,color=GREY)
text('Contains milk. AI-generated product concept; not a finished recipe.',70,646,11,'Body',GREY)
end()

# 04 — actual menu-tab mockup, no functioning QR or purchase claim.
base(4,'The specialty drinks tab')
text('Here is how guests find it.',48,104,52,'Display')
rect(48,192,870,443,'#FFFFFF',25)
text('katte',78,217,32,'Display')
text('Coffee',280,231,17);text('Tea',380,231,17);pill('Specialty drinks',462,220,176,INK);text('Food',683,231,17)
rule(78,275,810)
image('openai-coffee.png',80,297,255,308,'contain',15)
text('SPECIALTY COLLABORATION',365,309,12,'Bold',ORANGE)
text(CONFIG['drink_name'],365,349,34,'Display')
text('Jaggery iced filter coffee',365,403,20,'Bold')
para('Filter coffee, milk and jaggery, poured over ice. Contains milk.',365,443,480,18)
text('Proposed with',365,517,13,'Body',GREY);brand(468,512,23)
text('₹190*',365,563,26,'Unicode')
rect(949,192,283,443,LILAC,25)
text('A clear\nplace for\nyour drink.',973,231,31,'Display')
para('Name, flavour, brand and price together at the point of choice.',975,385,230,21)
para('One specialty drink is sponsored. Other menu categories remain Katte’s.',975,507,230,17)
text('Menu mockup. *Illustrative customer price, subject to recipe costing. No ordering or payment function.',50,648,11,'Body',GREY)
end()

# 05 — a concrete value example, with execution and attribution boundaries.
base(5,'An example of sponsor value',INK,True)
text('A coffee. A useful prompt.\nA reason to try.',48,104,53,'Display',CREAM)
steps=[('01','ORDER','A guest chooses\nPrompt & Pour.'),('02','EXPLORE','They scan a table card\nfor a founder prompt.'),('03','TRY','They choose to continue\nto ChatGPT.'),('04','RETURN','The drink and useful\nexperience build familiarity.')]
for i,(num,head,body) in enumerate(steps):
    xx=48+i*300;text(num,xx,269,18,'Bold',LILAC);text(head,xx,306,24,'Bold',CREAM);text(body,xx,351,19,'Body',CREAM)
    if i<3:arrow(xx+243,314,LILAC)
rect(48,451,1184,163,LILAC,24)
text('EXAMPLE PROMPT CARD',76,476,12,'Bold')
para('“Help me turn this business idea into five customer-interview questions. Ask me about my customer and assumptions first.”',76,510,1070,26,font='Bold')
text('Proposed activation. QR destination and content require agreement. Product usage is not inferred from a scan.',50,643,12,'Body','#B8C4BA')
end()

# 06 — deliverables with no fabricated quantities.
base(6,'The annual package')
text('Your year with Katte.',48,106,56,'Display')
text('ONE CO-CREATED SPECIALTY DRINK',50,185,14,'Bold',ORANGE)
tiles=[('01','Recipe & identity','Collaborative tasting, drink naming and approved presentation.'),('02','12-month placement','The signature drink listed throughout the agreed partnership term.'),('03','Serving materials','Agreed sleeves, coasters or table cards carrying the collaboration.'),('04','Launch tasting','A drink introduction with the serving allowance agreed in advance.'),('05','Optional digital link','A dedicated destination for a prompt guide, offer or brand story.'),('06','Reporting & reviews','Monthly activity reporting and a quarterly partnership review.')]
for i,(num,title,body) in enumerate(tiles):
    col=i%3;row=i//3;xx=48+col*404;yy=252+row*184
    rule(xx,yy,367);text(num,xx,yy+18,15,'Bold',ORANGE);text(title,xx,yy+54,25,'Bold');para(body,xx,yy+96,350,20)
text('Proposed scope. Production quantities, availability and launch details are recorded in the final agreement.',50,648,12,'Body',GREY)
end()

# 07 — practical cadence.
base(7,'Create · launch · continue')
text('From first taste\nto familiar order.',48,103,56,'Display')
image('openai-wide.png',48,284,550,347,'cover',25)
rh=[('BEFORE LAUNCH','Make it yours','Agree the objective, taste the recipe and approve the drink identity.'),('LAUNCH','Introduce the signature','Release the drink, serving materials and agreed tasting activity.'),('MONTHLY','See what is happening','Review orders, availability and tracked digital engagement.'),('QUARTERLY','Keep it relevant','Review feedback and agree any recipe or content refresh.')]
for i,(tag,head,body) in enumerate(rh):
    yy=109+i*134;text(tag,655,yy,12,'Bold',ORANGE);text(head,655,yy+28,25,'Bold');para(body,655,yy+66,540,19)
text('The twelve-month term begins when the approved drink launches.',50,648,12,'Body',GREY)
end()

# 08 — measurement connects sponsor benefits to evidence, without invented forecasts.
base(8,'Measurement')
text('Know what people choose.',48,108,54,'Display')
para('A shared scorecard keeps drink engagement and business outcomes distinct.',50,191,1080,24)
rows=[('Drink engagement','Paid units, tasting units and availability','Katte billing and service records'),('Digital interest','Campaign-page visits and outbound clicks','Agreed campaign tracking'),('Qualified interest','Voluntary enquiries or registrations','Opt-in form, if included'),('Product outcomes','Trials, usage or paid conversion','Sponsor-side attribution, if available')]
rect(48,274,1184,48,INK,8)
text('WHAT WE MEASURE',68,290,12,'Bold',CREAM);text('EXAMPLE SIGNALS',370,290,12,'Bold',CREAM);text('EVIDENCE SOURCE',852,290,12,'Bold',CREAM)
for i,(a,b,d) in enumerate(rows):
    yy=342+i*64;text(a,68,yy,21,'Bold');para(b,370,yy,450,18);para(d,852,yy,350,18);rule(68,yy+48,1142)
para('Orders are not unique people. Scans are not product usage. Reach, lead and sales targets must be agreed from a verified baseline.',50,616,1150,17,color=GREY)
end()

# 09 — exact user-authorized annual quote.
base(9,'The annual investment',LILAC)
text('One drink.\nTwelve months.',48,107,64,'Display')
text('₹15,00,000',48,300,112,'Unicode')
text('INR FIFTEEN LAKH  /  ANNUAL SPONSORSHIP',54,436,17,'Bold')
rule(50,493,1182,'#A89DBE')
para('Includes the proposed annual package on page 6. Customers pay separately for the drink.',52,527,675,23)
para('Tax treatment, payment milestones, production quantities and any extra activations will be specified in the final agreement.',842,527,366,18)
text('One specialty drink at Katte, HSR Layout, Bengaluru.',52,642,15,'Bold')
end()

# 10 — no invented contact details; a reusable invitation.
base(10,'The invitation')
text('Let’s make\nyour signature.',48,108,64,'Display')
para('A drink worth ordering.\nA collaboration worth coming back to.',50,291,530,25)
rect(48,421,536,168,LILAC,24)
text('katte',76,448,40,'Display');text('×',235,456,30);brand(285,454,35)
text('Agree the brief. Taste the concept. Set the date.',76,526,18,'Bold')
image('openai-wide.png',624,109,608,480,'cover',28)
text('DISCUSSION PROPOSAL  /  OCTOBER 2026',50,616,12,'Bold',ORANGE)
text('OpenAI is a prospective sponsor. No partnership or endorsement is implied.',50,641,12,'Body',GREY)
text('OpenAI marks belong to OpenAI. Brand reference: openai.com/brand. All mockups are illustrative.',50,658,10,'Body',GREY)
end()
c.save()
for page,line,x,y,width in checks:
    if x<0 or x+width>W+1 or y<0 or y>H-8:
        raise RuntimeError(f'Text overflow page {page}: {line!r} at {x},{y} width {width}')
(ROOT/'layout-check.json').write_text(json.dumps({'pages':10,'text_runs':len(checks),'overflow':False},indent=2))
print(OUT)
