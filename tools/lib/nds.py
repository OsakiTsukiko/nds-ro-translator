import struct
def lz10_decompress(d):
    assert d[0]==0x10
    size=d[1]|(d[2]<<8)|(d[3]<<16); out=bytearray(); i=4
    while len(out)<size:
        flags=d[i]; i+=1
        for b in range(8):
            if len(out)>=size: break
            if flags&(0x80>>b):
                v=(d[i]<<8)|d[i+1]; i+=2
                n=(v>>12)+3; disp=(v&0xFFF)+1
                for _ in range(n): out.append(out[-disp])
            else:
                out.append(d[i]); i+=1
    return bytes(out)
def lz10_compress(d):
    out=bytearray([0x10,len(d)&0xFF,(len(d)>>8)&0xFF,(len(d)>>16)&0xFF])
    i=0; n=len(d)
    # simple hash-chain matcher
    from collections import defaultdict
    table=defaultdict(list)
    while i<n:
        flagpos=len(out); out.append(0); flags=0
        for b in range(8):
            if i>=n: break
            best=0; bdisp=0
            if i+3<=n:
                key=d[i:i+3]
                for p in reversed(table[key][-64:]):
                    disp=i-p
                    if disp>4096: break
                    if disp<1: continue
                    l=0
                    while l<18 and i+l<n and d[p+l]==d[i+l]: l+=1
                    if l>best: best=l; bdisp=disp
                    if l==18: break
            if best>=3:
                flags|=0x80>>b
                v=((best-3)<<12)|(bdisp-1); out+=bytes([v>>8,v&0xFF])
                for k in range(best):
                    if i+k+3<=n: table[d[i+k:i+k+3]].append(i+k)
                i+=best
            else:
                if i+3<=n: table[d[i:i+3]].append(i)
                out.append(d[i]); i+=1
        out[flagpos]=flags
    while len(out)%4: out.append(0)
    return bytes(out)
def narc_parse(d):
    assert d[:4]==b'NARC'
    o=struct.unpack_from('<H',d,12)[0]
    # BTAF
    assert d[o:o+4]==b'BTAF'; bsz=struct.unpack_from('<I',d,o+4)[0]; n=struct.unpack_from('<H',d,o+8)[0]
    fat=[struct.unpack_from('<II',d,o+12+8*i) for i in range(n)]
    o2=o+bsz; assert d[o2:o2+4]==b'BTNF'; fsz=struct.unpack_from('<I',d,o2+4)[0]
    fnt=d[o2+8:o2+fsz]
    o3=o2+fsz; assert d[o3:o3+4]==b'GMIF'
    img=o3+8
    files=[d[img+s:img+e] for s,e in fat]
    # names
    names=[]
    sub=struct.unpack_from('<I',fnt,0)[0]
    if sub and sub<len(fnt):
        p=sub
        while p<len(fnt) and fnt[p]:
            l=fnt[p]&0x7f; names.append(fnt[p+1:p+1+l].decode()); p+=1+l
            if fnt[p-1-l]&0x80: p+=2
    return dict(files=files,names=names,fnt=fnt,raw=d)
def narc_build(p,files):
    fnt=p['fnt']
    fat=b''; data=b''
    for f in files:
        s=len(data); data+=f; e=len(data)
        fat+=struct.pack('<II',s,e)
        while len(data)%4: data+=b'\xff'
    btaf=b'BTAF'+struct.pack('<IHH',12+len(fat),len(files),0)+fat
    btnf=b'BTNF'+struct.pack('<I',8+len(fnt))+fnt
    gmif=b'GMIF'+struct.pack('<I',8+len(data))+data
    body=btaf+btnf+gmif
    hdr=b'NARC'+struct.pack('<HHIHH',0xFFFE,0x0100,16+len(body),16,3)
    return hdr+body

def ncgr_parse(d):
    assert d[:4] in (b'RGCN',b'NCGR'[::-1]) or d[:4]==b'RGCN'
    o=struct.unpack_from('<H',d,12)[0]
    assert d[o:o+4]==b'RAHC'
    h,w,bpp=struct.unpack_from('<HHI',d,o+8)
    mapping,=struct.unpack_from('<I',d,o+16)
    tiledflag,=struct.unpack_from('<I',d,o+20)
    dsize,doff=struct.unpack_from('<II',d,o+24)
    data=d[o+8+doff:o+8+doff+dsize]
    return dict(h=h,w=w,bpp=4 if bpp==3 else 8,data=data,dataoff=o+8+doff,mapping=mapping,tiled=tiledflag)
def nclr_parse(d):
    o=struct.unpack_from('<H',d,12)[0]
    assert d[o:o+4]==b'TTLP'
    bpp,=struct.unpack_from('<I',d,o+8); size,off=struct.unpack_from('<II',d,o+16)
    raw=d[o+8+off:o+8+off+size]
    cols=[struct.unpack_from('<H',raw,i)[0] for i in range(0,len(raw),2)]
    return [((c&31)*8,((c>>5)&31)*8,((c>>10)&31)*8) for c in cols]
def tiles_to_image(cg,pal,palbank=0,cols=16):
    from PIL import Image
    bpp=cg['bpp']; data=cg['data']; tsz=8*bpp
    n=len(data)//tsz; rows=(n+cols-1)//cols
    img=Image.new('RGB',(cols*8,rows*8),(255,0,255))
    for t in range(n):
        tx,ty=(t%cols)*8,(t//cols)*8
        td=data[t*tsz:(t+1)*tsz]
        for i in range(64):
            v = (td[i//2]>>((i&1)*4))&15 if bpp==4 else td[i]
            c=pal[(palbank*16+v)%len(pal)] if bpp==4 else pal[v%len(pal)]
            img.putpixel((tx+i%8,ty+i//8),c)
    return img

SHAPES={(0,0):(8,8),(0,1):(16,16),(0,2):(32,32),(0,3):(64,64),(1,0):(16,8),(1,1):(32,8),(1,2):(32,16),(1,3):(64,32),(2,0):(8,16),(2,1):(8,32),(2,2):(16,32),(2,3):(32,64)}
def ncer_parse(d):
    o=struct.unpack_from('<H',d,12)[0]
    assert d[o:o+4]==b'KBEC'
    ncell,ext=struct.unpack_from('<HH',d,o+8); celloff,mapping=struct.unpack_from('<II',d,o+12)
    base=o+8+celloff
    cellsz=16 if ext==1 else 8
    oambase=base+ncell*cellsz
    cells=[]
    for i in range(ncell):
        nobj,attr,ooff=struct.unpack_from('<HHI',d,base+i*cellsz)
        objs=[]
        for j in range(nobj):
            a0,a1,a2=struct.unpack_from('<HHH',d,oambase+ooff+j*6)
            y=a0&0xFF; y = y-256 if y>=128 else y
            x=a1&0x1FF; x = x-512 if x>=256 else x
            shape=(a0>>14)&3; size=(a1>>14)&3
            w,h=SHAPES[(shape,size)]
            objs.append(dict(x=x,y=y,w=w,h=h,tile=a2&0x3FF,pal=(a2>>12)&15,hflip=(a1>>12)&1,vflip=(a1>>13)&1,bpp8=(a0>>13)&1))
        cells.append(objs)
    return dict(cells=cells,mapping=mapping)
def render_cell(objs,cg,pal,shift=0):
    from PIL import Image
    if not objs: return None
    x0=min(o['x'] for o in objs); y0=min(o['y'] for o in objs)
    x1=max(o['x']+o['w'] for o in objs); y1=max(o['y']+o['h'] for o in objs)
    img=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0))
    data=cg['data']; tsz=32
    for o in reversed(objs):
        base=o['tile']<<shift
        nt=(o['w']//8)*(o['h']//8)
        for t in range(nt):
            tx=(t%(o['w']//8))*8; ty=(t//(o['w']//8))*8
            td=data[(base+t)*tsz:(base+t+1)*tsz]
            if len(td)<32: continue
            for i in range(64):
                v=(td[i//2]>>((i&1)*4))&15
                if not v: continue
                px=tx+i%8; py=ty+i//8
                if o['hflip']: px=o['w']-1-px
                if o['vflip']: py=o['h']-1-py
                c=pal[(o['pal']*16+v)%len(pal)]
                img.putpixel((o['x']-x0+px,o['y']-y0+py),c+(255,))
    return img
