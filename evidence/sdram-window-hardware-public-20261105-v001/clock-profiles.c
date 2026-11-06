#include <stdio.h>
#include "serdes4_clock.h"
int main(void){ for(unsigned p=0;p<360;p+=5){serdes4_clock c={0};if(!serdes4_clock_calculate(166000,p*1000,&c))return 1;printf("%u %u %u %u %u %u %u %u\n",p,c.actual_hz,c.m8,c.d,c.o,c.read_phase_mdeg,c.read_div_phase_mdeg,c.phase_ticks);}return 0;}
