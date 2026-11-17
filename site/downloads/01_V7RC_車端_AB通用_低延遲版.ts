// ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ┃ 貼上程式「之前」先做完這幾項，否則會出現 Cannot find name 'xxx' 的紅字
// ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//   □ V7RC         擴展 → 搜尋框貼上 github:lioujj/pxt-V7RC
//                  → 跳出「要移除 radio」→ 按確定（正常，藍牙和 radio 不能並存）
//                  ★ 一定要裝 V7RC，不要只裝 bluetooth！
//                    V7RC 擴充套件會自動把藍牙設成「免配對、對所有手機廣播」；
//                    只裝 bluetooth 的話，手機 App 會「找不到」這顆 micro:bit。
//   □ flashstorage 擴展 → 搜尋框貼上 github:bsiever/microbit-pxt-flashstorage
// 做完後：右上角切到「JavaScript」→ 全選刪除 → 貼上本檔

/**********************************************************************
 *  R4M 車端（A車夾車 / B車推扒車 通用） — V7RC 低延遲版  v2.4 / 2026
 *  車城科技中心
 *
 *  ★ 一支程式通吃：A車 / B車、智高 1269 / 1409 主控盒
 *    全部在開機選單設定並寫入 Flash，所以「絕對不會灌錯機器人」。
 *
 *  ══════════════ 操 控 佈 局（V7RC「Game ADV」介面）══════════════
 *
 *    左類比搖桿                     右八向方向鍵
 *    ────────────                   ──────────────
 *    ↕  前後（類比，可微調力道）        ↑   升降 上
 *    ↔  轉向（類比，大幅轉向用）        ↓   升降 下
 *                                    ←   左微調（固定小轉速）
 *                                    →   右微調（固定小轉速）
 *                                    ↖   A車 夾爪張開 / B車 閘門關
 *                                    ↗   A車 夾爪閉合 / B車 閘門開
 *                                    ↙ ↘ 保留（見「方向碼」區）
 *
 *    這等於把 KSB 搖桿的 E / C / F / D / A / B 六顆鍵搬到方向鍵上。
 *    左右微調是「固定轉速」，所以不會像推類比搖桿那樣一不小心就轉過頭；
 *    而且「點一下馬上放」也保證至少轉一個固定小角度（微調最短毫秒）。
 *
 *  ══════════════ 通 道 對 應 ══════════════
 *    通道1 ← 左搖桿 水平   連續值 1000–1500–2000
 *    通道2 ← 左搖桿 垂直   連續值
 *    通道3 ← 右方向鍵 上下 只有三段：1000 / 1500 / 2000
 *    通道4 ← 右方向鍵 左右 只有三段
 *
 *    八個方向是由 通道3、通道4 的組合解出來的（見 方向碼()），
 *    所以同一時間只會有一個方向成立，不會兩個機構一起亂動。
 *
 *  ══════════════ 開 機 操 作 ══════════════
 *   開機 3 秒內按 B → 設定選單，兩頁，每頁按 A 或 B 直接選：
 *       第 1 頁  CAR ：按 A ＝ A車(夾車)    按 B ＝ B車(推扒車)
 *       第 2 頁  BOX ：按 A ＝ 1269 主控盒  按 B ＝ 1409 主控盒
 *     選完自動存檔離開（顯示 ✓）
 *   平時開機會先捲出「車編號 + 主控盒」，確認無誤再上場。
 *   還沒連上手機時按 A → 捲出這台的藍牙名稱（例如 zuvat），在 V7RC 清單裡找這個名字
 *
 *  ══════════════ 怎 麼 燒 ══════════════
 *   1. MakeCode 新專案 → 擴充套件加入 V7RC（github:lioujj/pxt-V7RC）
 *      它會自動帶入 bluetooth，並把藍牙設成「免配對、對所有手機廣播」——手機才找得到。
 *      只裝 bluetooth 是不夠的（預設要先配對，沒配對過的手機看不到它）。
 *      不需要 RoboticsWorkshop，本程式直接控腳位。
 *   2. 再加入 flashstorage（github:bsiever/microbit-pxt-flashstorage）
 *   3. 切「JavaScript」→ 全選刪除 → 貼上 → 燒錄
 *   4. 手機 V7RC → Game ADV 介面 → 連線
 *
 *  ══════════════ 不 卡 頓 的 七 個 設 計 ══════════════
 *   1. 藍牙事件只解析存值，絕不 pause / show / 寫馬達；而且一開機就登記（見「藍牙接收」區）
 *   2. 馬達輸出集中在單一 20ms 控制迴圈；數值沒變就不重寫腳位
 *   3. charCodeAt 手動解析，零字串配置（不用 substr / parseInt）
 *   4. 馬達 PWM 維持 micro:bit 預設 50Hz（實測比 1kHz 有力、沒有電流嘯叫，B 車伺服也只能用 50Hz）
 *   5. 停止時用 digitalWrite 釋放 PWM 通道
 *   6. 加速斜坡，避免瞬間全速拉垮電池 → 板子重開／藍牙斷線
 *   7. 看門狗：300ms 沒封包就全停
 *
 *  Game ADV 實測（2026-10-13，封包探測器）：前綴 SRT、19 字元、每秒約 33 包（≈30ms 一包），
 *  四個通道的順序與正負號都與本程式的 CH_ 設定一致。另外也相容 SRV / SS8。
 *
 *  ※ 車端請用 micro:bit V2
 *  ※ 需要擴充套件 flashstorage：擴充套件 → 貼上 github:bsiever/microbit-pxt-flashstorage
 **********************************************************************/


// ═══════════════════ 決 賽 鎖 定 模 式 ═══════════════════
//  平時（練習、多隊共用器材）：鎖定設定 = false → 開機選單可調，存 Flash
//  決賽（晶片與選手都固定）：鎖定設定 = true，並填好下面兩個值
//      → 完全忽略 Flash 與選單，選手就算誤按 B 也改不掉任何東西

const 鎖定設定: boolean = false
const 鎖定_車編號: string = "A"      // "A" 或 "B"
const 鎖定_主控盒: number = 1409     // 1269 或 1409（一定要寫「: number」，否則改值時會編譯錯誤）


// ═══════════════════ 調 校 區 ═══════════════════

const 死區 = 8              // 左搖桿死區（±100 尺度）
//                            實測：推純左右時另一軸會漂到 ±6.6（原始值 1467），死區要大於這個值
const 曲線量 = 0.40         // 0=線性；越大低速越細膩，建議 0.3~0.6
const 全域限速 = 100        // % 行走最高速
const 對位慢速 = 45         // % 機構作動或微調時，行走自動降到這個速度
const 機構作動時降速 = true // false：升降、夾爪動作時不自動降速（想邊走邊升降搶時間時用）

// 左右微調（取代 KSB 的 F / D 鍵）
const 微調轉速 = 35         // % 固定轉速，相當於 KSB 的 T_override = 300
const 微調最短毫秒 = 120    // 點一下馬上放，也保證轉這麼久（點按定量）
const 微調覆蓋搖桿 = true   // true：微調時完全取代搖桿轉向（與 KSB 行為相同）
//                            false：微調量疊加在搖桿轉向之上

const 機構升速 = 100        // % 升降／耙子 上升
const 機構降速 = 45         // % 升降／耙子 下降（防重力加速）
const 夾爪力道 = 70         // % A車夾爪

const 斜率 = 12             // 每 20ms 行走指令最多變化量（越小越柔、越護電池）
const 馬達最低 = 190        // 克服靜摩擦的最低 PWM（0~1023）
// PWM 頻率：A、B 車都用 micro:bit 預設的 50Hz（2026-10-14 實車比較後定案）
//   v2.3 以前 A 車用 1kHz → 實測有高頻電流嘯叫，而且比 50Hz 的 B 車沒力。
//   ※ micro:bit 所有 PWM 腳共用同一個頻率，B 車的閘門伺服本來就只能用 50Hz。
const 控制週期 = 20         // ms
const 斷線毫秒 = 300        // 沒封包超過這麼久 → 全停

const 方向鍵門檻 = 50       // 通道3/4 超過這個量才算「有按」（±100 尺度）

// B車閘門（伺服，接在第 4 組馬達的速度腳上：1269→P8，1409→P1）
const 閘門角_關 = 0
const 閘門角_開 = 100

// 馬達方向：[0]左輪 [1]右輪 [2]升降/耙子 [3]夾爪 —— 方向反了就把該格 true / false 對調
//   ‧ 1409＋V7RC ✔ 實車驗證（與舊版推吊車程式相同）
//   ‧ 1269＋V7RC ✔ 實車驗證（2026-10-14）——結果兩種主控盒的輪子方向其實一樣
//     （以前以為不同，是因為 KSB 搖桿「往上推數值變小」，跟 V7RC 相反；差別在遙控器，不在主控盒）
//   保留兩組是為了萬一某台盒子接線不同，可以單獨改
const 反轉_1269: boolean[] = [true, false, false, false]
const 反轉_1409: boolean[] = [true, false, false, false]
// 轉向正負號只跟「遙控器」有關，跟主控盒無關。V7RC 用 false（與舊版程式一致）
const 反轉_轉向: boolean = false


// ═══════════════════ 通 道 對 應 ═══════════════════
//  若實測發現通道順序不同（用封包探測器測），只改這四個數字

const CH_轉向 = 0           // 左搖桿 水平（類比）
const CH_前後 = 1           // 左搖桿 垂直（類比）
const CH_鍵縱 = 2           // 右方向鍵 上下（三段）
const CH_鍵橫 = 3           // 右方向鍵 左右（三段）
const CH_慢速 = 4           // 只有 8 通道模式（SS8）才有


// ═══════════════════ 方 向 碼 ═══════════════════
//  把 (通道3, 通道4) 解成單一方向，所以同時只有一個動作成立
//
//        8 ↖   1 ↑   2 ↗
//        7 ←   0 ‧   3 →
//        6 ↙   5 ↓   4 ↘
//
//  目前指派：
//      1 ↑ 機構上升    5 ↓ 機構下降
//      7 ← 左微調      3 → 右微調
//      8 ↖ 夾爪張開 / 閘門關      2 ↗ 夾爪閉合 / 閘門開
//      6 ↙ 、 4 ↘ 保留（要加功能就在主迴圈的 dir == 6 / dir == 4 處理）

const D_無 = 0
const D_上 = 1
const D_右上 = 2
const D_右 = 3
const D_右下 = 4
const D_下 = 5
const D_左下 = 6
const D_左 = 7
const D_左上 = 8


// ═══════════════════ 狀 態 ═══════════════════

const K_CAR = "R4MCAR"
const K_BOX = "R4MBOX"

// ═══════════════════ Flash 存取 ═══════════════════
//  使用擴充套件 microbit-pxt-flashstorage（作者 bsiever）
//      擴充套件 → 貼上網址：github:bsiever/microbit-pxt-flashstorage
//  它只能存「字串」，所以這裡包成 存數字 / 讀數字，程式其他地方不用管細節。
//  ※ 重新燒錄程式後 Flash 可能被清空 → 開機會自動進設定選單，重設一次即可。

function 已存(key: string): boolean {
    const s = flashstorage.get(key)
    return s != null && s.length > 0       // 實機沒存過回傳空字串；模擬器會回傳 undefined
}

function 讀數字(key: string): number {
    if (!已存(key)) return 0
    const v = parseInt(flashstorage.get(key))
    return isNaN(v) ? 0 : v
}

function 存數字(key: string, n: number) {
    flashstorage.put(key, "" + n)
}

const PWM滿 = 1023

let 車編號 = "A"
let 主控盒 = 1269
let 馬達數 = 4
let 反轉: boolean[] = 反轉_1409

let 方向腳: DigitalPin[] = []
let 速度腳: AnalogPin[] = []
let 速度腳D: DigitalPin[] = []
let 閘門腳 = AnalogPin.P8
let 閘門腳D = DigitalPin.P8

let ch: number[] = [0, 0, 0, 0, 0, 0, 0, 0]   // 統一成 -100 ~ +100
let 上次輸出: number[] = [0, 0, 0, 0]
let 上次收到 = 0
let 平滑_前後 = 0
let 平滑_轉向 = 0
let 閘門角 = 閘門角_關
let 上次閘門角 = -1

let 微調方向 = 0            // -1 左、0 無、+1 右
let 微調到期 = 0            // 這個時間點之前，微調都算有效


// ═══════════════════ 腳 位 表 ═══════════════════
//  智高 1269 主控盒（方向 / 速度）
//      左 P13/P14   右 P15/P16   升降 P12/P2   夾爪 P1/P8
//  智高 1409 主控盒（RoboticsWorkshop DDM，取 C D B A 四組）
//      左 P15/P14   右 P0/P16    升降 P13/P8   夾爪 P2/P1
//  兩種盒子的共同點：第 4 組的「速度腳」在 B 車就是閘門伺服腳。

function 套用腳位() {
    if (主控盒 == 1409) {
        方向腳 = [DigitalPin.P15, DigitalPin.P0, DigitalPin.P13, DigitalPin.P2]
        速度腳 = [AnalogPin.P14, AnalogPin.P16, AnalogPin.P8, AnalogPin.P1]
        速度腳D = [DigitalPin.P14, DigitalPin.P16, DigitalPin.P8, DigitalPin.P1]
    } else {
        方向腳 = [DigitalPin.P13, DigitalPin.P15, DigitalPin.P12, DigitalPin.P1]
        速度腳 = [AnalogPin.P14, AnalogPin.P16, AnalogPin.P2, AnalogPin.P8]
        速度腳D = [DigitalPin.P14, DigitalPin.P16, DigitalPin.P2, DigitalPin.P8]
    }
    閘門腳 = 速度腳[3]
    閘門腳D = 速度腳D[3]
    馬達數 = 車編號 == "A" ? 4 : 3      // B車第 4 組讓給閘門伺服，完全不驅動
    反轉 = 主控盒 == 1409 ? 反轉_1409 : 反轉_1269
}


// ═══════════════════ 封 包 解 析（零字串配置）═══════════════════

function hex1(c: number): number {
    if (c >= 48 && c <= 57) return c - 48       // 0-9
    if (c >= 97 && c <= 102) return c - 87      // a-f
    if (c >= 65 && c <= 70) return c - 55       // A-F
    return -1
}

function 解析(s: string) {
    if (s.length < 19) return
    if (s.length > 19) s = s.substr(s.length - 19)   // 前面黏到殘渣時，只取最後一包（正常情況不會配置新字串）
    const c0 = s.charCodeAt(0)
    const c1 = s.charCodeAt(1)
    const c2 = s.charCodeAt(2)

    // ── SRT(坦克 / Game ADV) / SRV(車輛)：4 通道 × 4 位十進位 ──
    if (c0 == 83 && c1 == 82 && (c2 == 84 || c2 == 86)) {
        for (let i = 0; i < 4; i++) {
            const p = 3 + i * 4
            const v = (s.charCodeAt(p) - 48) * 1000
                + (s.charCodeAt(p + 1) - 48) * 100
                + (s.charCodeAt(p + 2) - 48) * 10
                + (s.charCodeAt(p + 3) - 48)
            if (v < 900 || v > 2100) return      // 封包壞了，整包丟掉
            ch[i] = Math.clamp(-100, 100, (v - 1500) / 5)
        }
        for (let i = 4; i < 8; i++) ch[i] = 0     // 4 通道模式沒有 5~8，清掉免得殘留 SS8 的舊值
        上次收到 = input.runningTime()
        return
    }

    // ── SS8(專家 / BOT)：8 通道 × 2 位十六進位 ──
    if (c0 == 83 && c1 == 83 && c2 == 56) {
        for (let i = 0; i < 8; i++) {
            const p = 3 + i * 2
            const h = hex1(s.charCodeAt(p))
            const l = hex1(s.charCodeAt(p + 1))
            if (h < 0 || l < 0) return
            ch[i] = Math.clamp(-100, 100, (h * 16 + l - 150) * 2)
        }
        上次收到 = input.runningTime()
        return
    }
}


// ═══════════════════ 方 向 鍵 解 碼 ═══════════════════

function 方向碼(): number {
    const 上 = ch[CH_鍵縱] > 方向鍵門檻
    const 下 = ch[CH_鍵縱] < -方向鍵門檻
    const 右 = ch[CH_鍵橫] > 方向鍵門檻
    const 左 = ch[CH_鍵橫] < -方向鍵門檻

    if (上 && 右) return D_右上
    if (上 && 左) return D_左上
    if (下 && 右) return D_右下
    if (下 && 左) return D_左下
    if (上) return D_上
    if (下) return D_下
    if (右) return D_右
    if (左) return D_左
    return D_無
}


// ═══════════════════ 訊 號 整 形 ═══════════════════

// 死區 + 指數曲線：低速細膩、全推仍是滿速
function 整形(v: number): number {
    const a = Math.abs(v)
    if (a < 死區) return 0
    let x = (a - 死區) / (100 - 死區)
    if (x > 1) x = 1
    const y = (1 - 曲線量) * x + 曲線量 * x * x * x
    return (v > 0 ? 1 : -1) * y * 100
}

// 斜坡：每個控制週期最多變化 step，護電池也讓手感線性
function 逼近(現值: number, 目標: number, step: number): number {
    if (目標 > 現值 + step) return 現值 + step
    if (目標 < 現值 - step) return 現值 - step
    return 目標
}


// ═══════════════════ 馬 達 與 伺 服 輸 出 ═══════════════════

function 輸出(i: number, cmd: number) {
    let v = Math.round(Math.clamp(-100, 100, cmd))
    if (反轉[i]) v = -v

    const 前值 = 上次輸出[i]
    if (v == 前值) return                        // 沒變就不寫腳位（省 CPU）
    上次輸出[i] = v

    if (v == 0) {
        // 數位寫 0（不是類比寫 0）→ 把 PWM 通道還給系統
        pins.digitalWritePin(速度腳D[i], 0)
        pins.digitalWritePin(方向腳[i], 0)
        return
    }

    const mag = 馬達最低 + Math.idiv((PWM滿 - 馬達最低) * Math.abs(v), 100)
    pins.digitalWritePin(方向腳[i], v > 0 ? 1 : 0)
    pins.analogWritePin(速度腳[i], mag)
}

// 混控 + 飽和等比縮放（全速直行時仍保有轉向權限）
function 移動(前後: number, 轉向: number) {
    if (反轉_轉向) 轉向 = -轉向
    let l = 前後 + 轉向
    let r = 前後 - 轉向
    const peak = Math.max(Math.abs(l), Math.abs(r))
    if (peak > 100) {
        l = l * 100 / peak
        r = r * 100 / peak
    }
    輸出(0, l)
    輸出(1, r)
}

function 更新閘門() {
    if (閘門角 != 上次閘門角) {
        pins.servoWritePin(閘門腳, 閘門角)
        上次閘門角 = 閘門角
    }
}

function 全停() {
    平滑_前後 = 0
    平滑_轉向 = 0
    微調方向 = 0
    微調到期 = 0
    for (let i = 0; i < 馬達數; i++) 輸出(i, 0)
    // 注意：不碰閘門伺服，失聯時閘門維持現狀，不會掉落
}


// ═══════════════════ 設 定 選 單 ═══════════════════

// 等使用者按 A 或 B，回傳 true = 按了 A，false = 按了 B
function 等待選擇(標題: string): boolean {
    basic.showString(標題)
    while (true) {
        if (input.buttonIsPressed(Button.A)) { basic.pause(250); return true }
        if (input.buttonIsPressed(Button.B)) { basic.pause(250); return false }
        basic.pause(25)
    }
}

function 設定選單() {
    車編號 = 等待選擇("CAR") ? "A" : "B"
    basic.showString(車編號)
    basic.pause(400)

    主控盒 = 等待選擇("BOX") ? 1269 : 1409
    basic.showNumber(主控盒)

    存數字(K_CAR, 車編號 == "B" ? 1 : 0)
    存數字(K_BOX, 主控盒)
    basic.showIcon(IconNames.Yes)
    basic.pause(500)
    basic.clearScreen()
}


// ═══════════════════ 藍 牙 接 收（必須放在開機選單「之前」）═══════════════════
//  ★ 2026-10-13 實測抓到的 bug：
//    V7RC 擴充套件在「開機的第一瞬間」就把藍牙打開，手機可以馬上連線並開始送封包。
//    如果收封包的事件要等開機選單跑完才登記，這段時間的封包會塞滿接收緩衝區（61 bytes，
//    只要約 0.1 秒），而 micro:bit 系統在緩衝區滿了之後會把新資料直接丟掉、也不再發出事件
//    → 事件永遠不會觸發，車子永遠收不到指令（中間的燈一直閃）。
//    所以事件一開機就登記，開機流程還沒跑完時照樣把封包讀出來（清掉緩衝區），只是先不用。

let 就緒 = false
bluetooth.setTransmitPower(7)
bluetooth.startUartService()

// 事件處理器：只解析、只存值，做完立刻返回（這裡絕對不能有 pause / show）
bluetooth.onUartDataReceived(serial.delimiters(Delimiters.Hash), function () {
    const s = bluetooth.uartReadUntil(serial.delimiters(Delimiters.Hash))   // 一定要讀，緩衝區才不會塞住
    if (就緒) 解析(s)
})


// ═══════════════════ 開 機 流 程 ═══════════════════

if (鎖定設定) {
    // ── 決賽模式：值寫死在程式裡，選手動不了 ──
    車編號 = 鎖定_車編號
    主控盒 = 鎖定_主控盒 == 1409 ? 1409 : 1269
    basic.showString(車編號)
    basic.showNumber(主控盒)
} else {
    // ── 平時模式：讀 Flash，開機 3 秒內按 B 可進選單 ──
    let 有記錄 = false
    if (已存(K_CAR)) {
        車編號 = 讀數字(K_CAR) == 1 ? "B" : "A"
        有記錄 = true
    }
    if (已存(K_BOX)) 主控盒 = 讀數字(K_BOX)
    if (主控盒 != 1409) 主控盒 = 1269

    basic.showString(車編號)
    basic.showNumber(主控盒)

    let 進選單 = !有記錄
    const t0 = input.runningTime()
    while (!進選單 && input.runningTime() - t0 < 3000) {
        if (input.buttonIsPressed(Button.B)) 進選單 = true
        basic.pause(25)
    }
    if (進選單) 設定選單()
}

套用腳位()

for (let i = 0; i < 4; i++) {
    pins.digitalWritePin(速度腳D[i], 0)
    pins.digitalWritePin(方向腳[i], 0)
    上次輸出[i] = 0
}
if (車編號 == "B") {
    pins.servoWritePin(閘門腳, 閘門角_關)
    上次閘門角 = 閘門角_關
}

就緒 = true                 // 從這一刻起，收到的封包才會拿來控制馬達
basic.clearScreen()


// ═══════════════════ 主 控 制 迴 圈（固定 20ms）═══════════════════

basic.forever(function () {
    const now = input.runningTime()

    // ── 看門狗：沒封包就全停 ──
    if (now - 上次收到 > 斷線毫秒) {
        全停()
        if (車編號 == "B") 更新閘門()
        // 沒連上時按 A：捲出藍牙名稱，方便在手機清單裡找到自己這台
        if (input.buttonIsPressed(Button.A)) {
            basic.showString(control.deviceName())
            basic.clearScreen()
        }
        if (now % 700 < 350) { led.plot(2, 2) } else { led.unplot(2, 2) }
        basic.pause(控制週期)
        return
    }
    led.plot(2, 2)

    // ── 解出方向鍵的單一方向 ──
    const dir = 方向碼()

    // ── 機構1：升降 / 耙子升降（↑ ↓）──
    let 機構 = 0
    if (dir == D_上) 機構 = 機構升速
    else if (dir == D_下) 機構 = -機構降速
    輸出(2, 機構)

    // ── 機構2：A車夾爪（↖ 張開、↗ 閉合）/ B車閘門（↖ 關、↗ 開）──
    let 機構2作動 = false
    if (車編號 == "A") {
        let 夾 = 0
        if (dir == D_左上) 夾 = 夾爪力道
        else if (dir == D_右上) 夾 = -夾爪力道
        輸出(3, 夾)
        機構2作動 = 夾 != 0
    } else {
        if (dir == D_右上) 閘門角 = 閘門角_開
        else if (dir == D_左上) 閘門角 = 閘門角_關
        更新閘門()
    }

    // ── 左右微調：固定轉速 ＋ 點按定量 ──
    //    按住時 微調到期 一直被往後推 → 持續有效
    //    點一下就放，也還會維持 微調最短毫秒，不會因為按太快而沒反應
    if (dir == D_右) {
        微調方向 = 1
        微調到期 = now + 微調最短毫秒
    } else if (dir == D_左) {
        微調方向 = -1
        微調到期 = now + 微調最短毫秒
    }
    const 微調中 = now < 微調到期

    // ── 保留方向（要加功能就寫在這裡）──
    // if (dir == D_左下) { ... }
    // if (dir == D_右下) { ... }

    // ── 行走：機構作動或微調時自動降速（R4M 對位時很好用）──
    const 機構在動 = 機構作動時降速 && (機構 != 0 || 機構2作動)
    const 限速 = (機構在動 || 微調中 || ch[CH_慢速] > 50) ? 對位慢速 : 全域限速

    let 轉向目標 = 整形(ch[CH_轉向]) * 限速 / 100
    if (微調中) {
        const 微調量 = 微調方向 * 微調轉速
        轉向目標 = 微調覆蓋搖桿 ? 微調量 : Math.clamp(-100, 100, 轉向目標 + 微調量)
    }

    平滑_前後 = 逼近(平滑_前後, 整形(ch[CH_前後]) * 限速 / 100, 斜率)
    平滑_轉向 = 逼近(平滑_轉向, 轉向目標, 斜率)
    移動(平滑_前後, 平滑_轉向)

    basic.pause(控制週期)
})
