#include "Vcu77_yuv_rgb.h"
#include "verilated.h"
#include <array>
#include <deque>
#include <iostream>
#include <random>
#include <stdexcept>
static void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
struct P{unsigned u,v,y;std::array<unsigned,4>cb,cr;bool hud,error;unsigned rgb;};
static unsigned ref(const P&p){
 auto c=[&](const auto&a){int t=a[0],b=a[2];if(p.u&1){t=(t+int(a[1])+1)/2;b=(b+int(a[3])+1)/2;}if(p.v&1)t=(t+b+1)/2;return t-128;};
 auto floor256=[](int n){return n>=0?n/256:-((-n+255)/256);};auto clamp=[](int n){return std::max(0,std::min(255,n));};int cb=c(p.cb),cr=c(p.cr);
 unsigned r=clamp(int(p.y)+floor256(359*cr+128)),g=clamp(int(p.y)-floor256(88*cb+183*cr+128)),b=clamp(int(p.y)+floor256(454*cb+128));
 return p.hud?p.rgb:((r>>3)<<11)|((g>>2)<<5)|(b>>3);
}
int main(){try{
 VerilatedContext ctx;ctx.threads(1);Vcu77_yuv_rgb d{&ctx};std::mt19937 rng(7701);std::deque<P>q;unsigned accepted=0,emitted=0,flushed=0,abort_probes=0,ii1=0;bool held=false;unsigned hu=0,hv=0,hr=0,he=0;
 auto tick=[&](bool abort){d.clk=0;d.abort_i=abort;d.eval();if(held&&!abort){need(d.out_valid&&d.out_u==hu&&d.out_v==hv&&d.out_rgb==hr&&d.out_error==he,"held output changed");}bool in=d.in_valid&&d.in_ready,out=d.out_valid&&d.out_ready;if(abort){flushed+=q.size();q.clear();abort_probes++;}else{
  if(out){need(!q.empty(),"unowned output");auto p=q.front();q.pop_front();if(!(d.out_u==p.u&&d.out_v==p.v&&d.out_rgb==ref(p)&&bool(d.out_error)==p.error)){std::cerr<<"mismatch u="<<p.u<<" v="<<p.v<<" y="<<p.y<<" cb="<<p.cb[0]<<","<<p.cb[1]<<","<<p.cb[2]<<","<<p.cb[3]<<" cr="<<p.cr[0]<<","<<p.cr[1]<<","<<p.cr[2]<<","<<p.cr[3]<<" got="<<d.out_rgb<<" expected="<<ref(p)<<"\n";need(false,"pixel mismatch");}emitted++;}
  if(in){P p{d.in_u,d.in_v,d.in_y,{d.in_cb00,d.in_cb10,d.in_cb01,d.in_cb11},{d.in_cr00,d.in_cr10,d.in_cr01,d.in_cr11},bool(d.in_hud_hit),bool(d.in_error),d.in_hud};q.push_back(p);accepted++;}
 }held=d.out_valid&&!d.out_ready&&!abort;hu=d.out_u;hv=d.out_v;hr=d.out_rgb;he=d.out_error;d.clk=1;d.eval();return std::array<bool,2>{in,out};};
 d.rst=1;d.in_valid=0;d.out_ready=0;tick(false);tick(false);d.rst=0;
 for(unsigned n=0;n<180000;n++){
  d.in_valid=n<150000&&(n<10000||rng()%5);d.out_ready=n<10000||rng()%4;
  unsigned sel=n%32;auto value=[&](){return sel<4?(sel==0?0:sel==1?255:sel==2?127:128):unsigned(rng()%256);};
  d.in_u=n%720;d.in_v=(n/720)%480;d.in_y=value();d.in_cb00=value();d.in_cb10=value();d.in_cb01=value();d.in_cb11=value();d.in_cr00=value();d.in_cr10=value();d.in_cr01=value();d.in_cr11=value();d.in_hud_hit=n%7==0;d.in_hud=rng();d.in_error=n%13==0;
  bool abort=n>10000&&n%7919==0;auto e=tick(abort);if(n>=3&&n<10000){need(e[0]&&e[1],"II1 failure");ii1++;}
 }
 d.in_valid=0;d.out_ready=1;for(unsigned n=0;n<8;n++)tick(false);need(q.empty()&&accepted==emitted+flushed,"final accounting");need(abort_probes>10&&ii1==9997,"coverage");std::cout<<"PIXEL_PASS accepted="<<accepted<<" emitted="<<emitted<<" flushed="<<flushed<<" aborts="<<abort_probes<<" II1_cycles="<<ii1<<"\n";
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
