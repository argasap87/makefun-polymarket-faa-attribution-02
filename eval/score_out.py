import json, glob, sys, os
sys.path.insert(0, '/home/hatch/workspace/makefun/polymarket-faa-02/eval')
from eval import cases, real, TAUS
def score_dir(d):
    per={}; tot=0.0; n=0; mederr=0; mm=0; cov=0
    for cid, case in cases.items():
        f=os.path.join(d, cid+'.out')
        out=json.load(open(f))
        assert set(out.keys())=={'forecasts'}, out.keys()
        fmap={r['id']: r['q'] for r in out['forecasts']}
        assert set(fmap)=={m['id'] for m in case['markets']}, 'market set mismatch'
        t=0.0; nn=0
        for m in case['markets']:
            q=fmap[m['id']]
            assert len(q)==240, len(q)
            for row in q:
                assert len(row)==5 and all(0<=v<=1 for v in row), row
                assert all(row[i]<=row[i+1] for i in range(4)), row
            ys=real[cid][m['id']]
            for qrow,y in zip(q,ys):
                mederr+=abs(y-qrow[2]); mm+=1
                if qrow[0]<=y<=qrow[4]: cov+=1
                for tau,qq in zip(TAUS,qrow):
                    dd=y-qq; t+=100*max(tau*dd,(tau-1)*dd); nn+=1
        per[cid]=t/nn; tot+=t; n+=nn
    per['ALL']=tot/n
    return per, 100*mederr/mm, cov/mm
if __name__=='__main__':
    for d in sys.argv[1:]:
        per, med, cov = score_dir(d)
        print(d, {k: round(v,6) for k,v in per.items()}, f'mederr={med:.4f} cov={cov:.4f}')
