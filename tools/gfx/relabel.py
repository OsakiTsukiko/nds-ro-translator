"""Replace baked English labels in NARC sprite graphics with Romanian text."""
import sys,os,json,collections
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','lib'))
import nds as ndsfmt, nftr as nftr2
from PIL import Image
W=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # template root
class _Fonts(dict):
    # patched, uncompressed fonts written by build.py into work/fonts/<name>.nftr
    def __missing__(s,k):
        s[k]=nftr2.Font(os.path.join(W,'work','fonts',k+'.nftr')); return s[k]
FONTS=_Fonts()
SHIFT={0:0,1:1,2:2,3:3,4:0}
class Arc:
    def __init__(s,path):
        s.path=path; s.p=ndsfmt.narc_parse(ndsfmt.lz10_decompress(open(path,'rb').read()))
        s.fs=dict(zip(s.p['names'],s.p['files']))
        s.cgname=[k for k in s.fs if k.lower().endswith('.ncgr')][0]
        s.cgraw=bytearray(s.fs[s.cgname]); s.cg=ndsfmt.ncgr_parse(bytes(s.cgraw))
        s.data=bytearray(s.cg['data'])
        s.pal=ndsfmt.nclr_parse(s.fs[[k for k in s.fs if k.endswith('.NCLR')][0]])
        s.ce=ndsfmt.ncer_parse(s.fs[[k for k in s.fs if k.lower().endswith('.ncer')][0]])
        s.shift=SHIFT.get(s.ce['mapping'],0)
    def cellmap(s,ci):
        """return dict (x,y)->(tileidx,pixel_in_tile,palbank) for topmost OAM, plus origin"""
        objs=s.ce['cells'][ci]; m={}
        for o in objs:  # lower index = on top -> first wins
            base=o['tile']<<s.shift; tw=o['w']//8
            for py in range(o['h']):
                for px in range(o['w']):
                    sx = o['w']-1-px if o['hflip'] else px
                    sy = o['h']-1-py if o['vflip'] else py
                    t=base+(sy//8)*tw+(sx//8); pi=(sy%8)*8+(sx%8)
                    key=(o['x']+px,o['y']+py)
                    if key not in m: m[key]=(t,pi,o['pal'])
        x0=min(k[0] for k in m); y0=min(k[1] for k in m)
        return m,x0,y0
    def get(s,t,pi): return (s.data[t*32+pi//2]>>((pi&1)*4))&15
    def put(s,t,pi,v):
        b=s.data[t*32+pi//2]
        b = (b&0xF0)|v if not (pi&1) else (b&0x0F)|(v<<4)
        s.data[t*32+pi//2]=b
    def index_image(s,ci):
        m,x0,y0=s.cellmap(ci)
        w=max(k[0] for k in m)-x0+1; h=max(k[1] for k in m)-y0+1
        grid=[[0]*w for _ in range(h)]
        for (x,y),(t,pi,pb) in m.items(): grid[y-y0][x-x0]=s.get(t,pi)
        return grid,m,x0,y0
    def save(s,out):
        cg=bytearray(s.cgraw); off=s.cg['dataoff']; cg[off:off+len(s.data)]=s.data
        s.fs[s.cgname]=bytes(cg)
        files=[s.fs[n] for n in s.p['names']]
        nb=ndsfmt.narc_build(s.p,files)
        os.makedirs(os.path.dirname(out),exist_ok=True)
        open(out,'wb').write(ndsfmt.lz10_compress(nb))
def text_mask(text,font='zeldaDS_15',bold=1,spacing=0):
    F=FONTS[font]; M=(1<<F.bpp)-1
    cols=[]; x=0; pix=[]
    for ch in text:
        g=F.map.get(ord(ch))
        if g is None: g=F.map[ord('?')]
        bm=F.bitmap(g); lw,gw,adv=F.widths[g]
        for r in range(F.h):
            for c in range(F.w):
                v=bm[r][c]
                if F.bpp==1: on=v>0
                elif F.bpp==2: on=v>=2
                else: on=v in (1,2)
                if on: pix.append((x+lw+c,r))
        x+=adv+spacing
    s=set(pix)
    if bold: s|={(a+1,b) for a,b in s}
    if not s: return set(),0,0
    xs=[a for a,b in s]; ys=[b for a,b in s]
    mx,my=min(xs),min(ys)
    return {(a-mx,b-my) for a,b in s}, max(xs)-mx+1, max(ys)-my+1
def relabel(arc,ci,text,box=None,fill=None,outline=None,font='zeldaDS_15',bold=1,spacing=0,dy=0,shadow=None,erase=None,outline_w=1):
    grid,m,x0,y0=arc.index_image(ci); h=len(grid); w=len(grid[0])
    if box is None: box=(0,0,w,h)
    bx,by,bw,bh=box
    reg=[(x,y) for y in range(by,by+bh) for x in range(bx,bx+bw) if 0<=x<w and 0<=y<h]
    hist=collections.Counter(grid[y][x] for x,y in reg)
    if erase is None:
        erase=[fill,outline]+([shadow] if shadow is not None else [])
    erase=set(e for e in erase if e is not None)
    # inpaint: replace erase-colored pixels by nearest non-erase pixel on same row (left, then right), within box
    for y in range(by,by+bh):
        row=grid[y]
        for x in range(bx,bx+bw):
            if row[x] in erase:
                v=None
                for d in range(1,bw):
                    for xx in (x-d,x+d):
                        if bx<=xx<bx+bw and row[xx] not in erase: v=row[xx]; break
                    if v is not None: break
                row[x]=v if v is not None else row[x]
    # draw text
    mask,tw,th=text_mask(text,font,bold,spacing)
    if tw>bw-2 and spacing==0 and len(text)>1:
        mask,tw,th=text_mask(text,font,bold,-1)
    if tw>bw-2 and bold:
        mask,tw,th=text_mask(text,font,0,-1 if tw>bw else 0)
    ox=bx+(bw-tw)//2; oy=by+(bh-th)//2+dy
    ol=set()
    for a,b in mask:
        for dx in range(-outline_w,outline_w+1):
            for dyy in range(-outline_w,outline_w+1):
                if (a+dx,b+dyy) not in mask: ol.add((a+dx,b+dyy))
    if shadow is not None:
        for a,b in mask|ol:
            X,Y=ox+a+1,oy+b+1
            if 0<=X<w and 0<=Y<h and (a+1,b+1) not in mask and (a+1,b+1) not in ol: grid[Y][X]=shadow
    if outline is not None:
        for a,b in ol:
            X,Y=ox+a,oy+b
            if 0<=X<w and 0<=Y<h: grid[Y][X]=outline
    for a,b in mask:
        X,Y=ox+a,oy+b
        if 0<=X<w and 0<=Y<h: grid[Y][X]=fill
    # write back
    for (x,y),(t,pi,pb) in m.items():
        arc.put(t,pi,grid[y-y0][x-x0])
    return tw,bw
def preview(arc,cells,out,scale=3):
    from PIL import ImageDraw
    ims=[ndsfmt.render_cell(arc.ce['cells'][c],dict(arc.cg,data=bytes(arc.data)),arc.pal,arc.shift) for c in cells]
    Wd=max(i.width for i in ims)+4; H=sum(i.height+4 for i in ims)
    can=Image.new('RGBA',(Wd,H),(40,40,60,255)); y=0
    for i in ims: can.alpha_composite(i,(2,y)); y+=i.height+4
    can.resize((Wd*scale,H*scale),Image.NEAREST).save(out)
def analyze(arc,ci):
    grid,m,x0,y0=arc.index_image(ci)
    for row in grid: print(''.join('.123456789ABCDEF'[v] if v else ' ' for v in row))

def autodetect(arc,ci,box=None,ring=4):
    grid,m,x0,y0=arc.index_image(ci); h=len(grid); w=len(grid[0])
    if box is None: box=(ring,ring,w-2*ring,h-2*ring)
    bx,by,bw,bh=box
    inside=collections.Counter(); outside=collections.Counter()
    for y in range(h):
        for x in range(w):
            v=grid[y][x]
            if bx<=x<bx+bw and by<=y<by+bh: inside[v]+=1
            else: outside[v]+=1
    cand=[v for v,c in inside.items() if v and c>=4 and outside[v]<=max(2,0.03*c)]
    cs=set(cand)
    core=collections.Counter(); edge=collections.Counter()
    for y in range(by,by+bh):
        for x in range(bx,bx+bw):
            v=grid[y][x]
            if v not in cs: continue
            nb=[grid[yy][xx] for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)) if 0<=xx<w and 0<=yy<h]
            if all(n in cs for n in nb): core[v]+=1
            else: edge[v]+=1
    fill=core.most_common(1)[0][0] if core else (cand[0] if cand else None)
    outl=None
    for v,c in edge.most_common():
        if v!=fill: outl=v; break
    return dict(erase=cand,fill=fill,outline=outl,box=box,size=(w,h))

def smart(arc,ci,text,margin=(8,4,8,4),font='zeldaDS_15',bold=1,dy=0,fill=None,outline=None,outline_w=1,colmode=False,keep=()):
    grid,m,x0,y0=arc.index_image(ci); h=len(grid); w=len(grid[0])
    l,t,r,b=margin; bx,by,bw,bh=l,t,w-l-r,h-t-b
    removed=collections.Counter(); core=collections.Counter(); edge=collections.Counter()
    textpix=set(); modes={}
    for y in range(by,by+bh):
        row=[grid[y][x] for x in range(bx,bx+bw)]
        modes[y]=collections.Counter(row).most_common(1)[0][0]
    for y in range(by,by+bh):
        for x in range(bx,bx+bw):
            if grid[y][x]!=modes[y] and grid[y][x] not in keep: textpix.add((x,y))
    for (x,y) in textpix:
        v=grid[y][x]; removed[v]+=1
        nb=[(xx,yy) for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))]
        if all(n in textpix for n in nb): core[v]+=1
        else: edge[v]+=1
    if fill is None: fill=core.most_common(1)[0][0] if core else removed.most_common(1)[0][0]
    if outline is None:
        outline=next((v for v,c in edge.most_common() if v!=fill),None)
    for (x,y) in textpix: grid[y][x]=modes[y]
    mask,tw,th=text_mask(text,font,bold,0)
    if tw>bw-2: mask,tw,th=text_mask(text,font,bold,-1)
    if tw>bw-2 and bold: mask,tw,th=text_mask(text,font,0,0)
    if tw>bw-2: mask,tw,th=text_mask(text,font,0,-1)
    ox=bx+(bw-tw)//2; oy=by+(bh-th)//2+dy
    ol=set()
    if outline is not None and outline_w:
        for a,c in mask:
            for dx in range(-outline_w,outline_w+1):
                for dyy in range(-outline_w,outline_w+1):
                    if (a+dx,c+dyy) not in mask: ol.add((a+dx,c+dyy))
    for a,c in ol:
        X,Y=ox+a,oy+c
        if 0<=X<w and 0<=Y<h: grid[Y][X]=outline
    ys=sorted(rowfill)
    for a,c in mask:
        X,Y=ox+a,oy+c
        if 0<=X<w and 0<=Y<h:
            f=fill
            if rowfill:
                # map text row proportionally onto original text rows
                yy=ys[0]+int((c/(max(1,th-1)))*(ys[-1]-ys[0])) if len(ys)>1 else ys[0]
                f=rowfill.get(yy,fill)
            grid[Y][X]=f
    for (x,y),(tt,pi,pb) in m.items(): arc.put(tt,pi,grid[y-y0][x-x0])
    return dict(fill=fill,outline=outline,tw=tw,bw=bw,fits=tw<=bw)

def smart2(arc,ci,text,margin=(8,4,8,4),font='zeldaDS_15',bold=0,dy=0,dx=0,fill=None,outline=None,outline_w=1,xref=None,refcol=None,ref='col',fillrows=False,exclude=(),swap=False):
    grid,m,x0,y0=arc.index_image(ci); h=len(grid); w=len(grid[0])
    l,t,r,b=margin; bx,by,bw,bh=l,t,w-l-r,h-t-b
    if xref is None: xref=bx
    refv={}
    for y in range(by,by+bh):
        if ref=='col': refv[y]=grid[y][xref]
        else: refv[y]=collections.Counter(grid[y][bx:bx+bw]).most_common(1)[0][0]
    textpix={(x,y) for y in range(by,by+bh) for x in range(bx,bx+bw) if grid[y][x]!=refv[y]}
    core=collections.Counter(); edge=collections.Counter()
    for (x,y) in textpix:
        v=grid[y][x]
        if all(n in textpix for n in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))): core[v]+=1
        else: edge[v]+=1
    if fill is None: fill=(core.most_common(1) or edge.most_common(1))[0][0]
    if outline is None: outline=next((v for v,c in edge.most_common() if v!=fill),None)
    if swap and outline is not None: fill,outline=outline,fill
    rowfill={}
    if fillrows:
        for y in range(by,by+bh):
            cc=collections.Counter(grid[y][x] for x in range(bx,bx+bw) if (x,y) in textpix and grid[y][x] not in (outline,)+tuple(exclude))
            if cc: rowfill[y]=cc.most_common(1)[0][0]
    for y in range(by,by+bh):
        for x in range(bx,bx+bw): grid[y][x]=refv[y]
    for bb,sp in ((bold,0),(bold,-1),(0,0),(0,-1)):
        mask,tw,th=text_mask(text,font,bb,sp)
        if tw<=bw-2*outline_w: break
    ox=bx+(bw-tw)//2+dx; oy=by+(bh-th)//2+dy
    ol=set()
    if outline is not None and outline_w:
        for a,c in mask:
            for ddx in range(-outline_w,outline_w+1):
                for ddy in range(-outline_w,outline_w+1):
                    if (a+ddx,c+ddy) not in mask: ol.add((a+ddx,c+ddy))
    for a,c in ol:
        X,Y=ox+a,oy+c
        if 0<=X<w and 0<=Y<h: grid[Y][X]=outline
    ys=sorted(rowfill)
    for a,c in mask:
        X,Y=ox+a,oy+c
        if 0<=X<w and 0<=Y<h:
            f=fill
            if rowfill:
                # map text row proportionally onto original text rows
                yy=ys[0]+int((c/(max(1,th-1)))*(ys[-1]-ys[0])) if len(ys)>1 else ys[0]
                f=rowfill.get(yy,fill)
            grid[Y][X]=f
    for (x,y),(tt,pi,pb) in m.items(): arc.put(tt,pi,grid[y-y0][x-x0])
    return dict(fill=fill,outline=outline,tw=tw,bw=bw,fits=tw<=bw)
def dump_cells(path,out,cells):
    a=Arc(path); preview(a,cells,out)
