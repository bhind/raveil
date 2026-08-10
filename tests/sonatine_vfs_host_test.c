#include <assert.h>
#include <stdint.h>
#include "vfs.h"
int main(void) {
  uint8_t value=0u; size_t size=0u; bool writable=false;
  vfs_init();
  assert(vfs_lookup("/hello")==VFS_NODE_HELLO);
  assert(vfs_lookup("/scratch")==VFS_NODE_SCRATCH);
  assert(vfs_lookup("hello")==0u && vfs_lookup("/../hello")==0u);
  assert(vfs_lookup("/hell")==0u && vfs_lookup("/hello/x")==0u);
  assert(vfs_stat(VFS_NODE_HELLO,&size,&writable)==VFS_OK && size==21u && !writable);
  assert(vfs_read(VFS_NODE_HELLO,0u,&value)==VFS_OK && value=='h');
  assert(vfs_write(VFS_NODE_HELLO,0u,'X')==VFS_DENIED);
  assert(vfs_read(VFS_NODE_HELLO,0u,&value)==VFS_OK && value=='h');
  assert(vfs_write(VFS_NODE_SCRATCH,0u,'R')==VFS_OK);
  assert(vfs_read(VFS_NODE_SCRATCH,0u,&value)==VFS_OK && value=='R');
  assert(vfs_write(VFS_NODE_SCRATCH,2u,'X')==VFS_NO_SPACE);
  assert(vfs_write(VFS_NODE_SCRATCH,VFS_FILE_CAPACITY,'X')==VFS_NO_SPACE);
  assert(vfs_read(99u,0u,&value)==VFS_INVALID);
  vfs_init();
  assert(vfs_read(VFS_NODE_SCRATCH,0u,&value)==VFS_NOT_FOUND);
  return 0;
}
