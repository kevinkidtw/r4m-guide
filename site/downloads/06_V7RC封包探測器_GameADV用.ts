// ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ┃ 貼上程式「之前」先做完這幾項，否則會出現 Cannot find name 'xxx' 的紅字
// ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//   □ V7RC         擴展 → 搜尋框貼上 github:lioujj/pxt-V7RC
//                  → 跳出「要移除 radio」→ 按確定（正常，藍牙和 radio 不能並存）
//                  ★ 一定要裝 V7RC，不要只裝 bluetooth！
//                    V7RC 擴充套件會自動把藍牙設成「免配對、對所有手機廣播」；
//                    只裝 bluetooth 的話，手機 App 會「找不到」這顆 micro:bit。
// 做完後：右上角切到「JavaScript」→ 全選刪除 → 貼上本檔

/**********************************************************************
 *  V7RC 封包探測器 — 用來搞清楚「Game ADV」介面到底送什麼
 *  車城科技中心 / 2026
 *
 *  Game ADV 這個介面沒有出現在 V7RC 的公開協定文件裡（文件只寫了
 *  SRV 車輛 / SRT 坦克 / SS8 專家 / SS8 BOT 四種），所以它的前綴、
 *  通道數、通道順序都必須實測。這支程式就是拿來測的。
 *
 *  ══════════════ 怎麼用 ══════════════
 *   1. 新專案 → 擴充套件加入 V7RC（github:lioujj/pxt-V7RC）
 *      ★ 不要只裝 bluetooth，否則手機找不到（原因見最上面的清單）
 *   2. 貼上本檔 → 燒錄 → 手機 V7RC 用 Game ADV 介面連上
 *
 *   【不用接電腦的看法】
 *     A 鍵：切換要看的通道（0~7），畫面顯示該通道目前數值
 *     B 鍵：顯示「封包前綴」與「每秒封包數」
 *          前綴會用 3 個字母捲過去，例如 SS8 / SRT / GAM …
 *
 *   【接電腦看得更清楚】
 *     用 USB 線接電腦 → MakeCode 左下角「顯示裝置資料」
 *     每 250ms 會印出一行原始字串，例如：
 *       [19] SS86496c8956495c896
 *     中括號是字串長度。推一下某個搖桿／按一下某個按鈕，
 *     看哪幾個字元在變，就知道那個控制對應第幾通道。
 *
 *  ══════════════ 測完要回報的三件事 ══════════════
 *   1. 前綴是什麼（前 3 個字元）、整串長度多少
 *   2. 推「左搖桿上下」「左搖桿左右」「右搖桿上下」「右搖桿左右」
 *      各是哪一個通道在變
 *   3. 按各個按鈕時，是哪一個通道變、變成什麼值
 *      （有些介面按鈕會另外送一包，前綴可能不一樣，例如 LED / LE2）
 **********************************************************************/


let 原文 = ""
let 前綴 = "---"
let 長度 = 0
let 封包數 = 0
let 每秒封包 = 0
let 看通道 = 0
let 有新封包 = false

// 通道解碼結果（三種已知格式都試著解，未知格式就只看原文）
let ch: number[] = [0, 0, 0, 0, 0, 0, 0, 0]
let 解碼方式 = "?"


function hex1(c: number): number {
    if (c >= 48 && c <= 57) return c - 48
    if (c >= 97 && c <= 102) return c - 87
    if (c >= 65 && c <= 70) return c - 55
    return -1
}

function 試解碼(s: string) {
    const n = s.length
    解碼方式 = "?"
    for (let k = 0; k < 8; k++) ch[k] = 0

    // 前綴是 SS 開頭（SS8 這一族）就不要用十進位解：
    // SS8 的中立值 0x96 剛好全是數字，會被誤判成十進位
    const 是SS = n >= 2 && s.charCodeAt(0) == 83 && s.charCodeAt(1) == 83

    // 4 位十進位 × N 通道（SRV / SRT 這一族）
    if (!是SS && n >= 7 && s.charCodeAt(3) >= 48 && s.charCodeAt(3) <= 57) {
        const 組數 = Math.idiv(n - 3, 4)
        if (組數 >= 1 && 組數 <= 8 && n - 3 == 組數 * 4) {
            let ok = true
            for (let i = 0; i < 組數; i++) {
                const p = 3 + i * 4
                const v = (s.charCodeAt(p) - 48) * 1000
                    + (s.charCodeAt(p + 1) - 48) * 100
                    + (s.charCodeAt(p + 2) - 48) * 10
                    + (s.charCodeAt(p + 3) - 48)
                if (v < 0 || v > 9999) { ok = false; break }
                ch[i] = v
            }
            if (ok) { 解碼方式 = "DEC4"; return }
        }
    }

    // 2 位十六進位 × N 通道（SS8 這一族）
    if (n >= 5 && n - 3 <= 16 && (n - 3) % 2 == 0) {
        let ok = true
        const 組數 = Math.idiv(n - 3, 2)
        for (let i = 0; i < 組數; i++) {
            const p = 3 + i * 2
            const h = hex1(s.charCodeAt(p))
            const l = hex1(s.charCodeAt(p + 1))
            if (h < 0 || l < 0) { ok = false; break }
            ch[i] = h * 16 + l
        }
        if (ok) { 解碼方式 = "HEX2"; return }
    }
}


// ═══ 藍牙：只存值，不做任何顯示（顯示放到主迴圈）═══

bluetooth.setTransmitPower(7)
bluetooth.startUartService()

bluetooth.onUartDataReceived(serial.delimiters(Delimiters.Hash), function () {
    原文 = bluetooth.uartReadUntil(serial.delimiters(Delimiters.Hash))
    長度 = 原文.length
    if (長度 >= 3) 前綴 = 原文.substr(0, 3)
    封包數 += 1
    有新封包 = true
})


// ═══ 每秒統計封包數（這個數字就是 App 的實際送出頻率）═══

control.inBackground(function () {
    while (true) {
        basic.pause(1000)
        每秒封包 = 封包數
        封包數 = 0
    }
})


// ═══ 每 250ms 往 USB 序列埠印一行原文 ═══

control.inBackground(function () {
    while (true) {
        basic.pause(250)
        if (有新封包) {
            有新封包 = false
            試解碼(原文)
            serial.writeLine("[" + 長度 + "][" + 解碼方式 + "][" + 每秒封包 + "/s] " + 原文)
        }
    }
})


// ═══ 按鍵：A = 換通道，B = 看前綴與封包率 ═══

input.onButtonPressed(Button.A, function () {
    看通道 = (看通道 + 1) % 8
    basic.showNumber(看通道)
})

input.onButtonPressed(Button.B, function () {
    basic.showString(前綴)
    basic.showNumber(長度)
    basic.showNumber(每秒封包)
})


// ═══ 主迴圈：顯示目前選中的通道值 ═══

basic.showString("SNIF")

basic.forever(function () {
    試解碼(原文)
    basic.showNumber(ch[看通道])
    basic.pause(200)
})
