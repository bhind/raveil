#include "fold_bridge.h"
#include "console.h"
#include "platform.h"
#include "raveil/affine_fold.h"

static uint8_t response[1084];
static void hex(uint64_t v,unsigned digits) {
  static const char alphabet[]="0123456789abcdef";
  for(int shift=(int)(digits*4u)-4;shift>=0;shift-=4)
    console_putc(alphabet[(v>>(unsigned)shift)&15u]);
}
static uint64_t now(void) {return *(volatile uint64_t *)QEMU_CLINT_MTIME;}
static int receive_hex(uint64_t deadline) {
  /* One character credit at a time: never overrun polled UART RX. */
  console_putc('>');
  while(now()<deadline) {
    char c;
    if(console_try_getc(&c)) {
      if(c>='0'&&c<='9')return c-'0';
      if(c>='a'&&c<='f')return c-'a'+10;
      return -1;
    }
    cpu_relax();
  }
  return -1;
}
bool fold_bridge_exchange(const uint8_t *request,size_t size,
                          const struct sonatine_submission *issued,
                          uint32_t count,uint32_t output[256]) {
  return fold_bridge_exchange_checked(request,size,issued,count,output,NULL);
}
bool fold_bridge_exchange_checked(const uint8_t *request,size_t size,
                          const struct sonatine_submission *issued,
                          uint32_t count,uint32_t output[256],bool *framed) {
  if(framed!=NULL)*framed=false;
  console_write("RAVEIL-FOLD-DISPATCH-V1 request=");hex(issued->job.job_id,16);
  console_write(" epoch=");hex(issued->execution_epoch,16);
  console_write(" sequence=");hex(issued->execution_sequence,16);
  console_write(" cookie=");for(unsigned i=0;i<16;++i)hex(issued->completion_cookie[i],2);
  console_write(" count=");console_write_dec(count);
  console_write(" envelope=");for(size_t i=0;i<size;++i)hex(request[i],2);
  console_write("\n");
  const uint64_t deadline=now()+60u*QEMU_TIMEBASE_HZ;
  size_t length=60u+4u*count;
  for(size_t i=0;i<length;++i) {
    int high=receive_hex(deadline);if(high<0) {console_write("\n");return false;}
    int low=receive_hex(deadline);if(low<0) {console_write("\n");return false;}
    response[i]=(uint8_t)((unsigned)high*16u+(unsigned)low);
  }
  console_write("\n");
  if(framed!=NULL)*framed=true;
  return raveil_fold_response_decode(response,length,issued->job.job_id,
    issued->execution_epoch,issued->execution_sequence,issued->completion_cookie,count,output);
}
