#include "raveil/affine_fold.h"
static uint32_t word(const uint8_t *p) {
  return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
}
static uint32_t crc(const uint8_t *p,size_t n) {
  uint32_t v=UINT32_MAX;
  for(size_t i=0;i<n;++i) {
    v^=p[i];
    for(unsigned j=0;j<8;++j) v=(v>>1)^((0u-(v&1u))&UINT32_C(0xedb88320));
  }
  return ~v;
}
bool raveil_fold_session_decode(const uint8_t *p,size_t n,
                                struct raveil_fold_session *session) {
  if(p==NULL||session==NULL||n<332u||n>RAVEIL_FOLD_SESSION_MAX_BYTES||
     word(p)!=RAVEIL_FOLD_SESSION_MAGIC||word(p+4)!=1||word(p+8)!=n||
     word(p+12)<1||word(p+12)>8||word(p+n-4)!=RAVEIL_FOLD_SESSION_END||
     word(p+n-8)!=crc(p,n-8)) return false;
  struct raveil_fold_session admitted={0};
  admitted.epoch=(uint64_t)word(p+16)|((uint64_t)word(p+20)<<32);
  admitted.count=word(p+12);
  if(!admitted.epoch)return false;
  uint64_t ids[8]={0};
  struct raveil_fold_request request;
  size_t offset=24;
  for(uint32_t i=0;i<admitted.count;++i) {
    if(offset+300u>n-8u||word(p+offset)!=RAVEIL_FOLD_BRIDGE_MAGIC)return false;
    uint32_t length=word(p+offset+8);
    if(length<300u||length>RAVEIL_FOLD_MAX_BYTES||length>n-8u-offset||
       !raveil_fold_decode(p+offset,length,&request))return false;
    for(uint32_t j=0;j<i;++j)if(ids[j]==request.request_id)return false;
    ids[i]=request.request_id;
    admitted.offsets[i]=(uint32_t)offset;admitted.lengths[i]=length;offset+=length;
  }
  if(offset!=n-8u)return false;
  *session=admitted;return true;
}
bool raveil_fold_validate(const uint32_t c[65]) {
  if(c==NULL||c[0]!=UINT32_C(0x4d463031)||c[1]<1||c[1]>16||
     c[2]<1||c[2]>16||c[3]<1||c[3]>64||c[4]>1||
     c[5]>324||c[6]>324||c[7]<1||c[7]>8||c[8]<2||c[8]>16) return false;
  for(unsigned v=0;v<8;++v) {
    const uint32_t *p=c+9+5*v;
    if(v>=c[7]) {for(unsigned j=0;j<5;++j) if(p[j]) return false;continue;}
    if(p[0]>1||p[1]>323||p[2]>323||p[3]>323||p[4]>323) return false;
    uint64_t last=(uint64_t)p[1]+(uint64_t)p[2]*(c[1]-1u)+
      (uint64_t)p[3]*(c[2]-1u)+(uint64_t)p[4]*(c[3]-1u);
    if(last>=c[5+p[0]]) return false;
  }
  uint32_t defined=0;
  for(unsigned pc=0;pc<16;++pc) {
    uint32_t w=c[49+pc],op=w>>28,d=(w>>25)&7u,a=(w>>22)&7u,b=(w>>19)&7u;
    if(pc>=c[8]) {if(w) return false;continue;}
    if(pc==c[8]-1) {
      if(op!=3||d||(w&UINT32_C(0x3fffff))||!(defined&(1u<<a))) return false;
    } else {
      if(op==1) {if(a>=c[7]||(w&UINT32_C(0x3fffff))) return false;}
      else if(op==2||op==4||op==5) {
        if(!(defined&(1u<<a))||!(defined&(1u<<b))||(w&UINT32_C(0x7ffff))) return false;
      } else if(op==6||op==7) {if(!(defined&(1u<<a))) return false;}
      else return false;
      defined|=1u<<d;
    }
  }
  return true;
}
bool raveil_fold_decode(const uint8_t *bytes,size_t size,struct raveil_fold_request *r) {
  if(bytes==NULL||r==NULL||size<300||size>RAVEIL_FOLD_MAX_BYTES||
     (word(bytes)!=RAVEIL_FOLD_MAGIC&&word(bytes)!=RAVEIL_FOLD_BRIDGE_MAGIC)||
     word(bytes+4)!=1||word(bytes+8)!=size||
     word(bytes+12)>324||word(bytes+16)>324||word(bytes+20)!=0||
     size!=300u+4u*(word(bytes+12)+word(bytes+16))||
     word(bytes+size-4)!=RAVEIL_FOLD_END||word(bytes+size-8)!=crc(bytes,size-8)) return false;
  uint64_t id=(uint64_t)word(bytes+24)|((uint64_t)word(bytes+28)<<32);
  if(!id) return false;
  uint32_t c[65];for(unsigned i=0;i<65;++i)c[i]=word(bytes+32+4*i);
  if(!raveil_fold_validate(c)||c[5]!=word(bytes+12)||c[6]!=word(bytes+16))return false;
  r->request_id=id;
  for(unsigned i=0;i<65;++i)r->config[i]=c[i];
  for(unsigned i=0;i<648;++i)r->inputs[i]=0;
  for(unsigned i=0;i<c[5];++i)r->inputs[i]=word(bytes+292+4*i);
  for(unsigned i=0;i<c[6];++i)r->inputs[324+i]=word(bytes+292+4*(c[5]+i));
  return true;
}

bool raveil_fold_response_decode(const uint8_t *p,size_t n,
  uint64_t id,uint64_t epoch,uint64_t sequence,const uint8_t cookie[16],
  uint32_t count,uint32_t output[256]) {
  if(p==NULL||cookie==NULL||output==NULL||count<1||count>256||
     n!=60u+4u*count||word(p)!=UINT32_C(0x46525231)||word(p+4)!=1u||
     word(p+48)!=count||word(p+52)!=0u||word(p+n-4)!=crc(p,n-4))return false;
  const uint64_t expected[3]={id,epoch,sequence};
  for(unsigned i=0;i<3;++i)
    if(((uint64_t)word(p+8+8*i)|((uint64_t)word(p+12+8*i)<<32))!=expected[i])return false;
  for(unsigned i=0;i<16;++i)if(p[32+i]!=cookie[i])return false;
  for(uint32_t i=0;i<count;++i)output[i]=word(p+56+4*i);
  return true;
}
bool raveil_fold_evaluate(const struct raveil_fold_request *r,uint32_t output[256]) {
  if(r==NULL||output==NULL||!raveil_fold_validate(r->config))return false;
  const uint32_t *c=r->config;
  for(uint32_t i=0;i<c[1];++i)for(uint32_t j=0;j<c[2];++j) {
    uint32_t acc=0;
    for(uint32_t k=0;k<c[3];++k) {
      uint32_t values[8]={0};
      for(unsigned pc=0;pc<c[8];++pc) {
        uint32_t w=c[49+pc],op=w>>28,d=(w>>25)&7u,a=(w>>22)&7u,b=(w>>19)&7u;
        uint32_t imm=w&UINT32_C(0x3fffff);
        switch(op) {
          case 1: {
            const uint32_t *v=c+9+5*a;
            uint32_t address=v[1]+v[2]*i+v[3]*j+v[4]*k;
            values[d]=r->inputs[324*v[0]+address];break;
          }
          case 2: values[d]=values[a]+values[b];break;
          case 3: acc=c[4]?(acc>values[a]?acc:values[a]):acc+values[a];break;
          case 4: values[d]=values[a]>values[b]?values[a]:values[b];break;
          case 5: values[d]=(uint32_t)((uint64_t)values[a]*values[b]);break;
          case 6: values[d]=values[a]+imm;break;
          case 7: values[d]=values[a]>=imm?1u:0u;break;
          default:return false;
        }
      }
    }
    output[i*c[2]+j]=acc;
  }
  return true;
}

static void putword(uint8_t *p,uint32_t value) {
  for(unsigned i=0;i<4;++i)p[i]=(uint8_t)(value>>(8u*i));
}
bool raveil_fold_bridge_encode(const struct raveil_fold_request *r,
                               uint8_t *p,size_t capacity,size_t *size) {
  if(r==NULL||p==NULL||size==NULL||!r->request_id||!raveil_fold_validate(r->config))return false;
  size_t n=300u+4u*(r->config[5]+r->config[6]);if(capacity<n)return false;
  putword(p,RAVEIL_FOLD_BRIDGE_MAGIC);putword(p+4,1);putword(p+8,(uint32_t)n);
  putword(p+12,r->config[5]);putword(p+16,r->config[6]);putword(p+20,0);
  putword(p+24,(uint32_t)r->request_id);putword(p+28,(uint32_t)(r->request_id>>32));
  for(unsigned i=0;i<65;++i)putword(p+32+4*i,r->config[i]);
  for(unsigned i=0;i<r->config[5];++i)putword(p+292+4*i,r->inputs[i]);
  for(unsigned i=0;i<r->config[6];++i)putword(p+292+4*(r->config[5]+i),r->inputs[324+i]);
  putword(p+n-8,crc(p,n-8));putword(p+n-4,RAVEIL_FOLD_END);*size=n;return true;
}
bool raveil_fold_chain_decode(const uint8_t *p,size_t n,struct raveil_fold_chain *chain) {
  if(p==NULL||chain==NULL||n<340u||n>RAVEIL_FOLD_CHAIN_MAX_BYTES||
     word(p)!=RAVEIL_FOLD_CHAIN_MAGIC||word(p+4)!=1||word(p+8)!=n||
     word(p+12)<1||word(p+12)>8||word(p+n-4)!=RAVEIL_FOLD_CHAIN_END||
     word(p+n-8)!=crc(p,n-8))return false;
  struct raveil_fold_chain admitted={0};
  admitted.jobs.epoch=(uint64_t)word(p+16)|((uint64_t)word(p+20)<<32);
  admitted.jobs.count=word(p+12);if(!admitted.jobs.epoch)return false;
  uint64_t ids[8]={0};uint32_t counts[8]={0};size_t offset=24;
  struct raveil_fold_request request;
  for(uint32_t i=0;i<admitted.jobs.count;++i) {
    if(offset+308u>n-8u)return false;
    uint32_t source=word(p+offset),mask=word(p+offset+4);offset+=8;
    uint32_t length=word(p+offset+8);
    if(word(p+offset)!=RAVEIL_FOLD_BRIDGE_MAGIC||length<300u||
       length>RAVEIL_FOLD_MAX_BYTES||length>n-8u-offset||
       !raveil_fold_decode(p+offset,length,&request))return false;
    for(uint32_t j=0;j<i;++j)if(ids[j]==request.request_id)return false;
    if(mask>3u||(mask==0u?source!=UINT32_MAX:source>=i))return false;
    for(unsigned input=0;input<2;++input)if(mask&(1u<<input)) {
      if(request.config[5+input]!=counts[source])return false;
      for(unsigned k=0;k<request.config[5+input];++k)
        if(request.inputs[324u*input+k]!=0u)return false;
    }
    ids[i]=request.request_id;counts[i]=request.config[1]*request.config[2];
    admitted.sources[i]=source;admitted.masks[i]=mask;
    admitted.jobs.offsets[i]=(uint32_t)offset;admitted.jobs.lengths[i]=length;offset+=length;
  }
  if(offset!=n-8u)return false;
  *chain=admitted;return true;
}

bool raveil_fold_dag_decode(const uint8_t *p,size_t n,struct raveil_fold_dag *dag) {
  if(p==NULL||dag==NULL||n<348u||n>RAVEIL_FOLD_DAG_MAX_BYTES||
     word(p)!=RAVEIL_FOLD_DAG_MAGIC||(word(p+4)!=1&&word(p+4)!=2)||word(p+8)!=n||
     word(p+12)<1||word(p+12)>8||word(p+24)>=word(p+12)||word(p+28)!=0||
     word(p+n-4)!=RAVEIL_FOLD_DAG_END||word(p+n-8)!=crc(p,n-8))return false;
  struct raveil_fold_dag admitted={0};
  admitted.jobs.epoch=(uint64_t)word(p+16)|((uint64_t)word(p+20)<<32);
  admitted.jobs.count=word(p+12);admitted.output=word(p+24);
  if(!admitted.jobs.epoch)return false;
  uint64_t ids[8]={0};uint32_t counts[8]={0},read_chunks[8]={0};size_t offset=32;
  uint32_t version=word(p+4),metadata=version==2?24u:8u;
  struct raveil_fold_request request;
  for(uint32_t i=0;i<admitted.jobs.count;++i) {
    if(offset+metadata+300u>n-8u)return false;
    uint32_t extents[2]={0};
    for(unsigned b=0;b<2;++b) {
      admitted.sources[i][b]=word(p+offset+(version==2?12u*b:4u*b));
      if(version==2) {
        admitted.input_offsets[i][b]=word(p+offset+12u*b+4u);
        extents[b]=word(p+offset+12u*b+8u);
      }
    }
    offset+=metadata;
    uint32_t length=word(p+offset+8);
    if(word(p+offset)!=RAVEIL_FOLD_BRIDGE_MAGIC||length<300u||
       length>RAVEIL_FOLD_MAX_BYTES||length>n-8u-offset||
       !raveil_fold_decode(p+offset,length,&request))return false;
    for(uint32_t j=0;j<i;++j)if(ids[j]==request.request_id)return false;
    for(unsigned b=0;b<2;++b) {
      uint32_t source=admitted.sources[i][b],start=admitted.input_offsets[i][b];
      uint32_t extent=request.config[5+b];
      if(version==2&&extents[b]!=extent)return false;
      if(source==UINT32_MAX) {if(start)return false;continue;}
      if(source>=i||extent==0u||start>counts[source]||extent>counts[source]-start||
         (version==1&&extent!=counts[source]))return false;
      for(uint32_t chunk=start/128u;chunk<=(start+extent-1u)/128u;++chunk)
        read_chunks[i]|=1u<<(2u*source+chunk);
      for(unsigned k=0;k<request.config[5+b];++k)if(request.inputs[324u*b+k])return false;
      admitted.last_use[source]=i;
    }
    ids[i]=request.request_id;counts[i]=request.config[1]*request.config[2];
    admitted.chunks[i]=(counts[i]+127u)/128u;admitted.last_use[i]=i;
    admitted.jobs.offsets[i]=(uint32_t)offset;admitted.jobs.lengths[i]=length;offset+=length;
  }
  if(offset!=n-8u)return false;
  admitted.last_use[admitted.output]=admitted.jobs.count;
  uint32_t owners[8];for(unsigned j=0;j<8;++j)owners[j]=UINT32_MAX;
  for(uint32_t i=0;i<admitted.jobs.count;++i) {
    uint32_t refs=admitted.chunks[i];
    for(unsigned bit=0;bit<16;++bit)if(read_chunks[i]&(1u<<bit))++refs;
    if(refs>4u)return false;
    uint32_t found=0;
    for(unsigned slot=0;slot<8&&found<admitted.chunks[i];++slot)
      if(owners[slot]==UINT32_MAX||admitted.last_use[owners[slot]]<i)
        admitted.destinations[i][found++]=slot;
    if(found!=admitted.chunks[i])return false;
    for(unsigned j=0;j<found;++j)owners[admitted.destinations[i][j]]=i;
  }
  *dag=admitted;return true;
}
