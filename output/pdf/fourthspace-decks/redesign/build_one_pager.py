"""Rebuild the unchanged sponsorship deck and a matching A4 introduction."""
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import build_sponsorship as d

OUT = d.ROOT / 'Fourthspace-Introduction-One-Pager.pdf'
# Work in a generous design coordinate system, scaled to true A4 at export.
d.W, d.H = 900, 1273
d.C = canvas.Canvas(str(OUT), pagesize=A4, pageCompression=1)
d.C.scale(A4[0]/d.W, A4[1]/d.H)
d.C.setTitle('Fourthspace | A house for founders')
d.C.setAuthor('Fourthspace / HSR Founders Club')
d.C.setSubject('An introduction to Fourthspace in HSR Layout, Bengaluru')
d.page=1
d.boxes=[]

d.rect(0,0,900,1273,d.PAPER)
d.rect(0,0,900,402,d.GREEN)
d.txt('FOURTHSPACE',56,34,20,'Bold',d.PAPER)
d.head('A house for founders.\nA place to return to.',56,99,788,62,d.PAPER)
d.para('Fourthspace is a community house being built in HSR Layout, Bengaluru: a public café, founder workspaces, meeting rooms and a programme of gatherings under one roof.',58,263,778,25,color=d.PAPER,leading=34)

for i,(name,label) in enumerate([('cafe','A public café'),('court','Space to connect'),('event','Room to gather')]):
    x=56+i*270
    d.photo(f'blender/{name}-baked.png',x,436,248,174,'contain')
    d.txt(label,x,627,23,'Display',d.GREEN)
d.para('Proposed fit-outs shown in Blender renders. Final room uses and capacities are subject to review.',56,671,788,13,color=d.MUTED,leading=18)

d.head('Good conversations need continuity.',56,730,788,40)
rows=[
    ('Visit the café','Open to founders and non-founders: a place for coffee, conversation and selected public events.'),
    ('Build alongside others','Founder-only membership brings spaces to work and meet, founder sessions, and a board for asks and offers.'),
    ('Keep coming back','Return for circles, breakfasts, demos and member-hosted gatherings. Let useful relationships develop across visits.')
]
for i,(title,body) in enumerate(rows):
    y=814+i*94
    d.line(56,y-15,788)
    d.para(title,56,y,226,23,'Display',d.GREEN,27)
    d.para(body,316,y,528,21,leading=28)

d.line(56,1110,788)
d.para('From the team behind HSR Founders Club.',56,1133,788,22,'Bold',d.GREEN)
d.para('The house builds on a community already bringing founders together around HSR.',56,1171,788,19,color=d.MUTED,leading=26)
d.txt('HSR LAYOUT, BENGALURU',56,1230,12,'Bold',d.GREEN)
d.txt('PLANNED OPENING / 30 NOVEMBER 2026',472,1230,12,'Body',d.GREEN)
d.C.showPage()
d.C.save()
bad=[b for b in d.boxes if b['x']<0 or b['y']<0 or b['x']+b['w']>d.W+1 or b['y']+b['h']>d.H]
assert not bad,bad
(d.ROOT/'one-pager-layout-check.json').write_text(json.dumps({'pages':1,'format':'A4 portrait','text_boxes':len(d.boxes),'out_of_bounds':bad},indent=2))
print(OUT)
