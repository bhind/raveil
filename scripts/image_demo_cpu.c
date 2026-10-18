/* Independent scalar C compute-only context for EXP-0013. No accelerator claim. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
static void process(const uint8_t *input,int h,int w,int32_t *gradient,uint32_t *active,uint32_t *pooled) {
  for(int r=0;r<h;r++) for(int c=0;c<w;c++) {
    int left=c ? c-1 : 0, right=c+1<w ? c+1 : w-1;
    int32_t value=(int32_t)input[r*w+right]-input[r*w+left];
    gradient[r*w+c]=value;active[r*w+c]=value>0 ? (uint32_t)value : 0;
  }
  for(int r=0;r<h;r+=2) for(int c=0;c<w;c+=2) {
    uint32_t value=0;
    for(int dr=0;dr<2;dr++) for(int dc=0;dc<2;dc++)
      if(active[(r+dr)*w+c+dc]>value) value=active[(r+dr)*w+c+dc];
    pooled[(r/2)*(w/2)+c/2]=value;
  }
}
static double now(void) {struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t)) exit(2);return t.tv_sec+t.tv_nsec*1e-9;}
int main(int argc,char **argv) {
  if(argc!=3) return 2;
  FILE *f=fopen(argv[1],"rb");if(!f)return 2;
  int w=0,h=0,max=0;char magic[3]={0};
  if(fscanf(f,"%2s\n%d %d\n%d",magic,&w,&h,&max)!=4 || strcmp(magic,"P5") ||
     max!=255 || w<2 || w>64 || h<2 || h>64 || w%2 || h%2 || fgetc(f)!='\n')return 2;
  uint8_t input[4096];int32_t gradient[4096];uint32_t active[4096],pooled[1024];
  if(fread(input,1,w*h,f)!=(size_t)(w*h)||fgetc(f)!=EOF)return 2;fclose(f);
  char *end;long n=strtol(argv[2],&end,10);if(*end||n<1||n>1000000)return 2;
  void (* volatile call)(const uint8_t*,int,int,int32_t*,uint32_t*,uint32_t*)=process;
  call(input,h,w,gradient,active,pooled); /* one untimed warmup */
  double start=now();for(long i=0;i<n;i++)call(input,h,w,gradient,active,pooled);double elapsed=now()-start;
  printf("{\"iterations\":%ld,\"elapsed_seconds\":%.12f,\"nanoseconds_per_image\":%.6f,\"outputs\":[",n,elapsed,elapsed*1e9/n);
  for(int k=0;k<3;k++) {
    if(k)printf(",");printf("[");int count=k==2?w*h/4:w*h;
    for(int j=0;j<count;j++){if(j)printf(",");printf("%u",k==0?(uint32_t)gradient[j]:k==1?active[j]:pooled[j]);}printf("]");
  }
  printf("]}\n");return 0;
}
