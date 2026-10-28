"""Offline reproduction and executable-timing audit. Never places orders."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

BAN = ['2022-05', '2024-02']

def features(code, bars):
    d = pd.DataFrame(bars).sort_values('date').drop_duplicates('date').copy()
    for c in ['open','high','low','close','volume']:
        d[c] = pd.to_numeric(d[c], errors='coerce')
    d['code'] = code
    d['pct'] = d.close.pct_change(fill_method=None)*100
    d['ret20'] = d.close.pct_change(20, fill_method=None)*100
    d['ma5'] = d.close.rolling(5).mean()
    d['vol_ratio'] = d.volume/d.volume.rolling(5).mean()
    d['prev2_pct'] = d.pct.shift(2)
    d['next_date'] = d.date.shift(-1)
    d['next_open'] = d.open.shift(-1)
    d['next_low'] = d.low.shift(-1)
    d['next_high'] = d.high.shift(-1)
    d['exit_date'] = d.date.shift(-2)
    d['exit_close'] = d.close.shift(-2)
    d['r1'] = (d.close.shift(-1)/d.close-1)*100-.3
    # T+1 open buy -> T+2 close sell: earliest daily-bar exit consistent with T+1.
    d['executable_net'] = (d.exit_close/d.next_open-1)*100-.3
    return d

def summarize(d, col='r1'):
    d = d.dropna(subset=[col]).copy()
    def stat(x):
        return {'N':len(x), 'win_pct':round(float((x[col]>0).mean()*100),3) if len(x) else None,
                'net_pct':round(float(x[col].mean()),4) if len(x) else None}
    monthly = d.groupby(d.date.str[:7]).apply(lambda x: pd.Series(stat(x))).to_dict('index') if len(d) else {}
    counts = d.groupby('date').size()
    return {**stat(d),'unique_signal_days':int(len(counts)),
            'largest_day_count':int(counts.max()) if len(counts) else 0,
            'exclude_extreme_months':stat(d[~d.date.str[:7].isin(BAN)]),
            'years':{str(y):stat(x) for y,x in d.groupby(d.date.str[:4])},
            'months':monthly}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,default=Path(__file__).parent)
    args=ap.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(args.source))
    import mkt_state_daily as msd
    data=json.loads((args.source/'kline_day_long_v2.json').read_text(encoding='utf-8'))
    market=msd.build_index(data)[['date','state','depth']]
    frames=[]
    for code,bars in data.items():
        if code.startswith(('60','00')) and len(bars)>=40:
            frames.append(features(code,bars))
    d=pd.concat(frames,ignore_index=True).merge(market,on='date',how='left')
    del frames,data
    lu=(d.pct>=9.5).groupby(d.date).sum()
    q=float(lu.quantile(.75))
    d['n_limit']=d.date.map(lu)
    d['a2']=(d.prev2_pct>=9.5)&(d.vol_ratio<=.6)&(d.close>d.ma5)&d.pct.between(-2,1)
    base=(d.depth=='浅熊')&(d.ret20<=-15)&(d.vol_ratio<=.6)&d.pct.between(-2,2)
    common=(d.vol_ratio<=.6).astype(int)+(d.ret20<=-15).astype(int)+(d.close>d.ma5).astype(int)+(d.pct>0).astype(int)+d.a2.astype(int)
    def mask(threshold):
        hot=d.n_limit>=threshold
        return base&hot&((common+hot.astype(int))>=5)&d.r1.notna()
    original=d[mask(q)].copy()
    fixed=d[mask(51)].copy()
    capped=fixed[fixed.close.between(.01,20)].copy()
    # Deterministic order; daily maximum five, with costs reserved in each 2000 budget.
    allocated=capped.sort_values(['date','vol_ratio','ret20','code']).groupby('date').head(5).copy()
    executable=allocated[(allocated.next_open>0)&(allocated.next_open*100*1.0015<=2000)&
                         ~((allocated.next_high==allocated.next_low)&(allocated.next_open>allocated.close*1.08))].copy()
    calendar=sorted(d.date.unique()); nextday=dict(zip(calendar,calendar[1:])); day2=dict(zip(calendar,calendar[2:]))
    executable=executable[(executable.next_date==executable.date.map(nextday))&
                          (executable.exit_date==executable.date.map(day2))].copy()
    result={'source':str(args.source),'dates':[str(min(calendar)),str(max(calendar))],
            'legacy_hot_threshold_full_sample':q,
            'legacy_reproduced':summarize(original),
            'fixed_51':summarize(fixed), 'fixed_51_price20':summarize(capped),
            'price20_max5':summarize(allocated),
            'next_open_to_day2_close_diagnostic':summarize(executable,'executable_net'),
            'limitations':['Legacy threshold uses future full-sample distribution.',
             'All variants are in-sample research, not independent out-of-sample tests.',
             'Universe completeness, historical ST status, adjustment and source consistency unverified.',
             'Executable timing diagnostic is not a portfolio backtest; overlapping holdings, sell-limit locks and slippage remain unmodeled.',
             'Historical complete sentiment snapshots unavailable; live score cannot replace historical proxy without revalidation.']}
    expected=json.loads((args.source/'final_recommendation_v2.json').read_text(encoding='utf-8'))['R1 浅熊B4+score>=5']
    result['legacy_matches_saved_N']=len(original)==expected['N']
    (args.output/'b4_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    fixed.to_csv(args.output/'b4_signal_ledger.csv',index=False,encoding='utf-8-sig')
    for k,v in result.items():
        if isinstance(v,dict) and 'N' in v:
            print(k, {a:b for a,b in v.items() if a not in ['months','years']},flush=True)
    print('legacy_threshold',q,'matches',result['legacy_matches_saved_N'],flush=True)

if __name__=='__main__': main()
