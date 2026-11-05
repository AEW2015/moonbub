// SPDX-License-Identifier: GPL-3.0-or-later
// Actual pinned render565 of selected reconstructed planes, excluding HUD.
#include "oracle-native/body_decoder.h"
#include <fstream>
#include <iomanip>
#include <iostream>
int main(int argc,char**argv){
 if(argc!=2)return 2;
 std::ifstream source(argv[1],std::ios::binary);if(!source)return 3;
 gamebub::v20::body::Planes p;
 for(unsigned plane=0;plane<3;++plane){
  p[plane].resize(plane?360*240:720*480);
  for(auto&v:p[plane]){int c=source.get();if(c<0)return 4;v=c;}
 }
 if(source.get()!=EOF)return 5;
 auto words=gamebub::v20::body::render565(p,720,480);
 std::ofstream out("native-base-rgb.hex");out<<std::hex<<std::setfill('0');
 for(auto word:words)out<<std::setw(4)<<word<<'\n';
 std::cout<<"PINNED_NATIVE_BASE_PASS pixels="<<words.size()<<" preHUD=1\n";
}
