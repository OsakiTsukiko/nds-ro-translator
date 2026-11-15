import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import nftr as nftr2
def diac_rows(f, base, acc):
    a=f.bitmap(f.map[ord(base)]); b=f.bitmap(f.map[ord(acc)])
    return [r for r in range(f.h) if a[r]!=b[r] and any(b[r]) and not any(a[r])], b
def make_breve(f, base, circ):
    rows, bm = diac_rows(f, base, circ)
    bm=[row[:] for row in bm]; M=(1<<f.bpp)-1
    cols=[c for r in rows for c in range(f.w) if bm[r][c]]
    x0,x1=min(cols),max(cols)
    if x1-x0<3: x0-=1; x1+=1 if x1-x0<3 else 0
    for r in rows: bm[r]=[0]*f.w
    rows=sorted(rows)
    if len(rows)>=2:
        top,bot=rows[-2],rows[-1]
        bm[top][x0]=M; bm[top][x1]=M
        for c in range(x0+1,x1): bm[bot][c]=M
    else:
        r=rows[0]
        for c in range(x0,x1+1): bm[r][c]=M
    return bm
def ink(f):
    import collections
    c=collections.Counter(v for row in f.bitmap(f.map[ord('l')]) for v in row if v)
    return c.most_common(1)[0][0]
def edge(f):
    return 3 if ink(f)==1 and f.bpp==3 else (1<<f.bpp)//2
def make_comma(f, base):
    g=f.map[ord(base)]; bm=[row[:] for row in f.bitmap(g)]; M=ink(f)
    c0=f.bitmap(f.map[ord('c')]); cc=f.bitmap(f.map[ord('ç')])
    last=max(r for r in range(f.h) if any(c0[r]))
    desc=[r for r in range(last+1,f.h) if any(cc[r])]
    cols=[c for r in range(f.h) for c in range(f.w) if bm[r][c]==M]
    cx=(min(cols)+max(cols))//2
    if base in 'tT':  # stem column
        stem=[c for c in range(f.w) if sum(1 for r in range(f.h) if bm[r][c]==M)>=4]
        if stem: cx=stem[0]
    r1=desc[0]; r2=desc[1] if len(desc)>1 else None
    bm[r1][cx]=M
    if f.w>cx+1 and f.bpp>1: bm[r1][cx+1]=edge(f)
    if r2 is not None: bm[r2][max(cx-1,0)]=M
    return bm
RO_CHARS='ăĂșȘțȚşŞţŢ„'
def patch(src,dst=None):
    """Add Romanian glyphs to an NFTR font. src: path or bytes (uncompressed). Returns Font (and saves to dst if given).
    Needs â/Â (breve source), s/S/t/T + ç (comma depth), ” and , in the original font."""
    f=nftr2.Font(src)
    if ord('ă') in f.map: return f  # already patched
    wa=f.widths[f.map[ord('â')]]; wA=f.widths[f.map[ord('Â')]]
    if f.bpp==3:  # Spirit Tracks 3bpp message font: hand-placed breve pixels (check visually on other games!)
        a=[r[:] for r in f.bitmap(f.map[ord('a')])]; A=[r[:] for r in f.bitmap(f.map[ord('A')])]
        a[4][2]=2; a[4][6]=2; a[5][3]=a[5][4]=a[5][5]=1
        A[0][3]=2; A[0][7]=2; A[1][4]=A[1][5]=A[1][6]=1
        f.add('ă',a,f.widths[f.map[ord('a')]]); f.add('Ă',A,f.widths[f.map[ord('A')]])
    else:
        f.add('ă',make_breve(f,'a','â'),wa)
        f.add('Ă',make_breve(f,'A','Â'),wA)
    for ch,base in [('ș','s'),('Ș','S'),('ț','t'),('Ț','T')]:
        f.add(ch,make_comma(f,base),f.widths[f.map[ord(base)]])
    for ch,base in [('ş','ș'),('Ş','Ș'),('ţ','ț'),('Ţ','Ț')]:  # cedilla aliases -> comma glyphs
        g=f.map[ord(base)]; f.add(ch,f.bitmap(g),f.widths[g])
    # „ : take ” and move it down so its bottom sits where ',' bottom is
    q=f.bitmap(f.map[ord('”')]); cm=f.bitmap(f.map[ord(',')])
    qb=max(r for r in range(f.h) if any(q[r])); cb=max(r for r in range(f.h) if any(cm[r]))
    sh=cb-qb; nq=[[0]*f.w for _ in range(f.h)]
    for r in range(f.h):
        if 0<=r+sh<f.h: nq[r+sh]=q[r][:]
    f.add('„',nq,f.widths[f.map[ord('”')]])
    fold_cmap(f)
    if dst: f.save(dst)
    return f
NEW='ăĂșȘțȚşŞţŢ'
def fold_cmap(f):
    """Fold the Romanian glyphs into the type-1 (direct table) CMAP when its range already covers one of them.
    The game's glyph lookup stops at the first CMAP whose range contains the char, so a char inside a type-1
    range (0x20-0x153 in Spirit Tracks) with a 0xFFFF entry is never found in the type-2 list we appended to."""
    for i,(lo,hi,typ,ex,body) in enumerate(f.cmaps):
        if typ!=1 or lo>0x20 or not any(lo<=ord(c)<=hi for c in NEW): continue
        nhi=max(hi, max(ord(c) for c in NEW))
        tab=[f.map.get(ch,0xFFFF) if (ch<=hi and struct.unpack_from('<H',body,2*(ch-lo))[0]!=0xFFFF) or chr(ch) in NEW else 0xFFFF
             for ch in range(lo,nhi+1)]
        f.cmaps[i]=[lo,nhi,typ,ex,b''.join(struct.pack('<H',g) for g in tab)]
if __name__=='__main__':
    f=patch(sys.argv[1],sys.argv[2])
    if len(sys.argv)>3:
        for c in 'ăĂșȘțȚ': f.show(c)
