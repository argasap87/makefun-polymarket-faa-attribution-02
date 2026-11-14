import sys, math
sys.path.insert(0, '/home/hatch/workspace/makefun/polymarket-faa-02/eval')
import eval as E
ZN=[-1.644854,-0.67449,0,0.67449,1.644854]
ZT3=[-2.353363,-0.764892,0,0.764892,2.353363]
ZT5=[-2.015048,-0.726687,0,0.726687,2.015048]
def price6(x): return round(min(1,max(0,x))*1e6)/1e6+0
def make_fn(W=60, wcap=0.02, mult=1.0, floor=0.0003, cap=0.004, z=ZN, drift=0.0, driftW=240, level=False):
    def fn(m, horizon):
        p=m['prices']; x=p[-1]; n=len(p)
        w=min(W, n-1)
        diffs=[p[i+1]-p[i] for i in range(n-1-w, n-1)]
        wd=[max(-wcap, min(wcap, d)) for d in diffs]
        sig=math.sqrt(sum(d*d for d in wd)/len(wd)) if wd else 0.0
        sig=min(cap, max(floor, mult*sig))
        if level:
            sig *= math.sqrt(max(x*(1-x),0.01))/0.5
            sig=min(cap, max(floor, sig))
        dr=0.0
        if drift:
            dw=min(driftW, n-1)
            dr=drift*(p[-1]-p[-1-dw])/(dw/60.0)
        rows=[]
        for h in range(1, horizon+1):
            med=x+dr*h/60.0
            rows.append([price6(med+zz*sig*math.sqrt(h)) for zz in z])
        return rows
    return fn

def show(label, fn):
    s=E.score(fn)
    print(f"{s['ALL']:.6f}  {label}   per-case: " + " ".join(f"{k}={v:.4f}" for k,v in s.items() if k!='ALL'))

show('base W60 f.0003 c.004 normal', make_fn())
show('t3', make_fn(z=ZT3))
show('t5', make_fn(z=ZT5))
show('drift 0.25 W240', make_fn(drift=0.25))
show('drift 0.5 W240', make_fn(drift=0.5))
show('drift -0.25 (mean-revert) W240', make_fn(drift=-0.25))
show('level scaling', make_fn(level=True))
for W in [30,45,90,120,180]:
    show(f'W={W}', make_fn(W=W))
for wcap in [0.005,0.01,0.05,0.1]:
    show(f'wcap={wcap}', make_fn(wcap=wcap))
for floor,cap in [(0.0002,0.004),(0.0003,0.003),(0.0004,0.004),(0.0003,0.005),(0.0005,0.004),(0.0001,0.004)]:
    show(f'floor={floor} cap={cap}', make_fn(floor=floor,cap=cap))
for mult in [0.8,0.9,1.1,1.25]:
    show(f'mult={mult}', make_fn(mult=mult))
# fixed sigma for reference
show('fixed sigma 0.001', make_fn(mult=0, floor=0.001, cap=0.001))
show('fixed sigma 0.0012', make_fn(mult=0, floor=0.0012, cap=0.0012))
