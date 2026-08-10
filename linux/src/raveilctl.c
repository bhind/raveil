#ifndef __linux__
#error "raveilctl requires Linux"
#endif
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include "uapi/raveil_driver.h"
int main(void) {
  const char *runtime=getenv("XDG_RUNTIME_DIR"); if(runtime==0||runtime[0]!='/') return 2;
  struct sockaddr_un address={.sun_family=AF_UNIX};
  int length=snprintf(address.sun_path,sizeof(address.sun_path),"%s/raveil-driver.sock",runtime);
  if(length<=0||(size_t)length>=sizeof(address.sun_path)) return 2;
  int fd=socket(AF_UNIX,SOCK_SEQPACKET,0); if(fd<0) return 3;
  if(connect(fd,(struct sockaddr *)&address,sizeof(address))!=0) return 4;
  struct raveil_driver_request request={RAVEIL_DRIVER_MAGIC,RAVEIL_DRIVER_ABI_VERSION,
      sizeof(request),RAVEIL_OP_PING,0u,1u,0x83u};
  struct raveil_driver_completion completion;
  if(send(fd,&request,sizeof(request),0)!=(ssize_t)sizeof(request) ||
     recv(fd,&completion,sizeof(completion),MSG_TRUNC)!=(ssize_t)sizeof(completion)) return 5;
  close(fd);
  if(completion.magic!=RAVEIL_DRIVER_MAGIC ||
     completion.abi_version!=RAVEIL_DRIVER_ABI_VERSION ||
     completion.struct_size!=sizeof(completion) ||
     completion.status!=RAVEIL_STATUS_OK || completion.detail!=0u ||
     completion.request_id!=1u || completion.result!=0x83u) return 6;
  puts("raveil linux driver ping: OK"); return 0;
}
