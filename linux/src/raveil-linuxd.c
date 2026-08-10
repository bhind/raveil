#ifndef __linux__
#error "raveil-linuxd requires Linux"
#endif
#define _GNU_SOURCE
#include <errno.h>
#include <stddef.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>
#include "raveil_driver_core.h"

static volatile sig_atomic_t stop_requested;
static void request_stop(int signal_number) { (void)signal_number; stop_requested=1; }

static int socket_address(struct sockaddr_un *address) {
  const char *runtime=getenv("XDG_RUNTIME_DIR");
  if(runtime==0 || runtime[0]!='/' || strstr(runtime,"..")!=0) return -1;
  struct stat directory;
  if(lstat(runtime,&directory)!=0 || !S_ISDIR(directory.st_mode) ||
     directory.st_uid!=getuid() || (directory.st_mode&0022u)!=0u) return -1;
  memset(address,0,sizeof(*address)); address->sun_family=AF_UNIX;
  int length=snprintf(address->sun_path,sizeof(address->sun_path),
                      "%s/raveil-driver.sock",runtime);
  return length>0 && (size_t)length<sizeof(address->sun_path)?0:-1;
}
static struct raveil_driver_completion rejected(const struct raveil_driver_request *request,
                                                  uint32_t status) {
  struct raveil_driver_completion value={0}; value.magic=RAVEIL_DRIVER_MAGIC;
  value.abi_version=RAVEIL_DRIVER_ABI_VERSION; value.struct_size=sizeof(value);
  value.status=status; value.request_id=request->request_id; return value;
}
int main(void) {
  struct sockaddr_un address; if(socket_address(&address)!=0) return 2;
  int result=0,server=-1,client=-1; bool bound=false;
  mode_t old_mask=umask(0077);
  server=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0);
  if(server<0) { result=3; goto cleanup; }
  if(bind(server,(struct sockaddr *)&address,sizeof(address))!=0) { result=4; goto cleanup; }
  bound=true;
  if(chmod(address.sun_path,0600)!=0 || listen(server,1)!=0) { result=4; goto cleanup; }
  umask(old_mask); old_mask=(mode_t)-1;
  struct sigaction action={0}; action.sa_handler=request_stop;
  sigemptyset(&action.sa_mask); (void)sigaction(SIGINT,&action,0); (void)sigaction(SIGTERM,&action,0);
  client=accept4(server,0,0,SOCK_CLOEXEC);
  if(client<0) { result=stop_requested?0:5; goto cleanup; }
  struct ucred peer; socklen_t peer_size=sizeof(peer);
  if(getsockopt(client,SOL_SOCKET,SO_PEERCRED,&peer,&peer_size)!=0 || peer.uid!=getuid()) {
    result=6; goto cleanup;
  }
  struct raveil_driver_core core; raveil_driver_core_init(&core);
  for(;;) {
    struct raveil_driver_request request={0};
    ssize_t count=recv(client,&request,sizeof(request),MSG_TRUNC);
    if(count==0) break;
    if(count<0) { result=stop_requested?0:7; break; }
    struct raveil_driver_completion completion;
    if(count!=(ssize_t)sizeof(request)) completion=rejected(&request,RAVEIL_STATUS_INVALID);
    else {
      uint32_t status=raveil_driver_submit(&core,&request);
      if(status==RAVEIL_STATUS_OK) (void)raveil_driver_reap(&core,&completion);
      else completion=rejected(&request,status);
    }
    if(send(client,&completion,sizeof(completion),MSG_NOSIGNAL)!=(ssize_t)sizeof(completion)) {
      result=7; break;
    }
  }
cleanup:
  if(old_mask!=(mode_t)-1) umask(old_mask);
  if(client>=0) close(client);
  if(server>=0) close(server);
  if(bound) unlink(address.sun_path);
  return result;
}
