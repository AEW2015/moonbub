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
void v58_note_allocation(size_t,size_t);
void* v58_test_malloc(size_t);
namespace cu66_port {
struct Error : std::exception { const char* text; explicit Error(const char* p):text(p){} const char* what() const noexcept override{return text;} };
struct Arena {
 size_t limit,live=0,peak=0,maximum=0,allocations=0,failures=0;
 size_t(*free_probe)()=nullptr;size_t(*largest_probe)()=nullptr;size_t reserve=0;
 struct Failure {size_t kind=0,requested=0,live=0,free=0,largest=0,probes=0;} last_failure;
 void failure(size_t kind,size_t n,size_t free=0,bool have_free=false)noexcept{last_failure={kind,n,live,free,0,have_free?size_t(1):size_t(0)};if(!have_free&&free_probe){last_failure.free=free_probe();last_failure.probes|=1;}if(largest_probe){last_failure.largest=largest_probe();last_failure.probes|=2;}}

 explicit Arena(size_t n):limit(n){}
 void* allocate(size_t n){if(n>limit-live){++failures;failure(1,n);throw Error("HUD allocation budget");} if(free_probe){size_t free=free_probe();if(free<reserve||n>free-reserve){++failures;failure(2,n,free,true);throw Error("HUD physical heap reserve");}} void* p=::v58_test_malloc(n?n:1);if(!p){++failures;failure(3,n);throw Error("HUD allocation unavailable");}if(free_probe)(void)free_probe();live+=n;if(live>peak)peak=live;if(n>maximum)maximum=n;++allocations;return p;}
 void release(void*p,size_t n)noexcept{std::free(p);live-=n;}
};
inline thread_local Arena* active=nullptr;
struct Scope { Arena* prior; explicit Scope(Arena&a):prior(active){active=&a;}~Scope(){active=prior;} };
template<class T> struct Alloc {
 using value_type=T; using propagate_on_container_move_assignment=std::true_type;
 Arena* owner;
 Alloc():owner(active){if(!owner)throw Error("HUD allocation outside owner");}
 template<class U>Alloc(const Alloc<U>&a):owner(a.owner){}
 T* allocate(size_t n){if(n>SIZE_MAX/sizeof(T)){owner->failure(4,n);throw Error("HUD allocation overflow");}::v58_note_allocation(sizeof(T),n*sizeof(T));return static_cast<T*>(owner->allocate(n*sizeof(T)));}
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
