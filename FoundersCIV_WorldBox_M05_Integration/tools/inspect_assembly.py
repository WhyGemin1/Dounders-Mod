#!/usr/bin/env python3
"""Read-only minimal ECMA-335 metadata inspector: TypeDef/MethodDef names/signatures.
No Unity or .NET runtime required. Supports #~/#- and compressed signatures.
"""
import struct, sys, json, hashlib
from pathlib import Path

class Reader:
    def __init__(self, path):
        self.path = Path(path); self.b = self.path.read_bytes(); self.parse()
    def u16(self, x): return struct.unpack_from('<H', self.b, x)[0]
    def u32(self, x): return struct.unpack_from('<I', self.b, x)[0]
    def u64(self, x): return struct.unpack_from('<Q', self.b, x)[0]
    def rva(self, r):
        for virt, vs, off, rawsize in self.sections:
            if virt <= r < virt + max(vs,rawsize): return off + (r - virt)
        raise ValueError('Invalid RVA '+hex(r))
    def parse(self):
        b=self.b
        if b[:2]!=b'MZ': raise ValueError('not PE')
        pe=self.u32(0x3c)
        if b[pe:pe+4]!=b'PE\0\0': raise ValueError('not PE')
        num=self.u16(pe+6); opt=pe+24; pe32plus=(self.u16(opt)==0x20b)
        dd=opt+(112 if pe32plus else 96)
        cli_rva=self.u32(dd+14*8)
        sect_off=opt+self.u16(pe+20)
        self.sections=[]
        for i in range(num):
            p=sect_off+40*i
            self.sections.append((self.u32(p+12),self.u32(p+8),self.u32(p+20),self.u32(p+16)))
        cli=self.rva(cli_rva); md=self.rva(self.u32(cli+8))
        if b[md:md+4]!=b'BSJB': raise ValueError('missing BSJB metadata')
        vlen=self.u32(md+12)
        p=(md+16+vlen+3)&~3
        self.flags, streams=struct.unpack_from('<HH',b,p);p+=4
        self.streams={}
        for _ in range(streams):
            off,sz=struct.unpack_from('<II',b,p);p+=8
            e=b.index(0,p);name=b[p:e].decode('ascii');p=(e+4)&~3
            self.streams[name]=(md+off,sz)
        st=self.streams.get('#~') or self.streams.get('#-')
        if st is None: raise ValueError('missing metadata tables')
        m=st[0];self.heap_flags=b[m+6];valid=self.u64(m+8)
        t=m+24;self.counts={}
        for tab in range(64):
            if valid >>tab & 1:
                self.counts[tab]=self.u32(t); t+=4
        self.table_start=t
        self.string_size = 4 if self.heap_flags &1 else 2
        self.guid_size = 4 if self.heap_flags &2 else 2
        self.blob_size = 4 if self.heap_flags &4 else 2
        self.row_offsets={}
        for table in range(7):
            self.row_offsets[table] = t
            t+=self.counts.get(table,0)*self.rowsize(table)
        self.string_heap=self.streams['#Strings'][0]
        self.blob_heap=self.streams['#Blob'][0]
        self.types=[];self.methods=[]
        for i in range(1,self.counts.get(2,0)+1):
            p=self.row_offsets[2]+(i-1)*self.rowsize(2)
            p+=4
            name=self.idx(p,self.string_size);p+=self.string_size
            ns=self.idx(p,self.string_size);p+=self.string_size
            p+=self.coded_size((2,1,27),2) + self.tabsize(4)
            meth=self.idx(p,self.tabsize(6))
            self.types.append({'rid':i,'name':self.str_at(name),'namespace':self.str_at(ns),'first_method':meth})
        for i in range(1,self.counts.get(6,0)+1):
            p=self.row_offsets[6]+(i-1)*self.rowsize(6)
            rva=self.u32(p);p+=8
            name=self.idx(p,self.string_size);p+=self.string_size
            sig=self.idx(p,self.blob_size)
            self.methods.append({'rid':i,'name':self.str_at(name),'rva':rva,'sig':self.signature(sig)})
        for i,ty in enumerate(self.types):
            start=ty['first_method'];end=self.types[i+1]['first_method'] if i+1<len(self.types) else len(self.methods)+1
            for mid in range(start,end):
                if mid>=1 and mid<=len(self.methods):self.methods[mid-1]['owner']=('.'.join(x for x in (ty['namespace'],ty['name']) if x))
    def idx(self,p,sz): return self.u32(p) if sz==4 else self.u16(p)
    def tabsize(self,n):return 2 if self.counts.get(n,0)<65536 else 4
    def coded_size(self,tables,tagbits):return 2 if max(self.counts.get(i,0) for i in tables) < (1<<(16-tagbits)) else 4
    def rowsize(self,n):
        s=self.string_size;g=self.guid_size;b=self.blob_size
        if n==0:return 2+s+3*g
        if n==1:return self.coded_size((0,26,35,1),2)+2*s
        if n==2:return 4+2*s+self.coded_size((1,2,27),2)+self.tabsize(4)+self.tabsize(6)
        if n==3:return self.tabsize(4)
        if n==4:return 2+s+b
        if n==5:return self.tabsize(6)
        if n==6:return 4+2+2+s+b+self.tabsize(8)
    def str_at(self,i):
        if i==0:return ''
        off=self.string_heap+i
        return self.b[off:self.b.index(0,off)].decode('utf-8','replace')
    def compressed(self,buf,pos):
        first=buf[pos]
        if first&0x80==0:return first,pos+1
        if first&0xc0==0x80:return ((first&0x3f)<<8)|buf[pos+1],pos+2
        return ((first&0x1f)<<24)|(buf[pos+1]<<16)|(buf[pos+2]<<8)|buf[pos+3],pos+4
    def blob_at(self,i):
        if i==0:return b''
        p=self.blob_heap+i
        n,p=self.compressed(self.b,p)
        return self.b[p:p+n]
    def signature(self,blob_idx):
        z=self.blob_at(blob_idx)
        if not z:return None
        try:
            pos=0;header=z[pos];pos+=1
            if header&0x10:gc,pos=self.compressed(z,pos)
            argc,pos=self.compressed(z,pos)
            ret,pos=self.type_sig(z,pos)
            params=[]
            for i in range(min(argc,200)):
                v,pos=self.type_sig(z,pos);params.append(v)
            return {'calling_convention':header,'return':ret,'params':params}
        except Exception:
            return {'signature_hex':z.hex()}
    def type_sig(self,z,pos):
        primitives={0x01:'void',0x02:'bool',0x03:'char',0x04:'int8',0x05:'uint8',0x06:'int16',0x07:'uint16',0x08:'int32',0x09:'uint32',0x0a:'int64',0x0b:'uint64',0x0c:'float32',0x0d:'float64',0x0e:'string',0x18:'nativeint',0x19:'nativeuint',0x1c:'object',0x16:'typedbyref'}
        t=z[pos];pos+=1
        if t in primitives:return primitives[t],pos
        if t in (0x0f,0x10,0x1d):
            typ,pos=self.type_sig(z,pos)
            return {0x0f:'ptr',0x10:'ref',0x1d:'array'}[t]+'<'+typ+'>',pos
        if t in (0x11,0x12):
            token,pos=self.compressed(z,pos)
            return ('valuetype' if t==0x11 else 'class')+'#'+str(token),pos
        if t in (0x13,0x1e):
            n,pos=self.compressed(z,pos)
            return ('typeparam' if t==0x13 else 'methodtype')+str(n),pos
        if t==0x15:
            base,pos=self.type_sig(z,pos)
            n,pos=self.compressed(z,pos)
            vals=[]
            for i in range(n):
                a,pos=self.type_sig(z,pos);vals.append(a)
            return base+'<'+','.join(vals)+'>',pos
        if t==0x14:
            val,pos=self.type_sig(z,pos);rank,pos=self.compressed(z,pos)
            ns,pos=self.compressed(z,pos)
            for _ in range(ns):_,pos=self.compressed(z,pos)
            nl,pos=self.compressed(z,pos)
            for _ in range(nl):_,pos=self.compressed(z,pos)
            return 'multidim<'+val+'>',pos
        if t in (0x1f,0x20):
            _,pos=self.compressed(z,pos)
            return self.type_sig(z,pos)
        if t==0x45:return self.type_sig(z,pos)
        if t==0x41:return 'sentinel',pos
        return 'element0x%02x'%t,pos

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('assembly');ap.add_argument('--terms',default='eat,nutrition,hunt,attack,death,kill,repro,birth,food,meat,consume,digest,die,damage');ap.add_argument('--output')
    a=ap.parse_args();r=Reader(a.assembly);terms=a.terms.lower().split(',')
    filtered=[m for m in r.methods if any(s in (m.get('owner','')+'.'+m['name']).lower() for s in terms)]
    d={'assembly':str(Path(a.assembly).name),'sha256':hashlib.sha256(r.b).hexdigest(),'metadata_counts':{'types':len(r.types),'methods':len(r.methods)},'matches':filtered}
    if a.output:Path(a.output).write_text(json.dumps(d,indent=2))
    print('Types:',len(r.types),'methods:',len(r.methods),'matches:',len(filtered))
    for m in filtered[:500]:
        sig=m['sig'] or {};
        print(f"{m.get('owner','?')}.{m['name']}({', '.join(sig.get('params',[]))}) -> {sig.get('return','?')} [0x{m['rva']:x}]")
