#include "raveil/job_contract.h"
#include "raveil/object_manifest.h"

bool raveil_object_manifest_validate_v1(
    const struct raveil_object_manifest_v1 *manifest) {
  if(manifest==NULL || manifest->magic!=RAVEIL_OBJECT_MANIFEST_MAGIC ||
     manifest->schema_version!=RAVEIL_OBJECT_MANIFEST_V1 ||
     manifest->struct_size!=sizeof(*manifest) || manifest->flags!=0u ||
     manifest->object_id==0u || manifest->generation==0u ||
     manifest->version==0u || manifest->byte_length==0u ||
     (manifest->permitted_access!=RAVEIL_OBJECT_READ &&
      manifest->permitted_access!=(RAVEIL_OBJECT_READ|RAVEIL_OBJECT_WRITE)) ||
     (manifest->backing!=RAVEIL_OBJECT_BACKING_VOLATILE &&
      manifest->backing!=RAVEIL_OBJECT_BACKING_IMMUTABLE) ||
     manifest->reserved0!=0u) return false;
  for(size_t index=0;index<sizeof(manifest->reserved1);++index)
    if(manifest->reserved1[index]!=0u) return false;
  return manifest->backing!=RAVEIL_OBJECT_BACKING_IMMUTABLE ||
         manifest->permitted_access==RAVEIL_OBJECT_READ;
}
