#pragma once
#include <cstdlib>
#include <cstddef>
#include <cstdint>
#include <new>
#include <exception>
#include <vector>
#include <map>
#include <set>
#include <string>
#include <memory>
namespace cu66_port {
struct Error : std::exception { const char* text; explicit Error(const char* p):text(p){} const char* what() const noexcept override{return text;} };
struct Arena {
 size_t limit,live=0,peak=0,maximum=0,allocations=0,failures=0;
 explicit Arena(size_t n):limit(n){}
 void* allocate(size_t n){if(n>limit-live){++failures;throw Error("HUD allocation budget");} void* p=std::malloc(n?n:1);if(!p){++failures;throw Error("HUD allocation unavailable");}live+=n;if(live>peak)peak=live;if(n>maximum)maximum=n;++allocations;return p;}
 void release(void*p,size_t n)noexcept{std::free(p);live-=n;}
};
inline thread_local Arena* active=nullptr;
struct Scope { Arena* prior; explicit Scope(Arena&a):prior(active){active=&a;}~Scope(){active=prior;} };
template<class T> struct Alloc {
 using value_type=T; using propagate_on_container_move_assignment=std::true_type;
 Arena* owner;
 Alloc():owner(active){if(!owner)throw Error("HUD allocation outside owner");}
 template<class U>Alloc(const Alloc<U>&a):owner(a.owner){}
 T* allocate(size_t n){if(n>SIZE_MAX/sizeof(T))throw Error("HUD allocation overflow");return static_cast<T*>(owner->allocate(n*sizeof(T)));}
 void deallocate(T*p,size_t n)noexcept{owner->release(p,n*sizeof(T));}
 template<class U>bool operator==(const Alloc<U>&a)const{return owner==a.owner;}
 template<class U>bool operator!=(const Alloc<U>&a)const{return owner!=a.owner;}
};
template<class T>using Vector=std::vector<T,Alloc<T>>;
template<class K,class V>using Map=std::map<K,V,std::less<K>,Alloc<std::pair<const K,V>>>;
template<class T>using Set=std::set<T,std::less<T>,Alloc<T>>;
using String=std::basic_string<char,std::char_traits<char>,Alloc<char>>;
template<class T,class...A>std::shared_ptr<T> make_shared(A&&...a){return std::allocate_shared<T>(Alloc<T>{},std::forward<A>(a)...);}
}
