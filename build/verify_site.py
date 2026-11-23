#!/usr/bin/env python3
"""機關王 R4M 程式說明站 (r4m-guide) 驗證腳本

支援模式：
1. 靜態檢查：python3 build/verify_site.py --quick
2. 線上／容器回歸檢查：python3 build/verify_site.py --url <URL>

檢查項目（有任何一項 ❌ 立即 sys.exit(1)；全數通過 sys.exit(0)）：
1. 頁面完整性（PAGES 全數存在、含共用導覽列、麵包屑、頁尾更新日期）
2. 快取破壞雜湊一致性（引用 rg.css?v= 與 rg.js?v= 且雜湊符合檔案真實內容）
3. 內部連結與資源存在性（相對連結與 downloads/ 檔案全數存在，無外部 CDN/http://）
4. CSS class 前綴鐵則（自訂 class 一律帶 rg- 前綴或 is- 狀態前綴）
5. SEO 與行動版標籤（Title, Viewport, Robots, 表格包在 .rg-table-wrap 內）
6. WCAG 對比度自動計算（淺色/深色共 13 組對比度全數 >= 4.5:1）
7. 內容一致性（無絕對用語、學生頁無版本修正字樣、關鍵事實齊全）
"""

import argparse
import html.parser
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request

# 將 build 目錄加入 sys.path 以便 import build_site
BUILD_DIR = pathlib.Path(__file__).resolve().parent
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

try:
    from build_site import PAGES, get_asset_hashes, ROOT, SITE, BUILD
except ImportError:
    print('❌ 無法匯入 build_site.py，請確認檔案位置', file=sys.stderr)
    sys.exit(1)


class LinkExtractor(html.parser.HTMLParser):
    """提取 HTML 中所有的 href, src 屬性與 class 名稱、表格層級結構。"""
    def __init__(self):
        super().__init__()
        self.links = []          # [(tag, attr, val)]
        self.classes = []        # [class_name]
        self.tables = []         # [{'in_table_wrap': bool}]
        self.tag_stack = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        classes = attr_dict.get('class', '').split()
        for c in classes:
            if c:
                self.classes.append(c)

        is_table_wrap = 'rg-table-wrap' in classes
        self.tag_stack.append({'tag': tag, 'is_table_wrap': is_table_wrap})

        if tag in ('a', 'link'):
            if 'href' in attr_dict:
                self.links.append((tag, 'href', attr_dict['href']))
        elif tag in ('script', 'img', 'source', 'iframe'):
            if 'src' in attr_dict:
                self.links.append((tag, 'src', attr_dict['src']))

        if tag == 'table':
            in_wrap = any(item['is_table_wrap'] for item in self.tag_stack)
            self.tables.append({'in_table_wrap': in_wrap})

    def handle_endtag(self, tag):
        for i in range(len(self.tag_stack) - 1, -1, -1):
            if self.tag_stack[i]['tag'] == tag:
                self.tag_stack = self.tag_stack[:i]
                break


def srgb_luminance(hex_str: str) -> float:
    """計算 sRGB 色碼 (#rrggbb) 的相對亮度 (WCAG 2.1 公式)。"""
    hex_str = hex_str.strip().lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c * 2 for c in hex_str])
    if len(hex_str) != 6:
        raise ValueError(f'無效的色碼: {hex_str}')
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0

    def f(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def calculate_contrast(hex1: str, hex2: str) -> float:
    """計算兩組色碼的對比度 (1.0 ~ 21.0)。"""
    l1 = srgb_luminance(hex1)
    l2 = srgb_luminance(hex2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def check_wcag_contrast(css_path: pathlib.Path) -> (bool, list):
    """解析 CSS 中的色彩變數，計算 WCAG 對比度。"""
    if not css_path.exists():
        return False, [f'找不到樣式檔: {css_path}']

    css_text = css_path.read_text(encoding='utf-8')
    logs = []
    all_pass = True

    # 解析 :root（淺色模式）
    root_match = re.search(r':root\s*\{([^}]+)\}', css_text)
    if not root_match:
        return False, ['無法在 CSS 中定位 :root 區塊']
    root_block = root_match.group(1)

    # 解析深色模式區塊（@media 或 :root[data-theme="dark"]）
    dark_match = re.search(r':root\[data-theme="dark"\]\s*\{([^}]+)\}', css_text)
    if not dark_match:
        dark_match = re.search(r'@media\s*\(prefers-color-scheme:\s*dark\)[^{]*\{\s*:root[^{]*\{([^}]+)\}', css_text)
    if not dark_match:
        return False, ['無法在 CSS 中定位深色模式區塊']
    dark_block = dark_match.group(1)

    def extract_vars(block):
        var_map = {}
        for m in re.finditer(r'(--[a-zA-Z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,6})', block):
            var_map[m.group(1)] = m.group(2)
        return var_map

    light_vars = extract_vars(root_block)
    dark_vars = extract_vars(dark_block)

    # 淺色模式測試清單
    light_tests = [
        ('--ink vs --plane', light_vars.get('--ink'), light_vars.get('--plane')),
        ('--ink vs --card', light_vars.get('--ink'), light_vars.get('--card')),
        ('--ink-2 vs --card', light_vars.get('--ink-2'), light_vars.get('--card')),
        ('#ffffff vs --accent-strong', '#ffffff', light_vars.get('--accent-strong')),
        ('#ffffff vs --accent-ink', '#ffffff', light_vars.get('--accent-ink')),
        ('#ffffff vs --warn-strong', '#ffffff', light_vars.get('--warn-strong')),
        ('#ffffff vs --danger-strong', '#ffffff', light_vars.get('--danger-strong')),
        ('#ffffff vs --ok-strong', '#ffffff', light_vars.get('--ok-strong')),
    ]

    logs.append('  [淺色模式對比度計算 (>= 4.5:1)]')
    for name, c1, c2 in light_tests:
        if not c1 or not c2:
            logs.append(f'    ❌ 遺漏色彩變數: {name}')
            all_pass = False
            continue
        cr = calculate_contrast(c1, c2)
        status = '✅' if cr >= 4.5 else '❌'
        if cr < 4.5:
            all_pass = False
        logs.append(f'    {status} {name:28s} ({c1} vs {c2}): {cr:.2f}:1')

    # 深色模式測試清單
    dark_tests = [
        ('--ink vs --plane', dark_vars.get('--ink'), dark_vars.get('--plane')),
        ('--ink vs --card', dark_vars.get('--ink'), dark_vars.get('--card')),
        ('--ink-2 vs --card', dark_vars.get('--ink-2'), dark_vars.get('--card')),
        ('#ffffff vs --accent-strong', '#ffffff', dark_vars.get('--accent-strong')),
        ('#ffffff vs --accent-ink', '#ffffff', dark_vars.get('--accent-ink')),
    ]

    logs.append('  [深色模式對比度計算 (>= 4.5:1)]')
    for name, c1, c2 in dark_tests:
        if not c1 or not c2:
            logs.append(f'    ❌ 遺漏色彩變數: {name}')
            all_pass = False
            continue
        cr = calculate_contrast(c1, c2)
        status = '✅' if cr >= 4.5 else '❌'
        if cr < 4.5:
            all_pass = False
        logs.append(f'    {status} {name:28s} ({c1} vs {c2}): {cr:.2f}:1')

    return all_pass, logs


def run_quick_checks() -> bool:
    """執行本機靜態全項檢查。"""
    print('======================================================')
    print('  機關王 R4M 說明站 本機靜態驗證 (--quick)')
    print('======================================================\n')

    errors = []
    css_hash, js_hash = get_asset_hashes()
    expected_css_ref = f'assets/rg.css?v={css_hash}'
    expected_js_ref = f'assets/rg.js?v={js_hash}'

    # 1. 頁面完整性檢查
    print(f'1. 檢查頁面完整性 ({len(PAGES)} 個 HTML 頁面、導覽列、麵包屑、頁尾更新日期)...')
    missing_pages = []
    html_contents = {}

    for rel in PAGES.keys():
        p = SITE / rel
        if not p.exists():
            missing_pages.append(rel)
        else:
            html_contents[rel] = p.read_text(encoding='utf-8')

    if missing_pages:
        for m in missing_pages:
            errors.append(f'缺漏頁面: site/{m}')
        print(f'   ❌ 缺漏 {len(missing_pages)} 個必要頁面: {", ".join(missing_pages)}')
    else:
        # 檢查已載入頁面的必要區塊
        page_ok = True
        for rel, html in html_contents.items():
            if '<!-- rg-nav:start' not in html:
                errors.append(f'{rel}: 缺少共用導覽列 (rg-nav:start)')
                page_ok = False
            if 'class="rg-bread-here"' not in html:
                errors.append(f'{rel}: 缺少麵包屑區塊 (rg-bread-here)')
                page_ok = False
            if '更新日期：2026-11-23' not in html:
                errors.append(f'{rel}: 缺少頁尾更新日期 2026-11-23')
                page_ok = False
        if page_ok:
            print(f'   ✅ {len(PAGES)} 個核心頁面全數存在，導覽列、麵包屑與頁尾更新日期皆齊全。')
        else:
            print(f'   ❌ 部分頁面缺少共用結構。')

    # 2. 快取破壞雜湊一致性
    print('\n2. 檢查快取破壞雜湊一致性 (Cache Busting)...')
    hash_ok = True
    for rel, html in html_contents.items():
        depth = rel.count('/')
        prefix = '../' * depth
        target_css = f'{prefix}{expected_css_ref}'
        target_js = f'{prefix}{expected_js_ref}'

        if target_css not in html:
            errors.append(f'{rel}: CSS 引用未匹配預期雜湊 ({target_css})')
            hash_ok = False
        if target_js not in html:
            errors.append(f'{rel}: JS 引用未匹配預期雜湊 ({target_js})')
            hash_ok = False

    if hash_ok and not missing_pages:
        print(f'   ✅ 全站頁面正確引用 rg.css?v={css_hash} 與 rg.js?v={js_hash}')
    elif hash_ok:
        print(f'   ⚠️ 既有頁面雜湊一致，但有缺漏頁面。')
    else:
        print(f'   ❌ 快取破壞雜湊檢查未通過。')

    # 3. 內部連結與資源存在性檢查
    print('\n3. 檢查內部相對連結與靜態資源存在性 (無外部 CDN/http)...')
    link_ok = True
    total_links_checked = 0

    for rel, html in html_contents.items():
        parser = LinkExtractor()
        parser.feed(html)
        file_dir = (SITE / rel).parent

        for tag, attr, val in parser.links:
            total_links_checked += 1
            val_clean = val.strip()

            # 允許官網根路徑
            if val_clean == '/':
                continue
            # 略過純錨點與特殊協議
            if val_clean.startswith('#') or val_clean.startswith(('mailto:', 'tel:', 'javascript:')):
                continue

            # 禁止外部 http:// 或外部 CDN
            if val_clean.startswith('http://'):
                errors.append(f'{rel}: 存在非安全 http:// 外部連結 ({val_clean})')
                link_ok = False
                continue

            if 'fonts.googleapis.com' in val_clean or 'fonts.gstatic.com' in val_clean or 'cdnjs.cloudflare.com' in val_clean:
                errors.append(f'{rel}: 引用外部 CDN 字體/資源，違反離線鐵則 ({val_clean})')
                link_ok = False
                continue

            if val_clean.startswith('https://'):
                # 允許一般外部參考網址（例如科技中心官網 https://ccmtc.mooo.com）
                continue

            # 相對路徑解析
            clean_path = val_clean.split('?')[0].split('#')[0]
            unquoted = urllib.parse.unquote(clean_path)
            target = (file_dir / unquoted).resolve()

            if not target.exists():
                errors.append(f'{rel}: 找不到內部引用資源 -> {unquoted} (解析路徑: {target})')
                link_ok = False

    if link_ok and not missing_pages:
        print(f'   ✅ 共檢查 {total_links_checked} 個連結與資源，全數存在且無外部 CDN。')
    else:
        print(f'   ❌ 內部連結或資源存在性檢查未通過。')

    # 4. CSS class rg- 前綴鐵則
    print('\n4. 檢查 CSS class rg- 前綴鐵則...')
    class_ok = True

    for rel, html in html_contents.items():
        parser = LinkExtractor()
        parser.feed(html)
        invalid_classes = set()
        for c in parser.classes:
            if not c.startswith('rg-') and not c.startswith('is-'):
                invalid_classes.add(c)
        if invalid_classes:
            errors.append(f'{rel}: 出現未帶 rg- 或 is- 前綴的自訂 class: {invalid_classes}')
            class_ok = False

    if class_ok and not missing_pages:
        print(f'   ✅ 全站 HTML 自訂 class 皆遵守 rg- 或 is- 前綴規範。')
    else:
        print(f'   ❌ 發現未符合前綴規範的 class 名稱。')

    # 5. SEO 與行動版標籤檢查（含表格包裹）
    print('\n5. 檢查 SEO 與行動版標籤 (Title, Viewport, Robots, .rg-table-wrap)...')
    seo_ok = True

    for rel, html in html_contents.items():
        if not re.search(r'<title>.*?</title>', html, re.I | re.S):
            errors.append(f'{rel}: 缺少 <title> 標籤')
            seo_ok = False
        if not re.search(r'<meta[^>]+name=["\']viewport["\'][^>]*>', html, re.I):
            errors.append(f'{rel}: 缺少 <meta name="viewport"> 標籤')
            seo_ok = False
        if not re.search(r'<meta[^>]+name=["\']robots["\'][^>]*noindex,nofollow', html, re.I):
            errors.append(f'{rel}: 缺少 <meta name="robots" content="noindex,nofollow">')
            seo_ok = False

        parser = LinkExtractor()
        parser.feed(html)
        for tbl in parser.tables:
            if not tbl['in_table_wrap']:
                errors.append(f'{rel}: 存在未包裹在 .rg-table-wrap 內的 <table>，行動版恐破版')
                seo_ok = False

    if seo_ok and not missing_pages:
        print(f'   ✅ 每頁皆具備 Title, Viewport, Robots 標籤，所有表格皆包在 .rg-table-wrap 內。')
    else:
        print(f'   ❌ SEO 或行動版標籤檢查未通過。')

    # 6. WCAG 對比度自動計算 (>= 4.5:1)
    print('\n6. 計算色彩變數 WCAG 對比度 (解析 rg.css)...')
    css_file = SITE / 'assets' / 'rg.css'
    wcag_pass, wcag_logs = check_wcag_contrast(css_file)
    for log in wcag_logs:
        print(log)
    if not wcag_pass:
        errors.append('WCAG 對比度檢查未達到 4.5:1 要求')
        print('   ❌ WCAG 對比度檢查未通過。')
    else:
        print('   ✅ 淺色與深色模式 13 組對比度全數達標 (>= 4.5:1)。')

    # 7. 內容一致性關鍵字檢查（學生頁只講現行功能；關鍵事實與程式一致）
    print('\n7. 檢查內容一致性 (無絕對用語、學生頁無版本修正字樣、關鍵事實一致)...')
    forbidden_words = ['絕不', '完全獨立', '100% 可靠', '100%可靠']
    version_words = re.compile(r'v[0-9](\.[0-9])?\s*修正|舊版|修正紀錄|已由.*取代')
    required = {
        'pairing.html': ['30 秒', '30 公分', '交叉測試', '按住 B', '按住 A'],
        'ksb.html': ['E / C', 'F / D', '慢速模式'],
        'v7rc.html': ['Game ADV', '先連先贏'],
        'ccar.html': ['MS_每公分', 'MS_每度', '急停'],
        'prepare.html': ['github:lioujj/pxt-V7RC', 'github:lioujj/pxt-KSB045', 'github:bsiever/microbit-pxt-flashstorage'],
    }
    fact_ok = True
    for rel, html in html_contents.items():
        for fw in forbidden_words:
            if fw in html:
                errors.append(f'{rel}: 包含禁止的絕對用語「{fw}」'); fact_ok = False
        if rel != 'tech.html':
            text = re.sub(r'<[^>]+>', '', html)
            m = version_words.search(text)
            if m:
                errors.append(f'{rel}: 學生頁出現版本修正字樣「{m.group(0)}」'); fact_ok = False
        for kw in required.get(rel, []):
            if kw not in html:
                errors.append(f'{rel}: 缺少關鍵內容「{kw}」'); fact_ok = False

    if fact_ok and not missing_pages:
        print('   ✅ 無絕對用語、學生頁無版本修正字樣，關鍵事實齊全。')
    else:
        print('   ❌ 內容一致性檢查未通過。')

    # 總結
    print('\n======================================================')
    if errors:
        print(f'❌ 驗證失敗！共計 {len(errors)} 個問題需要修正：')
        for err in errors:
            print(f'  • {err}')
        print('======================================================')
        return False
    else:
        print('✅ 全部檢查通過！網站靜態結構、樣式、雜湊與事實表 100% 合規。')
        print('======================================================')
        return True


def run_url_checks(base_url: str) -> bool:
    """對線上站台或本機容器 (如 http://127.0.0.1:3080) 執行回歸測試。"""
    base_url = base_url.rstrip('/')
    print('======================================================')
    print(f'  機關王 R4M 說明站 線上／容器回歸檢查 ({base_url})')
    print('======================================================\n')

    errors = []
    css_hash, js_hash = get_asset_hashes()

    # 測試首頁
    print(f'1. 測試首頁存取: {base_url}/...')
    try:
        req = urllib.request.Request(f'{base_url}/', headers={'User-Agent': 'VerifySiteBot/2.1'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            code = resp.getcode()
            cache_ctrl = resp.headers.get('Cache-Control', '')
            print(f'   HTTP 狀態碼: {code}, Cache-Control: {cache_ctrl}')
            if code != 200:
                errors.append(f'首頁 HTTP 狀態碼非 200: {code}')
            if 'no-cache' not in cache_ctrl:
                errors.append(f'首頁 Cache-Control 標頭未包含 no-cache: {cache_ctrl}')
    except Exception as e:
        errors.append(f'連線至首頁失敗: {e}')

    # 測試子頁面
    print(f'\n2. 測試子頁面存取: {base_url}/controls/index.html...')
    try:
        req = urllib.request.Request(f'{base_url}/controls/index.html', headers={'User-Agent': 'VerifySiteBot/2.1'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            code = resp.getcode()
            print(f'   HTTP 狀態碼: {code}')
            if code != 200:
                errors.append(f'子頁面 HTTP 狀態碼非 200: {code}')
    except Exception as e:
        errors.append(f'連線至子頁面失敗: {e}')

    # 測試靜態資源雜湊
    print(f'\n3. 測試 CSS 雜湊資源: {base_url}/assets/rg.css?v={css_hash}...')
    try:
        req = urllib.request.Request(f'{base_url}/assets/rg.css?v={css_hash}', headers={'User-Agent': 'VerifySiteBot/2.1'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            code = resp.getcode()
            print(f'   HTTP 狀態碼: {code}')
            if code != 200:
                errors.append(f'CSS 資源存取失敗: {code}')
    except Exception as e:
        errors.append(f'連線至 CSS 資源失敗: {e}')

    print('\n======================================================')
    if errors:
        print(f'❌ 線上回歸驗證失敗！共計 {len(errors)} 個問題：')
        for err in errors:
            print(f'  • {err}')
        print('======================================================')
        return False
    else:
        print('✅ 線上回歸驗證全部通過！')
        print('======================================================')
        return True


def main():
    parser = argparse.ArgumentParser(description='機關王 R4M 說明站靜態與線上驗證工具')
    parser.add_argument('--quick', action='store_true', help='執行本機靜態全項檢查')
    parser.add_argument('--url', type=str, help='指定 BASE_URL 進行線上回歸檢查')

    args = parser.parse_args()

    if not args.quick and not args.url:
        # 預設執行 --quick
        args.quick = True

    success = True
    if args.quick:
        if not run_quick_checks():
            success = False

    if args.url:
        if not run_url_checks(args.url):
            success = False

    if not success:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
