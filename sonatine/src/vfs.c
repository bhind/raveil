#include "vfs.h"

struct vfs_node { const char *path; uint8_t data[VFS_FILE_CAPACITY]; size_t size; bool writable; };
static struct vfs_node nodes[2];
static bool text_equal(const char *left,const char *right) {
  while(*left!='\0' && *left==*right) { ++left; ++right; }
  return *left==*right;
}
void vfs_init(void) {
  static const char hello[]="hello from initramfs\n";
  nodes[0].path="/hello"; nodes[0].size=sizeof(hello)-1u; nodes[0].writable=false;
  for(size_t i=0;i<nodes[0].size;++i) nodes[0].data[i]=(uint8_t)hello[i];
  nodes[1].path="/scratch"; nodes[1].size=0u; nodes[1].writable=true;
  for(size_t i=0;i<VFS_FILE_CAPACITY;++i) nodes[1].data[i]=0u;
}
uint32_t vfs_lookup(const char *path) {
  if(path==NULL || path[0]!='/') return 0u;
  for(size_t i=0;i<2u;++i) if(text_equal(path,nodes[i].path)) return (uint32_t)i+1u;
  return 0u;
}
static struct vfs_node *get_node(uint32_t node) { return node>=1u&&node<=2u?&nodes[node-1u]:NULL; }
enum vfs_result vfs_stat(uint32_t node,size_t *size,bool *writable) {
  struct vfs_node *entry=get_node(node); if(entry==NULL||size==NULL||writable==NULL) return VFS_INVALID;
  *size=entry->size; *writable=entry->writable; return VFS_OK;
}
enum vfs_result vfs_read(uint32_t node,size_t offset,uint8_t *value) {
  struct vfs_node *entry=get_node(node);
  if(entry==NULL||value==NULL) return VFS_INVALID;
  if(offset>=entry->size) return VFS_NOT_FOUND;
  *value=entry->data[offset];
  return VFS_OK;
}
enum vfs_result vfs_write(uint32_t node,size_t offset,uint8_t value) {
  struct vfs_node *entry=get_node(node);
  if(entry==NULL) return VFS_INVALID;
  if(!entry->writable) return VFS_DENIED;
  if(offset>entry->size||offset>=VFS_FILE_CAPACITY) return VFS_NO_SPACE;
  entry->data[offset]=value;
  if(offset==entry->size) ++entry->size;
  return VFS_OK;
}
