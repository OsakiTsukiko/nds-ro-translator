import struct
class Font:
    def __init__(s, path):
        d=path if isinstance(path,(bytes,bytearray)) else open(path,'rb').read(); d=bytes(d); s.raw=d
        s.hdr=bytearray(d[:16])
        o=struct.unpack_from('<H',d,12)[0]; secs=[]
        while o<len(d):
            mg=d[o:o+4]; sz=struct.unpack_from('<I',d,o+4)[0]; secs.append((mg,o,sz)); o+=sz
        f=[x for x in secs if x[0]==b'FNIF'][0]; s.finf=bytearray(d[f[1]:f[1]+f[2]])
        c=[x for x in secs if x[0]==b'PLGC'][0]
        s.cglp_hdr=bytearray(d[c[1]+8:c[1]+16])
        s.w,s.h,s.tsz,_,_,s.bpp,_=struct.unpack_from('<BBHBBBB',d,c[1]+8)
        n=(c[2]-16)//s.tsz
        s.tiles=[d[c[1]+16+i*s.tsz:c[1]+16+(i+1)*s.tsz] for i in range(n)]
        s.cglp_tail=d[c[1]+16+n*s.tsz:c[1]+c[2]]
        w=[x for x in secs if x[0]==b'HDWC'][0]
        first,last=struct.unpack_from('<HH',d,w[1]+8)
        s.cwdh_extra=d[w[1]+12:w[1]+16]
        s.widths=[d[w[1]+16+3*i:w[1]+19+3*i] for i in range(last-first+1)]
        s.cmaps=[]
        for m,o,sz in secs:
            if m!=b'PAMC': continue
            lo,hi,typ=struct.unpack_from('<HHH',d,o+8)
            body=d[o+20:o+sz]
            s.cmaps.append([lo,hi,typ,d[o+14:o+16],body])
        s.map={}
        for lo,hi,typ,_,body in s.cmaps:
            if typ==0:
                b=struct.unpack_from('<H',body,0)[0]
                for ch in range(lo,hi+1): s.map[ch]=b+ch-lo
            elif typ==1:
                for ch in range(lo,hi+1):
                    g=struct.unpack_from('<H',body,2*(ch-lo))[0]
                    if g!=0xFFFF: s.map[ch]=g
            else:
                nn=struct.unpack_from('<H',body,0)[0]
                for i in range(nn):
                    ch,g=struct.unpack_from('<HH',body,2+4*i); s.map[ch]=g
    def bitmap(s,g):
        t=s.tiles[g]; bits=''.join(f'{b:08b}' for b in t)
        px=[int(bits[i*s.bpp:(i+1)*s.bpp],2) for i in range(s.w*s.h)]
        return [px[r*s.w:(r+1)*s.w] for r in range(s.h)]
    def tobytes(s,bm):
        bits=''.join(format(v,f'0{s.bpp}b') for row in bm for v in row)
        bits+= '0'*(-len(bits)%8)
        b=bytes(int(bits[i:i+8],2) for i in range(0,len(bits),8))
        return b+bytes(s.tsz-len(b))
    def show(s,ch):
        g=s.map[ord(ch)]; print(ch, g, 'width', list(s.widths[g]))
        for r in s.bitmap(g): print(' '+''.join(' 1234567'[v] for v in r))
    def add(s,ch,bm,width):
        g=len(s.tiles); s.tiles.append(s.tobytes(bm)); s.widths.append(bytes(width)); s.map[ord(ch)]=g
        lo,hi,typ,ex,body=s.cmaps[-1]; assert typ==2
        nn=struct.unpack_from('<H',body,0)[0]
        pl=[struct.unpack_from('<HH',body,2+4*i) for i in range(nn)]+[(ord(ch),g)]
        pl.sort()
        nb=struct.pack('<H',nn+1)+b''.join(struct.pack('<HH',a,b) for a,b in pl)
        s.cmaps[-1][4]=nb
    def save(s,path=None):
        out=bytearray(s.hdr)
        fpos=len(out); out+=s.finf
        cpos=len(out); cg=s.cglp_hdr+b''.join(s.tiles)
        cg=b'PLGC'+struct.pack('<I',len(cg)+8)+cg
        cg+=b'\0'*(-len(cg)%4); cg=cg[:4]+struct.pack('<I',len(cg))+cg[8:]
        out+=cg
        wpos=len(out); wd=struct.pack('<HH',0,len(s.widths)-1)+s.cwdh_extra+b''.join(s.widths)
        wd=b'HDWC'+struct.pack('<I',len(wd)+8)+wd
        wd+=b'\0'*(-len(wd)%4); wd=wd[:4]+struct.pack('<I',len(wd))+wd[8:]
        out+=wd
        mpos=len(out); blocks=[]
        for lo,hi,typ,ex,body in s.cmaps:
            b=bytearray(b'PAMC'+b'\0'*4+struct.pack('<HHH',lo,hi,typ)+ex+b'\0'*4+body)
            b+=b'\0'*(-len(b)%4); struct.pack_into('<I',b,4,len(b)); blocks.append(b)
        p=mpos
        for i,b in enumerate(blocks):
            nxt = p+len(b)+8 if i<len(blocks)-1 else 0
            struct.pack_into('<I',b,16,nxt); p+=len(b)
        for b in blocks: out+=b
        # FINF offsets (point to section data, +8)
        struct.pack_into('<III',out,fpos+0x10,cpos+8,wpos+8,mpos+8)
        struct.pack_into('<I',out,8,len(out))
        struct.pack_into('<H',out,14,3+len(blocks))
        if path: open(path,'wb').write(out)
        return bytes(out)
