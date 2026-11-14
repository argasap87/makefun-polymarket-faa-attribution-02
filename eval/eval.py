import json, glob, math, statistics, sys
KIT='/home/hatch/workspace/makefun/kits/polymarket-faa-attribution-02-kit'
cases={}
for f in sorted(glob.glob(KIT+'/input/*.in')):
    d=json.load(open(f)); cases[d['case']]=d
# realized y[case][market_id] = list of 240 prices
real={}
for i in range(5):
    cid=f'p0{i}'; nxt=cases[f'p0{i+1}']; cur=cases[cid]
    real[cid]={}
    for m in cur['markets']:
        nm=[x for x in nxt['markets'] if x['id']==m['id']]
        if not nm: continue
        p=nm[0]['prices']; n=len(p)
        real[cid][m['id']]=[p[n-240+h-1] for h in range(1,241)]
real['p05']=json.load(open('/home/hatch/workspace/makefun/polymarket-faa-02/eval/p05-realized.json'))

TAUS=[0.05,0.25,0.5,0.75,0.95]
def pinball(qs, ys):
    tot=0.0; n=0
    for qrow, y in zip(qs, ys):
        for tau,q in zip(TAUS,qrow):
            d=y-q
            tot += 100*max(tau*d, (tau-1)*d); n+=1
    return tot/n

def score(forecast_fn):
    per={}
    all_tot=0.0; all_n=0
    for cid,d in cases.items():
        tot=0.0; n=0
        for m in d['markets']:
            if m['id'] not in real[cid]: continue
            qs=forecast_fn(m, d['horizon_minutes'])
            ys=real[cid][m['id']]
            for qrow,y in zip(qs,ys):
                for tau,q in zip(TAUS,qrow):
                    dd=y-q; tot+=100*max(tau*dd,(tau-1)*dd); n+=1
        per[cid]=tot/n; all_tot+=tot; all_n+=n
    per['ALL']=all_tot/all_n
    return per

Z=[-1.644854,-0.67449,0,0.67449,1.644854]
def price6(x): return round(min(1,max(0,x))*1e6)/1e6+0
def baseline(m,horizon):
    x=m['prices'][-1]
    return [[price6(x+z*0.0025*math.sqrt(h)) for z in Z] for h in range(1,horizon+1)]

if __name__=='__main__':
    print('baseline:', {k: round(v,6) for k,v in score(baseline).items()})
    print('house reported practice loss: 0.363589')
