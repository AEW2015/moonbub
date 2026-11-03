// Simulation-only blocking TCP bridge. No target/FPGA timing guarantees.
#include <arpa/inet.h>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
namespace {
constexpr uint32_t MAX_BODY=1039; // D: 15 bytes of header plus at most 1024 payload.
uint8_t body[MAX_BODY]; uint32_t len=0, sequence=0; int fd=-1;
bool read_all(void *out,size_t n) { auto p=static_cast<uint8_t*>(out);while(n){ssize_t r=recv(fd,p,n,0);if(r<0&&errno==EINTR)continue;if(r<=0)return false;p+=r;n-=r;}return true; }
bool write_all(const void *out,size_t n) { auto p=static_cast<const uint8_t*>(out);while(n){ssize_t r=send(fd,p,n,MSG_NOSIGNAL);if(r<0&&errno==EINTR)continue;if(r<=0)return false;p+=r;n-=r;}return true; }
uint32_t u32(unsigned i){return (uint32_t(body[i])<<24)|(uint32_t(body[i+1])<<16)|(uint32_t(body[i+2])<<8)|body[i+3];}
bool connect_server(){
 const char* h=getenv("BRIDGE_HOST");if(!h)h="127.0.0.1"; const char* p=getenv("BRIDGE_PORT");char* end=nullptr;long port=p?strtol(p,&end,10):15534;
 if(port<1||port>65535||(p&&(!end||*end)))return false;
 fd=socket(AF_INET,SOCK_STREAM,0);if(fd<0)return false;timeval timeout{15,0};setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
 sockaddr_in addr{};addr.sin_family=AF_INET;addr.sin_port=htons(port);if(inet_pton(AF_INET,h,&addr.sin_addr)!=1||connect(fd,(sockaddr*)&addr,sizeof(addr))!=0){close(fd);fd=-1;return false;}return true;
}
}
extern "C" int bridge_next(){
 if(fd<0&&!connect_server()){std::fprintf(stderr,"bridge: connect failed: %s\n",strerror(errno));return -1;}
 uint8_t h[4];if(!read_all(h,4)){std::fprintf(stderr,"bridge: header timeout/disconnect\n");return -2;}
 len=(uint32_t(h[0])<<24)|(uint32_t(h[1])<<16)|(uint32_t(h[2])<<8)|h[3];
 if(len<9||len>MAX_BODY){std::fprintf(stderr,"bridge: invalid body length %u\n",len);return -3;}
 if(!read_all(body,len)){std::fprintf(stderr,"bridge: body timeout/disconnect\n");return -4;}
 sequence=u32(1);uint8_t type=body[0];
 if((type=='B'&&len!=17)||(type=='D'&&(len<16||len!=uint32_t(15+((unsigned(body[13])<<8)|body[14]))))||((type=='C'||type=='A')&&len!=9)||(type!='B'&&type!='D'&&type!='C'&&type!='A')){
  std::fprintf(stderr,"bridge: invalid type/length\n");return -5;
 }
 return int(len);
}
extern "C" int bridge_byte(int idx){return idx>=0&&uint32_t(idx)<len?body[idx]:-1;}
extern "C" int bridge_ack(int status){uint8_t a[5]={uint8_t(status),uint8_t(sequence>>24),uint8_t(sequence>>16),uint8_t(sequence>>8),uint8_t(sequence)};return fd>=0&&write_all(a,sizeof(a))?0:-1;}
