// =====================================================================
//  2027 世界機關王 R4M 基礎組 ─ C 機器人（循跡自主車）
//  任務二：自行從「飼料暫放區」取料 → 沿黑線運送 → 卸入對應顏色放置區
//  車城科技中心 / 貼到 MakeCode 的 JavaScript(TypeScript) 分頁即可
//  --------------------------------------------------------------------
//  按鍵：A = 急停  |  B = 開始任務  |  A+B(搖晃) = 感測器校正顯示
//  所有「要在場地上實測」的數字都放在最上面的參數區
// =====================================================================

// ========== 1. 腳位設定（依主控盒實際標示修改）==========
const PIN_S_L = DigitalPin.P8      // 左循跡感應器
const PIN_S_C = DigitalPin.P12     // 中循跡感應器（主要）
const PIN_S_R = DigitalPin.P2      // 右循跡感應器
const 有中央感測器 = true           // 只有 2 顆時改成 false（見說明）
const 黑 = 1                       // 壓到黑線時讀到的值；若相反改成 0

const PIN_L_DIR = DigitalPin.P13   // 左馬達 方向
const PIN_L_PWM = AnalogPin.P14    // 左馬達 速度
const PIN_R_DIR = DigitalPin.P15   // 右馬達 方向
const PIN_R_PWM = AnalogPin.P16    // 右馬達 速度
const L_正轉 = 1                   // 若左輪方向相反改成 0
const R_正轉 = 1                   // 若右輪方向相反改成 0

const PIN_GATE = AnalogPin.P1      // 料斗閘門伺服
// 注意：micro:bit 同時只能輸出 3 路 PWM（V1）。
// 兩顆馬達(2) + 一顆伺服(1) = 3，剛好用滿；要加第二顆伺服請改用 V2 並實測。

// ========== 2. 速度與行為參數（實測後調整）==========
const V_直行 = 380                 // 循跡基礎速度 0~1023
const V_慢 = 260                   // 進區、找線用的慢速
const V_轉外 = 520                 // 修正時外側輪
const V_轉內 = -160                // 修正時內側輪（負值=倒轉，轉得更急）
const V_原地 = 330                 // 原地旋轉速度

// ---- 里程校正：用 V_慢 前進 1 公分要幾毫秒（所有定距動作都用 V_慢）----
// 量法：讓車以 V_慢 直行 3000ms，量出走了幾公分 D，MS_每公分 = 3000 / D
const MS_每公分 = 38
// ---- 旋轉校正：以 V_原地 原地轉 1 度要幾毫秒 ----
// 量法：轉 2000ms 看轉了幾度 A，MS_每度 = 2000 / A
const MS_每度 = 7

// ---- 幾何備忘（不是程式用的，是算微調值用的）----
// 停在橫線上時，料斗中心會落在「橫線後方 感測器到料斗 公分」的位置。
// 微調值 = 想讓料斗中心停的位置 − 橫線位置 + 感測器到料斗
//   感測器到料斗（公分）＝ 量你的車：循跡感測器 到 料斗中心 的前後距離

// ---- 取料動作 ----
const 取料前進 = 14                // 車頭朝西後往前衝幾公分把飼料收進料斗
const 取料後退 = 15                // 收完往後退幾公分回到出發區上方

// ---- 卸料動作（三個放置區可分別微調）----
const 紅_微調 = 0                  // 偵測到橫線後先前進(+)/後退(-) 幾公分再轉彎
const 綠_微調 = 0
const 藍_微調 = 0
const 進區距離 = 6                 // 轉向放置區後再前進幾公分
// 退出距離：卸完往後退幾公分。
//   前開式推箱(料斗前方開口) → 必須大於「料斗深度」才能把料留下，例如 進區距離+16
//   可傾倒/可提起式料斗       → 設成和 進區距離 一樣即可
const 退出距離 = 22

// ---- 閘門角度（脈衝寬度 us，實測）----
const 閘_關 = 2400
const 閘_紅 = 1800
const 閘_綠 = 1400
const 閘_藍 = 1000

const 逾時_毫秒 = 20000            // 一段路超過這個時間還沒看到橫線就停車報錯

// ========== 3. 全域變數 ==========
let 中止 = false
let sL = false, sC = false, sR = false
let 最後偏向 = 0                   // -1=線在左邊, +1=線在右邊

// ========== 4. 底層：馬達 ==========
function 馬達(速度: number, dirPin: DigitalPin, pwmPin: AnalogPin, 正轉值: number) {
    if (速度 > 1023) 速度 = 1023
    if (速度 < -1023) 速度 = -1023
    if (速度 >= 0) {
        pins.digitalWritePin(dirPin, 正轉值)
        pins.analogWritePin(pwmPin, 速度)
    } else {
        pins.digitalWritePin(dirPin, 1 - 正轉值)
        pins.analogWritePin(pwmPin, -速度)
    }
}
function 左輪(v: number) { 馬達(v, PIN_L_DIR, PIN_L_PWM, L_正轉) }
function 右輪(v: number) { 馬達(v, PIN_R_DIR, PIN_R_PWM, R_正轉) }
function 停車() { 左輪(0); 右輪(0) }

// ========== 5. 底層：感測器 ==========
function 讀感測器() {
    sL = (pins.digitalReadPin(PIN_S_L) == 黑)
    sR = (pins.digitalReadPin(PIN_S_R) == 黑)
    if (有中央感測器) {
        sC = (pins.digitalReadPin(PIN_S_C) == 黑)
    } else {
        sC = !sL && !sR          // 兩顆版本：左右都沒壓到線 = 視為在線上
    }
}
// 橫線／路口：三顆同時壓到黑
function 是橫線(): boolean { return sL && sR && sC }
// 完全脫線：三顆都看不到黑（兩顆版本偵測不到，這也是建議裝三顆的原因）
function 是脫線(): boolean { return 有中央感測器 && !sL && !sC && !sR }

// ========== 6. 底層：定時移動（會被急停打斷）==========
function 等待(ms: number): boolean {
    const t0 = input.runningTime()
    while (input.runningTime() - t0 < ms) {
        if (中止) { 停車(); return false }
        basic.pause(5)
    }
    return true
}
// 正值前進、負值後退（用 V_慢，配合 MS_每公分）
function 直行(公分: number): boolean {
    const v = 公分 >= 0 ? V_慢 : -V_慢
    const ms = Math.abs(公分) * MS_每公分
    左輪(v); 右輪(v)
    const ok = 等待(ms)
    停車(); basic.pause(80)
    return ok
}
// 正值右轉、負值左轉（原地）
function 原地轉(度: number): boolean {
    const s = 度 >= 0 ? 1 : -1
    左輪(V_原地 * s); 右輪(-V_原地 * s)
    const ok = 等待(Math.abs(度) * MS_每度)
    停車(); basic.pause(80)
    return ok
}

// ========== 7. 循跡核心 ==========
function 循跡一步() {
    讀感測器()
    if (sC && !sL && !sR) {                 // 正中央
        左輪(V_直行); 右輪(V_直行)
    } else if (sL && !sR) {                 // 線偏左 → 向左修
        最後偏向 = -1
        左輪(V_轉內); 右輪(V_轉外)
    } else if (sR && !sL) {                 // 線偏右 → 向右修
        最後偏向 = 1
        左輪(V_轉外); 右輪(V_轉內)
    } else if (是脫線()) {                   // 脫線 → 往最後看到線的方向找
        左輪(最後偏向 >= 0 ? V_原地 : -V_原地)
        右輪(最後偏向 >= 0 ? -V_原地 : V_原地)
    } else {                                 // 其他（含壓到橫線）照直走
        左輪(V_直行); 右輪(V_直行)
    }
}

// 循跡前進，直到遇到「下一條橫線」；回傳 true=找到，false=逾時或急停
// 出發時若人就站在橫線/路口上，會先等離開該線才開始偵測（避免原地重複觸發）
function 循跡直到橫線(): boolean {
    const t0 = input.runningTime()
    let 已解除 = false
    while (!中止) {
        if (input.runningTime() - t0 > 逾時_毫秒) {
            停車(); basic.showString("T"); return false
        }
        讀感測器()
        if (!已解除) {
            if (!是橫線()) 已解除 = true
        } else if (是橫線()) {
            停車(); basic.pause(120); return true
        }
        循跡一步()
        basic.pause(5)
    }
    停車(); return false
}

// 慢速找線：轉彎掃描直到任一感測器壓到黑（離線動作後用來重新對正）
function 尋線(): boolean {
    左輪(V_慢); 右輪(V_慢)
    const t0 = input.runningTime()
    while (input.runningTime() - t0 < 1200) {
        if (中止) { 停車(); return false }
        讀感測器()
        if (sL || sC || sR) { 停車(); return true }
        basic.pause(5)
    }
    停車()
    // 直走沒找到就左右掃
    for (let i = 0; i < 6; i++) {
        if (中止) return false
        原地轉(i % 2 == 0 ? -15 * (i + 1) : 15 * (i + 1))
        讀感測器()
        if (sL || sC || sR) return true
    }
    basic.showString("L")          // Lost
    return false
}

// ========== 8. 任務動作 ==========
// 取料：車停在 C 車出發區（島形環）上、車頭朝北
//   左轉90° → 車頭朝西 → 前進撈料 → 後退回來 → 轉回原方向
function 取料(轉回右轉: boolean) {
    pins.servoSetPulse(PIN_GATE, 閘_關)
    原地轉(-90)                    // 朝西
    直行(取料前進)                  // 衝進暫放區，把飼料掃進料斗
    basic.pause(200)
    直行(-取料後退)                 // 退回出發區
    原地轉(轉回右轉 ? 90 : -90)      // 90=轉回朝北(順時針路線)；-90=轉成朝南(逆時針路線)
    尋線()                          // 回到島形環的線上
}

// 斜向回線：卸完料退出來時車身會落在黑線外側，斜著切回去找線
//   側 = 卸料時放置區的方向（1=右、-1=左）；黑線就在車子的這一側
function 回到線上(側: number): boolean {
    原地轉(25 * 側)                  // 車頭朝向黑線那一側
    const t0 = input.runningTime()
    左輪(V_慢); 右輪(V_慢)
    while (input.runningTime() - t0 < 3000) {
        if (中止) { 停車(); return false }
        讀感測器()
        if (sL || sC || sR) { 停車(); 原地轉(-25 * 側); return true }
        basic.pause(5)
    }
    停車(); basic.showString("L")     // Lost：找不到線
    return false
}

// 卸料：已停在該區橫線上
//   側 = 1 表示放置區在右手邊（順時針路線）、-1 在左手邊（逆時針路線）
function 卸料(側: number, 微調公分: number, 閘門: number) {
    if (微調公分 != 0) 直行(微調公分)
    原地轉(90 * 側)                 // 車頭轉向放置區
    直行(進區距離)
    pins.servoSetPulse(PIN_GATE, 閘門)   // 開閘門
    basic.pause(700)
    直行(-退出距離)                  // 直直退出來，飼料留在區內
    pins.servoSetPulse(PIN_GATE, 閘_關)
    原地轉(-90 * 側)                // 轉回行進方向
    回到線上(側)                     // 黑線在放置區那一側
}

// ========== 9. 主任務流程 ==========
// 路線（依場地量測，黑線寬約 2.8cm、三條橫線各在一個放置區的邊界）
//  第一趟：出發區 →(北, 順時針)→ 紅區橫線 → 卸紅 → 迴轉 →(南)→ 回出發區
//  第二趟：出發區 →(南, 逆時針)→ 藍區橫線 → 卸藍 →→ 綠區橫線 → 卸綠 → 完成
function 執行任務() {
    中止 = false
    basic.showNumber(1)

    // ---- 第一趟：紅色（16 顆 ×15 分 = 240 分，先拿最大分）----
    取料(true)                      // 撈紅色，轉回朝北
    if (中止) return
    if (!循跡直到橫線()) return      // 上方橫線 = 紅色放置區
    卸料(1, 紅_微調, 閘_紅)
    basic.showNumber(2)

    // ---- 回出發區：原地迴轉，往回走到島形環的路口 ----
    原地轉(180)
    尋線()
    if (!循跡直到橫線()) return      // 回程第一個路口 = C 車出發區(島形環)上緣
    直行(15)                        // 往前一點，讓車身停回出發區中央
    原地轉(180)                     // 轉回朝北，方便用同一套取料動作
    basic.showNumber(3)

    // ---- 第二趟：綠 + 藍 ----
    取料(false)                     // 撈綠+藍，轉成朝南（逆時針）
    if (中止) return
    if (!循跡直到橫線()) return      // 下方橫線 = 藍色放置區
    卸料(-1, 藍_微調, 閘_藍)
    if (!循跡直到橫線()) return      // 右側橫線 = 綠色放置區
    卸料(-1, 綠_微調, 閘_綠)

    停車()
    basic.showIcon(IconNames.Yes)
}

// ========== 10. 按鍵 ==========
input.onButtonPressed(Button.A, function () {      // 急停
    中止 = true
    停車()
    pins.servoSetPulse(PIN_GATE, 閘_關)
    basic.showIcon(IconNames.No)
})

input.onButtonPressed(Button.B, function () {      // 開始
    執行任務()
})

// 校正模式：搖一搖，LED 即時顯示三顆感測器狀態（左/中/右）
input.onGesture(Gesture.Shake, function () {
    basic.showString("S")
    const t0 = input.runningTime()
    while (input.runningTime() - t0 < 15000) {
        讀感測器()
        basic.clearScreen()
        if (sL) { led.plot(0, 2); led.plot(0, 3) }
        if (sC) { led.plot(2, 2); led.plot(2, 3) }
        if (sR) { led.plot(4, 2); led.plot(4, 3) }
        basic.pause(60)
    }
    basic.clearScreen()
})

// ========== 11. 開機初始化 ==========
pins.servoSetPulse(PIN_GATE, 閘_關)
停車()
basic.showIcon(IconNames.Happy)
