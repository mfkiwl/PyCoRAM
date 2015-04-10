#define UIO_MEM "/dev/uio0"
#define UMEM_SIZE (0x10000000)
#define UMEM_OFFSET (0x10000000)

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <assert.h>
#include <sys/mman.h>
#include <fcntl.h>

int fd_umem;
volatile char* umem_ptr = NULL;
unsigned int umem_used = 0;

void umem_open()
{
  fd_umem = open(UIO_MEM, O_RDWR);
  if(fd_umem < 1){
    printf("umem_open(): Invalid UIO device file: '%s'\n", UIO_MEM);
    exit(1);
  }
  umem_ptr = (volatile char*) mmap(NULL, UMEM_SIZE, PROT_READ|PROT_WRITE, MAP_SHARED, fd_umem, 0);
  umem_used = 0;
}

void* umem_malloc(unsigned int bytes)
{
  if(umem_ptr == NULL){
    printf("umem_malloc(): UMEM is not opened.\n");
    return NULL;
  }
  if(umem_used + bytes > UMEM_SIZE){
    return NULL;
  }
  void* ptr = (void*)(umem_ptr + umem_used);
  umem_used += bytes;
  return ptr;
}

void umem_cache_clean(char* addr, unsigned int bytes)
{
  __clear_cache(addr, addr + bytes);
}

void umem_close()
{
  if(umem_ptr == NULL){
    printf("umem_close(): UMEM is not opened.\n");
    return;
  }
  munmap((void*) umem_ptr, UMEM_SIZE);
  umem_ptr = NULL;
}
