from pathlib import Path
from html.parser import HTMLParser
import json,hashlib,subprocess,re
from PIL import Image
r=Path(__file__).resolve().parents[1];repo=r.parents[1]
manifest=json.loads((r/'MANIFEST.json').read_text());prompts=json.loads((r/'PROMPTS.json').read_text())
assert len(manifest)==42
expected={x['file'] for x in manifest};actual={p.name for p in r.glob('*.png')};assert expected==actual,(expected-actual,actual-expected)
for name in sorted(expected):
 with Image.open(r/name) as im:
  assert im.format=='PNG';assert im.size==((390,844) if name.startswith('mobile-') else (1920,1080));im.verify()
selected={x['file'] for x in prompts['generations'] if x['status']=='selected'};assert selected==expected,(expected-selected,selected-expected)
class Links(HTMLParser):
 def __init__(self):super().__init__();self.img=[];self.links=[];self.ids=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  if tag=='img':self.img.append(a['src']);assert a.get('alt')
  if tag=='a':self.links.append(a.get('href',''))
p=Links();p.feed((r/'boards.html').read_text());assert p.img==[x['file'] for x in manifest]
for link in p.links:
 if link.startswith('#'):assert link[1:] in p.ids
 else:assert (r/link).is_file(),link
for file in ['README.md','CONTENT.md']:
 for link in re.findall(r'\]\(([^)]+)\)',(r/file).read_text()):assert (r/link).exists(),(file,link)
status=subprocess.check_output(['git','status','--short','--untracked-files=all'],cwd=repo,text=True)
(r/'review/final-status.txt').write_text(status)
outside=[s for s in status.splitlines() if not s[3:].startswith('reference/astra-design/')];assert not outside,outside
changed=subprocess.check_output(['git','diff','--name-only','--','site/'],cwd=repo,text=True);assert not changed
before=(r/'review/site-before.sha1').read_text();after='';drift=[]
for line in before.splitlines():
 sha,path=line.split('  ',1);got=hashlib.sha1((repo/path).read_bytes()).hexdigest();after+=got+'  '+path+'\n'
 if got!=sha:
  assert path in ['site/src/world/details.js','site/src/world/world.js'],path
  assert hashlib.sha1(subprocess.check_output(['git','show','2eedc67:'+path],cwd=repo)).hexdigest()==sha
  assert hashlib.sha1(subprocess.check_output(['git','show','8dba5c7:'+path],cwd=repo)).hexdigest()==got
  drift.append(path)
(r/'review/site-after.sha1').write_text(after)
report={'png_count':42,'homepage_count':24,'mobile_count':4,'desktop_and_system_size':[1920,1080],'mobile_size':[390,844],'all_pngs_decode':True,'contact_sheet_order_and_links_valid':True,'selected_prompt_for_every_file':True,'generation_attempts':len(prompts['generations']),'failed_requests':sum(x['status']=='failed' for x in prompts['generations']),'site_tracked_diff':False,'source_hashes_match':not drift,'concurrent_source_changes':drift,'concurrent_commit':'8dba5c7','baseline_source_commit':'2eedc67','task_site_edits':False,'changed_paths_outside_output':outside,'visual_review':'All generated outputs individually inspected; two final contact sheets inspected; rejected variants and corrections documented. Exact font identity and surveyed geometry not guaranteed by raster generation.','implementation':'None; no product build or browser workflow claimed.','commit_made':False}
(r/'review/validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
