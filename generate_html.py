"""
OWtics 스크래핑 결과 → HTML 대시보드 생성기
- ow_hero_stats_v6.xlsx + ow_hero_map_stats.csv → index.html
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime


def load_data():
    stats_df, map_df = pd.DataFrame(), pd.DataFrame()

    if Path("ow_hero_stats_v6.xlsx").exists():
        stats_df = pd.read_excel("ow_hero_stats_v6.xlsx")
        print(f"  stats: {len(stats_df)}행 로드")
    else:
        print("  [WARN] ow_hero_stats_v6.xlsx 없음")

    if Path("ow_hero_map_stats.csv").exists():
        map_df = pd.read_csv("ow_hero_map_stats.csv")
        print(f"  map: {len(map_df)}행 로드")
    else:
        print("  [WARN] ow_hero_map_stats.csv 없음")

    return stats_df, map_df


def df_to_json(df):
    if df.empty:
        return "[]"
    return df.to_json(orient="records", force_ascii=False)


def generate_html(stats_df, map_df):
    updated = datetime.now().strftime("%Y-%m-%d %H:%M")

    stats_json = df_to_json(stats_df)
    map_json = df_to_json(map_df)

    # Region/tier 옵션
    regions = sorted(stats_df["region"].unique().tolist()) if not stats_df.empty else []
    tiers = ["ALL","BRONZE","SILVER","GOLD","PLATINUM","DIAMOND","MASTER","GRANDMASTER"]

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OW 영웅 통계 대시보드</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0a0c10;
    --surface: #12151c;
    --surface2: #1a1f2e;
    --border: #2a2f42;
    --accent: #f97316;
    --accent2: #3b82f6;
    --text: #e2e8f0;
    --mute: #64748b;
    --win: #22c55e;
    --loss: #ef4444;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 14px;
    min-height: 100vh;
  }}

  /* Header */
  header {{
    background: linear-gradient(135deg, #0f1623 0%, #1a0a05 100%);
    border-bottom: 1px solid var(--border);
    padding: 24px 40px;
    display: flex;
    align-items: center;
    gap: 16px;
  }}
  .logo {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 36px;
    color: var(--accent);
    letter-spacing: 2px;
    line-height: 1;
  }}
  .logo span {{ color: var(--text); }}
  .updated {{
    margin-left: auto;
    color: var(--mute);
    font-size: 12px;
  }}

  /* Tabs */
  .tabs {{
    display: flex;
    gap: 2px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 40px;
  }}
  .tab-btn {{
    background: none;
    border: none;
    color: var(--mute);
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 14px;
    font-weight: 500;
    padding: 14px 20px;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all .2s;
  }}
  .tab-btn.active, .tab-btn:hover {{
    color: var(--accent);
    border-bottom-color: var(--accent);
  }}

  /* Main */
  main {{ padding: 32px 40px; }}
  .panel {{ display: none; }}
  .panel.active {{ display: block; }}

  /* Filters */
  .filters {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 24px;
    align-items: center;
  }}
  .filters label {{
    color: var(--mute);
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}
  select, input[type=text] {{
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 6px;
    padding: 7px 12px;
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 13px;
    outline: none;
    transition: border-color .2s;
  }}
  select:focus, input:focus {{ border-color: var(--accent); }}

  /* Table */
  .table-wrap {{
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  thead tr {{
    background: var(--surface2);
  }}
  th {{
    padding: 12px 16px;
    text-align: left;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--mute);
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
  }}
  th:hover {{ color: var(--accent); }}
  th.sort-asc::after {{ content: " ↑"; color: var(--accent); }}
  th.sort-desc::after {{ content: " ↓"; color: var(--accent); }}
  tbody tr {{
    border-top: 1px solid var(--border);
    transition: background .15s;
  }}
  tbody tr:hover {{ background: var(--surface2); }}
  td {{
    padding: 11px 16px;
    vertical-align: middle;
  }}
  .hero-name {{
    font-weight: 700;
    color: var(--text);
  }}
  .role-tag {{
    display: inline-block;
    font-size: 11px;
    color: var(--mute);
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 2px 6px;
    margin-left: 6px;
  }}
  .win-bar {{
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .bar-bg {{
    flex: 1;
    height: 6px;
    background: var(--border);
    border-radius: 3px;
    overflow: hidden;
  }}
  .bar-fill {{
    height: 100%;
    border-radius: 3px;
    transition: width .3s;
  }}
  .badge {{
    font-size: 12px;
    font-weight: 700;
    min-width: 44px;
    text-align: right;
  }}
  .badge.high {{ color: var(--win); }}
  .badge.mid {{ color: var(--accent); }}
  .badge.low {{ color: var(--loss); }}

  /* Summary cards */
  .cards {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
  }}
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
  }}
  .card-label {{ color: var(--mute); font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
  .card-value {{ font-family: 'Bebas Neue', sans-serif; font-size: 32px; color: var(--accent); }}
  .card-sub {{ color: var(--mute); font-size: 12px; margin-top: 4px; }}

  /* Pagination */
  .pagination {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 16px;
    justify-content: flex-end;
  }}
  .page-btn {{
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 6px;
    padding: 6px 12px;
    cursor: pointer;
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 13px;
  }}
  .page-btn:hover, .page-btn.active {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
  .page-btn:disabled {{ opacity: 0.3; cursor: default; }}
  .page-info {{ color: var(--mute); font-size: 13px; }}
</style>
</head>
<body>

<header>
  <div class="logo">OW<span>stats</span></div>
  <div style="color:var(--mute);font-size:13px;">Overwatch 영웅 통계 대시보드</div>
  <div class="updated">🕐 마지막 업데이트: {updated}</div>
</header>

<div class="tabs">
  <button class="tab-btn active" onclick="switchTab('stats', this)">영웅 통계</button>
  <button class="tab-btn" onclick="switchTab('maps', this)">맵별 통계</button>
</div>

<main>

<!-- === 영웅 통계 탭 === -->
<div id="panel-stats" class="panel active">
  <div class="cards" id="summary-cards"></div>
  <div class="filters">
    <label>지역</label>
    <select id="f-region" onchange="renderStats()">
      <option value="">전체</option>
      {"".join(f'<option value="{r}">{r}</option>' for r in regions)}
    </select>
    <label>티어</label>
    <select id="f-tier" onchange="renderStats()">
      <option value="">전체</option>
      {"".join(f'<option value="{t}">{t}</option>' for t in tiers)}
    </select>
    <label>역할</label>
    <select id="f-role" onchange="renderStats()">
      <option value="">전체</option>
    </select>
    <label>정렬</label>
    <select id="f-sort" onchange="renderStats()">
      <option value="win_rate_desc">승률 높은 순</option>
      <option value="win_rate_asc">승률 낮은 순</option>
      <option value="pick_rate_desc">픽률 높은 순</option>
      <option value="pick_rate_asc">픽률 낮은 순</option>
    </select>
    <input type="text" id="f-search" placeholder="영웅 검색..." oninput="renderStats()" style="margin-left:auto;">
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>영웅</th>
          <th>지역</th>
          <th>티어</th>
          <th>픽률</th>
          <th>승률</th>
        </tr>
      </thead>
      <tbody id="stats-body"></tbody>
    </table>
  </div>
  <div class="pagination" id="stats-pagination"></div>
</div>

<!-- === 맵 통계 탭 === -->
<div id="panel-maps" class="panel">
  <div class="filters">
    <label>지역</label>
    <select id="mf-region" onchange="renderMaps()">
      <option value="">전체</option>
      {"".join(f'<option value="{r}">{r}</option>' for r in regions)}
    </select>
    <label>맵 타입</label>
    <select id="mf-type" onchange="renderMaps()">
      <option value="">전체</option>
    </select>
    <label>영웅</label>
    <select id="mf-hero" onchange="renderMaps()">
      <option value="">전체</option>
    </select>
    <input type="text" id="mf-search" placeholder="맵 이름 검색..." oninput="renderMaps()" style="margin-left:auto;">
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>맵</th>
          <th>타입</th>
          <th>영웅</th>
          <th>지역</th>
          <th>픽률</th>
          <th>승률</th>
        </tr>
      </thead>
      <tbody id="maps-body"></tbody>
    </table>
  </div>
  <div class="pagination" id="maps-pagination"></div>
</div>

</main>

<script>
const STATS = {stats_json};
const MAPS = {map_json};

const PAGE_SIZE = 50;
let statsPage = 1, mapsPage = 1;

// --- Tab ---
function switchTab(name, btn) {{
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
  btn.classList.add('active');
}}

// --- Util ---
function winClass(v) {{
  if (v == null) return '';
  if (v >= 52) return 'high';
  if (v >= 48) return 'mid';
  return 'low';
}}
function barColor(v) {{
  if (v == null) return '#64748b';
  if (v >= 52) return '#22c55e';
  if (v >= 48) return '#f97316';
  return '#ef4444';
}}
function pct(v) {{ return v != null ? v.toFixed(1) + '%' : '--'; }}

// --- Summary Cards ---
function renderSummary(data) {{
  if (!data.length) return;
  const wins = data.map(d => d.win_rate).filter(v => v != null);
  const picks = data.map(d => d.pick_rate).filter(v => v != null);
  const avgWin = wins.reduce((a,b) => a+b, 0) / (wins.length || 1);
  const topWin = [...data].sort((a,b) => (b.win_rate||0)-(a.win_rate||0))[0];
  const topPick = [...data].sort((a,b) => (b.pick_rate||0)-(a.pick_rate||0))[0];
  const heroes = [...new Set(data.map(d => d.hero))];
  document.getElementById('summary-cards').innerHTML = `
    <div class="card"><div class="card-label">데이터 행 수</div><div class="card-value">${{data.length.toLocaleString()}}</div><div class="card-sub">현재 필터 기준</div></div>
    <div class="card"><div class="card-label">평균 승률</div><div class="card-value">${{avgWin.toFixed(1)}}%</div><div class="card-sub">전체 평균</div></div>
    <div class="card"><div class="card-label">최고 승률</div><div class="card-value">${{topWin?.win_rate?.toFixed(1)}}%</div><div class="card-sub">${{topWin?.hero || ''}}</div></div>
    <div class="card"><div class="card-label">최고 픽률</div><div class="card-value">${{topPick?.pick_rate?.toFixed(1)}}%</div><div class="card-sub">${{topPick?.hero || ''}}</div></div>
    <div class="card"><div class="card-label">영웅 수</div><div class="card-value">${{heroes.length}}</div><div class="card-sub">고유 영웅</div></div>
  `;
}}

// --- Stats ---
function getFilteredStats() {{
  const region = document.getElementById('f-region').value;
  const tier = document.getElementById('f-tier').value;
  const role = document.getElementById('f-role').value;
  const search = document.getElementById('f-search').value.toLowerCase();
  const sort = document.getElementById('f-sort').value;

  let data = STATS.filter(d => {{
    if (region && d.region !== region) return false;
    if (tier && d.tier !== tier) return false;
    if (role && !(d.role || '').includes(role)) return false;
    if (search && !(d.hero || '').toLowerCase().includes(search)) return false;
    return true;
  }});

  const [field, dir] = sort.split('_').slice(0, 2).join('_') === 'win_rate'
    ? ['win_rate', sort.endsWith('asc') ? 1 : -1]
    : ['pick_rate', sort.endsWith('asc') ? 1 : -1];
  data.sort((a,b) => ((a[field]||0) - (b[field]||0)) * dir);

  return data;
}}

function renderStats() {{
  const data = getFilteredStats();
  renderSummary(data);

  // Populate role filter
  const roles = [...new Set(STATS.map(d => d.role).filter(Boolean))];
  const rsel = document.getElementById('f-role');
  if (rsel.options.length <= 1) {{
    roles.forEach(r => {{ const o = new Option(r, r); rsel.add(o); }});
  }}

  const start = (statsPage - 1) * PAGE_SIZE;
  const page = data.slice(start, start + PAGE_SIZE);

  document.getElementById('stats-body').innerHTML = page.map((d, i) => `
    <tr>
      <td style="color:var(--mute)">${{start + i + 1}}</td>
      <td><span class="hero-name">${{d.hero || ''}}</span><span class="role-tag">${{d.role || ''}}</span></td>
      <td><span class="role-tag">${{d.region || ''}}</span></td>
      <td><span class="role-tag">${{d.tier || ''}}</span></td>
      <td>
        <div class="win-bar">
          <div class="bar-bg"><div class="bar-fill" style="width:${{Math.min(d.pick_rate||0, 30)/30*100}}%;background:var(--accent2)"></div></div>
          <span class="badge mid">${{pct(d.pick_rate)}}</span>
        </div>
      </td>
      <td>
        <div class="win-bar">
          <div class="bar-bg"><div class="bar-fill" style="width:${{((d.win_rate||0)-40)/20*100}}%;background:${{barColor(d.win_rate)}}"></div></div>
          <span class="badge ${{winClass(d.win_rate)}}">${{pct(d.win_rate)}}</span>
        </div>
      </td>
    </tr>
  `).join('');

  renderPagination('stats', data.length, statsPage, n => {{ statsPage = n; renderStats(); }});
}}

// --- Maps ---
function getFilteredMaps() {{
  const region = document.getElementById('mf-region').value;
  const type = document.getElementById('mf-type').value;
  const hero = document.getElementById('mf-hero').value;
  const search = document.getElementById('mf-search').value.toLowerCase();

  return MAPS.filter(d => {{
    if (region && d.region !== region) return false;
    if (type && d.map_type !== type) return false;
    if (hero && d.hero !== hero) return false;
    if (search && !(d.map_name || '').toLowerCase().includes(search)) return false;
    return true;
  }}).sort((a, b) => (b.win_rate || 0) - (a.win_rate || 0));
}}

function renderMaps() {{
  const data = getFilteredMaps();

  // Populate map type filter
  const types = [...new Set(MAPS.map(d => d.map_type).filter(Boolean))];
  const tsel = document.getElementById('mf-type');
  if (tsel.options.length <= 1) {{
    types.forEach(t => {{ tsel.add(new Option(t, t)); }});
  }}
  const heroes = [...new Set(MAPS.map(d => d.hero).filter(Boolean))].sort();
  const hsel = document.getElementById('mf-hero');
  if (hsel.options.length <= 1) {{
    heroes.forEach(h => {{ hsel.add(new Option(h, h)); }});
  }}

  const start = (mapsPage - 1) * PAGE_SIZE;
  const page = data.slice(start, start + PAGE_SIZE);

  document.getElementById('maps-body').innerHTML = page.map((d, i) => `
    <tr>
      <td style="color:var(--mute)">${{start + i + 1}}</td>
      <td style="font-weight:600">${{d.map_name || ''}}</td>
      <td><span class="role-tag">${{d.map_type || ''}}</span></td>
      <td><span class="hero-name">${{d.hero || ''}}</span></td>
      <td><span class="role-tag">${{d.region || ''}}</span></td>
      <td>
        <div class="win-bar">
          <div class="bar-bg"><div class="bar-fill" style="width:${{Math.min(d.pick_rate||0,30)/30*100}}%;background:var(--accent2)"></div></div>
          <span class="badge mid">${{pct(d.pick_rate)}}</span>
        </div>
      </td>
      <td>
        <div class="win-bar">
          <div class="bar-bg"><div class="bar-fill" style="width:${{((d.win_rate||0)-40)/20*100}}%;background:${{barColor(d.win_rate)}}"></div></div>
          <span class="badge ${{winClass(d.win_rate)}}">${{pct(d.win_rate)}}</span>
        </div>
      </td>
    </tr>
  `).join('');

  renderPagination('maps', data.length, mapsPage, n => {{ mapsPage = n; renderMaps(); }});
}}

// --- Pagination ---
function renderPagination(id, total, current, onChange) {{
  const pages = Math.ceil(total / PAGE_SIZE);
  const el = document.getElementById(id + '-pagination');
  if (pages <= 1) {{ el.innerHTML = ''; return; }}

  let btns = `<span class="page-info">${{total}}건 / ${{pages}}페이지</span>`;
  btns += `<button class="page-btn" onclick="((${{onChange}}))(${{current - 1}})" ${{current <= 1 ? 'disabled' : ''}}>←</button>`;
  for (let p = Math.max(1, current-2); p <= Math.min(pages, current+2); p++) {{
    btns += `<button class="page-btn ${{p === current ? 'active' : ''}}" onclick="((${{onChange}}))(${{p}})">${{p}}</button>`;
  }}
  btns += `<button class="page-btn" onclick="((${{onChange}}))(${{current + 1}})" ${{current >= pages ? 'disabled' : ''}}>→</button>`;
  el.innerHTML = btns;
}}

// Init
renderStats();
renderMaps();
</script>
</body>
</html>"""

    return html


def main():
    print("=== HTML 대시보드 생성기 시작 ===")
    print("데이터 로딩...")
    stats_df, map_df = load_data()

    print("HTML 생성 중...")
    html = generate_html(stats_df, map_df)

    out = "index.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"저장 완료: {out}")


if __name__ == "__main__":
    main()
