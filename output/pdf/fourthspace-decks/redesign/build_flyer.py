"""Fourthspace introduction and sponsor-benefits flyer, without pricing."""
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import build_sponsorship as d

OUT=d.ROOT/'Fourthspace-Partnership-Flyer.pdf'
d.W,d.H=900,1273
d.C=canvas.Canvas(str(OUT),pagesize=A4,pageCompression=1)
d.C.scale(A4[0]/d.W,A4[1]/d.H)
d.C.setTitle('Fourthspace | Founding brand partnerships')
d.C.setAuthor('Fourthspace / HSR Founders Club')
d.C.setSubject('The house and founding partnership benefits; no pricing')
d.page=1; d.boxes=[]
d.rect(0,0,900,1273,d.PAPER)
d.rect(0,0,900,386,d.GREEN)
d.txt('FOURTHSPACE',52,30,20,'Bold',d.PAPER)
d.head('A house for founders.\nA place for your brand.',52,91,796,55,d.PAPER)
d.para('A community house being built in HSR Layout, Bengaluru, with a public café, founder-only membership, workspaces, meeting rooms and gatherings.',54,235,788,24,color=d.PAPER,leading=32)
d.txt('FROM THE TEAM BEHIND HSR FOUNDERS CLUB',54,345,13,'Bold',d.PAPER)

d.photo('branded-cup.png',52,420,244,292,'contain')
d.head('Become part of\nthe everyday.',336,418,510,48)
d.para('Co-create a signature coffee or mocktail that brings your brand onto the Fourthspace menu, with your story and a QR link to your website or offer.',338,539,506,22,leading=29)
d.txt('ONE CATEGORY / 12 MONTHS / HSR HOUSE',338,674,13,'Bold',d.RUST)
d.para('Illustrative AI-generated drink and packaging concept; final creative requires approval.',52,724,796,12,color=d.MUTED,leading=16)

d.head('What your partnership includes',52,765,796,37)
benefits=[
    ('Your signature drink','One co-created coffee or mocktail, with a brand story and menu QR for 12 months.'),
    ('Merchandise distribution','One agreed bay for your supplied stock, offered voluntarily to agreed visitor groups.'),
    ('Quarterly event-space use','Four sponsor-led uses a year, one per quarter, plus 20% off pre-agreed event catering.'),
    ('Category exclusivity','One defined sponsor category at the HSR house for the contracted term.'),
    ('A two-week spotlight','One annual feature supporting your signature drink, story and QR campaign.'),
    ('Reporting & reviews','Weekly activity reports and four quarterly reviews of delivery and outcomes.')
]
for i,(title,body) in enumerate(benefits):
    x=52+(i%2)*416; y=833+(i//2)*96
    d.line(x,y-10,380)
    d.txt(title,x,y,22,'Display',d.GREEN)
    d.para(body,x,y+34,380,17,leading=22)

d.rect(52,1126,796,62,d.GREEN)
d.txt('Explore a founding category partnership.',69,1136,23,'Display',d.PAPER)
d.txt('Start a conversation with HSR Founders Club.',69,1165,13,'Body',d.PAPER)
d.para('Sponsor runs its events; production and dedicated staffing are extra. Unused quarterly uses expire. Catering discount excludes taxes and service charges. No member lists or guaranteed leads. Final terms and launch timing agreed in writing.',52,1201,796,11.5,color=d.MUTED,leading=15)
d.txt('PLANNED OPENING / 30 NOVEMBER 2026',52,1252,10,'Bold',d.GREEN)
d.txt('FIVE FOUNDING CATEGORIES IN THE LAUNCH PLAN',530,1252,10,'Body',d.GREEN)
d.C.showPage(); d.C.save()
bad=[b for b in d.boxes if b['x']<0 or b['y']<0 or b['x']+b['w']>d.W+1 or b['y']+b['h']>d.H]
assert not bad,bad
(d.ROOT/'flyer-layout-check.json').write_text(json.dumps({'pages':1,'text_boxes':len(d.boxes),'out_of_bounds':bad},indent=2))
print(OUT)
