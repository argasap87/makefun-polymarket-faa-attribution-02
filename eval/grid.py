import sys, math, statistics
sys.path.insert(0, '/home/hatch/workspace/makefun/polymarket-faa-02/eval')
from eval import score, cases, real, TAUS, price6

ZN=[-1.644854,-0.67449,0,0.67449,1.644854]
ZT3=[-2.353363,-0.764892,0,0.764892,2.353363]  # Student t df=3
ZT5=[-2.015048,-0.726687,0,0.726687,2.015048]  # t df=5

def make_fn(W=240, wcap=0.02, mult=1.0, floor=0.0003, cap=0.004, z=ZN, drift=0.0, driftW=240, level=False):
    def fn(m, horizon):
        p=m['prices']; x=p[-1]; n=len(p)
        w=min(W, n-1)
        diffs=[p[i+1]-p[i] for i in range(n-1-w, n-1)]
        # winsorized RMS
        wd=[max(-wcap, min(wcap, d)) for d in diffs]
        sig=math.sqrt(sum(d*d for d in wd)/len(wd)) if wd else 0.0
        sig=min(cap, max(floor, mult*sig))
        if level:
            sig *= math.sqrt(max(x*(1-x),0.01))/0.5
            sig=min(cap, max(floor, sig))
        # drift per hour from driftW window, shrunk
        dr=0.0
        if drift:
            dw=min(driftW, n-1)
            dr=drift*(p[-1]-p[-1-dw])/(dw/60.0)  # per hour
        rows=[]
        for h in range(1, horizon+1):
            med=x+dr*h/60.0
            rows.append([price6(med+zz*sig*math.sqrt(h)) for zz in z])
        return rows
    return fn

results=[]
# 1) fixed sigma sweep (sanity)
for sig in [0.0005,0.0008,0.001,0.0012,0.0015,0.002,0.0025]:
    fn=make_fn(W=240, mult=0, floor=sig, cap=sig)
    s=score(fn); results.append((s['ALL'], f'fixed sigma={sig}'))
# 2) realized vol windows / mult / floor / cap
for W in [60,240,1440,4320]:
    for mult in [1.0,1.5,2.0]:
        for floor,cap in [(0.0003,0.004),(0.0005,0.003),(0.0002,0.006)]:
            fn=make_fn(W=W, mult=mult, floor=floor, cap=cap)
            s=score(fn); results.append((s['ALL'], f'W={W} mult={mult} floor={floor} cap={cap}'))
results.sort()
for v,desc in results[:15]:
    print(f'{v:.6f}  {desc}')
print('--- baseline 0.363589 ---')
# 3) best few: try t-z, drift, level scaling
best_desc=results[0][1]
print('best so far:', best_desc)
