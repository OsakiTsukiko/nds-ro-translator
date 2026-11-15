import sys,os,json,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','lib'))
import relabel, nds as ndsfmt
from PIL import Image
W=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # template root
import shutil
shutil.rmtree(os.path.join(W,'work','gfx_out'),ignore_errors=True)
spec=json.load(open(os.path.join(W,'docs','gfx_spec.json')))
by=collections.OrderedDict()
for arc,cell,text,opt in spec: by.setdefault(arc,[]).append((cell,text,opt))
prev=[]
for arc,items in by.items():
    for lang in ['English']:
        a=relabel.Arc(os.path.join(W,'work','ext','data',lang,'Menu',arc+'.bin'))
        for cell,text,opt in items:
            o=dict(opt); mg=tuple(o.pop('margin',(8,4,8,4)))
            r=relabel.smart2(a,cell,text,margin=mg,**o)
            if not r['fits']: print('DOES NOT FIT',arc,cell,text,r)
        a.save(os.path.join(W,'work','gfx_out',lang,'Menu',arc+'.bin'))
        for cell,text,opt in items:
            prev.append(ndsfmt.render_cell(a.ce['cells'][cell],dict(a.cg,data=bytes(a.data)),a.pal,a.shift))
if len(sys.argv)>1:
    Wd=520; x=y=rh=0; pos=[]
    for im in prev:
        if x+im.width>Wd: x=0; y+=rh+4; rh=0
        pos.append((x,y)); x+=im.width+4; rh=max(rh,im.height)
    can=Image.new('RGBA',(Wd,y+rh+4),(40,40,60,255))
    for im,p in zip(prev,pos): can.alpha_composite(im,p)
    can.resize((can.width*2,can.height*2),Image.NEAREST).save(sys.argv[1])
print('gfx done', len(spec))
