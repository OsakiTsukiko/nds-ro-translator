import sys,os; sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','lib')); import nds as ndsfmt
from PIL import Image, ImageDraw
def sheet(path,out,scale=2):
    p=ndsfmt.narc_parse(ndsfmt.lz10_decompress(open(path,'rb').read()))
    fs=dict(zip(p['names'],p['files']))
    cg=ndsfmt.ncgr_parse([v for k,v in fs.items() if k.lower().endswith('.ncgr')][0])
    pal=ndsfmt.nclr_parse([v for k,v in fs.items() if k.endswith('.NCLR')][0])
    ce=ndsfmt.ncer_parse([v for k,v in fs.items() if k.lower().endswith('.ncer')][0])
    shift={0:0,1:1,2:2,3:3,4:0}.get(ce['mapping'],0)
    imgs=[render_cell(c,cg,pal,shift) for c in ce['cells']] if False else [ndsfmt.render_cell(c,cg,pal,shift) for c in ce['cells']]
    W=520; x=y=0; rowh=0; pos=[]
    for i,im in enumerate(imgs):
        if im is None: pos.append(None); continue
        w,h=im.size
        if x+w+4>W: x=0; y+=rowh+12; rowh=0
        pos.append((x,y)); x+=w+6; rowh=max(rowh,h)
    H=y+rowh+12
    can=Image.new('RGBA',(W,H),(40,40,60,255)); d=ImageDraw.Draw(can)
    for i,(im,ps) in enumerate(zip(imgs,pos)):
        if ps: can.alpha_composite(im,(ps[0],ps[1]+10)); d.text((ps[0],ps[1]),str(i),fill=(255,255,0,255))
    can=can.resize((W*scale,H*scale),Image.NEAREST); can.save(out)
    return ce['mapping']
if __name__=='__main__':
    for a in sys.argv[2:]:
        m=sheet(a, os.path.join(sys.argv[1],os.path.basename(a)[:-4]+'_cells.png'))
        print(a, hex(m))
