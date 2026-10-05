from pathlib import Path
import json,subprocess,html,hashlib
from PIL import Image,ImageDraw
r=Path(__file__).resolve().parents[1]
home=json.loads((r/'review/home-catalog.json').read_text())
# Rename once, via temporary names, to avoid numbering collisions.
if not (r/'review/renumbered.json').exists():
 for i,x in enumerate(home): (r/x['source_file']).rename(r/f'.renumber-{i}.png')
 for i,x in enumerate(home): (r/f'.renumber-{i}.png').rename(r/x['file'])
 (r/'review/renumbered.json').write_text(json.dumps({x['source_file']:x['file'] for x in home},indent=2)+'\n')
remap={x['source_file']:x['file'] for x in home}
prompts=json.loads((r/'PROMPTS.json').read_text())
if not prompts.get('finalized'):
 last={}
 for i,g in enumerate(prompts['generations']): last[g['file']]=i
 for i,g in enumerate(prompts['generations']):
  orig=g['file']; g['generation_file']=orig;g['file']=remap.get(orig,orig)
  g['references_at_generation']=g['references']
  g['references']=[str(Path(p).parent/remap.get(Path(p).name,Path(p).name)) if 'astra-design/' in p else p for p in g['references']]
  g['status']='selected' if last[orig]==i else 'superseded'
  if (orig=='home-20-membership-focus.png' and 'Hover/focus state of same membership scene.' in g['prompt']) or (orig=='interaction-05-play.png' and 'People selector alternate state.' in g['prompt']):
   g['status']='failed';g['error']='HTTP 504: bb connect timed out waiting for tunnel client; later built-in retry succeeded.'
  g['attempt']=i+1
 prompts['finalized']=True
 prompts['reference_note']='Self-references denote the immediately preceding variant, not the selected final file. Original filenames are retained for audit. Superseded variants were visually reviewed and replaced; failed requests produced no selected artifact.'
 (r/'PROMPTS.json').write_text(json.dumps(prompts,ensure_ascii=False,indent=2)+'\n')
extras=[
('mobile-01-dawn.png','Mobile / dawn','Whole facade, portrait composition and location copy.'),
('mobile-02-courtyard.png','Mobile / first floor','Complete courtyard above its caption and Explore action.'),
('mobile-03-memberships.png','Mobile / memberships','Regular selected, with direct tier labels and visible previous/next controls.'),
('mobile-04-call.png','Mobile / invitation','One chair and a quiet booking invitation.'),
('interaction-01-explore-closed.png','Explore / closed + focus','Underline, dot and leader redraw; the world remains readable.'),
('interaction-02-explore-open.png','Explore / open + decoded','Longer content, a dimmed court, walkthrough and call actions.'),
('interaction-03-artists.png','Who’s inside / Artists','Sketching, shared perspectives and unchanged architecture.'),
('interaction-04-music.png','Who’s inside / Music','A small acoustic conversation; no stage or crowd.'),
('interaction-05-play.png','Who’s inside / Play','Two people and one quiet board game.'),
('state-01-loading.png','Loading','One petal, honest status and a still-mode escape.'),
('state-02-not-found.png','404 / this room isn’t here','A closed book, useful return navigation and booking access.'),
('state-03-booking-unavailable.png','Booking / unavailable','Honest empty-destination state; no fake times or confirmation.'),
('state-04-load-failed.png','Loading / recovery','Retry or continue without motion.'),
('state-05-without-motion.png','Without motion / first chapter','Still scene art with explicit chapter controls.'),
('walkthrough-01-courtyard.png','Walkthrough / courtyard','Eye-level photo-grounded room tour with previous/next and return-to-story.'),
('system-01-type-and-hud.png','System / type + HUD','Three type families, corner placement, scale and interaction states.'),
('system-02-palette-fog.png','System / palette + fog','House materials and five hour chips with exact hex labels.'),
('system-03-components.png','System / components','Actions, callouts, sound, scroll and memberships as world objects.')]
allitems=[dict(file=x['file'],title=x['title'],caption=x['seen'],group='Homepage',range=x['range']) for x in home]+[dict(file=f,title=t,caption=c,group='Mobile' if f.startswith('mobile') else 'System' if f.startswith('system') else 'States and walkthrough') for f,t,c in extras]
assert len(allitems)==42
sizes=[]
for x in allitems:
 p=r/x['file']; im=Image.open(p);original=im.size;expected=(390,844) if p.name.startswith('mobile-') else (1920,1080)
 if original!=expected:
  result=subprocess.run(['sips','-z',str(expected[1]),str(expected[0]),str(p)],capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stderr)
 with Image.open(p) as im:
  im.verify()
 with Image.open(p) as im:assert im.size==expected
 sizes.append(dict(file=p.name,native_size=list(original),export_size=list(expected)))
(r/'review/export-sizes.json').write_text(json.dumps(sizes,indent=2)+'\n')
(r/'MANIFEST.json').write_text(json.dumps(allitems,ensure_ascii=False,indent=2)+'\n')
intro='''# Space — complete website design comps

**42 image-generated comps:** 24 consecutive homepage frames at 1920×1080, four mobile views at 390×844, five interaction views, five utility/recovery states, one walkthrough view and three system boards. Generated and reviewed on 5 October 2026 with the built-in image model; exported to exact dimensions. This is a design delivery, not website implementation.

Open [the contact sheet](boards.html) to review everything in order. [CONTENT.md](CONTENT.md) contains the complete copy master, including all four floor overlays, memberships and recovery messages. [PROMPTS.json](PROMPTS.json) contains every generation/edit attempt. [MANIFEST.json](MANIFEST.json) is the file inventory.

The direction is the approved house and materials, with Igloo’s quiet corner HUD and fog-concealed scene changes. The user’s additions are incorporated: real content throughout, plus chairs, books and petals falling from the sky at the beginning. The objects settle into fog before the closed house appears, then return in the membership and final invitation scenes. The sequence is one journey through a day, ending at Book a call.

The supplied current brand facts and approved boards supersede the older painted-street direction in DESIGN.md and the old name in PRODUCT.md. Use **Space**, JetBrains Mono, Schibsted Grotesk and Newsreader; never import the old Bungee/pill/bright-sign system into this design.

## Tier naming proposal

**Visit / Regular / House** maps to the working Silver / Gold / Platinum. Visit describes mostly walk-in access with table booking; Regular describes quiet spaces and game rooms; House describes broader access with team and guests. These names are proposals. Each comp includes **Needs —**, with “Requirements to be confirmed on a call.” Eligibility, guest limits, booking terms and pricing are not invented. The full copy and boundaries are in CONTENT.md.

## Homepage sequence

Ranges are normalized scroll progress, inclusive at the start and exclusive at the end except 100%. They include hold time; the exact image is the representative pose within that range. A focus/selection frame shows an interaction state that can occur during its range, not a mandatory automatic selection.

'''
paragraphs=[]
for i,x in enumerate(home,1):
 paragraphs.append(f"**{i:02d} — [{x['title']}]({x['file']}) · {x['range'][0]}–{x['range'][1]}% · {x['hour']} IST.** {x['seen']} Camera: {x['camera']} Fog: {x['fog']} Build mapping: `{x['modules']}`.\n")
tail=(r/'review/spec-tail.md').read_text()
tail=tail.replace('| `state-03-booking-unavailable.png` |', '| `state-04-load-failed.png` | Retry and Continue without motion remain usable when the main scene fails to load. |\n| `state-05-without-motion.png` | First stop of the six-chapter still reader; direct Previous/Next controls replace scrolling animation. |\n| `state-03-booking-unavailable.png` |')
tail=tail.replace('Keep the same chapter order, all tier content and booking access.', 'Use six still chapters: house; lower level; café; first floor with interest picker; terrace with the night-rhythm copy; memberships with the final invitation. Keep the same narrative order, all tier content and booking access. The final Next becomes Book a call.')
tail=tail.replace('and three swapped corner labels on the type board.', 'three swapped corner labels on the type board; and a wrong gulmohar hex label on the palette board.')
(r/'README.md').write_text(intro+'\n'.join(paragraphs)+'\n'+tail)
styles='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#e8e4da;color:#252b2b;font:16px/1.5 system-ui,sans-serif}header{padding:40px 4vw 24px;border-bottom:1px solid #b3a68b}h1{font:400 32px/1.1 ui-monospace,monospace;margin:0 0 20px}header p{max-width:850px}nav{display:flex;gap:20px;flex-wrap:wrap}a{color:inherit;text-underline-offset:4px}a:focus-visible{outline:2px solid #383b3a;outline-offset:5px}main{padding:0 4vw 50px}h2{font:400 20px/1.4 ui-monospace,monospace;margin:40px 0 20px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:32px 24px}figure{margin:0}figure>a{display:block;background:#d1bfc2;line-height:0}img{width:100%;height:auto;display:block;object-fit:contain}figcaption{padding:12px 0 18px;border-bottom:1px solid #c4bcae}figcaption strong{font:500 14px/1.4 ui-monospace,monospace;display:block;margin-bottom:6px}figcaption p{margin:0;font-size:14px}.mobile{grid-template-columns:repeat(4,minmax(0,1fr))}.meta{font:12px/1.5 ui-monospace,monospace;color:#62645c}footer{padding:32px 4vw;border-top:1px solid #b3a68b}@media(max-width:760px){.grid{grid-template-columns:1fr}.mobile{grid-template-columns:repeat(2,minmax(0,1fr))}header{padding-top:28px}h1{font-size:25px}}@media print{@page{size:A3 landscape;margin:15mm}header{break-after:page}.grid,.mobile{display:block}figure{break-inside:avoid;break-after:page}img{max-height:225mm;width:100%;object-fit:contain}nav{display:none}}'''
head='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Space — complete design sequence</title><style>'''+styles+'''</style></head><body><header><h1>SPACE / A DAY IN THE HOUSE</h1><p>42 finished design comps, including the falling-object opening, content, 24-frame homepage, mobile, interactions, recovery, walkthrough and system. Select any image to open the full export.</p><p class="meta">DESIGN HANDOFF · 5 OCTOBER 2026 · BUILT-IN IMAGE GENERATION · NOT WEBSITE IMPLEMENTATION</p><nav><a href="#homepage">Homepage</a><a href="#mobile">Mobile</a><a href="#states">States + walkthrough</a><a href="#system">System</a><a href="README.md">Build spec</a><a href="CONTENT.md">Copy master</a><a href="PROMPTS.json">Prompts</a></nav></header><main>'''
body=[]
for grp,anchor in [('Homepage','homepage'),('Mobile','mobile'),('States and walkthrough','states'),('System','system')]:
 body.append(f'<section id="{anchor}"><h2>{html.escape(grp)}</h2><div class="grid'+(' mobile' if grp=='Mobile' else '')+'">')
 for x in [a for a in allitems if a['group']==grp]:
  label=x['file'].removesuffix('.png')+' / '+x['title'];rng=f" · {x['range'][0]}–{x['range'][1]}%" if 'range' in x else ''
  body.append(f'<figure><a href="{x["file"]}" aria-label="Open {html.escape(x["title"],quote=True)}"><img src="{x["file"]}" alt="{html.escape(x["caption"],quote=True)}" loading="lazy" width="{390 if grp=="Mobile" else 1920}" height="{844 if grp=="Mobile" else 1080}"></a><figcaption><strong>{html.escape(label+rng)}</strong><p>{html.escape(x["caption"])}</p></figcaption></figure>')
 body.append('</div></section>')
footer='''</main><footer><p>Decisions: Visit / Regular / House; eligibility and guest rules; final invitation copy; booking destination.</p><p class="meta">Geometry and type remain subject to the measured house and exact build fonts. See README for reviewed limitations. This design task made no site edits or commit.</p></footer></body></html>'''
(r/'boards.html').write_text(head+''.join(body)+footer)
# Inspection-only contact sheets, not substitutes for generated deliverables.
for label,items in [('home',allitems[:24]),('secondary',allitems[24:])]:
 cols=4;w=1600;cw=400;ch=280 if label=='home' else 350
 canvas=Image.new('RGB',(w,((len(items)+cols-1)//cols)*ch),'#e8e4da');draw=ImageDraw.Draw(canvas)
 for i,x in enumerate(items):
  im=Image.open(r/x['file']);im.thumbnail((cw,ch-45));xx=i%cols*cw;yy=i//cols*ch
  canvas.paste(im,(xx+(cw-im.width)//2,yy));draw.text((xx+8,yy+ch-38),x['file'],fill='#252b2b')
 canvas.save(r/f'review/{label}-contact.jpg',quality=90)
print(json.dumps({'images':len(allitems),'home':len(home),'mobile':4,'prompts':len(prompts['generations']),'failed_requests':sum(g['status']=='failed' for g in prompts['generations'])}))
