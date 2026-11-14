import sys, math
sys.path.insert(0, '/home/hatch/workspace/makefun/polymarket-faa-02/eval')
import eval as E
ZN=[-1.644854,-0.67449,0,0.67449,1.644854]
def price6(x): return round(min(1,max(0,x))*1e6)/1e6+0
def make_fn(W=60, wcap=0.02, mult=0.9, floor=0.0003, cap=0.004, z=ZN, power=0.5, outer=1.0, ewma=None):
    def fn(m, horizon):
        p=m['prices']; x=p[-1]; n=len(p)
        if ewma:
            # exponentially weighted RMS, halflife in minutes
            hl=ewma; lam=0.5**(1.0/hl); s2=0.0; wsum=0.0; wgt=1.0
            for i in range(n-2, max(-1, n-2-4320), -1):
                d=max(-wcap, min(wcap, p[i+1]-p[i]))
                s2+=wgt*d*d; wsum+=wgt; wgt*=lam
            sig=math.sqrt(s2/wsum) if wsum else 0.0
        else:
            w=min(W, n-1)
            diffs=[p[i+1]-p[i] for i in range(n-1-w, n-1)]
            wd=[max(-wcap, min(wcap, d)) for d in diffs]
            sig=math.sqrt(sum(d*d for d in wd)/len(wd)) if wd else 0.0
        sig=min(cap, max(floor, mult*sig))
        rows=[]
        for h in range(1, horizon+1):
            s=sig*(h**power)
            row=[]
            for j,zz in enumerate(z):
                zz2=zz*(outer if j in (0,4) else 1.0)
                row.append(price6(x+zz2*s))
            rows.append(row)
        return rows
    return fn
def show(label, fn):
    s=E.score(fn)
    print(f"{s['ALL']:.6f}  {label}   " + " ".join(f"{k}={v:.4f}" for k,v in s.items() if k!='ALL'))
show('W60 mult0.9 (candidate)', make_fn())
show('W60 mult0.85', make_fn(mult=0.85))
show('W30 mult0.8', make_fn(W=30, mult=0.8))
show('W45 mult0.85', make_fn(W=45, mult=0.85))
show('W60 mult0.9 power0.55', make_fn(power=0.55))
show('W60 mult0.9 power0.6', make_fn(power=0.6))
show('W60 mult0.9 outer1.3', make_fn(outer=1.3))
show('W60 mult0.9 outer1.5', make_fn(outer=1.5))
show('EWMA hl60 mult0.9', make_fn(ewma=60))
show('EWMA hl120 mult0.9', make_fn(ewma=120))
show('EWMA hl30 mult0.9', make_fn(ewma=30))
# coverage / median error for candidate vs baseline
def diag(label, fn):
    tot=0; n=0; mederr=0; cov=0; mm=0
    for cid,d in E.cases.items():
        for m in d['markets']:
            if m['id'] not in E.real[cid]: continue
            qs=fn(m, d['horizon_minutes']); ys=E.real[cid][m['id']]
            for qrow,y in zip(qs,ys):
                mederr+=abs(y-qrow[2]); mm+=1
                if qrow[0]<=y<=qrow[4]: cov+=1
    print(f"{label}: median|err| x100={100*mederr/mm:.4f}  90% coverage={cov/mm:.4f}")
from eval import baseline
diag('baseline', baseline)
diag('candidate W60 mult0.9', make_fn())
