# -*- coding: utf-8 -*-
"""
每日选股主脚本 (daily_pick)
============================
每个交易日收盘后运行:
  1) 增量更新全市场主板日K缓存 (thsdk, 失败降级缓存)
  2) 市况判定 (复用 mkt_state_daily: 等权指数/MA20/深度分层)
  3) 情绪采集 (复用 mkt_sentiment.main(): 涨停结构/散户人气/舆情)
  4) A2 信号全量扫描 (全缓存主板股, 与回测定义一致)
  5) 按市况/情绪门控输出明日操作建议 (买入清单 vs 观察名单)
  6) 生成可视化 HTML 报告 (ECharts CDN, 单文件自包含)
  7) 落盘 daily_pick_latest.json

A2 信号定义 (与回测一致):
  prev2_pct (涨停后第二日: 即两天前涨停日涨幅) >= 9.5%
  vol_ratio (当日量/5日均量) <= 0.6
  close > ma5
  当日 pct ∈ [-2, 1]

过滤条件:
  仅沪深主板 (60/00 开头, 排除 30/688)
  收盘价 <= 20 元 (1万分散5只、每只2000元可买一手)
"""
import json, os, sys, time, traceback
import pandas as pd
import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
TEMP = BASE + r'\temp'
OUT = BASE + r'\output'
LONG = TEMP + r'\kline_day_long.json'
HTML_OUT = OUT + r'\每日选股_YYYYMMDD.html'
JSON_OUT = TEMP + r'\daily_pick_latest.json'   # 供后续读取的最新选股结果

sys.path.insert(0, TEMP)
import mkt_state_daily as msd
import mkt_sentiment as mkt_sent

MAX_PRICE = 20.0          # 收盘价上限, 保证2000元/只可买1手(20*100=2000)
PER_STOCK_BUDGET = 2000.0

# 回测分层胜率标注 (全样本N=155 胜率75.5% r1+1.19%; 深熊舒适区N=95 胜率94.7% r1+1.88%; 中熊档胜率37.5%)
TIER_STATS = {
    '深熊': {'label': '深熊舒适区', 'n': 95, 'win_rate': 94.7, 'r1': 1.88},
    '中熊': {'label': '中熊档', 'n': None, 'win_rate': 37.5, 'r1': None},
    'default': {'label': '全样本', 'n': 155, 'win_rate': 75.5, 'r1': 1.19},
}


def load_cache():
    with open(LONG, encoding='utf-8') as f:
        return json.load(f)


def incremental_update(data, skip=False):
    """增量更新日K: 拉最近若干交易日并合并入缓存; 失败返回False (降级用缓存)"""
    if skip:
        print('[增量] 跳过 (--no-update 测试模式, 使用现有缓存)')
        return False
    try:
        from datetime import timedelta
        today = pd.Timestamp.now().strftime('%Y-%m-%d')
        start = (pd.Timestamp.now() - timedelta(days=msd.UPDATE_DAYS * 2)).strftime('%Y-%m-%d')
        upd, new_days = msd.fetch_incremental(list(data.keys()), start, today)
        print(f'[增量] 更新{upd}只, 新增日期{new_days}')
        return True
    except Exception as e:
        print(f'[增量] 失败(使用缓存): {str(e)[:120]}')
        return False


def scan_a2(data, as_of):
    """全缓存 A2 信号全量扫描 (与回测/a2_realtime_screen 定义一致)"""
    hits = []
    for code, bars in data.items():
        # 过滤: 仅沪深主板 60/00 开头, 排除 30/688
        if not (code.startswith(('60', '00'))):
            continue
        if code.startswith(('30', '688')):
            continue
        if len(bars) < 8:
            continue
        # 仅使用与全场最新交易日一致的数据 (停牌/缺失直接跳过, 避免过期信号)
        if bars[-1]['date'] != as_of:
            continue
        df = pd.DataFrame(bars)
        for c in ['open', 'high', 'low', 'close', 'volume', 'amount']:
            df[c] = df[c].astype(float)
        df['pct'] = df['close'].pct_change() * 100
        df['prev_pct'] = df['pct'].shift(1)
        df['prev2_pct'] = df['pct'].shift(2)
        df['ma5'] = df['close'].rolling(5).mean()
        df['vol5'] = df['volume'].rolling(5).mean()
        df['vol_ratio'] = df['volume'] / df['vol5']
        s = df.iloc[-1]
        if not (np.isfinite(s['prev2_pct']) and np.isfinite(s['vol_ratio']) and np.isfinite(s['ma5'])):
            continue
        if s['close'] > MAX_PRICE:
            continue
        # A2 条件: prev2_pct(两天前涨停)>=9.5 且 缩量vol_ratio<=0.6 且 close>ma5 且 当日pct∈[-2,1]
        cond = (s['prev2_pct'] >= 9.5) and (s['vol_ratio'] <= 0.6) and (s['close'] > s['ma5']) and (-2 <= s['pct'] <= 1)
        if cond:
            hits.append({
                'code': code, 'date': s['date'],
                'close': round(float(s['close']), 2),
                'pct': round(float(s['pct']), 2),
                'prev2_pct': round(float(s['prev2_pct']), 2),
                'vol_ratio': round(float(s['vol_ratio']), 2),
                'ma5': round(float(s['ma5']), 2),
                'vol5': round(float(s['vol5']), 2),
            })
    return hits


def fetch_names(codes):
    """批量拉股票名称 (腾讯行情)"""
    if not codes:
        return {}
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('asd', TEMP + r'\a_stock_data.py')
        asd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(asd)
        r = asd.tencent_quote(codes)
        return {c: v.get('name', c) for c, v in r.items()}
    except Exception as e:
        print(f'[名称] 拉取失败(用代码代替): {str(e)[:80]}')
        return {}


def gate_verdict(verdict, state, depth):
    """市况/情绪门控: 返回 (watch_only, gate_note)
    watch_only=True 表示"暂空仓/反弹脉冲"等门控, 仅列观察名单不列买入清单"""
    watch_only = False
    note = ''
    keys = str(verdict or '')
    if ('暂空仓' in keys) or ('空仓' in keys) or ('反弹脉冲' in keys) or ('追高' in keys):
        watch_only = True
        note = f'{state}/{depth} 市况门控触发: 当前不宜追买, 仅列观察名单等企稳信号'
    return watch_only, note


def tier_for(depth):
    return TIER_STATS.get(depth, TIER_STATS['default'])


def build_html(mkt_df, mkt_res, sent, cands, watch_only, gate_note, as_of, html_path, coverage=0):
    """生成单文件自包含 HTML (ECharts CDN)"""
    # 指数序列 (最近120个交易日)
    tail = mkt_df.tail(120)
    dates = list(tail['date'])
    idx = [None if pd.isna(x) else round(float(x), 2) for x in tail['idx']]
    ma20 = [None if pd.isna(x) else round(float(x), 2) for x in tail['ma20']]

    sent_score = mkt_res.get('sentiment_score') if mkt_res else None
    sent_label = mkt_res.get('sentiment_label') if mkt_res else None
    lu = (sent or {}).get('limit_up', {}).get('count', 0)
    ld = (sent or {}).get('limit_down', {}).get('count', 0)
    zb = (sent or {}).get('broken', {}).get('count', 0)
    br = (sent or {}).get('broken_rate', 0)
    lb_max = (sent or {}).get('lianban', {}).get('max', 0)
    lb_2plus = (sent or {}).get('lianban', {}).get('count_2plus', 0)

    # 表格行: 候选 + 分层标注
    tier = tier_for(mkt_res.get('depth', ''))
    table_rows = []
    for c in cands:
        nm = c.get('name', c['code'])
        tier_html = f"{tier['win_rate']}%" + (f" (N={tier['n']})" if tier['n'] else '')
        exp = f"r1 {tier['r1']:+.2f}%" if tier['r1'] is not None else '-'
        table_rows.append(
            f"<tr><td>{c['code']}</td><td>{nm}</td><td>{c['prev2_pct']:.2f}%</td>"
            f"<td>{c['vol_ratio']:.2f}</td><td>{c['close']:.2f}</td><td>{c['ma5']:.2f}</td>"
            f"<td>{c['pct']:+.2f}%</td><td>{tier_html}</td><td>{exp}</td></tr>"
        )
    table_body = '\n'.join(table_rows) if table_rows else '<tr><td colspan="9" style="text-align:center;color:#888;">今日无A2信号命中</td></tr>'

    # 门控横幅
    gate_banner = ''
    if watch_only:
        gate_banner = f'''
        <div class="banner danger">
          <div class="banner-title">⚠ 市况门控: 暂空仓 / 反弹脉冲</div>
          <div class="banner-sub">{gate_note}</div>
          <div class="banner-sub">下方仅列观察名单 (N={len(cands)}), 不构成买入清单。等企稳信号后重新评估。</div>
        </div>'''
    else:
        gate_banner = f'''
        <div class="banner ok">
          <div class="banner-title">市况允许: 可正常参与</div>
          <div class="banner-sub">{gate_note or mkt_res.get('verdict', '')}</div>
        </div>'''

    chart_data = {
        'dates': dates, 'idx': idx, 'ma20': ma20,
        'sent_score': sent_score, 'sent_label': sent_label,
        'bars': {'up': lu, 'down': ld, 'broken': zb, 'broken_rate': br, 'lianban_max': lb_max, 'lianban_2plus': lb_2plus},
    }
    chart_json = json.dumps(chart_data, ensure_ascii=False).replace('</', '<\\/')

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>每日选股报告 {as_of}</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>
<script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
<style>
  body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background:#f5f6fa; margin:0; padding:24px; color:#333; }}
  .wrap {{ max-width:1200px; margin:0 auto; }}
  h1 {{ font-size:26px; margin:0 0 6px; }}
  .meta {{ color:#888; font-size:13px; margin-bottom:18px; }}
  .cards {{ display:flex; gap:14px; flex-wrap:wrap; margin-bottom:18px; }}
  .card {{ background:#fff; border-radius:10px; padding:16px 18px; box-shadow:0 2px 8px rgba(0,0,0,.06); flex:1; min-width:200px; }}
  .card .k {{ font-size:13px; color:#888; margin-bottom:6px; }}
  .card .v {{ font-size:24px; font-weight:700; }}
  .banner {{ border-radius:10px; padding:16px 18px; margin-bottom:18px; font-size:15px; }}
  .banner.danger {{ background:#fff1f0; border:1px solid #ffa39e; color:#cf1322; }}
  .banner.ok {{ background:#f6ffed; border:1px solid #b7eb8f; color:#389e0d; }}
  .banner-title {{ font-size:18px; font-weight:700; margin-bottom:6px; }}
  .banner-sub {{ font-size:13px; opacity:.9; margin-top:4px; }}
  .chart-box {{ background:#fff; border-radius:10px; padding:16px; margin-bottom:18px; box-shadow:0 2px 8px rgba(0,0,0,.06); }}
  .chart-box h2 {{ font-size:17px; margin:0 0 10px; }}
  .chart {{ width:100%; height:340px; }}
  .chart.small {{ height:260px; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; border-radius:10px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,.06); font-size:14px; }}
  th, td {{ padding:10px 12px; text-align:right; border-bottom:1px solid #eee; }}
  th {{ background:#2f54eb; color:#fff; text-align:right; }}
  th:first-child, td:first-child {{ text-align:left; }}
  th:nth-child(2), td:nth-child(2) {{ text-align:left; }}
  tr:last-child td {{ border-bottom:none; }}
  tr:hover {{ background:#f0f5ff; }}
  .tier-badge {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:12px; }}
  .tier-high {{ background:#f6ffed; color:#389e0d; }}
  .tier-mid {{ background:#fff7e6; color:#d46b08; }}
  .tier-low {{ background:#fff1f0; color:#cf1322; }}
  .disc {{ color:#999; font-size:12px; margin-top:18px; line-height:1.7; }}
  .section-title {{ font-size:18px; font-weight:700; margin:22px 0 10px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>每日选股报告 {as_of}</h1>
  <div class="meta">生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')} | 覆盖全市场主板 {coverage} 只 | A2信号: 涨停后第二日缩量企稳形态</div>

  <div class="cards">
    <div class="card"><div class="k">市况判定</div><div class="v">{mkt_res.get('state', '-')} / {mkt_res.get('depth', '-')}</div></div>
    <div class="card"><div class="k">等权指数偏离MA20</div><div class="v">{mkt_res.get('dev', 0):+.2f}%</div></div>
    <div class="card"><div class="k">近5日 / 近20日</div><div class="v">{mkt_res.get('ret5', 0):+.2f}% / {mkt_res.get('ret20', 0):+.2f}%</div></div>
    <div class="card"><div class="k">情绪评分</div><div class="v">{sent_score if sent_score is not None else '-'} ({sent_label or '-'})</div></div>
    <div class="card"><div class="k">涨停 / 炸板率</div><div class="v">{lu}家 / {br}%</div></div>
    <div class="card"><div class="k">候选股</div><div class="v">{len(cands)}只</div></div>
  </div>

  {gate_banner}

  <div class="chart-box">
    <h2>全市场等权指数走势 + MA20</h2>
    <div id="chartIndex" class="chart"></div>
  </div>

  <div class="chart-box">
    <h2>情绪评分 (仪表盘)</h2>
    <div id="chartSent" class="chart small"></div>
  </div>

  <div class="chart-box">
    <h2>涨停家数 / 炸板率</h2>
    <div id="chartBars" class="chart small"></div>
  </div>

  <div class="section-title">候选股清单 ({'观察名单' if watch_only else '买入清单'})</div>
  <table>
    <thead><tr><th>代码</th><th>名称</th><th>prev2_pct(涨停日涨幅)</th><th>vol_ratio</th><th>close</th><th>ma5</th><th>当日pct</th><th>形态胜率</th><th>预期收益</th></tr></thead>
    <tbody>
    {table_body}
    </tbody>
  </table>
  <div style="margin-top:8px;font-size:13px;color:#888;">
    形态胜率/预期收益按当前市况深度分层标注: 深熊舒适区 N=95 胜率94.7% r1+1.88% | 中熊档 胜率37.5% | 全样本 N=155 胜率75.5% r1+1.19%
  </div>

  <div class="disc">
    免责声明: 本报告由本地量化脚本自动生成, 仅供研究参考, 不构成投资建议。股市有风险, 入市需谨慎。A2形态为历史回测统计规律, 不代表未来收益保证。
  </div>
</div>

<script>
var DATA = {chart_json};
var dates = DATA.dates;
// 图1: 等权指数 + MA20
var c1 = echarts.init(document.getElementById('chartIndex'));
c1.setOption({{
  tooltip: {{ trigger: 'axis' }},
  legend: {{ data: ['等权指数', 'MA20'] }},
  grid: {{ left: 60, right: 40, top: 40, bottom: 40 }},
  xAxis: {{ type: 'category', data: dates }},
  yAxis: {{ type: 'value', scale: true }},
  series: [
    {{ name: '等权指数', type: 'line', data: DATA.idx, showSymbol: false, lineStyle: {{ width: 2 }} }},
    {{ name: 'MA20', type: 'line', data: DATA.ma20, showSymbol: false, lineStyle: {{ type: 'dashed', width: 1.5 }} }}
  ]
}});
// 图2: 情绪评分仪表盘
var c2 = echarts.init(document.getElementById('chartSent'));
c2.setOption({{
  series: [{{
    type: 'gauge', min: -6, max: 6, splitNumber: 6,
    axisLine: {{ lineStyle: {{ color: [[0.2, '#cf1322'], [0.35, '#faad14'], [0.6, '#91cc75'], [0.8, '#52c41a'], [1, '#389e0d']] }} }},
    detail: {{ formatter: DATA.sent_score + ' (' + (DATA.sent_label || '-') + ')' }},
    data: [{{ value: DATA.sent_score }}]
  }}]
}});
// 图3: 涨停/跌停/炸板 柱状 + 炸板率折线
var c3 = echarts.init(document.getElementById('chartBars'));
c3.setOption({{
  tooltip: {{ trigger: 'axis' }},
  legend: {{ data: ['涨停', '跌停', '炸板', '炸板率'] }},
  grid: {{ left: 60, right: 60, top: 40, bottom: 30 }},
  xAxis: {{ type: 'category', data: ['当日市场'] }},
  yAxis: [{{ type: 'value', name: '家数' }}, {{ type: 'value', name: '炸板率%', max: 100 }}],
  series: [
    {{ name: '涨停', type: 'bar', data: [DATA.bars.up], itemStyle: {{ color: '#cf1322' }} }},
    {{ name: '跌停', type: 'bar', data: [DATA.bars.down], itemStyle: {{ color: '#52c41a' }} }},
    {{ name: '炸板', type: 'bar', data: [DATA.bars.broken], itemStyle: {{ color: '#faad14' }} }},
    {{ name: '炸板率', type: 'line', yAxisIndex: 1, data: [DATA.bars.broken_rate], lineStyle: {{ width: 2 }}, itemStyle: {{ color: '#2f54eb' }} }}
  ]
}});
</script>
</body>
</html>
'''
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return html_path


def main():
    t0 = time.time()
    no_update = '--no-update' in sys.argv[1:]
    print('=' * 60)
    print('每日选股 daily_pick 启动' + (' (快速测试模式)' if no_update else ''))

    # 1. 加载缓存 + 增量更新
    data = load_cache()
    incremental_update(data, skip=no_update)
    data = load_cache()

    # 全场最新交易日
    as_of = max(bars[-1]['date'] for bars in data.values() if bars)
    print(f'[数据] 覆盖 {len(data)} 只, 最新交易日 {as_of}')

    # 2. 市况判定 (复用 mkt_state_daily)
    mkt_df = msd.build_index(data)
    latest = mkt_df.iloc[-1]
    prev = mkt_df.iloc[-2] if len(mkt_df) > 1 else None

    # 3. 情绪采集 (复用 mkt_sentiment.main(), 返回 dict; 失败置空)
    sent = None
    try:
        sent = mkt_sent.main()
    except Exception as e:
        print(f'[情绪] 采集失败: {str(e)[:120]}')
        sent = None

    verdict = msd.a2_window_judge(latest, sent)
    mkt_res = {
        'date': latest['date'], 'mkt': round(float(latest['mkt']), 2),
        'idx': round(float(latest['idx']), 1), 'ma20': round(float(latest['ma20']), 1),
        'dev': round(float(latest['dev']), 2), 'ret5': round(float(latest['ret5']), 2),
        'ret20': round(float(latest['ret20']), 2), 'state': latest['state'],
        'depth': latest['depth'], 'verdict': verdict,
        'sentiment_score': sent['sentiment_score'] if sent else None,
        'sentiment_label': sent['sentiment_label'] if sent else None,
        'divergence': msd.sentiment_divergence(latest, sent) or None,
    }
    print(f'[市况] {latest["state"]}/{latest["depth"]} dev={latest["dev"]:+.2f}% ret5={latest["ret5"]:+.2f}% ret20={latest["ret20"]:+.2f}%')
    print(f'[判定] {verdict}')

    # 4. A2 信号全量扫描
    cands_raw = scan_a2(data, as_of)
    print(f'[扫描] A2信号原始命中 {len(cands_raw)} 只')
    names = fetch_names([c['code'] for c in cands_raw])
    for c in cands_raw:
        c['name'] = names.get(c['code'], c['code'])
    cands_raw.sort(key=lambda x: (x['vol_ratio'], -x['prev2_pct']))

    # 5. 门控
    watch_only, gate_note = gate_verdict(verdict, latest['state'], latest['depth'])
    print(f'[门控] watch_only={watch_only} note={gate_note}')

    # 6. HTML 报告
    os.makedirs(OUT, exist_ok=True)
    html_path = HTML_OUT.replace('YYYYMMDD', as_of.replace('-', ''))
    build_html(mkt_df, mkt_res, sent, cands_raw, watch_only, gate_note, as_of, html_path, coverage=len(data))
    print(f'[HTML] {html_path}')

    # 7. 落盘 JSON (供后续读取/自动更新)
    out = {
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'as_of': as_of,
        'mkt_state': {k: mkt_res[k] for k in ['date', 'mkt', 'idx', 'ma20', 'dev', 'ret5', 'ret20', 'state', 'depth', 'verdict', 'sentiment_score', 'sentiment_label', 'divergence']},
        'sentiment': {
            'score': sent['sentiment_score'] if sent else None,
            'label': sent['sentiment_label'] if sent else None,
            'limit_up': sent['limit_up']['count'] if sent else None,
            'limit_down': sent['limit_down']['count'] if sent else None,
            'broken': sent['broken']['count'] if sent else None,
            'broken_rate': sent['broken_rate'] if sent else None,
            'lianban_max': sent['lianban']['max'] if sent else None,
            'lianban_2plus': sent['lianban']['count_2plus'] if sent else None,
        },
        'verdict': verdict,
        'watch_only': watch_only,
        'gate_note': gate_note,
        'n_candidates': len(cands_raw),
        'candidates': cands_raw,
        'html_path': html_path,
    }
    with open(JSON_OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f'[JSON] {JSON_OUT}')

    # 控制台摘要
    print('=' * 60)
    print(f'市况: {latest["state"]}/{latest["depth"]} | 情绪: {mkt_res["sentiment_score"]} {mkt_res["sentiment_label"]} | 建议: {verdict}')
    print(f'候选: {len(cands_raw)} 只 -> {"观察名单" if watch_only else "买入清单"}')
    for c in cands_raw:
        tier = tier_for(mkt_res['depth'])
        print(f"  {c['code']} {c['name']} close={c['close']:.2f} pct={c['pct']:+.2f}% prev2={c['prev2_pct']:.2f}% volr={c['vol_ratio']:.2f} ma5={c['ma5']:.2f} | 胜率{tier['win_rate']}%")
    print(f'耗时 {time.time() - t0:.1f}s')
    return out


if __name__ == '__main__':
    main()
