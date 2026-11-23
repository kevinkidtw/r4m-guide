#!/usr/bin/env python3
"""機關王 R4M 程式說明站：頁面內容原稿。

執行後依 page-template.html 產生 site/*.html，再由 build_site.py 注入導覽列、頁尾與快取雜湊。
內容只描述目前的功能與操作，不寫版本修正歷程。
"""
import pathlib

BUILD = pathlib.Path(__file__).resolve().parent
SITE = BUILD.parent / 'site'
TEMPLATE = (BUILD / 'page-template.html').read_text(encoding='utf-8')

DL = {
    'v7rc': '01_V7RC_車端_AB通用_低延遲版.ts',
    'ksb_tx': '03_KSB發射端_搖桿_v2.ts',
    'ksb_car': '04_KSB_車端_AB通用_v2.ts',
    'probe': '06_V7RC封包探測器_GameADV用.ts',
    'ccar': 'R4M_C車_循跡取料_2027.ts',
}


def table(head, rows):
    th = ''.join(f'<th>{h}</th>' for h in head)
    trs = '\n'.join('          <tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
    return f'''<div class="rg-table-wrap">
      <table class="rg-table">
        <thead><tr>{th}</tr></thead>
        <tbody>
{trs}
        </tbody>
      </table>
    </div>'''


def checks(prefix, items):
    out = []
    for i, (title, desc) in enumerate(items, 1):
        out.append(f'''      <label class="rg-check-item">
        <input type="checkbox" data-rg-check="{prefix}{i}">
        <div>
          <strong>{title}</strong>
          <p>{desc}</p>
        </div>
      </label>''')
    return '<div class="rg-check-list">\n' + '\n'.join(out) + '\n    </div>'


def dl_row(title, desc, file, label, secondary=True):
    cls = 'rg-btn rg-btn-secondary' if secondary else 'rg-btn'
    return f'''      <div class="rg-dl-row">
        <div class="rg-dl-info">
          <div class="rg-dl-title">{title}</div>
          <div class="rg-dl-desc">{desc}</div>
        </div>
        <a class="{cls}" href="downloads/{file}" download>{label}</a>
      </div>'''


PAGES = {}

# ───────────────────────── 首頁 ─────────────────────────
PAGES['index.html'] = dict(
    title='首頁', kicker='2027 WORLD MECHANICAL KING · R4M BASIC',
    h1='機關王 R4M 基礎組<br>A／B／C 三車程式說明站',
    dek='A 車（夾車）、B 車（推扒車）用遙控操作，C 車用程式自動循跡取料。這裡整理三台車的燒錄、設定、配對、操作與調整方法。',
    body=f'''<div class="rg-doors">
    <section class="rg-door">
      <div class="rg-door-who">選手 · 上場前</div>
      <h2>我要準備上場</h2>
      <p class="rg-door-sub">燒錄哪支程式、車子怎麼設定、遙控器怎麼配對，以及每次上場前的檢查。</p>
      <ul class="rg-door-list">
        <li><a href="prepare.html">上場前準備</a><span>三台車用哪支程式、要裝的擴充套件、燒錄步驟、賽前檢查清單（可勾選）</span></li>
        <li><a href="pairing.html">A／B 車 設定與配對</a><span>車編號與主控盒設定、遙控器配對、燈號圖鑑、四項驗收</span></li>
      </ul>
      <a class="rg-btn" href="prepare.html">開始準備 →</a>
    </section>

    <section class="rg-door rg-door-warn">
      <div class="rg-door-who">選手 · 操作</div>
      <h2>我要開 A／B 車</h2>
      <p class="rg-door-sub">兩種遙控方式的按鍵和手感刻意做成一樣，換遙控器不用重新適應。</p>
      <ul class="rg-door-list">
        <li><a href="ksb.html">KSB 搖桿操作</a><span>E／C 升降、F／D 微調、A／B 夾爪或閘門、按下搖桿慢速</span></li>
        <li><a href="v7rc.html">手機 V7RC 操作</a><span>Game ADV 介面、藍牙名稱怎麼找、先連先贏</span></li>
      </ul>
      <a class="rg-btn rg-btn-warn" href="ksb.html">看按鍵 →</a>
    </section>

    <section class="rg-door rg-door-ok">
      <div class="rg-door-who">選手 · 程式車</div>
      <h2>我要調 C 車</h2>
      <p class="rg-door-sub">C 車在比賽中不能遙控，靠三顆循跡感測器沿黑線取料、卸料。</p>
      <ul class="rg-door-list">
        <li><a href="ccar.html">C 車 循跡取料</a><span>任務路線、按鍵、參數表、里程與轉角校正、燈號意思</span></li>
        <li><a href="faq.html">常見問題</a><span>車子不動、配錯遙控器、手機找不到車、C 車找不到線</span></li>
      </ul>
      <a class="rg-btn rg-btn-ok" href="ccar.html">看 C 車 →</a>
    </section>
  </div>

  <section class="rg-section">
    <h2>三台車一覽</h2>
    {table(['車', '任務', '控制方式', '燒錄的程式'], [
        ['<strong>A 車</strong>（夾車）', '小雞、蜜蜂的夾取搬運', 'KSB 搖桿 <em>或</em> 手機 V7RC', f'KSB：<code>{DL["ksb_car"]}</code><br>V7RC：<code>{DL["v7rc"]}</code>'],
        ['<strong>B 車</strong>（推扒車）', '用耙子與閘門推送鬱金香、牽牛花、大樹、小樹、蘑菇等物件', 'KSB 搖桿 <em>或</em> 手機 V7RC', '和 A 車同一支程式，開機選單選「B」'],
        ['<strong>KSB 遙控器</strong>', '給 A 或 B 車用', '—', f'<code>{DL["ksb_tx"]}</code>（免設定）'],
        ['<strong>C 車</strong>（循跡車）', '把紅、綠、藍飼料從暫放區運到對應顏色的放置區（滿分 600 分）', '程式自動，<strong>不能遙控</strong>', f'<code>{DL["ccar"]}</code>'],
    ])}
    <div class="rg-callout rg-callout-warn">
      <strong>A 車和 B 車用同一支程式。</strong>差別只在開機選單選的車編號：A 車的 A／B 鍵控制夾爪，B 車的 A／B 鍵控制閘門、E／C 鍵控制耙子。車子端的 micro:bit 一律用 V2，KSB 遙控器用 V1 或 V2 都可以。
    </div>
  </section>

  <section class="rg-section">
    <h2>檔案下載</h2>
    <p>程式是 MakeCode 的 JavaScript 原始碼（<code>.ts</code>）。用法：MakeCode 新專案 → 先裝好擴充套件 → 切到 <strong>JavaScript</strong> 分頁 → 全選刪除後貼上 → 下載燒錄。詳細步驟見<a href="prepare.html">上場前準備</a>。</p>
    <div class="rg-dl-list">
{dl_row('1. A／B 車：KSB 搖桿版（車端）', f'<code>{DL["ksb_car"]}</code> · 需要擴充套件 flashstorage', DL['ksb_car'], '下載', False)}
{dl_row('2. KSB 遙控器（發射端）', f'<code>{DL["ksb_tx"]}</code> · 需要擴充套件 KSB045', DL['ksb_tx'], '下載', False)}
{dl_row('3. A／B 車：手機 V7RC 版（車端）', f'<code>{DL["v7rc"]}</code> · 需要擴充套件 V7RC、flashstorage', DL['v7rc'], '下載', False)}
{dl_row('4. C 車：循跡取料', f'<code>{DL["ccar"]}</code> · 不需要額外擴充套件', DL['ccar'], '下載', False)}
{dl_row('5. 老師用：V7RC 封包探測器', f'<code>{DL["probe"]}</code> · 換用其他 V7RC 介面時測通道用', DL['probe'], '下載')}
{dl_row('6. 本站離線瀏覽包', '<code>r4m-guide-offline.zip</code> · 解壓縮後打開 <code>index.html</code>，比賽現場沒網路也能看', 'r4m-guide-offline.zip', '下載')}
    </div>
  </section>''')

# ───────────────────────── 上場前準備 ─────────────────────────
PAGES['prepare.html'] = dict(
    title='上場前準備', kicker='PREPARE · FLASH · CHECKLIST',
    h1='上場前準備', dek='燒錄程式、安裝擴充套件、賽前檢查。比賽前一天在教室做完，到會場只要開機驗收。',
    body=f'''<section class="rg-section">
    <h2>一、每台車燒哪支程式</h2>
    {table(['燒在哪裡', '程式檔', '要先裝的擴充套件'], [
        ['A 車或 B 車（用 KSB 搖桿時）', f'<code>{DL["ksb_car"]}</code>', 'flashstorage（radio 新專案預設就有）'],
        ['KSB 遙控器', f'<code>{DL["ksb_tx"]}</code>', 'KSB045（radio 預設就有）'],
        ['A 車或 B 車（用手機 V7RC 時）', f'<code>{DL["v7rc"]}</code>', 'V7RC、flashstorage'],
        ['C 車', f'<code>{DL["ccar"]}</code>', '不需要'],
    ])}
    <div class="rg-callout rg-callout-warn">
      <strong>KSB 遙控器和 KSB 車端要用同一批下載的程式。</strong>兩邊的封包格式要一致才連得上，換其中一邊時，另一邊也一起換成本站下載的版本。
    </div>
  </section>

  <section class="rg-section">
    <h2>二、擴充套件</h2>
    <p>在 MakeCode 點「擴充功能」，把下面的網址貼進搜尋框。<strong>貼程式之前就要裝好</strong>，沒裝會出現 <code>Cannot find name 'xxx'</code> 的紅字。</p>
    {table(['擴充套件', '搜尋框貼上', '注意'], [
        ['V7RC', '<code>github:lioujj/pxt-V7RC</code>', '會跳出「要移除 radio」→ 按確定（藍牙和 radio 不能同時用）。<strong>手機遙控一定要裝這個，不能只裝 bluetooth</strong>，否則手機找不到車子'],
        ['KSB045', '<code>github:lioujj/pxt-KSB045</code>', '只有 KSB 遙控器要裝'],
        ['flashstorage', '<code>github:bsiever/microbit-pxt-flashstorage</code>', '車子端要裝，用來記住車編號、主控盒和配對'],
    ])}
    <p>擴充套件加進專案後會跟著專案存，比賽現場沒網路也能編譯；但<strong>第一次加入要有網路</strong>。</p>
  </section>

  <section class="rg-section">
    <h2>三、燒錄步驟</h2>
    <ol>
      <li>打開 MakeCode for micro:bit，建立新專案。</li>
      <li>依上表裝好擴充套件。</li>
      <li>切到上方的 <strong>JavaScript</strong> 分頁，全選、刪除原本的內容。</li>
      <li>用文字編輯器打開下載的 <code>.ts</code> 檔，全選複製，貼進 MakeCode。</li>
      <li>確認沒有紅字後按「下載」，把產生的 <code>.hex</code> 拖進 micro:bit 的磁碟（或用 USB 直接燒錄）。</li>
      <li><strong>車子重新燒錄後，車編號、主控盒和配對都要重做</strong>（見<a href="pairing.html">設定與配對</a>）。</li>
    </ol>
  </section>

  <section class="rg-section">
    <h2>四、賽前檢查清單</h2>
    <p>勾選狀態會記在這支手機的瀏覽器裡，換頁不會不見。</p>
    <h3>前一天（在教室）</h3>
    {checks('d', [
        ('兩台車的車編號、主控盒都設對', '開機時畫面先顯示車編號，再捲出主控盒號碼（1269 或 1409），和設定卡一致。'),
        ('兩組都完成配對，並做過交叉測試', '同一時間只讓一組配對；別支遙控器按了，自己的車不能動。'),
        ('每台車單獨通電，每個動作都試過', '前進、後退、左右轉、升降（耙子）、夾爪（閘門）都要會動。'),
        ('方向測試', '搖桿往前車子往前、往右車子往右轉。方向反了不要自己改，告訴老師。'),
        ('失效保護測試', '直接關掉遙控器電源，車子要在 0.3 秒內停下、畫面中心開始閃爍。'),
        ('電池全部充飽，備用電池也充飽並貼標籤', '電量不足是比賽中最常見的「怪問題」來源。'),
        ('車子和它配對的遙控器貼上同一個編號', '避免上場時拿錯遙控器。'),
        ('C 車：在練習場地跑完一次完整任務', '確認三個放置區都卸得準；參數改過要記在紙上。'),
    ])}
    <h3>進場前 10 分鐘</h3>
    {checks('m', [
        ('開機看畫面', '車編號、主控盒是不是你預期的。'),
        ('交叉測試', '用 A 組遙控器去按，B 車不可以有任何反應；反過來也一樣。'),
        ('機構歸零', '夾爪張開、升降降到底、閘門關閉。'),
        ('換上剛充飽的電池', '換完重新確認畫面顯示沒有跑掉。'),
        ('C 車：搖一搖檢查三顆感測器', '畫面出現 S 後，把車放在黑線上，左、中、右三格會跟著亮，確認三顆都讀得到黑線。'),
    ])}
    <p><button type="button" class="rg-btn rg-btn-secondary" id="rg-checklist-reset">清除全部勾選</button></p>
  </section>

  <section class="rg-section">
    <h2>五、比賽規則重點</h2>
    <ul>
      <li>每台車尺寸限 長 30 × 寬 20 cm，高度不限；比賽開始時三台車分別放在 A、B、C 車出發區（黑框外線範圍內）。</li>
      <li>場地沒有外圍擋板，<strong>四個輪子都開出底圖範圍算違規</strong>，第一次口頭警告，第二次起扣 5 分。</li>
      <li>未經裁判同意不得用手碰觸場內機器人或移動任務物件。</li>
      <li>C 車只能用程式自主運作，比賽中可以修改程式重新上傳，但時間照算。</li>
    </ul>
  </section>''')

# ───────────────────────── 設定與配對 ─────────────────────────
def led(caption, rows, note='', blink=False):
    """5×5 LED 示意圖（inline SVG）。rows 用 '#' 表示亮、'.' 表示暗、'o' 表示閃爍。"""
    cells = []
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            cx, cy = 8 + x * 16, 8 + y * 16
            if c == '#':
                cells.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="var(--svg-wall)"/>')
            elif c == 'o':
                cells.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="none" stroke="var(--svg-wall)" stroke-width="2" stroke-dasharray="3 2"/>')
            else:
                cells.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="var(--sunk)" stroke="var(--ink-2)" stroke-width="0.6"/>')
    svg = f'<svg viewBox="0 0 80 80" width="80" height="80" role="img" aria-label="{caption}">' + ''.join(cells) + '</svg>'
    return f'<figure style="margin:0;text-align:center;width:120px">{svg}<figcaption><strong>{caption}</strong><br>{note}</figcaption></figure>'


LED = '<div style="display:flex;flex-wrap:wrap;gap:16px;justify-content:flex-start">' + ''.join([
    led('連線正常', ['.....', '.....', '..#..', '.....', '.....'], '中心恆亮'),
    led('失聯', ['.....', '.....', '..o..', '.....', '.....'], '中心一亮一暗，車子已自動停止'),
    led('配對中（P）', ['###..', '#..#.', '###..', '#....', '#....'], '等遙控器'),
    led('成功（✓）', ['.....', '....#', '...#.', '#.#..', '.#...'], '設定或配對完成'),
    led('失敗／取消（✗）', ['#...#', '.#.#.', '..#..', '.#.#.', '#...#'], '配對逾時或取消'),
]) + '</div>'

PAGES['pairing.html'] = dict(
    title='A／B 車 設定與配對', kicker='SETUP · PAIRING · CHECK',
    h1='A／B 車 設定與配對', dek='照著步驟做，一步都不要跳。畫面跟說明不一樣時，先停下來問老師。',
    body=f'''<section class="rg-section">
    <h2>先搞懂兩個名詞</h2>
    <ul>
      <li><strong>車編號</strong>：A 或 B。A 是夾車，B 是推扒車。<strong>只有車子要設定</strong>，遙控器不用設定。</li>
      <li><strong>配對</strong>：讓車子記住你這支遙控器。配對之後車子<strong>只聽這一支</strong>，別人的遙控器怎麼按都控制不了你的車。每支遙控器天生有一個獨一無二的晶片序號，車子記住的就是這個號碼。</li>
    </ul>
    <div class="rg-callout rg-callout-ok">
      <strong>口訣：車子開機按住 B ＝ 設定，按住 A ＝ 配對，什麼都不按 ＝ 正常開車。遙控器直接開；要配對才按住 A 開機。</strong>
    </div>
  </section>

  <section class="rg-section">
    <h2>開機前必記：三條規則</h2>
    <ol>
      <li><strong>遙控器開機時，不要碰搖桿。</strong>開機瞬間會記住搖桿放開時的位置當中心點；手壓著搖桿開機，車子之後會自己慢慢跑。</li>
      <li><strong>開機時，步驟沒叫你按就什麼鍵都不要按。</strong>開機時按著按鍵會進入特殊模式。</li>
      <li><strong>「按住不放」比「按一下」可靠。</strong>寫「按住 A」就是一直壓著，直到畫面出現該出現的東西才放開。</li>
    </ol>
  </section>

  <section class="rg-section">
    <h2>畫面燈號圖鑑</h2>
    <p>micro:bit 正面有 5×5 個小燈。實心是亮、空心是暗、虛線圈是閃爍（圖形是示意，實際字型可能稍有不同）。</p>
    {LED}
  </section>

  <section class="rg-section">
    <h2>步驟一：遙控器開機</h2>
    <ol>
      <li>手不要碰搖桿、不要按任何鍵。</li>
      <li>打開遙控器電源。</li>
      <li>感覺震一下，就準備好了。遙控器沒有任何設定要做。</li>
    </ol>
  </section>

  <section class="rg-section">
    <h2>步驟二：設定車子</h2>
    <p><strong>什麼時候要做</strong>：第一次使用、程式重新燒錄過。</p>
    <ol>
      <li><strong>按住 B 不放</strong>，同時打開車子電源。</li>
      <li>畫面先出現字母、再捲出主控盒號碼，B 繼續按著。</li>
      <li>看到畫面捲出 <code>CAR</code> 才放開 B（第一次使用會自動進入，不用按）。</li>
      <li><strong>第 1 頁 CAR</strong>：等 <code>CAR</code> 捲完再按。夾車按 <strong>A</strong>，推扒車按 <strong>B</strong>。</li>
      <li><strong>第 2 頁 BOX</strong>：等 <code>BOX</code> 捲完再按。主控盒 1269 按 <strong>A</strong>，1409 按 <strong>B</strong>。不知道是哪個就問老師，選錯車子會亂動。</li>
      <li>畫面顯示你選的數字，接著出現 ✓，設定完成。<strong>接著做步驟三。</strong></li>
    </ol>
  </section>

  <section class="rg-section">
    <h2>步驟三：配對（KSB 搖桿版）</h2>
    <p><strong>什麼時候要做</strong>：第一次使用（開機會自動出現 P）、程式重新燒錄過、換了一支遙控器。配對會記住，關機也不會忘；<strong>比賽前在教室配好</strong>，到會場直接開機就能用。</p>
    <div class="rg-callout rg-callout-warn">
      <strong>配對要兩邊一起來：車子和遙控器都要進入配對模式（都顯示 P）。</strong>平常開著的遙控器不會被別人配走，所以其他組的遙控器不用關。但<strong>同一時間只讓一組配對</strong>：兩組同時配、又靠很近，還是可能配錯。
    </div>
    <ol>
      <li>車子<strong>先關機</strong>，遙控器<strong>也先關機</strong>。</li>
      <li><strong>車子：按住 A 不放</strong>，同時打開車子電源（從沒配對過的車子不用按，會自動進入）。</li>
      <li>畫面出現字母、捲出主控盒號碼，A 繼續按著，看到 <strong>P</strong> 才放開。</li>
      <li>把遙控器拿到<strong>車子旁邊（30 公分內）</strong>，手不要碰搖桿。</li>
      <li><strong>遙控器：按住 A 不放</strong>，同時打開遙控器電源。</li>
      <li>遙控器最下面一排燈會由左到右亮起來，大約 2 秒亮滿、出現 <strong>P</strong>，才放開 A。</li>
      <li>一兩秒內，<strong>車子和遙控器都會出現 ✓</strong>，遙控器會震一下，配對完成。遙控器出現 ✗ 但車子是 ✓：通常也成功了，看兩邊中心燈有沒有恆亮。</li>
      <li><strong>馬上做步驟四的交叉測試</strong>，確認沒有配錯。</li>
    </ol>
    <h3>一直停在 P</h3>
    <ul>
      <li>以前配對過的車子：等 <strong>30 秒</strong>沒配到，會出現 ✗ 並自動取消，恢復原本配對的遙控器。</li>
      <li>從沒配對過的車子：會一直停在 P 等遙控器，沒有時間限制。</li>
      <li>遙控器：30 秒沒配到會出現 ✗，然後照常可以開車（但車子不會聽它的）。</li>
    </ul>
    {table(['原因', '處理'], [
        ['遙控器沒有進配對模式', '遙控器關機，按住 A 開機，等到 P 出現才放'],
        ['遙控器離車子太遠', '拿到車子旁邊再試（配對訊號用最小功率送）'],
        ['遙控器電池沒電', '換電池'],
        ['遙控器燒的程式和車子不是同一批', '請老師把遙控器重新燒成本站下載的程式（v3.1）'],
    ])}
    <p>手機 V7RC 版不用配對遙控器，連線方式見<a href="v7rc.html">手機 V7RC 操作</a>。</p>
  </section>

  <section class="rg-section">
    <h2>步驟四：驗收（每次上場前都要做）</h2>
    <h3>① 看燈</h3>
    {table(['車子畫面', '遙控器畫面', '意思'], [
        ['中心恆亮', '中心恆亮', '✅ 正常'],
        ['停在 P', '—', '車子還沒配對，看步驟三'],
        ['中心閃爍', '閃爍＋震動', '❌ 沒連上：遙控器沒開，或手上這支不是車子配對的那支'],
    ])}
    <h3>② 輪子架空測試</h3>
    <p>把車子架高，輪子不要碰地：搖桿往前兩輪都往前轉、往右車子往右轉；E／C 鍵升降（或耙子）上下；F／D 鍵小小地左轉、右轉；A／B 鍵夾爪開合（A 車）或閘門開關（B 車）。方向不對<strong>不要自己改程式</strong>，告訴老師。</p>
    <h3>③ 失效保護測試</h3>
    <p><strong>直接關掉遙控器電源</strong>，車子要馬上停下來，畫面中心開始閃爍。關掉遙控器車子還在跑，<strong>不能上場</strong>，馬上找老師。</p>
    <h3>④ 交叉測試（配對後一定要做）</h3>
    <p>拿別隊（或另一組）的遙控器操作，你的車不可以有任何反應；再用自己的遙控器，只有你的車會動。別人的遙控器也控得到你的車，代表配錯了，重新配對。</p>
  </section>

  <section class="rg-section">
    <h2>決賽模式（老師設定，選手不用動）</h2>
    <p>決賽時老師會把車編號、主控盒直接寫進車子的程式裡，開機選單會被關掉：不管怎麼按 B 都不會進設定，避免比賽中誤按改掉設定。開機畫面一樣會顯示字母和數字，請照樣確認跟設定卡一致。</p>
    <p><strong>配對仍然可以做</strong>（萬一比賽中要換備用遙控器）：車子和新遙控器都按住 A 開機、出現 P 才放開，跟平常一樣；同一時間只讓一組配對。</p>
  </section>''')

# ───────────────────────── KSB 搖桿 ─────────────────────────
PAGES['ksb.html'] = dict(
    title='A／B 車 KSB 搖桿操作', kicker='KSB045 JOYSTICK · CONTROLS',
    h1='A／B 車 KSB 搖桿操作', dek='一支遙控器控一台車。搖桿負責行走，六顆按鍵負責機構與微調。',
    body=f'''<section class="rg-section">
    <h2>按鍵對照</h2>
    {table(['按鍵', 'A 車（夾車）', 'B 車（推扒車）'], [
        ['<strong>搖桿 前後</strong>', '前進／後退（類比，推越多越快）', '同左'],
        ['<strong>搖桿 左右</strong>', '轉向（大幅轉向用）', '同左'],
        ['<strong>E / C</strong>', '升降 上／下', '耙子 上／下'],
        ['<strong>F / D</strong>', '左／右微調（固定小轉速）', '同左'],
        ['<strong>A / B</strong>', '夾爪 張開／閉合', '閘門 關／開'],
        ['<strong>按下搖桿</strong>', '慢速模式（按著時有效）', '同左'],
    ])}
    <p>按鍵可以同時按，例如一邊前進一邊升降。</p>
  </section>

  <section class="rg-section">
    <h2>對位技巧</h2>
    <ul>
      <li><strong>F / D 微調比推搖桿準。</strong>微調的轉速固定（20%），按幾下就轉幾次同樣的量，很快就能建立手感。微調時會取代搖桿的轉向，前後仍照搖桿走，可以一邊往前開一邊微調方向。</li>
      <li><strong>點一下也會轉。</strong>點一下馬上放，微調仍會持續 0.04 秒才停，不會「點太快所以車子沒反應」；每點一下的轉動量固定、放開立刻停。按住則一直轉。</li>
      <li><strong>機構在動時自動降速。</strong>升降、夾爪動作或微調時，行走速度自動降到 45%，對位比較穩。按下搖桿也會進入同樣的慢速。</li>
      <li><strong>起步不會暴衝。</strong>行走指令有加速斜坡，搖桿推到底也是平順加速，可以保護電池、避免板子瞬間沒電重開。</li>
    </ul>
  </section>

  <section class="rg-section">
    <h2>畫面與震動</h2>
    {table(['看到什麼', '意思', '怎麼辦'], [
        ['車子、遙控器 中心恆亮', '連線正常', '—'],
        ['車子中心閃爍', '失聯，馬達已全停（閘門維持原狀）', '確認遙控器有開、拿對支'],
        ['遙控器閃爍＋每 2.5 秒震動', '收不到車子的回應，或車子配對的是別支遙控器', '確認車子有開、有電；拿回自己那支'],
        ['畫面出現 <code>L</code>', '開機時按著 A＋B，進入「頻段鎖定」模式', '關機、手放開再開機'],
    ])}
    <div class="rg-callout rg-callout-warn">
      <strong>頻段鎖定（L）只在主辦要求使用固定頻段時才用。</strong>遙控器和車子都要按住 A＋B 開機才會一起進入，只有一邊是 L 會連不上。
    </div>
  </section>

  <section class="rg-section">
    <h2>為什麼別隊的遙控器控制不了你的車</h2>
    <p>KSB 遙控器用 2.4GHz 無線廣播，全場的遙控器都在空中送訊號，所以程式用三層把別人擋掉：</p>
    {table(['層', '做法', '擋掉什麼'], [
        ['頻段', '每支遙控器依晶片序號自動選一個頻段（避開 WiFi 常用頻道）', '大部分別隊的訊號，晶片直接不收'],
        ['封包名稱', '只收名稱是 <code>R4</code> 的封包', '格式不同的其他程式'],
        ['<strong>配對</strong>', '車子只認配對過的那支遙控器序號', '<strong>別人的遙控器（真正的隔離靠這一層）</strong>'],
    ])}
    <p>配對要車子和遙控器兩邊都進入配對模式，正常開著的遙控器不會被配走；配完一定要做交叉測試。</p>
  </section>''')

# ───────────────────────── V7RC ─────────────────────────
PAGES['v7rc.html'] = dict(
    title='A／B 車 手機 V7RC 操作', kicker='V7RC APP · GAME ADV',
    h1='A／B 車 手機 V7RC 操作', dek='用手機藍牙控制車子，不需要配對遙控器：手機連上哪台，就只控那台。',
    body=f'''<section class="rg-section">
    <h2>一、第一次設定車子</h2>
    <ol>
      <li><strong>按住 B 不放</strong>，同時打開車子電源。</li>
      <li>畫面捲出字母和主控盒數字，B 繼續按著，看到 <code>CAR</code> 才放開。</li>
      <li>等 <code>CAR</code> 捲完：夾車按 <strong>A</strong>、推扒車按 <strong>B</strong>。</li>
      <li>等 <code>BOX</code> 捲完：1269 按 <strong>A</strong>、1409 按 <strong>B</strong>。</li>
      <li>出現 ✓ 完成。</li>
    </ol>
  </section>

  <section class="rg-section">
    <h2>二、連線</h2>
    <ol>
      <li>車子開機，<strong>還沒連上手機時按 A</strong>，畫面會捲出一串英文字母（例如 <code>zuvat</code>），這是這台車的藍牙名稱。</li>
      <li>把這個名稱寫在車身貼紙上。</li>
      <li>手機打開 V7RC，選 <strong>Game ADV</strong> 介面，在裝置清單找 <code>BBC micro:bit [zuvat]</code> 這種名稱，點它。</li>
      <li>車子畫面中心恆亮，就是連上了。</li>
    </ol>
    <div class="rg-callout rg-callout-danger">
      <strong>先連先贏：</strong>車子在還沒被連上之前，任何一支手機都連得進去（包括別隊的手機誤點）。一台車同時只能被一支手機連，所以<strong>車子開機後就馬上用自己的手機連上</strong>，連上之後別人就進不來了。
    </div>
  </section>

  <section class="rg-section">
    <h2>三、操作佈局（Game ADV）</h2>
    {table(['手機上的位置', 'A 車（夾車）', 'B 車（推扒車）'], [
        ['<strong>左搖桿 ↕</strong>', '前進／後退（類比，推越多越快）', '同左'],
        ['<strong>左搖桿 ↔</strong>', '轉向（大幅轉向用）', '同左'],
        ['<strong>方向鍵 ↑ / ↓</strong>', '升降 上／下', '耙子 上／下'],
        ['<strong>方向鍵 ← / →</strong>', '左／右微調（固定小轉速）', '同左'],
        ['<strong>方向鍵 ↖ / ↗</strong>', '夾爪 張開／閉合', '閘門 關／開'],
        ['<strong>方向鍵 ↙ / ↘</strong>', '沒有功能', '沒有功能'],
    ])}
    <ul>
      <li><strong>← → 微調</strong>：每按一下轉一小段，對位置時用這個，比推搖桿準。點一下也保證轉 0.04 秒，每點一下的轉動量固定。</li>
      <li><strong>↖ ↗ 要按斜角</strong>：手指偏了會變成升降，按準一點。同一時間只會有一個方向鍵動作成立，兩個機構不會一起亂動。</li>
      <li>機構在動或微調時，行走速度自動降到 45%，方便對位。</li>
      <li>和 KSB 搖桿版的按鍵功能、手感一致：↑↓ 對應 E／C，←→ 對應 F／D，↖↗ 對應 A／B。</li>
    </ul>
  </section>

  <section class="rg-section">
    <h2>四、安全設計</h2>
    <ul>
      <li>手機斷線，或 0.3 秒沒收到訊號，車子會全停、畫面中心閃爍。</li>
      <li><strong>手機一鎖螢幕車子就停</strong>，這是安全設計。比賽時手機螢幕保持亮著。</li>
    </ul>
  </section>

  <section class="rg-section">
    <h2>五、V7RC 常見問題</h2>
    {table(['症狀', '處理'], [
        ['清單裡找不到車子', '確認車子有開、沒被別支手機連著；手機以前連過這台但重燒過程式 → 到手機藍牙設定「忘記此裝置」。都不是 → 請老師確認燒錄時有裝 <strong>V7RC 擴充套件</strong>'],
        ['不知道哪個名字是我的車', '車子沒連線時按 A 看名字'],
        ['連上了但車子不動', '手機 App 要選 Game ADV 介面'],
        ['手機一鎖螢幕車子就停', '正常，手機螢幕保持亮著'],
        ['按 ↖ ↗ 卻變成升降', '斜角沒按準，手指偏上了'],
    ])}
  </section>''')

# ───────────────────────── C 車 ─────────────────────────
PAGES['ccar.html'] = dict(
    title='C 車 循跡取料', kicker='C ROBOT · LINE FOLLOWING · AUTONOMOUS',
    h1='C 車 循跡取料', dek='C 車在比賽中不能遙控。按下 B 之後，它會自己沿黑線把飼料送到對應顏色的放置區。',
    body=f'''<section class="rg-section">
    <h2>一、任務與計分</h2>
    <p>C 車必須裝循跡感應器（1247-W85-B3 或 1409-W85-D），用程式自主運作，把紅、綠、藍三種飼料從「飼料暫放區」沿黑線運到對應顏色的放置區。飼料的正投影要在框線或圖案內才算分，不可以用手把飼料放到車上啟動。</p>
    {table(['飼料', '數量', '每個', '小計'], [
        ['紅色 → 紅色放置區', '16', '15 分', '240 分'],
        ['綠色 → 綠色放置區', '10', '20 分', '200 分'],
        ['藍色 → 藍色放置區', '6', '10 分', '60 分'],
        ['放錯顏色區', '—', '5 分', '—'],
        ['三色全部送對', '—', '—', '加 100 分，滿分 600'],
    ])}
    <p>運送途中失敗或沒進得分區，可以把沒得分的飼料拿回暫放區，再讓 C 車重跑。程式可以在比賽中修改、重新上傳，但時間照算。</p>
  </section>

  <section class="rg-section">
    <h2>二、場地與路線</h2>
    <div class="rg-grid-2">
      <div class="rg-svg-wrap"><img src="assets/img/r4m-basic-map.jpg" alt="R4M 基礎組場地底圖：中央黑色循跡環線，左側島形 C 車出發區，紅、綠、藍放置區分別在環線上方、右側與下方" width="500" style="max-width:100%;height:auto"></div>
      <div>
        <p>中央的黑色環線就是 C 車的路。左側島形框是 C 車出發區，飼料暫放區在它的左邊（西邊）。環線上有三條橫線，分別在三個放置區旁邊：</p>
        <ul>
          <li><strong>上方橫線</strong>：紅色放置區</li>
          <li><strong>右側橫線</strong>：綠色放置區</li>
          <li><strong>下方橫線</strong>：藍色放置區</li>
        </ul>
        <p>程式跑兩趟：</p>
        <ol>
          <li><strong>第一趟（紅色）</strong>：在出發區取料 → 往北順時針走 → 停在上方橫線 → 右轉進紅色放置區卸料 → 原地迴轉，循線回到出發區。</li>
          <li><strong>第二趟（藍＋綠）</strong>：再取料 → 往南逆時針走 → 停在下方橫線卸藍色 → 繼續走到右側橫線卸綠色 → 完成，畫面顯示 ✓。</li>
        </ol>
        <p>先送紅色，是因為紅色總分最高（240 分）。</p>
      </div>
    </div>
  </section>

  <section class="rg-section">
    <h2>三、按鍵與畫面</h2>
    {table(['操作', '作用'], [
        ['按 <strong>B</strong>', '開始任務（車子要先放在出發區、車頭朝北）'],
        ['按 <strong>A</strong>', '<strong>急停</strong>：馬上停車、閘門關上，畫面顯示 ✗'],
        ['<strong>搖一搖</strong>車子', '感測器檢查模式（15 秒）：畫面左、中、右三格會跟著三顆感測器亮，壓到黑線就亮'],
    ])}
    {table(['畫面', '意思'], [
        ['笑臉', '開機完成，等你按 B'],
        ['<code>1</code> / <code>2</code> / <code>3</code>', '目前進度：1＝第一趟、2＝紅色卸完、3＝回到出發區準備第二趟'],
        ['✓', '任務完成'],
        ['<code>T</code>', '逾時：一段路走了 20 秒還沒看到橫線，車子已停'],
        ['<code>L</code>', '找不到線（Lost），車子已停'],
        ['✗', '按了 A 急停'],
    ])}
  </section>

  <section class="rg-section">
    <h2>四、參數在哪裡改</h2>
    <p>所有要在場地上實測的數字都放在程式最上面的參數區。改完重新下載燒錄即可。</p>
    <h3>腳位與方向</h3>
    {table(['參數', '預設', '說明'], [
        ['<code>PIN_S_L / PIN_S_C / PIN_S_R</code>', 'P8 / P12 / P2', '左、中、右循跡感應器的腳位，依主控盒實際接線修改'],
        ['<code>有中央感測器</code>', 'true', '只裝兩顆感應器時改成 false（建議裝三顆，才偵測得到完全脫線）'],
        ['<code>黑</code>', '1', '壓到黑線時讀到的值；搖一搖檢查時亮暗相反，就改成 0'],
        ['<code>L_正轉 / R_正轉</code>', '1 / 1', '某一輪往後轉就把那一輪改成 0'],
        ['<code>PIN_GATE</code>', 'P1', '料斗閘門伺服馬達的腳位'],
    ])}
    <h3>速度</h3>
    {table(['參數', '預設', '說明'], [
        ['<code>V_直行</code>', '380', '循跡時的基礎速度（0～1023）'],
        ['<code>V_慢</code>', '260', '取料、進區、找線的慢速；所有「走幾公分」都用這個速度'],
        ['<code>V_轉外 / V_轉內</code>', '520 / −160', '偏離黑線時外側輪、內側輪的速度（內側負值＝倒轉，修正得更急）'],
        ['<code>V_原地</code>', '330', '原地旋轉的速度'],
    ])}
    <h3>里程與轉角校正（最重要）</h3>
    <p>C 車沒有編碼器，「走幾公分」「轉幾度」都是用時間換算的。<strong>換電池、換輪子、換場地後都要重新量</strong>。</p>
    {table(['參數', '預設', '怎麼量'], [
        ['<code>MS_每公分</code>', '38', '讓車以 <code>V_慢</code> 直行 3000 毫秒，量走了幾公分 D，<code>MS_每公分 = 3000 ÷ D</code>'],
        ['<code>MS_每度</code>', '7', '讓車以 <code>V_原地</code> 原地轉 2000 毫秒，看轉了幾度 A，<code>MS_每度 = 2000 ÷ A</code>'],
    ])}
    <h3>取料與卸料</h3>
    {table(['參數', '預設', '說明'], [
        ['<code>取料前進 / 取料後退</code>', '14 / 15 cm', '車頭轉向西後往前衝多少把飼料收進料斗、再退多少回到出發區'],
        ['<code>紅_微調 / 綠_微調 / 藍_微調</code>', '0', '停在橫線後先前進（＋）或後退（−）幾公分再轉彎，用來對準各放置區的中心'],
        ['<code>進區距離</code>', '6 cm', '轉向放置區後再前進多少'],
        ['<code>退出距離</code>', '22 cm', '卸完往後退多少。前方開口的推箱式料斗要大於料斗深度，飼料才留得在區內'],
        ['<code>閘_關 / 閘_紅 / 閘_綠 / 閘_藍</code>', '2400 / 1800 / 1400 / 1000', '閘門伺服的脈衝寬度（微秒），依料斗實際結構實測'],
        ['<code>逾時_毫秒</code>', '20000', '一段路超過這個時間還沒看到橫線就停車，顯示 T'],
    ])}
    <div class="rg-callout rg-callout-ok">
      <strong>微調值怎麼算：</strong>車子停在橫線上時，料斗中心在「橫線後方、感測器到料斗中心的距離」那裡。<br>
      微調值 ＝ 想讓料斗中心停的位置 − 橫線位置 ＋ 感測器到料斗的距離（先量自己的車：循跡感測器到料斗中心的前後距離）。
    </div>
  </section>

  <section class="rg-section">
    <h2>五、第一次上場地的調整順序</h2>
    <ol>
      <li><strong>搖一搖檢查感測器</strong>：三顆都要能分辨黑線和白底。亮暗相反就改 <code>黑</code>。</li>
      <li><strong>輪子架空按 B</strong>：兩輪都要往前轉，反了改 <code>L_正轉 / R_正轉</code>。</li>
      <li><strong>量 <code>MS_每公分</code> 和 <code>MS_每度</code></strong>，填回程式。</li>
      <li><strong>只跑第一趟</strong>：看取料是否收得到飼料、紅色區卸得準不準，調 <code>取料前進</code>、<code>紅_微調</code>、<code>進區距離</code>。</li>
      <li><strong>跑完整任務</strong>：再調藍、綠的微調值與閘門角度。</li>
      <li>每次改了什麼、改成多少，記在紙上；比賽現場改程式時間照算，準備好的數字可以直接填。</li>
    </ol>
    <div class="rg-callout rg-callout-warn">
      <strong>硬體限制：</strong>micro:bit V1 同時只能輸出 3 路 PWM，兩顆馬達加一顆閘門伺服剛好用滿；要加第二顆伺服請改用 V2 並實測。比賽規定 C 車主控盒須用 1269-W85-A1 或 1409-W85-A。
    </div>
  </section>''')

# ───────────────────────── FAQ ─────────────────────────
PAGES['faq.html'] = dict(
    title='常見問題', kicker='TROUBLESHOOTING · FAQ',
    h1='常見問題', dek='先看症狀、再查原因。大部分「怪問題」都是電池或拿錯遙控器。',
    body=f'''<section class="rg-section">
    <h2>A／B 車（KSB 搖桿）</h2>
    {table(['症狀', '先檢查', '處理'], [
        ['車子完全不動，中心閃爍', '遙控器有開嗎？是不是拿錯支？', '打開遙控器；看貼紙拿回自己那支，或重新配對'],
        ['遙控器一直震動', '車子有開嗎？電池有電嗎？距離太遠？', '打開車子、換電池；拿錯支就拿回自己那支'],
        ['搖桿放開，車子自己慢慢跑', '開機時手有沒有碰到搖桿？', '遙控器關機，手放開再開機'],
        ['車子會動，但動一下就頓住、時好時壞', '電池快沒電', '<strong>先換電池</strong>，不要先懷疑程式'],
        ['畫面出現 L', '開機時按著 A 和 B', '關機，手放開再開機'],
        ['重新燒錄後設定都不見了', '正常', '重做設定與配對'],
        ['按了鍵沒反應', '按太快，或在畫面捲動時按', '改成按住不放，等畫面出現該出現的東西'],
        ['想進設定，結果出現 P（進了配對）', '按成 A 了', '等 30 秒會自動取消（出現 ✗），原本的配對不會不見'],
        ['車子停在 P，遙控器開了也配不到', '遙控器沒進配對模式，或離太遠', '遙控器關機，拿到車子旁邊，按住 A 開機等到 P 出現'],
        ['別人的遙控器也能控我的車', '兩組同時配對又靠很近', '同一時間只讓一組配對，重新配對，再做交叉測試'],
        ['車子一直停在 P', '遙控器沒開，或遙控器燒的程式和車子不是同一批', '打開遙控器；請老師重燒遙控器'],
        ['某個機構沒力或會抖', '電池電量', '換電池；仍然如此請老師檢查'],
    ])}
  </section>

  <section class="rg-section">
    <h2>A／B 車（手機 V7RC）</h2>
    {table(['症狀', '處理'], [
        ['清單裡找不到車子', '確認車子有開、沒被別支手機連著；手機以前連過這台 → 藍牙設定「忘記此裝置」；都不是 → 請老師確認燒錄時有裝 V7RC 擴充套件'],
        ['連上了但車子不動', '手機 App 要選 Game ADV 介面'],
        ['不知道哪台是我的', '車子沒連線時按 A，看捲出來的藍牙名稱'],
        ['手機一鎖螢幕車子就停', '正常的安全設計，螢幕保持亮著'],
        ['別隊連到我的車', '先連先贏：開機後立刻用自己的手機連上'],
    ])}
  </section>

  <section class="rg-section">
    <h2>C 車（循跡）</h2>
    {table(['症狀', '原因', '處理'], [
        ['按 B 後車子原地打轉或亂走', '感測器讀值相反', '搖一搖檢查，亮暗相反就把 <code>黑</code> 改成 0'],
        ['往後退而不是往前', '馬達方向相反', '改 <code>L_正轉</code> 或 <code>R_正轉</code>'],
        ['畫面顯示 T 後停車', '一段路超過 20 秒沒看到橫線', '確認三顆感測器都壓得到橫線；速度太慢就調高 <code>V_直行</code>'],
        ['畫面顯示 L 後停車', '卸料或迴轉後找不到黑線', '檢查 <code>MS_每度</code>（轉角不準會偏離太遠）與 <code>退出距離</code>'],
        ['取料、卸料的位置每次都差一點', '里程換算不準', '重新量 <code>MS_每公分</code>、<code>MS_每度</code>；換電池後也要重量'],
        ['卸料後飼料又被帶出來', '退出距離小於料斗深度', '加大 <code>退出距離</code>'],
        ['跑到一半要停', '—', '按 <strong>A</strong> 急停'],
    ])}
  </section>

  <section class="rg-section">
    <h2>燒錄</h2>
    {table(['症狀', '處理'], [
        ['出現 <code>Cannot find name \'flashstorage\'</code>', '擴充功能貼上 <code>github:bsiever/microbit-pxt-flashstorage</code>'],
        ['出現 <code>Cannot find name \'KSB045\'</code>', '擴充功能貼上 <code>github:lioujj/pxt-KSB045</code>'],
        ['出現 <code>Cannot find name \'bluetooth\'</code> 或 V7RC 相關紅字', '擴充功能貼上 <code>github:lioujj/pxt-V7RC</code>（會自動帶入藍牙）'],
        ['裝 V7RC 時跳出要移除 radio', '按確定，藍牙和 radio 不能同時用'],
    ])}
  </section>''')

# ───────────────────────── 老師專區 ─────────────────────────
PAGES['tech.html'] = dict(
    title='老師專區', kicker='FOR COACHES · ARCHITECTURE · TUNING',
    h1='老師專區：程式架構與調校', dek='腳位、訊號隔離、可調常數、決賽鎖定與封包探測器。選手不需要看這一頁。',
    body=f'''<section class="rg-section">
    <h2>一、兩套遙控的差別</h2>
    {table(['', 'V7RC（手機）', 'KSB 搖桿（micro:bit radio）'], [
        ['傳輸', 'BLE 藍牙，點對點連線', '2.4GHz 廣播'],
        ['別校干擾', '不會（手機獨佔一台車）', '會，靠頻段、封包名、配對三層隔離'],
        ['現場的問題', '「哪一台是我的」→ 按 A 看藍牙名稱', '「別人的訊號會進來」→ 配對＋交叉測試'],
        ['同一支程式並用', '不行：MakeCode 啟用藍牙後 radio 會被移除', '—'],
    ])}
  </section>

  <section class="rg-section">
    <h2>二、主控盒腳位</h2>
    {table(['主控盒', '左輪（方向／速度）', '右輪', '機構 1', '機構 2'], [
        ['<strong>1269</strong>', 'P13 / P14', 'P15 / P16', 'P12 / P2', 'P1 / P8'],
        ['<strong>1409</strong>', 'P15 / P14', 'P0 / P16', 'P13 / P8', 'P2 / P1'],
    ])}
    <ul>
      <li>兩組腳位表都內建在程式裡，開機選單選主控盒即可切換。</li>
      <li>第 4 組馬達的速度腳在 B 車就是閘門伺服腳（1269 → P8，1409 → P1）。B 車不驅動第 4 組，那支腳就是乾淨的伺服腳，不必改接線。</li>
      <li>B 車實際使用 3 馬達＋1 伺服＝4 路 PWM，剛好是 micro:bit V2 的上限。</li>
      <li><strong>馬達停止時類比寫 0，不釋放 PWM 通道。</strong>micro:bit V2 是輪流分配 PWM 通道，一支腳放掉通道後再要，可能搶走別支腳正在用的通道，被搶的機構會突然沒力（升降往下掉）。每台車剛好 4 支 PWM 腳，各自佔住一個通道就不會互搶。</li>
      <li>速度最大寫到 1000（不寫滿 1023），保留一點關斷時間給馬達驅動晶片。</li>
      <li><strong>micro:bit 所有 PWM 輸出共用同一個頻率</strong>，車上有伺服就不能改 PWM 頻率。兩台車都使用預設 50Hz。</li>
    </ul>
  </section>

  <section class="rg-section">
    <h2>三、馬達方向預設值</h2>
    {table(['組合', '狀態'], [
        ['1409 ＋ V7RC', '✔ 實車驗證'],
        ['1269 ＋ V7RC', '✔ 實車驗證'],
        ['1269 ＋ KSB 搖桿', '✔ 與實際輸出逐項比對一致'],
        ['1409 ＋ KSB 搖桿', '⚠ 由上面三項推得，<strong>第一次試車要確認</strong>'],
    ])}
    <p>兩種主控盒的輪子方向其實一樣，差別在遙控器：KSB 搖桿往上推數值變小，V7RC 往上推數值變大。所以 V7RC 版兩組都是 <code>[true, false, …]</code>，KSB 版兩組都是 <code>[false, true, …]</code> 再加上 <code>反轉_轉向 = true</code>。某台盒子接線不同時，單獨改 <code>反轉_1269</code> 或 <code>反轉_1409</code>。</p>
    <h3>第一次試車的順序</h3>
    <ol>
      <li>輪子架空。</li>
      <li>搖桿往前：兩輪都要往前轉。哪一輪反了，改這台主控盒那一組的第 0 格（左）或第 1 格（右）。</li>
      <li>搖桿往右：車子要往右轉，反了改 <code>反轉_轉向</code>。</li>
      <li>機構鍵：升降與夾爪方向不對，改第 2 格／第 3 格。</li>
      <li>落地跑一圈，再調 <code>曲線量</code> 和 <code>全域限速</code>。</li>
    </ol>
  </section>

  <section class="rg-section">
    <h2>四、可調常數（車端 01、04 共用）</h2>
    {table(['常數', '預設', '什麼時候調'], [
        ['<code>死區</code>', 'V7RC 8／KSB 6', '手放開車子會微微動 → 調大（V7RC 搖桿交叉漂移實測可到 6.6）'],
        ['<code>曲線量</code>', '0.40', '對位太敏感 → 調大到 0.5～0.6'],
        ['<code>全域限速</code>', '100 %', '場地小、太快撞出界 → 調到 70～80'],
        ['<code>對位慢速</code>', '45 %', '對位還是太快 → 調小'],
        ['<code>機構作動時降速</code>', 'true', '想邊走邊升降搶時間 → 改 false'],
        ['<code>微調轉速</code>', '20 %', '微調轉不動 → 調大；一下轉太多 → 調小（實測 35、25 都太多）'],
        ['<code>微調最短毫秒</code>', '40', '點按沒反應 → 調大（120、80 實測一下會轉 5～8 度）'],
        ['<code>微調覆蓋搖桿</code>', 'true', '想邊走邊用搖桿轉向又同時微調 → 改 false'],
        ['<code>方向鍵門檻</code>（V7RC）', '50', '↖ ↗ 不好按、常變成升降 → 調小到 30'],
        ['<code>機構升速 / 機構降速</code>', '60 / 35 %', '升過頭撞頂 → 升速調小；下降太快砸到東西 → 降速調小'],
        ['<code>夾爪力道</code>', '70 %', '夾太用力打滑 → 調小'],
        ['<code>斜率</code>', '12', '起步頓一下、板子重開 → 調小到 8'],
        ['<code>馬達最低</code>', '190', '低速時馬達不會轉 → 調大'],
        ['<code>閘門角_關 / 閘門角_開</code>', '0 / 100', '閘門沒關緊或頂到 → 微調'],
        ['<code>斷線毫秒</code>', '300', '沒收到封包超過這麼久就全停'],
    ])}
  </section>

  <section class="rg-section">
    <h2>五、決賽鎖定</h2>
    <p>車端程式（01、04）最上面有一段鎖定設定。決賽前改成 <code>true</code> 並寫死車編號、主控盒，開機選單就不會被誤按改掉；配對入口仍保留，方便臨時換遙控器。</p>
    <div class="rg-svg-wrap"><pre>const 鎖定設定: boolean = false      // 決賽前改成 true
const 鎖定_車編號: string = "A"      // "A" 或 "B"
const 鎖定_主控盒: number = 1269     // 1269 或 1409</pre></div>
    <p>型別標註（<code>: number</code>、<code>: string</code>）不能刪，刪掉後改值會編譯錯誤。</p>
  </section>

  <section class="rg-section">
    <h2>六、KSB 訊號隔離細節</h2>
    <ul>
      <li>群組固定 173，封包名稱固定 <code>R4</code>，遙控器每 30ms 送一包，一包帶搖桿與 7 顆按鍵的完整狀態。</li>
      <li>頻段由遙控器晶片序號算出：<code>((序號 ^ (序號 &gt;&gt; 16)) &amp; 0xFFFF) % 14</code>，對應 14 個避開 WiFi 1／6／11 與藍牙廣播頻道的頻段：22–24、48–51、72–78。</li>
      <li>雙向配對：車子與遙控器都切到配對專用頻道（band 7、群組 174）。遙控器以最小功率（0）送 <code>R4P</code>，所以只有近距離收得到；車子收到後記下序號存 Flash，回送 <code>R4OK</code>（數值＝遙控器序號），遙控器顯示 ✓。正常操控中的遙控器不送配對封包，不會被別台車配走。</li>
      <li>遙控器開機按住 A 滿 2 秒才進配對，避免誤觸；兩邊逾時都是 30 秒。若還是會配到遠處的遙控器，把車端 <code>配對最弱訊號</code>（預設 -128＝不限制）改成 -70 左右；要貼很近才配得到時，把遙控器 <code>配對功率</code> 改成 2。</li>
      <li>車子每 500ms 回報一次給遙控器；遙控器 1.2 秒沒收到就震動警告。</li>
      <li>主辦要求固定頻段時，遙控器與車子都按住 A＋B 開機（顯示 L），全部固定在 band 7，配對照樣有效。</li>
    </ul>
  </section>

  <section class="rg-section">
    <h2>七、V7RC 封包與探測器</h2>
    <p>Game ADV 介面送出 <code>SRT</code> 開頭、19 字元的封包，每秒約 33 包；四個通道 1000–1500–2000：通道 1 左搖桿左右、通道 2 左搖桿上下、通道 3 方向鍵上下、通道 4 方向鍵左右。放開時回到 <code>SRT1500150015001500</code>。</p>
    <p>改用其他 V7RC 介面前，先燒 <code>{DL["probe"]}</code>（<a href="downloads/{DL["probe"]}" download>下載</a>）測一次通道順序與數值範圍，再改車端程式頂端的 <code>CH_</code> 通道設定。</p>
  </section>

  <section class="rg-section">
    <h2>八、待實測項目</h2>
    <ul>
      <li>1409 ＋ KSB 搖桿的馬達方向。</li>
      <li>B 車行走時閘門會不會抖、會不會自己動。</li>
      <li>KSB 雙向配對：最小功率下的有效距離，以及兩組相鄰配對時的交叉測試。</li>
      <li>V7RC 的 ↖ ↗ 好不好按；<code>微調轉速</code>、<code>微調最短毫秒</code> 依選手習慣微調。</li>
      <li>C 車全部參數（里程、轉角、取料、卸料、閘門角度）都需要在場地上實測。</li>
    </ul>
  </section>''')


def main():
    for rel, p in PAGES.items():
        html = (TEMPLATE.replace('__TITLE__', p['title']).replace('__KICKER__', p['kicker'])
                .replace('__H1__', p['h1']).replace('__DEK__', p['dek'])
                .replace('__BODY__', p['body']).replace('__ROOT__', ''))
        out = SITE / rel
        old = out.read_text(encoding='utf-8') if out.exists() else None
        # 保留 build_site.py 已注入的區塊時仍以原稿為準，再交給 build_site.py 重新注入
        out.write_text(html, encoding='utf-8')
        print(('更新' if old else '新增'), rel)


if __name__ == '__main__':
    main()
