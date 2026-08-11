#ifndef SONATINE_VFS_H
#define SONATINE_VFS_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define VFS_ROOT_OBJECT 1u
#define VFS_NODE_HELLO 1u
#define VFS_NODE_SCRATCH 2u
#define VFS_FILE_CAPACITY 64u
enum vfs_result { VFS_OK=0, VFS_NOT_FOUND, VFS_DENIED, VFS_INVALID, VFS_NO_SPACE };
void vfs_init(void);
uint32_t vfs_lookup(const char *absolute_path);
const char *vfs_path(uint32_t node);
enum vfs_result vfs_stat(uint32_t node,size_t *size,bool *writable);
enum vfs_result vfs_read(uint32_t node,size_t offset,uint8_t *value);
enum vfs_result vfs_write(uint32_t node,size_t offset,uint8_t value);
#endif
