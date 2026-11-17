#!/usr/bin/env python3
"""機關王 R4M 程式說明站 (r4m-guide) 靜態網站建置腳本

功能：
1. 為全站 HTML 頁面注入／更新共用頁首 (nav.html)、防閃爍腳本、頁尾更新日期
2. 實作 Assets 內容雜湊快取破壞 (Cache Busting: ?v=<md5_8>)
3. 產生 100% 冪等的離線瀏覽壓縮包 (site/downloads/r4m-guide-offline.zip)
4. 完全冪等：重複執行時產物二進位內容完全不變，無更動不寫入磁碟

匯出項目供 verify_site.py 引用推導：
- PAGES: 頁面相對路徑對應麵包屑
- get_asset_hashes(): 取得當前 CSS/JS MD5 前 8 碼
- ROOT, SITE, BUILD: 專案重要路徑
"""

import hashlib
import io
import os
import pathlib
import re
import sys
import zipfile

# 專案絕對路徑定義
BUILD = pathlib.Path(__file__).resolve().parent
ROOT = BUILD.parent
SITE = ROOT / 'site'
NAV_FILE = BUILD / 'nav.html'

# 檔案相對路徑 → 麵包屑文字
PAGES = {
    'index.html': '首頁',
    'prepare.html': '上場前準備',
    'pairing.html': 'A／B 車 設定與配對',
    'ksb.html': 'A／B 車 KSB 搖桿操作',
    'v7rc.html': 'A／B 車 手機 V7RC 操作',
    'ccar.html': 'C 車 循跡取料',
    'faq.html': '常見問題',
    'tech.html': '老師用 程式架構與調校',
}

# 固定的區塊標記正規表示式
NAV_BLOCK = re.compile(r'<!-- rg-nav:start.*?<!-- rg-nav:end -->\n?', re.S)
EARLY_BLOCK = re.compile(r'<!-- rg-early:start.*?<!-- rg-early:end -->\n?', re.S)
FOOTER_BLOCK = re.compile(r'<!-- rg-footer:start.*?<!-- rg-footer:end -->\n?', re.S)

# 防閃爍腳本模板
EARLY_SCRIPT_TEMPLATE = """<!-- rg-early:start -->
<script>
(function(){try{
  var t=localStorage.getItem('rg-theme');
  if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t);
  var fs=localStorage.getItem('rg-fs');
  if(fs==='0.92'||fs==='1'||fs==='1.12')document.documentElement.style.setProperty('--fs-user',fs);
}catch(e){}})();
</script>
<!-- rg-early:end -->"""

# 頁尾模板
FOOTER_TEMPLATE = """<!-- rg-footer:start -->
<footer class="rg-footer">
  <div>車城自造教育科技中心 · 2027 世界機關王 R4M 基礎組程式說明站（更新日期：2026-10-31）</div>
  <div><a href="__ROOT__index.html">回說明站首頁</a> · <a href="https://ccmtc.mooo.com/">回科技中心官網</a></div>
</footer>
<!-- rg-footer:end -->"""


def get_asset_hashes():
    """計算 site/assets/rg.css 與 rg.js 的 MD5 前 8 碼。"""
    css_path = SITE / 'assets' / 'rg.css'
    js_path = SITE / 'assets' / 'rg.js'

    css_hash = '00000000'
    js_hash = '00000000'

    if css_path.exists():
        css_hash = hashlib.md5(css_path.read_bytes()).hexdigest()[:8]
    if js_path.exists():
        js_hash = hashlib.md5(js_path.read_bytes()).hexdigest()[:8]

    return css_hash, js_hash


def render_nav(rel: str, here: str, root_prefix: str) -> str:
    """根據當前頁面相對路徑與麵包屑，產生注入用的 nav HTML。"""
    raw_nav = NAV_FILE.read_text(encoding='utf-8').strip()

    # 替換前綴與麵包屑
    nav = raw_nav.replace('__ROOT__', root_prefix).replace('__HERE__', here)

    # 標記目前所在頁面的導覽項目（加上 is-current 與 aria-current="page"）
    target_attr = f'data-rg-page="{rel}"'
    if target_attr in nav:
        # 尋找 <a class="rg-nav-link" data-rg-page="{rel}"
        pattern = rf'(<a\s+class="rg-nav-link)("(?=[^>]*{re.escape(target_attr)}))'
        nav = re.sub(pattern, r'\1 is-current" aria-current="page"', nav, count=1)

    return nav


def process_html_content(rel: str, html: str, css_hash: str, js_hash: str) -> str:
    """處理單一 HTML 頁面內容，回傳更新後的 HTML 字串。完全純函式，確保冪等。"""
    depth = rel.count('/')
    root_prefix = '../' * depth
    here = PAGES.get(rel, '說明站')

    # 1. 導覽列注入／替換
    rendered_nav = render_nav(rel, here, root_prefix)
    if NAV_BLOCK.search(html):
        html = NAV_BLOCK.sub(rendered_nav + '\n', html)
    elif '<!-- RG_NAV_PLACEHOLDER -->' in html:
        html = html.replace('<!-- RG_NAV_PLACEHOLDER -->', rendered_nav)
    else:
        body_match = re.search(r'<body[^>]*>', html)
        if body_match:
            idx = body_match.end()
            html = html[:idx] + '\n' + rendered_nav + html[idx:]

    # 2. 防閃爍腳本 (Early Script)
    if EARLY_BLOCK.search(html):
        html = EARLY_BLOCK.sub(EARLY_SCRIPT_TEMPLATE + '\n', html)
    else:
        title_match = re.search(r'</title>\s*\n?', html, re.I)
        if title_match:
            idx = title_match.end()
            html = html[:idx] + '  ' + EARLY_SCRIPT_TEMPLATE + '\n' + html[idx:]

    # 3. Robots meta 標籤
    if not re.search(r'<meta\s+name=["\']robots["\']', html, re.I):
        meta_robots = '<meta name="robots" content="noindex,nofollow">\n'
        viewport_match = re.search(r'(<meta\s+name=["\']viewport["\'][^>]*>\s*\n?)', html, re.I)
        if viewport_match:
            idx = viewport_match.end()
            html = html[:idx] + '  ' + meta_robots + html[idx:]
        else:
            head_match = re.search(r'<head[^>]*>\s*\n?', html, re.I)
            if head_match:
                idx = head_match.end()
                html = html[:idx] + '  ' + meta_robots + html[idx:]

    # 4. 頁尾 (Footer) 注入／替換
    rendered_footer = FOOTER_TEMPLATE.replace('__ROOT__', root_prefix)
    if FOOTER_BLOCK.search(html):
        html = FOOTER_BLOCK.sub(rendered_footer + '\n', html)
    else:
        main_end = html.rfind('</main>')
        if main_end != -1:
            html = html[:main_end] + '  ' + rendered_footer + '\n' + html[main_end:]
        else:
            body_end = html.rfind('</body>')
            if body_end != -1:
                html = html[:body_end] + rendered_footer + '\n' + html[body_end:]

    # 5. 快取破壞（Cache Busting）
    # 更新 rg.css 引用（無論原本有無 ?v= 或其前綴為何）
    css_pat = re.compile(r'href="(?:\.\./|__ROOT__)*assets/rg\.css(?:\?v=[^"]*)?"')
    html = css_pat.sub(f'href="{root_prefix}assets/rg.css?v={css_hash}"', html)

    # 更新 rg.js 引用
    js_pat = re.compile(r'src="(?:\.\./|__ROOT__)*assets/rg\.js(?:\?v=[^"]*)?"')
    html = js_pat.sub(f'src="{root_prefix}assets/rg.js?v={js_hash}"', html)

    return html


def build_offline_zip() -> bool:
    """產生 100% 冪等的離線瀏覽壓縮包 site/downloads/r4m-guide-offline.zip。
    
    保證冪等要點：
    1. 檔案清單排序 (sorted)
    2. 固定 ZipInfo.date_time 為 (2026, 10, 23, 0, 0, 0)
    3. 固定 ZipInfo.external_attr 為 0o644 << 16
    4. 頂層目錄包裝在 r4m-guide/ 底下
    5. 若新舊二進位內容一致則不寫入磁碟
    """
    downloads_dir = SITE / 'downloads'
    downloads_dir.mkdir(parents=True, exist_ok=True)
    zip_path = downloads_dir / 'r4m-guide-offline.zip'

    # 收集 site/ 下的所有檔案（排除 zip 本身與 .DS_Store）
    all_files = []
    for p in SITE.rglob('*'):
        if p.is_file():
            rel = p.relative_to(SITE)
            rel_str = str(rel)
            if rel_str == 'downloads/r4m-guide-offline.zip' or p.name == '.DS_Store':
                continue
            all_files.append((rel_str, p))

    all_files.sort(key=lambda x: x[0])

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for rel_str, p in all_files:
            content = p.read_bytes()
            archive_path = f'r4m-guide/{rel_str}'
            info = zipfile.ZipInfo(filename=archive_path)
            info.date_time = (2026, 10, 23, 0, 0, 0)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, content)

    new_zip_bytes = buf.getvalue()

    if zip_path.exists():
        old_zip_bytes = zip_path.read_bytes()
        if old_zip_bytes == new_zip_bytes:
            return False  # 無需更新

    zip_path.write_bytes(new_zip_bytes)
    return True  # 已更新


def build_all():
    """執行全站建置，回傳 (更新頁面數, 離線包是否更新)。"""
    if not SITE.exists():
        print(f'❌ 錯誤：找不到站台目錄 {SITE}', file=sys.stderr)
        sys.exit(1)

    css_hash, js_hash = get_asset_hashes()
    print(f'=== 開始建置機關王 R4M 程式說明站 ===')
    print(f'資源雜湊：rg.css?v={css_hash} | rg.js?v={js_hash}')

    # 掃描 site/ 底下所有 HTML 檔案
    html_files = sorted(SITE.rglob('*.html'))
    updated_pages = 0

    for p in html_files:
        rel = str(p.relative_to(SITE))
        raw_html = p.read_text(encoding='utf-8')
        processed = process_html_content(rel, raw_html, css_hash, js_hash)

        if processed != raw_html:
            p.write_text(processed, encoding='utf-8')
            updated_pages += 1
            print(f'  [更新] {rel}')
        else:
            print(f'  [保持] {rel}')

    zip_updated = build_offline_zip()
    if zip_updated:
        print(f'  [打包] site/downloads/r4m-guide-offline.zip (已更新)')
    else:
        print(f'  [打包] site/downloads/r4m-guide-offline.zip (內容無變動，保持原樣)')

    print(f'=== 建置完成：共檢查 {len(html_files)} 個頁面，更新 {updated_pages} 頁 ===')
    return updated_pages, zip_updated


if __name__ == '__main__':
    build_all()
