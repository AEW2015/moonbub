from pathlib import Path
p=Path('C:/moon/dev/experiments/v58-hud-storage-plan-20261108/native/hud.hpp');s=p.read_text();old='inline cu66_port::Vector<uint8_t> huffman(Reader&r,unsigned count,unsigned maximum){cu66_port::Vector<uint8_t> out;out.reserve(count);huffman_emit(r,count,maximum,[&](uint8_t value){out.push_back(value);});return out;}'
new='inline cu66_port::Vector<uint8_t> huffman(Reader&r,unsigned count,unsigned maximum){HuffmanSymbols symbols;symbols.init(r,count,maximum);cu66_port::Vector<uint8_t> out;out.reserve(count);for(unsigned i=0;i<count;++i)out.push_back(symbols.next());symbols.end();return out;}'
assert old in s;p.write_text(s.replace(old,new))
