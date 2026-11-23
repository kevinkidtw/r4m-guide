// ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ┃ 貼上程式「之前」先做完這幾項，否則會出現 Cannot find name 'xxx' 的紅字
// ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//   □ radio        新專案預設就有，不用另外加（若被移除過，擴展 → 搜尋 radio 加回）
//   □ flashstorage 擴展 → 搜尋框貼上 github:bsiever/microbit-pxt-flashstorage
// 做完後：右上角切到「JavaScript」→ 全選刪除 → 貼上本檔

/**********************************************************************
 *  R4M 車端（A車夾車 / B車推扒車 通用） — KSB 搖桿 radio 版  v3.1 / 2026
 *  車城科技中心
 *
 *  ★ 一支程式通吃：A車 / B車、智高 1269 / 1409 主控盒
 *    全部在開機選單設定並寫入 Flash，所以「絕對不會灌錯機器人」。
 *  ★ v3：沒有頻道碼。車子只認配對過的遙控器，頻段由那支遙控器的序號自動算出。
 *
 *  ══════════════ 開 機 操 作 ══════════════
 *   開機 3 秒內按 B → 設定選單，兩頁，每頁按 A 或 B 直接選：
 *       第 1 頁  CAR ：按 A ＝ A車(夾車)    按 B ＝ B車(推扒車)
 *       第 2 頁  BOX ：按 A ＝ 1269 主控盒  按 B ＝ 1409 主控盒
 *     選完自動存檔離開（顯示 ✓）
 *   開機 3 秒內按 A → 配對模式（顯示 P），接著：
 *        遙控器「按住 A 開機」→ 遙控器也顯示 P → 兩邊都出現 ✓ 就完成
 *        30 秒內沒配到 → 顯示 ✗ 並恢復原本的配對
 *   還沒配對過的車子 → 開機直接進配對模式，一直等到配好為止
 *   按住 A+B 開機   → 頻段鎖定在預設 7（主辦要求用預設頻段時才用；遙控器也要一樣）
 *   ★ 雙向配對：車子只接受「也在配對模式」的遙控器。
 *     平常開著的遙控器（正常操控中）絕對不會被別台車配走。
 *
 *  ══════════════ 訊 號 隔 離 ══════════════
 *   頻段  由遙控器序號自動算出 → 各隊分散在 14 個頻段，互相碰撞少
 *   群組  固定 = 控制群組      → 硬體層濾掉不是本系統的封包
 *   配對  只認配對過的遙控器晶片序號 → 真正的隔離靠這一層
 *   配對在專用的配對頻段／群組進行；遙控器用最小功率送配對訊號（只有近距離收得到），
 *   車子收到後回送確認，遙控器顯示 ✓。配好後車子固定在那支遙控器的頻段。
 *
 *  ══════════════ 按 鍵 對 應 ══════════════
 *   E / C     升降（A車）／耙子升降（B車）　上 / 下
 *   F / D     原地 左轉 / 右轉（固定小轉速，點一下也保證轉一個定量）
 *   A / B     A車：夾爪 張開 / 閉合　　B車：閘門 關 / 開
 *   搖桿按下  慢速模式
 *
 *  ══════════════ 顯 示 ══════════════
 *   中心亮＝連線正常　閃爍＝失聯(已全停)　P＝配對模式
 *
 *  【擴充套件】radio、flashstorage（不需要智高的馬達擴充套件，本程式直接控腳位）
 *  ※ 車端請用 micro:bit V2。V1 發射器可以控 V2 車子，沒有問題。
 *  ※ 遙控器要用 03 的 v3 版（v2 遙控器的封包格式不同，配不起來）
 **********************************************************************/


// ═══════════════════ 決 賽 鎖 定 模 式 ═══════════════════
//  平時（練習、多隊共用器材）：鎖定設定 = false
//      → 開機選單可調，設定存 Flash，現場不用電腦
//  決賽（晶片與選手都固定）：鎖定設定 = true，並填好下面兩個值
//      → 完全忽略 Flash 與選單，選手就算誤按 B 也改不掉任何東西
//      → 配對仍保留（開機 3 秒內按 A），以防現場臨時換遙控器

const 鎖定設定: boolean = false
const 鎖定_車編號: string = "A"      // "A" 或 "B"
const 鎖定_主控盒: number = 1269     // 1269 或 1409（一定要寫「: number」，否則改成 1409 以外的值會編譯錯誤）


// ═══════════════════ 調 校 區 ═══════════════════

const 死區 = 6              // ±100 尺度
const 曲線量 = 0.40         // 0=線性；越大低速越細膩
const 全域限速 = 100        // % 行走最高速
const 對位慢速 = 45         // % 慢速模式與機構作動時的行走速度
const 機構作動時降速 = true // false：升降、夾爪動作時不自動降速（想邊走邊升降搶時間時用）

// 左右微調（F / D 鍵）
const 微調轉速 = 20         // % 固定轉速（實測：35 太多 → 25 仍太多 → 20）
const 微調最短毫秒 = 40     // 點一下至少轉這麼久（點按定量；120 → 80 仍轉 5~8 度 → 40）
const 微調覆蓋搖桿 = true   // true：微調時完全取代搖桿轉向（與舊版 T_override 相同）
//                            false：微調量疊加在搖桿轉向之上
const 機構升速 = 60         // % 升降／耙子 上升（原 100，學生常升過頭撞頂）
const 機構降速 = 35         // % 升降／耙子 下降（防重力加速）
const 夾爪力道 = 70         // % A車夾爪

const 斜率 = 12             // 每 20ms 行走指令最多變化量
const 馬達最低 = 190        // 克服靜摩擦的最低 PWM（0~1023）
// PWM 頻率：A、B 車都用 micro:bit 預設的 50Hz（2026-10-14 實車比較後定案）
//   以前 A 車用 1kHz → 實測有高頻電流嘯叫，而且比 50Hz 的 B 車沒力。
//   ※ micro:bit 所有 PWM 腳共用同一個頻率，B 車的閘門伺服本來就只能用 50Hz。
const 控制週期 = 20         // ms
const 斷線毫秒 = 300        // 沒封包超過這麼久 → 全停
const 回報週期 = 500        // ms，回報給遙控器讓它知道車子還活著
const 配對逾時毫秒 = 30000  // 進配對後這麼久都沒收到遙控器 → 自動取消，恢復原本的配對
const 配對最弱訊號 = -128   // 配對時只接受比這個強的訊號（dBm，-128 = 不限制）。
//                            若還是會配到遠處的遙控器，可改成 -70 左右（越大越要靠近）

// B車閘門（伺服，接在第 4 組馬達的速度腳上：1269→P8，1409→P1）
const 閘門角_關 = 0
const 閘門角_開 = 100

// 馬達方向：[0]左輪 [1]右輪 [2]升降/耙子 [3]夾爪 —— 方向反了就把該格 true / false 對調
//   ‧ 1269＋KSB ✔ 與舊版 KSB 程式（全國賽版）的實際輸出完全相同
//   ‧ 1409＋KSB ⚠ 推算值，第一次試車務必確認
//     2026-10-14 實車發現：兩種主控盒的輪子方向其實一樣，差別在遙控器——
//     KSB 搖桿「往上推數值變小」，跟 V7RC 相反，所以 KSB 版的表跟 V7RC 版（01）剛好左右相反。
//   保留兩組是為了萬一某台盒子接線不同，可以單獨改
const 反轉_1269: boolean[] = [false, true, false, false]
const 反轉_1409: boolean[] = [false, true, false, false]
// 轉向正負號只跟「遙控器」有關，跟主控盒無關。KSB 搖桿用 true（與舊版程式一致）
const 反轉_轉向: boolean = true


// ═══════════════════ 常 數 ═══════════════════

// 乾淨頻段（micro:bit 頻段 n = 2400+n MHz）：
//   避開 WiFi 第 1/6/11 頻道（台灣只開放 1~11），
//   也避開藍牙廣播頻道 38（2426 MHz）與 39（2480 MHz）——比賽場地滿是手機，這兩個頻率最擠。
//   ※ 遙控器與車子的這張表、群組、封包名、頻段公式必須完全相同
const 乾淨頻段: number[] = [22, 23, 24, 48, 49, 50, 51, 72, 73, 74, 75, 76, 77, 78]
const 控制群組 = 173
const 封包名 = "R4"
const 回報名 = "R4K"
// 配對專用頻道（遙控器必須相同）
const 配對頻段 = 7
const 配對群組 = 174
const 配對名 = "R4P"        // 遙控器在配對模式時送的封包
const 配對確認名 = "R4OK"   // 車子配好後回送，數值 = 遙控器序號

// 由遙控器序號算出頻段索引（與遙控器端同一個公式）
function 頻段索引(sn: number): number {
    return ((sn ^ (sn >> 16)) & 0xFFFF) % 乾淨頻段.length
}

const K_CAR = "R4MCAR"
const K_BOX = "R4MBOX"
const K_PAIR = "R4MPAIR"

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


const B_A = 1        // A車 夾爪張開　／ B車 閘門關
const B_B = 2        // A車 夾爪閉合　／ B車 閘門開
const B_C = 4        // 機構下降
const B_D = 8        // 右轉微調
const B_E = 16       // 機構上升
const B_F = 32       // 左轉微調
const B_SW = 64      // 慢速模式

const PWM滿 = 1000          // 最大寫 1000（與舊版智高程式相同），不寫滿 1023：保留一點關斷時間給馬達驅動晶片


// ═══════════════════ 狀 態 ═══════════════════

const 頻段鎖定 = input.buttonIsPressed(Button.A) && input.buttonIsPressed(Button.B)

let 車編號 = "A"
let 主控盒 = 1269
let 馬達數 = 4
let 反轉: boolean[] = 反轉_1269

let 方向腳: DigitalPin[] = []
let 速度腳: AnalogPin[] = []
let 速度腳D: DigitalPin[] = []
let 閘門腳 = AnalogPin.P8

let 配對序號 = 0
let 配對模式 = false
let 剛配對 = false
let 配對開始 = 0
let 舊配對序號 = 0
let rx = 100 + (100 << 8)      // 中立值（前後 0、轉向 0、無按鈕）
let 上次收到 = 0
let 上次輸出: number[] = [0, 0, 0, 0]
let 平滑_前後 = 0
let 平滑_轉向 = 0
let 閘門角 = 閘門角_關
let 上次閘門角 = -1
let 微調方向 = 0            // -1 左、0 無、+1 右
let 微調到期 = 0            // 這個時間點之前，微調都算有效
let 上次微調中 = false      // 用來判斷「微調剛結束」


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
    馬達數 = 車編號 == "A" ? 4 : 3      // B車第 4 組讓給閘門伺服，完全不驅動
    反轉 = 主控盒 == 1409 ? 反轉_1409 : 反轉_1269
}


// ═══════════════════ 訊 號 整 形 ═══════════════════

function 整形(v: number): number {
    const a = Math.abs(v)
    if (a < 死區) return 0
    let x = (a - 死區) / (100 - 死區)
    if (x > 1) x = 1
    const y = (1 - 曲線量) * x + 曲線量 * x * x * x
    return (v > 0 ? 1 : -1) * y * 100
}

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
    if (v == 前值) return                        // 沒變就不寫腳位
    上次輸出[i] = v

    if (v == 0) {
        // 停止：類比寫 0，「不」釋放 PWM 通道（2026-11 修正）
        //   micro:bit V2 分配 PWM 通道是「輪流」給的，不會找空的那一個：
        //   一支腳放掉通道、下次再要時，可能把「別支腳正在用的通道」搶走，
        //   被搶的那個機構會突然沒力（升降會往下掉）。
        //   每台車剛好 4 支 PWM 腳（A：四顆馬達；B：三顆馬達＋閘門伺服），
        //   各自佔住一個通道、永遠不放，就不會互搶。
        pins.analogWritePin(速度腳[i], 0)
        pins.digitalWritePin(方向腳[i], 0)
        return
    }

    const mag = 馬達最低 + Math.idiv((PWM滿 - 馬達最低) * Math.abs(v), 100)
    pins.digitalWritePin(方向腳[i], v > 0 ? 1 : 0)
    pins.analogWritePin(速度腳[i], mag)
}

// 混控 + 飽和等比縮放（全速直行時仍保有轉向權限，舊版在這裡會失去轉向）
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
    // 注意：不碰閘門伺服，失聯時閘門維持現狀
}


// ═══════════════════ 設 定 與 配 對 ═══════════════════

// 配對模式：切到配對專用頻段／群組
function 進入配對頻道() {
    radio.setGroup(配對群組)
    radio.setFrequencyBand(配對頻段)
    radio.setTransmitPower(7)
}

// 配好之後固定在「那支遙控器的頻段」
function 套用頻段() {
    radio.setGroup(控制群組)
    radio.setTransmitPower(7)
    if (頻段鎖定) radio.setFrequencyBand(7)
    else if (配對序號 != 0) radio.setFrequencyBand(乾淨頻段[頻段索引(配對序號)])
}

function 等待選擇(標題: string): boolean {
    basic.showString(標題)
    while (true) {
        if (input.buttonIsPressed(Button.A)) { basic.pause(250); return true }
        if (input.buttonIsPressed(Button.B)) { basic.pause(250); return false }
        basic.pause(25)
    }
}

function 設定選單() {
    // ── 第 1 頁：車編號 ──
    車編號 = 等待選擇("CAR") ? "A" : "B"
    basic.showString(車編號)
    basic.pause(400)

    // ── 第 2 頁：主控盒 ──
    主控盒 = 等待選擇("BOX") ? 1269 : 1409
    basic.showNumber(主控盒)

    存數字(K_CAR, 車編號 == "B" ? 1 : 0)
    存數字(K_BOX, 主控盒)
    basic.showIcon(IconNames.Yes)
    basic.pause(500)
    basic.clearScreen()
}


// ═══════════════════ 開 機 流 程 ═══════════════════

let 進選單 = false
let 進配對 = false

// 頻段鎖定：按住 A+B 開機。先顯示 L，等手放開，免得 B 順便觸發設定選單、A 觸發配對
if (頻段鎖定) {
    basic.showString("L")
    while (input.buttonIsPressed(Button.A) || input.buttonIsPressed(Button.B)) basic.pause(20)
}

if (鎖定設定) {
    // ── 決賽模式：值寫死在程式裡，選手動不了 ──
    車編號 = 鎖定_車編號
    主控盒 = 鎖定_主控盒 == 1409 ? 1409 : 1269
    basic.showString(車編號)
    basic.showNumber(主控盒)
    // 仍留一道配對入口：現場臨時換遙控器時用
    const tL = input.runningTime()
    while (input.runningTime() - tL < 2000) {
        if (input.buttonIsPressed(Button.A)) { 進配對 = true; break }
        basic.pause(25)
    }
} else {
    // ── 平時模式：讀 Flash，開機 3 秒內可進選單或配對 ──
    let 有記錄 = false
    if (已存(K_CAR)) {
        車編號 = 讀數字(K_CAR) == 1 ? "B" : "A"
        有記錄 = true
    }
    if (已存(K_BOX)) 主控盒 = 讀數字(K_BOX)
    if (主控盒 != 1409) 主控盒 = 1269

    basic.showString(車編號)
    basic.showNumber(主控盒)

    進選單 = !有記錄
    const t0 = input.runningTime()
    while (!進選單 && !進配對 && input.runningTime() - t0 < 3000) {
        if (input.buttonIsPressed(Button.B)) 進選單 = true
        else if (input.buttonIsPressed(Button.A)) 進配對 = true
        basic.pause(25)
    }
    if (進選單) 設定選單()
}

if (已存(K_PAIR)) 配對序號 = 讀數字(K_PAIR)

// 按了 A，或從來沒配對過 → 配對模式
if (進配對 || 配對序號 == 0) {
    舊配對序號 = 配對序號                         // 萬一配對失敗，可以還原（0 = 從沒配過 → 一直等，不逾時）
    配對序號 = 0
    配對模式 = true
    basic.showString("P")                          // P 會一直亮著，直到配對成功或逾時
    配對開始 = input.runningTime()
}

套用腳位()
if (配對模式) 進入配對頻道()
else 套用頻段()

for (let i = 0; i < 4; i++) {
    pins.digitalWritePin(速度腳D[i], 0)
    pins.digitalWritePin(方向腳[i], 0)
    上次輸出[i] = 0
}
if (車編號 == "B") {
    pins.servoWritePin(閘門腳, 閘門角_關)
    上次閘門角 = 閘門角_關
}

radio.onReceivedValue(function (name, value) {
    const sn = radio.receivedPacket(RadioPacketProperty.SerialNumber)

    if (配對模式) {
        // 只接受「也在配對模式」的遙控器送的配對封包；平常的操控封包一律不理
        if (name != 配對名 || sn == 0) return
        if (radio.receivedPacket(RadioPacketProperty.SignalStrength) < 配對最弱訊號) return
        配對序號 = sn                    // 寫 Flash、回確認、換頻段交給主迴圈做，事件裡不做慢動作
        配對模式 = false
        剛配對 = true
        return
    }
    if (name != 封包名) return
    if (sn != 配對序號) return           // 不是配對過的遙控器，整包丟掉

    rx = value
    上次收到 = input.runningTime()
})

// 心跳回報：讓遙控器知道車子還活著（遙控器收不到會震動警告）
control.inBackground(function () {
    while (true) {
        basic.pause(回報週期)
        if (!配對模式 && 配對序號 != 0) radio.sendValue(回報名, 配對序號)   // 回報「我配對的是誰」，遙控器比對是不是自己
    }
})

if (!配對模式) basic.clearScreen()                // 配對中就讓 P 留在畫面上


// ═══════════════════ 主 控 制 迴 圈（固定 20ms）═══════════════════

basic.forever(function () {
    const now = input.runningTime()

    if (剛配對) {
        剛配對 = false
        存數字(K_PAIR, 配對序號)
        // 還在配對頻道上：回送確認給遙控器（送 5 次，免得漏掉），遙控器收到才會顯示 ✓
        for (let k = 0; k < 5; k++) {
            radio.sendValue(配對確認名, 配對序號)
            basic.pause(30)
        }
        套用頻段()                                   // 切到這支遙控器的頻段
        basic.showIcon(IconNames.Yes)
        basic.pause(400)
        basic.clearScreen()
    }
    if (配對模式) {
        // 原本有配對、但等太久都沒收到遙控器 → 取消，恢復原本的配對對象
        //（從沒配對過的車子沒有東西可以恢復，就一直等）
        if (舊配對序號 != 0 && now - 配對開始 > 配對逾時毫秒) {
            配對模式 = false
            配對序號 = 舊配對序號
            套用頻段()
            basic.showIcon(IconNames.No)
            basic.pause(800)
            basic.clearScreen()
        }
        basic.pause(控制週期)
        return
    }

    // ── 看門狗 ──
    if (now - 上次收到 > 斷線毫秒) {
        全停()
        if (車編號 == "B") 更新閘門()
        if (now % 700 < 350) { led.plot(2, 2) } else { led.unplot(2, 2) }
        basic.pause(控制週期)
        return
    }
    led.plot(2, 2)

    // ── 解包（一個封包就是完整狀態）──
    const 前後 = (rx & 0xFF) - 100
    const 轉向raw = ((rx >> 8) & 0xFF) - 100
    const btn = (rx >> 16) & 0x7F

    const 慢速 = (btn & B_SW) != 0
    const 升 = (btn & B_E) != 0
    const 降 = (btn & B_C) != 0
    const 左 = (btn & B_F) != 0
    const 右 = (btn & B_D) != 0
    const 鍵A = (btn & B_A) != 0
    const 鍵B = (btn & B_B) != 0

    // ── 機構1：升降 / 耙子升降 ──
    let 機構 = 0
    if (升 && !降) 機構 = 機構升速
    else if (降 && !升) 機構 = -機構降速
    輸出(2, 機構)

    // ── 機構2：A車＝夾爪　B車＝閘門 ──
    let 機構2作動 = false
    if (車編號 == "A") {
        let 夾 = 0
        if (鍵A && !鍵B) 夾 = 夾爪力道
        else if (鍵B && !鍵A) 夾 = -夾爪力道
        輸出(3, 夾)
        機構2作動 = 夾 != 0
    } else {
        if (鍵B && !鍵A) 閘門角 = 閘門角_開
        else if (鍵A && !鍵B) 閘門角 = 閘門角_關
        更新閘門()
    }

    // ── 左右微調：固定轉速 ＋ 點按定量 ──
    //    按住時 微調到期 一直被往後推 → 持續有效
    //    點一下就放，也還會維持 微調最短毫秒，不會因為按太快而沒反應
    if (右 && !左) {
        微調方向 = 1
        微調到期 = now + 微調最短毫秒
    } else if (左 && !右) {
        微調方向 = -1
        微調到期 = now + 微調最短毫秒
    }
    const 微調中 = now < 微調到期

    // ── 行走（機構作動、微調、或按下搖桿時自動降速，對位好用）──
    const 機構在動 = 機構作動時降速 && (機構 != 0 || 機構2作動)
    const 限速 = (慢速 || 機構在動 || 微調中) ? 對位慢速 : 全域限速

    let 轉向目標 = 整形(轉向raw) * 限速 / 100
    if (微調中) {
        const 微調量 = 微調方向 * 微調轉速
        轉向目標 = 微調覆蓋搖桿 ? 微調量 : Math.clamp(-100, 100, 轉向目標 + 微調量)
    }

    平滑_前後 = 逼近(平滑_前後, 整形(前後) * 限速 / 100, 斜率)
    // 微調中、或微調剛結束：轉向不走斜坡，立刻到位、立刻停
    //   → 每點一下的轉動量固定，不會被斜坡的「慢慢加速、慢慢停」拖長
    if (微調中 || 上次微調中) 平滑_轉向 = 轉向目標
    else 平滑_轉向 = 逼近(平滑_轉向, 轉向目標, 斜率)
    上次微調中 = 微調中
    移動(平滑_前後, 平滑_轉向)

    basic.pause(控制週期)
})
