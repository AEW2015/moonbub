"""Integer/rational measured quality gates, separate from encoder optimality."""
from fractions import Fraction

def qualifies(sse,samples,complete,target_sse,target_samples,gate,cap=49152):
 if gate not in('mean','mean_and_peak','every_frame'):raise ValueError('explicit quality gate')
 if not(len(sse)==len(samples)==len(complete)==len(target_sse)==len(target_samples)) or not len(sse):raise ValueError('matched nonempty presentation sequences')
 if any(type(x)is not int or x<0 for x in(*sse,*target_sse,*complete)) or any(type(x)is not int or x<=0 for x in(*samples,*target_samples)):raise ValueError('nonnegative integer SSE/bytes and positive sample counts')
 if any(x>cap for x in complete):return False
 mean=sum(sse)*sum(target_samples)<=sum(target_sse)*sum(samples)
 if gate=='mean':return mean
 if gate=='every_frame':return all(a*d<=c*b for a,b,c,d in zip(sse,samples,target_sse,target_samples,strict=True))
 return mean and max(Fraction(a,b) for a,b in zip(sse,samples,strict=True))<=max(Fraction(a,b) for a,b in zip(target_sse,target_samples,strict=True))
