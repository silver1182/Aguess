# -*- coding: utf-8 -*-
"""
市况匹配自动化 (mkt_state_daily)
=================================
每日收盘后运行: 增量更新全市场日K → 构建等权指数 → 判定牛/熊/震荡与深度 → 输出市况报告
作为 A2 等短线信号的市况地基。

数据维度(当前):
  - 全市场等权指数: 1649只主板股日涨跌幅等权平均 → 累计净值
  - MA20 / MA60: 中期趋势; MA20斜率: 趋势方向
  - ret5 / ret20: 近5/20日等权指数涨跌 → 下跌窗口深度
  - 状态定义: 指数>MA20且MA20上行=牛; 指数<MA20且MA20下行=熊; 其余=震荡
  - 深度分层: dev = 指数/MA20-1; 深熊 dev<-6%, 中熊 -6~-3%, 浅熊 -3~0

输出:
  - 控制台/报告文件: 当前市况 + A2窗口建议
"""
import json, os, sys, time, warnings
import pandas as pd
import numpy as np
warnings.filterwarnings('ignore')

BASE = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
TEMP = BASE + r'\temp'
OUT = BASE + r'\output'
LONG = TEMP + r'\kline_day_long.json'
REPORT = OUT + r'\市况报告_latest.md'

COST = 0.0015
LIMIT = 9.5
UPDATE_DAYS = 8  # 每次运行增量拉最近8个交易日(覆盖缺口), 去重合并


def load_cache():
    with open(LONG, encoding='utf-8') as f:
        return json.load(f)


def fetch_incremental(codes, start_date, end_date):
    """thsdk 增量拉日K并合并入缓存"""
    from thsdk import api
    api.auth()
    def ths_code(code):
        return ('USHA' if code.startswith('6') else 'USZA') + code
    data = load_cache()
    updated = 0
    new_days = set()
    for i, code in enumerate(codes):
        try:
            df = api.get_price(ths_code(code), start_date=start_date, end_date=end_date)
            if df is not None and len(df):
                bars = [{'date': str(idx)[:10], 'open': float(r['open']), 'high': float(r['high']),
                         'low': float(r['low']), 'close': float(r['close']),
                         'volume': float(r['volume']), 'amount': float(r['turnover'])}
                        for idx, r in df.iterrows()]
                old = data.get(code) or []
                old_by_date = {b['date']: b for b in old}
                added = 0
                for b in bars:
                    if b['date'] not in old_by_date:
                        old_by_date[b['date']] = b
                        added += 1
                        new_days.add(b['date'])
                if added:
                    data[code] = sorted(old_by_date.values(), key=lambda x: x['date'])
                    updated += 1
        except Exception:
            pass
        time.sleep(0.02)
    with open(LONG, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    return updated, sorted(new_days)


def build_index(data):
    """构建全市场等权指数"""
    day_mkt = {}
    for code, bars in data.items():
        df = pd.DataFrame(bars)
        if len(df) < 3:
            continue
        df['pct'] = df['close'].astype(float).pct_change() * 100
        for d, p in zip(df['date'], df['pct']):
            day_mkt.setdefault(d, []).append(p)
    mkt = {d: float(np.nanmean(v)) for d, v in day_mkt.items()}
    mkt_df = pd.DataFrame({'date': list(mkt.keys()), 'mkt': list(mkt.values())}).sort_values('date').reset_index(drop=True)
    mkt_df['idx'] = (1 + mkt_df['mkt'] / 100).cumprod() * 100
    mkt_df['ma20'] = mkt_df['idx'].rolling(20).mean()
    mkt_df['ma60'] = mkt_df['idx'].rolling(60).mean()
    mkt_df['mkt_ma5'] = mkt_df['mkt'].rolling(5).mean()
    mkt_df['trend'] = mkt_df['ma20'].diff()
    mkt_df['ret5'] = mkt_df['idx'].pct_change(5) * 100
    mkt_df['ret20'] = mkt_df['idx'].pct_change(20) * 100
    mkt_df['dev'] = (mkt_df['idx'] / mkt_df['ma20'] - 1) * 100

    def state_of(row):
        if np.isnan(row['ma20']) or np.isnan(row['trend']):
            return '初始'
        if row['idx'] > row['ma20'] and row['trend'] > 0:
            return '牛'
        if row['idx'] < row['ma20'] and row['trend'] < 0:
            return '熊'
        return '震荡'
    mkt_df['state'] = mkt_df.apply(state_of, axis=1)

    def depth_of(row):
        if row['state'] != '熊':
            return row['state']
        if row['dev'] < -6:
            return '深熊'
        if row['dev'] < -3:
            return '中熊'
        return '浅熊'
    mkt_df['depth'] = mkt_df.apply(depth_of, axis=1)
    return mkt_df


def _sent_state(sentiment):
    """情绪强度归类: 返回 (hot, cold) 是否过热/恐慌"""
    if not sentiment:
        return False, False
    s_score = sentiment.get('sentiment_score', 0)
    s_label = sentiment.get('sentiment_label', '')
    hot = s_score >= 6 or s_label in ('亢奋', '偏热')
    cold = s_score <= -2 or s_label in ('恐慌', '冷淡')
    return hot, cold


def a2_window_judge(row, sentiment=None):
    """基于市况判定 A2 介入窗口 (对齐回测分层结论), 散户情绪作为修正维度"""
    if row is None:
        return '数据不足'
    st, dev, r5, r20 = row['state'], row['dev'], row['ret5'], row['ret20']
    hot, cold = _sent_state(sentiment)
    if st == '熊' and dev < -6 and r20 < -8:
        # A2舒适区: 回测N=95 r1+1.88% 胜率94.7%; 情绪恐慌/冷淡=出清更充分
        if cold:
            return '深熊+急跌+情绪恐慌/冷淡: 恐慌出清更充分, A2舒适区可精选介入'
        if hot:
            return '深熊+急跌+情绪亢奋: 短线脉冲特征, 追高危险, 仅做最强龙头轻仓'
        return '深熊+20日急跌: A2高胜率舒适区(回测N=95 r1+1.88%), 可精选介入'
    if st == '熊' and r5 < -3:
        if hot:
            return '中熊+急跌+情绪亢奋: 反弹脉冲特征, 追高易套, 暂空仓等企稳'
        return '熊市短期急跌: 中熊档胜率仅37%, 需等5日企稳, 暂空仓'
    if st == '熊':
        return '熊市缓跌: A2胜率偏低, 空仓观望'
    if st == '震荡' and r5 < 0:
        return '震荡偏弱: 谨慎, 只做最强信号'
    if st == '牛':
        if hot:
            return '牛市+情绪亢奋: 可参与但情绪过热, 分批/轻仓防回撤'
        return '牛市: 可正常参与'
    return '震荡: 中性, 按信号过滤'


def sentiment_divergence(row, sentiment):
    """情绪与市况背离检测: 返回提示文本或空串"""
    if not sentiment:
        return ''
    st = row['state']
    hot, cold = _sent_state(sentiment)
    if st == '熊' and hot:
        return '背离: 市况熊 + 情绪亢奋 → 短线脉冲反弹特征, 追高易套, 纪律等企稳'
    if st == '牛' and cold:
        return '背离: 市况牛 + 情绪冷淡 → 人气未跟上, 反弹持续性存疑, 轻仓试错'
    if st == '震荡' and hot:
        return '背离: 震荡 + 情绪亢奋 → 情绪先于指数, 防冲高回落'
    return ''


def main():
    data = load_cache()
    codes = list(data.keys())

    # 1. 增量更新: 拉最近N个交易日
    try:
        today = pd.Timestamp.now().strftime('%Y-%m-%d')
        from datetime import timedelta
        start = (pd.Timestamp.now() - timedelta(days=UPDATE_DAYS * 2)).strftime('%Y-%m-%d')
        upd, new_days = fetch_incremental(codes, start, today)
        if upd:
            print(f'[增量] 更新{upd}只, 新增日期{new_days}')
        data = load_cache()
    except Exception as e:
        print(f'[增量] 失败(使用缓存): {str(e)[:80]}')

    # 2. 构建指数
    mkt_df = build_index(data)
    latest = mkt_df.iloc[-1]
    prev = mkt_df.iloc[-2] if len(mkt_df) > 1 else None

    # 3. 报告
    lines = []
    lines.append('# 市况报告')
    lines.append(f'\n- 生成时间: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'- 数据截至: {latest["date"]} | 覆盖股票: {len(data)} 只')
    lines.append(f'- 最新交易日等权涨跌: {latest["mkt"]:+.2f}%')
    lines.append('')
    lines.append('## 当前市况')
    lines.append(f'\n| 指标 | 数值 |')
    lines.append(f'| --- | --- |')
    lines.append(f'| 等权指数 | {latest["idx"]:.0f} |')
    lines.append(f'| MA20 | {latest["ma20"]:.0f} (指数偏离 {latest["dev"]:+.2f}%) |')
    lines.append(f'| MA60 | {latest["ma60"]:.0f} |')
    lines.append(f'| 近5日涨跌 | {latest["ret5"]:+.2f}% |')
    lines.append(f'| 近20日涨跌 | {latest["ret20"]:+.2f}% |')
    lines.append(f'| 市场状态 | {latest["state"]} |')
    lines.append(f'| 深度分层 | {latest["depth"]} |')
    lines.append('')
    # 3.4 先采集散户情绪 (供 A2 判定修正)
    sent = None
    try:
        import sys as _sys
        sys_path_backup = list(_sys.path)
        _sys.path.insert(0, TEMP)
        from mkt_sentiment import main as sent_main
        sent = sent_main()
        _sys.path[:] = sys_path_backup
    except Exception as e:
        sent = None
        lines.append(f'## 散户情绪 (舆情维度)\n\n- 情绪模块异常: {str(e)[:80]}')
    lines.append(f'## A2 窗口判定')
    lines.append(f'\n{latest["state"]} / dev={latest["dev"]:+.1f}% / ret5={latest["ret5"]:+.1f}% / ret20={latest["ret20"]:+.1f}%')
    if sent:
        lines.append(f'\n情绪并入: 评分 {sent["sentiment_score"]} → {sent["sentiment_label"]} ({sent["limit_up"]["count"]}家涨停 / 炸板率 {sent["broken_rate"]}% / 最高 {sent["lianban"]["max"]}板)')
    lines.append(f'\n**结论: {a2_window_judge(latest, sent)}**')
    div = sentiment_divergence(latest, sent)
    if div:
        lines.append(f'\n[背离提示] {div}')
    lines.append('')
    # 3.5 散户情绪板块 (舆情维度扩展)
    if sent:
        lines.append('## 散户情绪 (舆情维度)')
        lines.append('')
        lines.append(f'\n- 情绪评分 {sent["sentiment_score"]} → **{sent["sentiment_label"]}**')
        lines.append(f'- 涨停 {sent["limit_up"]["count"]} 家 | 跌停 {sent["limit_down"]["count"]} 家 | 炸板 {sent["broken"]["count"]} 家 (炸板率 {sent["broken_rate"]}%) | 最高 {sent["lianban"]["max"]} 板, 2板以上 {sent["lianban"]["count_2plus"]} 家')
        lines.append(f'- 涨停行业热点: {", ".join(f"{n}({c})" for n, c in sent["hot_industry"][:5])}')
        lines.append('')
        lines.append('散户人气榜Top10 (★=今日涨停):')
        lines.append('\n| 排名 | 个股 | 代码 | 状态 |')
        lines.append('| --- | --- | --- | --- |')
        for h in sent['hot_rank'][:10]:
            lines.append(f'| {h["rank"]} | {h["name"]} | {h["code"]} | {"★涨停" if h["is_limit_up"] else "-"} |')
        lines.append('')
        lines.append('舆情提及个股Top5 (财联社+华尔街见闻):')
        if sent['cls_mention']:
            lines.append('')
            lines.append('| 个股 | 提及次数 |')
            lines.append('| --- | --- |')
            for m in sent['cls_mention'][:5]:
                lines.append(f'| {m["name"]} | {m["count"]} |')
        else:
            lines.append('\n今日快讯未匹配到个股名称。')
        lines.append('')
    lines.append('')
    lines.append('## 近10日市况走势')
    lines.append('\n| 日期 | 等权涨跌 | 指数 | MA20 | 状态 | ret5 | ret20 |')
    lines.append('| --- | --- | --- | --- | --- | --- | --- |')
    for _, r in mkt_df.tail(10).iterrows():
        lines.append(f'| {r["date"]} | {r["mkt"]:+.2f}% | {r["idx"]:.0f} | {r["ma20"]:.0f} | {r["depth"]} | {r["ret5"]:+.1f}% | {r["ret20"]:+.1f}% |')
    lines.append('')
    lines.append('## 数据维度说明')
    lines.append('')
    lines.append('- **全市场等权指数**: 1649只主板股日涨跌幅等权平均 → 累计净值, 反映普涨普跌而非权重股失真')
    lines.append('- **MA20/MA60**: 中期趋势锚; 指数>MA20且MA20上行=牛, 反之=熊, 其余震荡')
    lines.append('- **ret5/ret20**: 下跌/上涨窗口深度, 与A2胜率分层相关(深熊+20日跌>8%为舒适区)')
    lines.append('- **散户情绪(舆情维度)**: 涨停/跌停/炸板结构 + 东财人气榜(散户关注) + 财联社/华尔街见闻快讯个股提及')
    lines.append('- **局限**: 舆情仅覆盖快讯文本提及; 股吧/论坛贴热度暂未接入(需爬虫)')

    report = '\n'.join(lines)
    print(report[:1500])
    os.makedirs(OUT, exist_ok=True)
    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f'\n[报告] {REPORT}')

    # 4. 返回结论JSON
    return {
        'date': latest['date'], 'mkt': round(latest['mkt'], 2),
        'idx': round(latest['idx'], 1), 'ma20': round(latest['ma20'], 1),
        'dev': round(latest['dev'], 2), 'ret5': round(latest['ret5'], 2),
        'ret20': round(latest['ret20'], 2), 'state': latest['state'],
        'depth': latest['depth'], 'verdict': a2_window_judge(latest, sent),
        'sentiment_score': sent['sentiment_score'] if sent else None,
        'sentiment_label': sent['sentiment_label'] if sent else None,
        'divergence': sentiment_divergence(latest, sent) or None,
    }


if __name__ == '__main__':
    res = main()
    with open(TEMP + r'\mkt_state_latest.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print('\n[JSON]', json.dumps(res, ensure_ascii=False))
