"""Rebuild with bundled Python; dependencies from requirements.txt; optional KATTE_MAP_DEPS path.
Source coordinates are used directly, with no display jitter or invented points.
"""
from pathlib import Path
import sys,json,csv,math,collections,urllib.request,os
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,os.environ.get('KATTE_MAP_DEPS','/tmp/katte-map-deps'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
D=json.loads((ROOT/'hsr-startups-source.json').read_text())
rows=[r for r in D['startups'] if r['status']!='former']
assert len(rows)==116 and len({r['slug'] for r in rows})==116
fields=['slug','name','status','confidence','geocodePrecision','lat','lng','address','hsrSector','verifiedOn','sources','notes']
with (ROOT/'hsr-locations-filtered.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for r in rows:w.writerow({k:(r['at'][k] if k in ['lat','lng'] else json.dumps(r[k]) if k=='sources' else r.get(k,'')) for k in fields})
R=6378137
lat0=np.mean([r['at']['lat'] for r in rows]);scale=math.cos(math.radians(lat0))
def xy(lon,lat):return R*np.radians(lon),R*np.log(np.tan(np.pi/4+np.radians(lat)/2))
x,y=xy(np.array([r['at']['lng'] for r in rows]),np.array([r['at']['lat'] for r in rows]))
pad=270/scale
extent=[min(x)-pad,max(x)+pad,min(y)-pad,max(y)+pad]
# Render downloaded OSM road geometry directly; no tile API dependency.
basemap=None
roadfile=ROOT/'osm-roads.json'
roads=json.loads(roadfile.read_text()).get('elements',[]) if roadfile.exists() else []
cream='#F5F0E5';green='#193E35';rust='#9B4B32'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':green,'axes.labelcolor':green,'xtick.color':green,'ytick.color':green,'font.size':10})
def setup(title,subtitle):
 fig=plt.figure(figsize=(10,6),dpi=150,facecolor=cream)
 fig.text(.055,.945,title,fontsize=22,fontweight='bold');fig.text(.055,.903,subtitle,fontsize=10)
 ax=fig.add_axes([.055,.20,.70,.65],facecolor=cream)
 for road in roads:
  geom=road.get('geometry',[])
  if not geom:continue
  rx,ry=xy(np.array([p['lon'] for p in geom]),np.array([p['lat'] for p in geom]))
  major=road.get('tags',{}).get('highway') in ['primary','secondary','tertiary','trunk']
  ax.plot(rx,ry,color='#C3C1B7' if major else '#D9D6CD',lw=1.6 if major else .7,zorder=0)
 # Geographic anchors from source places (positions not independently re-geocoded).
 for slug,label,offset in [('315-work-avenue-16th-cross-sector-6','16th Cross · Sector 6',(-88,-22)),('315-work-avenue-17th-cross-sector-4','17th Cross · Sector 4',(-85,10)),('attic-space','Outer Ring Road',(-30,15))]:
  place=next((p for p in D['places'] if p['slug']==slug),None)
  if place:
   px,py=xy(place['at']['lng'],place['at']['lat']);ax.annotate(label,(px,py),xytext=offset,textcoords='offset points',fontsize=8,color='#6A7167',zorder=1,bbox={'facecolor':cream,'edgecolor':'none','alpha':.75,'pad':1})
 ax.set(xlim=extent[:2],ylim=extent[2:]);ax.set_aspect('equal')
 # Label longitude/latitude even though rendering uses Web Mercator.
 xt=np.linspace(extent[0]+150,extent[1]-150,4);yt=np.linspace(extent[2]+100,extent[3]-100,4)
 ax.set_xticks(xt,[f'{v/R*180/np.pi:.3f}°E' for v in xt],fontsize=8)
 ax.set_yticks(yt,[f'{(2*np.arctan(np.exp(v/R))-np.pi/2)*180/np.pi:.3f}°N' for v in yt],fontsize=8)
 for s in ax.spines.values():s.set_color('#C0BBAE')
 ax.text(.96,.96,'N ↑',transform=ax.transAxes,ha='right',va='top',fontweight='bold',bbox={'facecolor':cream,'edgecolor':'none','alpha':.9})
 sx=extent[0]+180;sy=extent[2]+160;ax.plot([sx,sx+500/scale],[sy,sy],color=green,lw=3);ax.text(sx,sy+45,'500 m',fontsize=8)
 fig.text(.055,.105,'Source: Akshat Goel · akshatgoel.com/hsr-startups · CC BY 4.0 · source dated 11 Sep 2026',fontsize=8)
 fig.text(.055,.077,'Adapted 22 Oct 2026. Retained dataset: 105 approximate / 11 address-level. Workplace status not independently verified.',fontsize=8)
 fig.text(.055,.049,('Road geometry © OpenStreetMap contributors (ODbL). ' if roads else 'Address-derived geographic anchors. ')+'Coverage is incomplete; no HSR boundary or community ties inferred.',fontsize=8)
 kx,ky=xy(77.639503,12.909688)
 ax.scatter(kx,ky,s=230,marker='*',color=rust,edgecolors=cream,linewidths=1.2,zorder=10)
 ax.annotate('KATTE',(kx,ky),xytext=(10,-17),textcoords='offset points',fontsize=11,fontweight='bold',color=rust,zorder=11,bbox={'facecolor':cream,'edgecolor':'none','alpha':.92,'pad':2})
 return fig,ax
fig,ax=setup('HSR: published company locations','116 source records retained · 2 moved-out entries excluded · no artificial point displacement')
# Bubble areas count records at identical coordinates, never purported buildings.
groups=collections.defaultdict(list)
for i,r in enumerate(rows):groups[(x[i],y[i])].append(r)
for (xx,yy),rr in groups.items():
 c=rust if all(r['confidence']=='low' for r in rr) else green
 ax.scatter(xx,yy,s=23+16*len(rr),c=c,alpha=.8,edgecolors=cream,linewidths=.7,zorder=3)
 # Address precision is a separate property from source confidence.
 if any(r['geocodePrecision']=='address' for r in rr):ax.scatter(xx,yy,s=9,marker='+',c=cream,linewidths=.8,zorder=4)
fig.text(.79,.78,'116',fontsize=31,fontweight='bold');fig.text(.79,.735,'company records',fontsize=10)
fig.text(.79,.66,'66',fontsize=27,fontweight='bold');fig.text(.79,.62,'unique coordinates',fontsize=10)
fig.text(.79,.55,'Marker size reflects records\nat one coordinate.\nShared geocodes may\nrepresent different\naddresses.',fontsize=9,linespacing=1.5,va='top')
fig.text(.79,.32,'Rust: only low-confidence\nrecords at this point.\n+ Address-level record.',fontsize=9,color=rust,linespacing=1.5,va='top')
fig.savefig(ROOT/'hsr-company-locations.png',dpi=150)
fig.savefig(ROOT/'hsr-company-locations-slide.png',dpi=200,bbox_inches=ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.02,1.02))
plt.close(fig)
fig,ax=setup('HSR: relative location density','103 records · 13 low-confidence entries excluded · not activity, footfall or founder density')
xx=np.linspace(extent[0],extent[1],420);yy=np.linspace(extent[2],extent[3],300);gx,gy=np.meshgrid(xx,yy)
bw=250.;density=np.zeros_like(gx)
for px,py,r in zip(x,y,rows):
 if r['confidence']=='low':continue
 density+=np.exp(-.5*(((gx-px)*scale/bw)**2+((gy-py)*scale/bw)**2))
density/=density.max()
cmap=LinearSegmentedColormap.from_list('katte',[(.0,(.96,.94,.90,0)),(.1,(.85,.78,.59,.35)),(.45,(.61,.29,.20,.65)),(1,(.10,.24,.21,.94))])
im=ax.imshow(density,extent=extent,origin='lower',cmap=cmap,vmin=0,vmax=1,zorder=2)
mask=np.array([r['confidence']!='low' for r in rows]);ax.scatter(x[mask],y[mask],s=4,color=green,alpha=.25,zorder=3)
cax=fig.add_axes([.80,.60,.025,.20]);bar=fig.colorbar(im,cax=cax,ticks=[0,.5,1]);bar.ax.tick_params(labelsize=8);fig.text(.79,.83,'Relative density',fontsize=11,fontweight='bold')
fig.text(.79,.54,'Gaussian bandwidth\nσ = 250 metres.\nPeak normalized to 1.\nOne equal weight\nper company record.',fontsize=9,linespacing=1.5,va='top')
fig.text(.79,.31,'Approximate geocodes\nand shared addresses\ncan create hotspots.',fontsize=9,color=rust,linespacing=1.5,va='top')
fig.savefig(ROOT/'hsr-relative-density.png',dpi=150)
fig.savefig(ROOT/'hsr-relative-density-slide.png',dpi=200,bbox_inches=ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.02,1.02))
plt.close(fig)
summary={'katte_pin':{'lat':12.909688,'lng':77.639503,'source':'https://maps.app.goo.gl/5VcSYFTCMnqyX1n5A','provided_by':'user via parent agent; resolved Google Maps search URL'},'source_url':'https://www.akshatgoel.com/hsr-startups','dataset_url':'https://www.akshatgoel.com/hsr-startups.json','source_date':D['verifiedOn'],'retrieved_date':'2026-10-22','license':D['license'],'input_records':len(D['startups']),'excluded_former':2,'retained_records':len(rows),'unique_coordinates':len(groups),'precision':dict(collections.Counter(r['geocodePrecision'] for r in rows)),'confidence':dict(collections.Counter(r['confidence'] for r in rows)),'road_geometries':len(roads),'roads_source':'https://overpass-api.de/api/interpreter','heatmap_records':103,'heatmap_precision':{'approx':93,'address':10},'bandwidth_metres':250,'coordinate_field':'at.lat / at.lng; no jitter','projection':'Web Mercator for rendering; local cosine correction for metre bandwidth','density':'Excludes 13 low-confidence entries; 103 equal-weight records; isotropic Gaussian sum normalized by maximum; no boundary correction; not population density','caveat':'Source methodology claims physical offices; individual notes admit unconfirmed shared registered addresses. No independent office verification; incomplete directory, not census.'}
(ROOT/'map-methods.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
for f in ['hsr-company-locations.png','hsr-relative-density.png']:
 with Image.open(ROOT/f) as im:assert im.size==(1500,900)
