# -*- coding: utf-8 -*-
"""
散户情绪量化模块 (mkt_sentiment)
================================
采集四类免费数据源, 输出当日市场情绪快照:
  1) 涨停结构: 涨停/跌停/炸板家数, 炸板率, 连板高度分布, 涨停行业热点
  2) 散户关注热度: 东财人气榜Top20 + 与涨停池交集(人气+涨停=次日风险/机会)
  3) 舆情热度: 财联社电报当日提及个股统计(按名称/代码匹配)
  4) 股吧/论坛热度: 东财股吧人气榜(gbcdn popularityList.js, AES解密),
     含热度分/历史排名变化, 反映散户舆论关注度
"""
import json, re, time
import requests, urllib3
from collections import Counter
urllib3.disable_warnings()

BASE = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
TEMP = BASE + r'\temp'
OUT = BASE + r'\output'
DATE = time.strftime('%Y%m%d')

sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

UT = '7eea3edcaed734bea9cbfc24409ed989'


def fetch_pool(kind):
    """kind: zt(涨停)/dt(跌停)/zb(炸板)"""
    url = {'zt': 'https://push2ex.eastmoney.com/getTopicZTPool',
           'dt': 'https://push2ex.eastmoney.com/getTopicDTPool',
           'zb': 'https://push2ex.eastmoney.com/getTopicZBPool'}[kind]
    params = {'ut': UT, 'dpt': 'wz.ztzt', 'Pageindex': 0, 'pagesize': 500,
              'sort': 'fbt:asc' if kind != 'dt' else 'fund:asc', 'date': DATE}
    try:
        d = sess.get(url, params=params, timeout=10).json()
        data = d.get('data') or {}
        pool = data.get('pool') or []
        return data.get('tc', len(pool)), pool
    except Exception as e:
        return 0, []


def fetch_hot_rank():
    """东财散户人气榜Top20"""
    try:
        r = sess.post('https://emappdata.eastmoney.com/stockrank/getAllCurrentList',
                      json={'appId': 'appId01', 'globalId': '786e4c21-70dc-435a-93bb-38',
                            'pageNo': 1, 'pageSize': 30},
                      timeout=10, headers={'Referer': 'https://data.eastmoney.com/'})
        d = r.json()
        return d.get('data') or []
    except Exception as e:
        return []


def fetch_guba_rank(pages=2):
    """
    东财股吧人气榜 (散户舆论热度代理)
    https://gbcdn.dfcfw.com/rank/popularityList.js
    数据 AES-256-CBC 加密, key=MD5('getUtilsFromFile').hex, iv='getClassFromFile'前16字节
    返回: [{code, rankNumber, ironsFans, newFans, hotScore, rankChg, hourChg, history}, ...]
    """
    import hashlib, base64
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    key = hashlib.md5(b'getUtilsFromFile').hexdigest().encode()
    iv = b'getClassFromFile'[:16]
    out = []
    try:
        for page in range(1, pages + 1):
            url = f'https://gbcdn.dfcfw.com/rank/popularityList.js?type=0&sort=0&page={page}&m=28'
            r = sess.get(url, timeout=10)
            payload = r.text.split("'", 1)[1].rsplit("'", 1)[0]
            raw = base64.b64decode(payload)
            plain = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(raw), AES.block_size).decode('utf-8')
            out.extend(json.loads(plain))
    except Exception as e:
        return []
    res = []
    for it in out[:40]:
        h = it.get('history') or []
        cur = h[-1] if h else {}
        prev = h[-2] if len(h) > 1 else {}
        res.append({
            'code': it.get('code', ''),
            'rank': it.get('rankNumber', 0),
            'irons_fans': float(it.get('ironsFans') or 0),
            'new_fans': float(it.get('newFans') or 0),
            'hot_score': round(cur.get('HOTRANKSCORE') or 0, 0) if cur else None,
            'rank_chg': (prev.get('RANK') - cur.get('RANK')) if cur and prev else None,  # 正=排名上升
            'hour_chg': cur.get('HOURRANKCHANGE') if cur else None,
        })
    return res


def fetch_cls(limit=50):
    """财联社电报(复用 a_stock_data), 接口上限50条"""
    import importlib.util
    spec = importlib.util.spec_from_file_location('asd', TEMP + r'\a_stock_data.py')
    asd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(asd)
    try:
        return asd.cls_telegraph(page_size=limit)
    except Exception:
        return []


def fetch_wallstreet(limit=50):
    """华尔街见闻快讯(补充舆情源)"""
    import importlib.util
    spec = importlib.util.spec_from_file_location('asd', TEMP + r'\a_stock_data.py')
    asd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(asd)
    try:
        rows = asd.wallstreetcn_lives(limit=limit)
        out = []
        for r in rows:
            t = r.get('title') or ''
            c = r.get('content') or ''
            if t and t != 'title':
                out.append({'title': t, 'content': c, 'time': str(r.get('time') or '')})
        return out
    except Exception:
        return []


def quote_names(codes):
    """批量拉名称"""
    import importlib.util
    spec = importlib.util.spec_from_file_location('asd', TEMP + r'\a_stock_data.py')
    asd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(asd)
    try:
        r = asd.tencent_quote(codes)
        return {c: v.get('name', c) for c, v in r.items()}
    except Exception:
        return {}


def main():
    res = {'date': DATE}

    # 1. 涨停结构
    zt_n, zt_pool = fetch_pool('zt')
    dt_n, dt_pool = fetch_pool('dt')
    zb_n, zb_pool = fetch_pool('zb')
    zt_codes = [p['c'] for p in zt_pool]
    zt_names = {p['c']: p['n'] for p in zt_pool}
    res['limit_up'] = {'count': zt_n, 'codes': zt_codes}
    res['limit_down'] = {'count': dt_n}
    res['broken'] = {'count': zb_n}
    # 炸板率 = 炸板/(涨停+炸板)
    res['broken_rate'] = round(zb_n / (zt_n + zb_n) * 100, 1) if (zt_n + zb_n) else None
    # 连板高度分布
    lbc = Counter(p.get('lbc', 0) for p in zt_pool)
    res['lianban'] = {'max': max(lbc) if lbc else 0,
                      'dist': {str(k): v for k, v in sorted(lbc.items())},
                      'count_2plus': sum(v for k, v in lbc.items() if k >= 2)}
    # 涨停行业热点
    ind = Counter(p.get('hybk', '?') for p in zt_pool)
    res['hot_industry'] = ind.most_common(6)

    # 2. 散户人气榜
    hot = fetch_hot_rank()
    hot_codes = [h['sc'][2:] for h in hot]
    nm = quote_names(hot_codes)
    hot_list = []
    for i, h in enumerate(hot[:20], 1):
        code = h['sc'][2:]
        hot_list.append({'rank': i, 'code': code, 'name': nm.get(code, code),
                         'is_limit_up': code in set(zt_codes)})
    res['hot_rank'] = hot_list

    # 3. 舆情热度: 财联社电报 + 华尔街见闻提及个股
    cls_rows = fetch_cls(50)
    ws_rows = fetch_wallstreet(50)
    text_all = ' '.join((r.get('title') or '') + ' ' + (r.get('content') or '') for r in cls_rows + ws_rows)
    mention = Counter()
    for code, name in zt_names.items():
        # 名称匹配(去空格), 短名称可能误匹配, 仅统计名称出现
        n = name.replace(' ', '')
        if n and len(n) >= 2:
            mention[name] += text_all.count(n)
    # 加上人气榜个股
    for h in hot_list:
        if h['name'] not in mention:
            mention[h['name']] = text_all.count(h['name'])
    hot_mention = sorted(mention.items(), key=lambda x: -x[1])[:10]
    res['cls_mention'] = [{'name': n, 'count': c} for n, c in hot_mention if c > 0]
    res['cls_total'] = len(cls_rows) + len(ws_rows)

    # 3.5 股吧/论坛热度 (散户舆论关注度)
    guba = fetch_guba_rank(2)
    zt_set = set(zt_codes)
    guba_list = []
    for i, g in enumerate(guba[:20], 1):
        guba_list.append({
            'rank': i, 'code': g['code'], 'name': nm.get(g['code'], g['code']),
            'hot_score': g['hot_score'], 'rank_chg': g['rank_chg'],
            'hour_chg': g['hour_chg'], 'is_limit_up': g['code'] in zt_set,
        })
    res['guba_rank'] = guba_list
    res['guba_max_score'] = max([g['hot_score'] for g in guba if g['hot_score']], default=0)
    res['guba_limit_up_cnt'] = sum(1 for g in guba_list if g['is_limit_up'])
    res['guba_up_cnt'] = sum(1 for g in guba_list if (g['rank_chg'] or 0) > 0)

    # 4. 情绪综合判定
    zt = res['limit_up']['count']
    dt = res['limit_down']['count']
    br = res['broken_rate']
    lb = res['lianban']
    score = 0
    if zt >= 60: score += 2
    elif zt >= 30: score += 1
    elif zt < 15: score -= 1
    if dt >= 30: score -= 2
    elif dt >= 10: score -= 1
    if br is not None:
        if br <= 15: score += 1
        elif br >= 35: score -= 1
    if lb['max'] >= 5: score += 2
    elif lb['max'] >= 3: score += 1
    # 股吧热度维度: 人气榜涨停股多=追涨情绪浓; 热度分极高=舆论过热
    if res['guba_limit_up_cnt'] >= 5: score += 1
    elif res['guba_limit_up_cnt'] >= 3: score += 1
    if res['guba_max_score'] >= 20000000: score += 1
    res['sentiment_score'] = score
    label_map = {6: '亢奋', 5: '亢奋', 4: '亢奋', 3: '偏热', 2: '偏热', 1: '活跃', 0: '中性',
                 -1: '偏冷', -2: '冷淡', -3: '恐慌', -4: '恐慌', -5: '恐慌', -6: '恐慌'}
    res['sentiment_label'] = label_map.get(score, '中性')

    # 保存
    with open(TEMP + r'\mkt_sentiment_latest.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    # 输出文本
    lines = []
    lines.append(f'## 散户情绪快照 ({DATE})')
    lines.append(f'\n涨停 {zt} 家 | 跌停 {dt} 家 | 炸板 {zb_n} 家 (炸板率 {br}%) | 最高连板 {lb["max"]} 板, 2板以上 {lb["count_2plus"]} 家')
    lines.append(f'情绪评分 {score} → {res["sentiment_label"]}')
    lines.append(f'\n涨停行业热点: {", ".join(f"{n}({c})" for n, c in res["hot_industry"])}')
    lines.append('\n散户人气榜Top10 (★=今日涨停):')
    for h in hot_list[:10]:
        lines.append(f'  {h["rank"]}. {h["name"]}({h["code"]}) {"★涨停" if h["is_limit_up"] else ""}')
    lines.append('\n财联社电报提及个股Top5:')
    for m in res['cls_mention'][:5]:
        lines.append(f'  {m["name"]} x{m["count"]}')
    lines.append('\n股吧人气榜Top10 (★=今日涨停, ↑=排名较昨日上升):')
    for g in res['guba_rank'][:10]:
        up = '↑' if (g['rank_chg'] or 0) > 0 else ('↓' if (g['rank_chg'] or 0) < 0 else '-')
        zt_mark = '★' if g['is_limit_up'] else ''
        hs = f"{g['hot_score']/1e4:.0f}万" if g['hot_score'] else '?'
        lines.append(f'  {g["rank"]}. {g["name"]}({g["code"]}) {zt_mark}{up} 热度{hs}')
    lines.append(f'  人气榜涨停 {res["guba_limit_up_cnt"]} 家 | 热度最高 {res["guba_max_score"]/1e4:.0f}万')
    text = '\n'.join(lines)
    print(text)
    return res


if __name__ == '__main__':
    main()
