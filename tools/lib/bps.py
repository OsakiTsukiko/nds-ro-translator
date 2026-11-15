import zlib,sys
def vint(n):
    out=bytearray()
    while True:
        x=n&0x7f; n>>=7
        if n==0: out.append(0x80|x); break
        out.append(x); n-=1
    return bytes(out)
def rint(d,i):
    data=0; shift=1
    while True:
        x=d[i]; i+=1
        data+=(x&0x7f)*shift
        if x&0x80: return data,i
        shift<<=7; data+=shift
def create(src,tgt,K=64,ALIGN=4):
    idx={}
    for o in range(0,len(src)-K,ALIGN):
        key=src[o:o+K]
        if key not in idx: idx[key]=o
    out=bytearray(b'BPS1'+vint(len(src))+vint(len(tgt))+vint(0))
    lit_start=0; i=0; srel=0; n=len(tgt)
    def flush_lit(end):
        nonlocal lit_start
        if end>lit_start:
            L=end-lit_start; out.extend(vint(((L-1)<<2)|1)); out.extend(tgt[lit_start:end])
        lit_start=end
    while i<n:
        # SourceRead: same offset match
        if i<len(src) and tgt[i:i+K]==src[i:i+K] and i+K<=n:
            j=i+K
            while j<n and j<len(src) and tgt[j]==src[j]: j+=1
            flush_lit(i); L=j-i; out.extend(vint(((L-1)<<2)|0)); i=j; lit_start=i; continue
        o=idx.get(tgt[i:i+K]) if (i%ALIGN==0 and i+K<=n) else None
        if o is not None:
            j=i+K; s=o+K
            while j<n and s<len(src) and tgt[j]==src[s]: j+=1; s+=1
            flush_lit(i); L=j-i; delta=o-srel
            out.extend(vint(((L-1)<<2)|2)); out.extend(vint((abs(delta)<<1)|(1 if delta<0 else 0)))
            srel=o+L; i=j; lit_start=i; continue
        i+=1
    flush_lit(n)
    out+= (zlib.crc32(src)&0xffffffff).to_bytes(4,'little')+(zlib.crc32(tgt)&0xffffffff).to_bytes(4,'little')
    out+= (zlib.crc32(out)&0xffffffff).to_bytes(4,'little')
    return bytes(out)
def apply(src,p):
    assert p[:4]==b'BPS1'; i=4
    ss,i=rint(p,i); ts,i=rint(p,i); ms,i=rint(p,i); i+=ms
    out=bytearray(); srel=0; trel=0; end=len(p)-12
    while i<end:
        d,i=rint(p,i); cmd=d&3; L=(d>>2)+1
        if cmd==0: out+=src[len(out):len(out)+L]
        elif cmd==1: out+=p[i:i+L]; i+=L
        elif cmd==2:
            d2,i=rint(p,i); srel+= -(d2>>1) if d2&1 else (d2>>1); out+=src[srel:srel+L]; srel+=L
        else:
            d2,i=rint(p,i); trel+= -(d2>>1) if d2&1 else (d2>>1)
            for _ in range(L): out.append(out[trel]); trel+=1
    assert len(out)==ts
    assert zlib.crc32(out)&0xffffffff==int.from_bytes(p[-8:-4],'little')
    return bytes(out)
if __name__=='__main__':
    src=open(sys.argv[1],'rb').read(); tgt=open(sys.argv[2],'rb').read()
    p=create(src,tgt); open(sys.argv[3],'wb').write(p)
    assert apply(src,p)==tgt; print('patch ok',len(p))
