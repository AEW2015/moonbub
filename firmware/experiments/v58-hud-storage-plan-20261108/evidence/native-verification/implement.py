from pathlib import Path
p=Path('C:/moon/dev/experiments/v58-hud-storage-plan-20261108/native/hud.hpp');s=p.read_text();out=Path('C:/moon/dev/experiments/v58-hud-storage-verification-20261108');(out/'V57-hud.hpp').write_text(s)
a=s.index('inline cu66_port::Vector<uint8_t> channel33(');z=s.index('inline cu66_port::Vector<uint16_t> byte_planes',a)
s=s[:a]+r'''template<class Emit>
inline void channel33_emit(Reader &r,unsigned count,unsigned maximum,Emit emit) {
  unsigned scheme=r.u8(),k=r.u8();
  uint32_t events=r.u32(),size=r.u32(),nb=r.u32();
  need(scheme<=2&&k<=14&&events<=count&&size<=6+506+2*count&&nb<=16*count+1,"HS33 channel bounds");
  cu66_port::Vector<uint8_t> symbols;
  if(events){Reader h(r.take(size));symbols=huffman(h,events,maximum);h.end();}
  else need(scheme==1&&!size,"HS33 empty symbols");
  Bits bits(r.take((nb+7)/8),nb);unsigned produced=0;
  auto put=[&](unsigned v){need(produced<count,"HS33 expansion");emit(uint8_t(v));++produced;};
  if(scheme==0){need(!k&&!nb&&events==count,"HS33 plain syntax");for(auto v:symbols)put(v);}
  else if(scheme==1){
    for(auto v:symbols){need(v!=0,"HS33 nonzero symbol");auto gap=plain_rice(bits,k,count-produced);while(gap--)put(0);put(v);}
    auto gap=plain_rice(bits,k,count-produced);while(gap--)put(0);
  }else{
    need(events>0,"HS33 repeat events");int last=-1;
    for(auto v:symbols){need(v!=last&&produced<count,"HS33 repeat order");last=v;auto n=plain_rice(bits,k,count-produced-1)+1;while(n--)put(v);}
  }
  need(produced==count,"HS33 exact expansion");bits.end();
}
inline cu66_port::Vector<uint8_t> channel33(Reader&r,unsigned count,unsigned maximum){
  cu66_port::Vector<uint8_t> out;out.reserve(count);
  channel33_emit(r,count,maximum,[&](uint8_t v){out.push_back(v);});return out;
}
inline void byte_planes_into(View data,unsigned n,cu66_port::Vector<uint16_t>&out,bool xor_values){
  Reader r(data);unsigned lo=r.u32(),hi=r.u32();need(size_t(lo)+hi+8==data.n,"HD25 planes lengths");
  out.resize(n);if(!xor_values)std::fill(out.begin(),out.end(),0);
  auto unpack=[&](View input,unsigned shift){
    need(input.n&&input.n<=n+(n+127)/128,"HD25 byte RLE bound");Reader a(input);unsigned pos=0;
    auto put=[&](uint8_t v){need(pos<n,"HD25 RLE overflow");const uint16_t value=uint16_t(uint16_t(v)<<shift);if(xor_values)out[pos]^=value;else out[pos]=uint16_t((out[pos]&~uint16_t(255u<<shift))|value);++pos;};
    while(a.pos<a.v.n){unsigned t=a.u8(),count;uint8_t value=0;
      if(t<128){count=t+1;auto raw=a.take(count);need(pos+count<=n,"HD25 literal overflow");for(unsigned i=0;i<count;++i)put(raw[i]);continue;}
      count=(t&63)+1;if(t>=192){value=a.u8();need(value!=0,"HD25 repeat zero");}need(pos+count<=n,"HD25 RLE overflow");while(count--)put(value);
    }need(pos==n,"HD25 RLE coverage");
  };
  unpack(r.take(lo),0);unpack(r.take(hi),8);r.end();
}
''' + s[z:]
a=s.index('inline cu66_port::Vector<uint16_t> byte_planes(');z=s.index('inline cu66_port::Vector<uint16_t> span_words(',a)
s=s[:a]+'''inline cu66_port::Vector<uint16_t> byte_planes(View data,unsigned n){cu66_port::Vector<uint16_t> out;byte_planes_into(data,n,out,false);return out;}\n'''+s[z:]
a=s.index('inline cu66_port::Vector<uint16_t> span_words(');z=s.index('inline cu66_port::Vector<uint16_t>\nrice_components',a)
part=s[a:z].replace('inline cu66_port::Vector<uint16_t> span_words(View data, unsigned w, unsigned hh) {','inline void span_words_into(View data,unsigned w,unsigned hh,cu66_port::Vector<uint16_t>&out,bool xor_values) {').replace('  cu66_port::Vector<uint16_t> out(w * hh);','  out.resize(w*hh);if(!xor_values)std::fill(out.begin(),out.end(),0);').replace('      out[y * w + x + j] = v[j];','      if(xor_values)out[y*w+x+j]^=v[j];else out[y*w+x+j]=v[j];').replace('  return out;\n','')
s=s[:a]+part+'''inline cu66_port::Vector<uint16_t> span_words(View data,unsigned w,unsigned hh){cu66_port::Vector<uint16_t> out;span_words_into(data,w,hh,out,false);return out;}\n'''+s[z:]
a=s.index('inline cu66_port::Vector<uint16_t>\nrice_components');z=s.index('inline std::pair<cu66_port::Vector<uint16_t>, size_t>\nmotion_prediction',a)
part=s[a:z].replace('inline cu66_port::Vector<uint16_t>\nrice_components(View data, unsigned w, unsigned hh,\n                const cu66_port::Vector<uint16_t> *prediction, bool left) {','inline void rice_components_into(View data,unsigned w,unsigned hh,const cu66_port::Vector<uint16_t>*prediction,bool left,cu66_port::Vector<uint16_t>&out) {').replace('  cu66_port::Vector<uint16_t> out(w * hh);','  out.resize(w*hh);').replace('  return out;\n','')
s=s[:a]+part+'''inline cu66_port::Vector<uint16_t> rice_components(View data,unsigned w,unsigned hh,const cu66_port::Vector<uint16_t>*prediction,bool left){cu66_port::Vector<uint16_t> out;rice_components_into(data,w,hh,prediction,left,out);return out;}\n'''+s[z:]
a=s.index('inline std::pair<cu66_port::Vector<uint16_t>, size_t>\nmotion_prediction');z=s.index('inline cu66_port::Vector<uint16_t>\ndecode_full_patch',a)
part=s[a:z].replace('inline std::pair<cu66_port::Vector<uint16_t>, size_t>\nmotion_prediction(const cu66_port::Vector<uint16_t> &ref, unsigned mode, View data,\n                  unsigned w, unsigned hh) {','inline size_t motion_prediction_into(const cu66_port::Vector<uint16_t>&ref,unsigned mode,View data,unsigned w,unsigned hh,cu66_port::Vector<uint16_t>&pred) {').replace('  cu66_port::Vector<uint16_t> pred(w * hh);','  pred.resize(w*hh);').replace('  if (mode == 1)\n    return {ref, 0};','  if(mode==1){pred.assign(ref.begin(),ref.end());return 0;}').replace('  return {pred, r.pos};','  return r.pos;')
s=s[:a]+part+'''inline std::pair<cu66_port::Vector<uint16_t>,size_t> motion_prediction(const cu66_port::Vector<uint16_t>&ref,unsigned mode,View data,unsigned w,unsigned hh){cu66_port::Vector<uint16_t> out;auto pos=motion_prediction_into(ref,mode,data,w,hh,out);return {std::move(out),pos};}\n'''+s[z:]
a=s.index('decode_full_patch(View packet, const std::array<uint16_t, 4> &rect)');s=s[:a]+s[a:].replace('decode_full_patch(View packet, const std::array<uint16_t, 4> &rect) {','decode_full_patch_into(View packet,const std::array<uint16_t,4>&rect,cu66_port::Vector<uint16_t> out) {',1)
a=s.index('decode_full_patch_into(');z=s.index('inline cu66_port::Vector<uint16_t> decode_patch(',a);part=s[a:z].replace('  cu66_port::Vector<uint16_t> out;','  out.clear();',1);s=s[:a]+part+'''inline cu66_port::Vector<uint16_t> decode_full_patch(View packet,const std::array<uint16_t,4>&rect){return decode_full_patch_into(packet,rect,cu66_port::Vector<uint16_t>{});}\n'''+s[z:]
s=s.replace('inline cu66_port::Vector<uint16_t> decode_patch(View packet, const Patch *reference,\n                                          unsigned expected_w,\n                                          unsigned expected_h) {','inline cu66_port::Vector<uint16_t> decode_patch_into(View packet,const Patch*reference,unsigned expected_w,unsigned expected_h,cu66_port::Vector<uint16_t> out) {',1)
a=s.index('inline cu66_port::Vector<uint16_t> decode_patch_into');z=s.index('inline cu66_port::Vector<Patch> decode_hud',a);part=s[a:z].replace('  cu66_port::Vector<uint16_t> out;','  out.clear();',1)
part=part.replace('      auto q = motion_prediction(reference->words, plain, data, w, hh);\n      out = std::move(q.first);\n      prediction = &out;\n      owned_prediction = true;\n      pos = q.second;','      pos=motion_prediction_into(reference->words,plain,data,w,hh,out);\n      prediction=&out;owned_prediction=true;')
lo=part.index('      auto mapped =');hi=part.index('    }\n    a.end();',lo)
part=part[:lo]+r'''      unsigned position=0;int rowdelta=0,resultsum=0;
      auto emit=[&](uint8_t symbol){
        need(position<w*hh,"HS expansion");const unsigned x=position%w;if(!x){rowdelta=0;resultsum=0;}
        int delta=signed_zig(symbol);if(mode&8){rowdelta+=delta;delta=rowdelta;}
        int result;if(!plain){resultsum+=delta;result=resultsum;}else result=int(((*prediction)[position]>>shift)&maximum)+delta;
        need(result>=0&&result<=int(maximum),"HS reconstructed range");out[position]=uint16_t((out[position]&~(uint32_t(maximum)<<shift))|(uint32_t(result)<<shift));++position;
      };
      if(magic=="HS33")channel33_emit(a,w*hh,(mode&8)?4*maximum:2*maximum,emit);
      else{auto mapped=huffman(a,w*hh,(mode&8)?4*maximum:2*maximum);for(auto value:mapped)emit(value);}
      need(position==w*hh,"HS exact channel pixels");
''' + part[hi:]
part=part.replace('      out = span_words(data, w, hh);\n      for (unsigned i = 0; i < out.size(); i++)\n        out[i] ^= (*base)[i];','      out.assign(base->begin(),base->end());span_words_into(data,w,hh,out,true);')
part=part.replace('      out = byte_planes(data, w * hh);\n      for (unsigned i = 0; i < out.size(); i++)\n        out[i] ^= (*base)[i];','      out.assign(base->begin(),base->end());byte_planes_into(data,w*hh,out,true);')
part=part.replace('      out = byte_planes(data, w * hh);','      byte_planes_into(data,w*hh,out,false);')
part=part.replace('      out = rice_components(data, w, hh, base, mode == 9);','      rice_components_into(data,w,hh,base,mode==9,out);')
lo=part.index('      auto q = motion_prediction(*base, mode == 4 ? 2 : 3, data, w, hh);');hi=part.index('      break;\n    }',lo)
part=part[:lo]+r'''      auto consumed=motion_prediction_into(*base,mode==4?2:3,data,w,hh,out);
      auto residual=data.sub(consumed,data.n-consumed);need(residual.n>0,"HD25 missing residual");
      unsigned grammar=residual[0];auto body=residual.sub(1,residual.n-1);
      if(grammar==0)span_words_into(body,w,hh,out,true);
      else if(grammar==1)byte_planes_into(body,w*hh,out,true);
      // The old grammar2 XORed prediction twice. In-place component decoding
      // produces that same absolute result; each channel reads its old bits
      // before replacing only that channel. Accepted storage is never written.
      else if(grammar==2)rice_components_into(body,w,hh,&out,false,out);
      else need(false,"HD25 residual grammar");
''' + part[hi:]
s=s[:a]+part+'''inline cu66_port::Vector<uint16_t> decode_patch(View packet,const Patch*reference,unsigned w,unsigned hh){return decode_patch_into(packet,reference,w,hh,cu66_port::Vector<uint16_t>{});}\n'''+s[z:]
s=s.replace('  for (unsigned i : order) {','  // Private candidate output storage is planned before component temporaries.\n  for(unsigned i:order){out[i].rect=rects[i];out[i].words.reserve(size_t(rects[i][2])*rects[i][3]);}\n  for (unsigned i : order) {',1)
s=s.replace('      p.words = decode_full_patch(data, p.rect);','      p.words = decode_full_patch_into(data,p.rect,std::move(out[i].words));',1)
s=s.replace('      p.words = decode_patch(data, reference ? &(*reference)[i] : nullptr,\n                             p.rect[2], p.rect[3]);','      p.words = decode_patch_into(data,reference?&(*reference)[i]:nullptr,p.rect[2],p.rect[3],std::move(out[i].words));',1)
p.write_text(s);print('V58_IMPLEMENTED_HUD_ONLY')
