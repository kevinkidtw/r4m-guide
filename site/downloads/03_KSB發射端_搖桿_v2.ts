// ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ┃ 貼上程式「之前」先做完這幾項，否則會出現 Cannot find name 'xxx' 的紅字
// ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//   □ radio        新專案預設就有，不用另外加（若被移除過，擴展 → 搜尋 radio 加回）
//   □ KSB045       擴展 → 搜尋框貼上 github:lioujj/pxt-KSB045
//   （v3 起遙控器不存任何設定，不需要 flashstorage）
// 做完後：右上角切到「JavaScript」→ 全選刪除 → 貼上本檔

/**********************************************************************
 *  R4M 遙控發射端 — KSB045 搖桿擴充板   v3.1 / 2026
 *  車城科技中心
 *
 *  ★ v3：遙控器「完全不用設定」——沒有頻道碼、沒有 A/B 車，開機就能用。
 *    ‧ 車子只認「配對過的遙控器序號」，所以不需要靠頻道碼區分隊伍
 *    ‧ 頻段由這支遙控器的晶片序號自動算出來，各隊自然分散到 14 個頻段
 *    ‧ 遙控器不知道自己控的是 A 車還是 B 車——按鍵功能由車子自己決定
 *
 *  ══════════════ 開 機 操 作 ══════════════
 *   直接開機即可。開機時不要碰搖桿（要量搖桿中心點）。
 *   按住 A 開機約 2 秒，出現 P → 配對模式（車子也要先進 P）
 *        兩邊都出現 ✓ 就完成；30 秒沒配到 → ✗，照常進入操控
 *        配對訊號用最小功率送，所以遙控器要拿到車子旁邊（30 公分內）
 *   按住 A+B 開機 → 頻段鎖定在預設 7（主辦要求用預設頻段時才用；車子也要一樣）
 *
 *  ══════════════ 平 時 操 作 ══════════════
 *   搖桿        前後＝移動，左右＝轉向
 *   E / C       升降 上 / 下
 *   F / D       原地 左轉 / 右轉（微調）
 *   A / B       A車：夾爪 張開 / 閉合    B車：閘門 關 / 開
 *   搖桿按下    慢速模式（對位用）
 *   畫面中心亮 = 與車子連線正常；閃爍＋震動 = 失聯（或車子配對的不是這支）
 *
 *  ══════════════ 協 定 ══════════════
 *   每 30ms 送「一個」封包，內容是完整狀態：
 *     名稱  = "R4"
 *     數值  = bit 0-7  前後 (0~200，減 100)
 *             bit 8-15 轉向 (0~200，減 100)
 *             bit16-22 按鈕 A B C D E F SW
 *             bit23-26 流水號
 *     封包自動附上本機序號（setTransmitSerialNumber）→ 車子靠它認主人
 *   頻段 = 乾淨頻段[ 由序號算出的索引 ]；群組固定 = 控制群組
 *   一包＝完整狀態，所以：不會漏指令、按鈕可同時按、封包本身就是心跳。
 *
 *  ※ 發射端用 micro:bit V1 完全沒問題。V1 與 V2 的 radio 協定完全相容。
 **********************************************************************/


// ═══════════════════ 調 校 區 ═══════════════════

const 送出週期 = 30          // ms（約 33 包/秒）。不要低於 20，會開始洗版
const 搖桿死區原始 = 45      // 0~1023 尺度的死區
const 失聯毫秒 = 1200        // 超過這麼久沒收到車子回報 → 警示
const 警告間隔 = 2500        // ms，失聯時每隔多久震動一次


// ═══════════════════ 常 數（遙控器與車子必須完全相同）═══════════════════

// 乾淨頻段（micro:bit 頻段 n = 2400+n MHz）：
//   避開 WiFi 第 1/6/11 頻道，也避開藍牙廣播頻道 38（2426 MHz）與 39（2480 MHz）。
const 乾淨頻段: number[] = [22, 23, 24, 48, 49, 50, 51, 72, 73, 74, 75, 76, 77, 78]
const 控制群組 = 173         // 固定群組：硬體層直接濾掉不是本系統的封包（舊程式用 55、預設是 0）
const 封包名 = "R4"
const 回報名 = "R4K"

// 配對專用頻道（車子必須相同）
const 配對頻段 = 7
const 配對群組 = 174
const 配對名 = "R4P"         // 配對模式時送的封包
const 配對確認名 = "R4OK"    // 車子配好後回送，數值 = 本機序號
const 配對功率 = 0           // 配對訊號的發射功率（0 最小）。要貼很近才配得到 → 改 2
const 配對按住毫秒 = 2000    // 開機時按住 A 這麼久才進配對（避免誤觸）
const 配對逾時毫秒 = 30000

// 由晶片序號算出頻段索引（車子用同一個公式，算出跟遙控器一樣的頻段）
function 頻段索引(sn: number): number {
    return ((sn ^ (sn >> 16)) & 0xFFFF) % 乾淨頻段.length
}

const B_A = 1
const B_B = 2
const B_C = 4
const B_D = 8
const B_E = 16
const B_F = 32
const B_SW = 64


// ═══════════════════ 狀 態 ═══════════════════

const 頻段鎖定 = input.buttonIsPressed(Button.A) && input.buttonIsPressed(Button.B)   // 按住 A+B 開機 → 預設頻段 7
const 我的序號 = control.deviceSerialNumber()
let midX = 512
let midY = 512
let seq = 0
let 上次回報 = 0
let 上次警告 = 0
let 配對成功 = false


// ═══════════════════ 小 工 具 ═══════════════════

function 震動(ms: number) {
    control.inBackground(function () {
        KSB045.setVibration(KSB045.vibrate.on)
        basic.pause(ms)
        KSB045.setVibration(KSB045.vibrate.off)
    })
}

// 取搖桿中心值：每支搖桿的中心都不是剛好 512，不校正會回中漂移
function 取中心() {
    let sx = 0
    let sy = 0
    for (let i = 0; i < 8; i++) {
        sx += KSB045.getJoystickValue(KSB045.valueType.X)
        sy += KSB045.getJoystickValue(KSB045.valueType.Y)
        basic.pause(10)
    }
    midX = Math.idiv(sx, 8)
    midY = Math.idiv(sy, 8)
}

// 原始 0~1023 → −100~+100，死區之外線性展開（左右行程各自算，處理中心偏移）
function 正規化(raw: number, center: number): number {
    let d = raw - center
    if (Math.abs(d) < 搖桿死區原始) return 0
    let span = 0
    if (d > 0) {
        d -= 搖桿死區原始
        span = 1023 - center - 搖桿死區原始
    } else {
        d += 搖桿死區原始
        span = center - 搖桿死區原始
    }
    if (span < 50) span = 50
    return Math.clamp(-100, 100, Math.round(d * 100 / span))
}


// ═══════════════════ 開 機 流 程 ═══════════════════

// 頻段鎖定：按住 A+B 開機。先顯示 L，等手放開
if (頻段鎖定) {
    basic.showString("L")
    while (input.buttonIsPressed(Button.A) || input.buttonIsPressed(Button.B)) basic.pause(20)
}

// 配對：按住 A 開機約 2 秒 → P
let 進配對 = false
if (!頻段鎖定 && input.buttonIsPressed(Button.A)) {
    const t0 = input.runningTime()
    let 第幾格 = 0
    while (input.buttonIsPressed(Button.A) && input.runningTime() - t0 < 配對按住毫秒) {
        // 按住期間由左到右亮起一排燈，亮滿就進配對
        const 應亮 = Math.idiv((input.runningTime() - t0) * 5, 配對按住毫秒)
        while (第幾格 <= 應亮 && 第幾格 < 5) { led.plot(第幾格, 4); 第幾格++ }
        basic.pause(20)
    }
    if (input.buttonIsPressed(Button.A)) {
        進配對 = true
        basic.showString("P")
        震動(100)
        while (input.buttonIsPressed(Button.A)) basic.pause(20)   // 等手放開
    } else {
        basic.clearScreen()                  // 沒按滿 2 秒 → 當作正常開機
    }
}

radio.setTransmitSerialNumber(true)          // 車子端靠這個認主人（配對）

// 接收車子的封包：
//   配對確認（數值＝我的序號）→ 配對成功
//   心跳回報（數值＝它配對的遙控器序號）→ 等於我才算連線
radio.onReceivedValue(function (name, value) {
    if (value != 我的序號) return
    if (name == 配對確認名) 配對成功 = true
    else if (name == 回報名) 上次回報 = input.runningTime()
})

if (進配對) {
    radio.setGroup(配對群組)
    radio.setFrequencyBand(配對頻段)
    radio.setTransmitPower(配對功率)
    const t0 = input.runningTime()
    while (!配對成功 && input.runningTime() - t0 < 配對逾時毫秒) {
        radio.sendValue(配對名, 0)            // 序號會自動附上
        basic.pause(100)
    }
    if (配對成功) {
        basic.showIcon(IconNames.Yes)
        震動(300)
    } else {
        basic.showIcon(IconNames.No)         // 沒收到車子確認（車子可能其實有配好，看中心燈就知道）
        震動(100)
    }
    basic.pause(1000)
    basic.clearScreen()
}

取中心()                                     // 手要離開搖桿

radio.setGroup(控制群組)
radio.setFrequencyBand(頻段鎖定 ? 7 : 乾淨頻段[頻段索引(我的序號)])
radio.setTransmitPower(7)

basic.clearScreen()
if (頻段鎖定) basic.showString("L")      // 提醒：現在是預設頻段模式
震動(120)


// ═══════════════════ 主 迴 圈（固定 30ms 送一包）═══════════════════

basic.forever(function () {
    const y = 正規化(KSB045.getJoystickValue(KSB045.valueType.Y), midY)
    const t = 正規化(KSB045.getJoystickValue(KSB045.valueType.X), midX)

    let btn = 0
    if (input.buttonIsPressed(Button.A)) btn |= B_A
    if (input.buttonIsPressed(Button.B)) btn |= B_B
    if (KSB045.getBtnValue(KSB045.btnName.C)) btn |= B_C
    if (KSB045.getBtnValue(KSB045.btnName.D)) btn |= B_D
    if (KSB045.getBtnValue(KSB045.btnName.E)) btn |= B_E
    if (KSB045.getBtnValue(KSB045.btnName.F)) btn |= B_F
    if (KSB045.getBtnValue(KSB045.btnName.SW)) btn |= B_SW

    seq = (seq + 1) % 16
    radio.sendValue(封包名, (y + 100) | ((t + 100) << 8) | (btn << 16) | (seq << 23))

    // 連線指示（全部非阻塞）
    const now = input.runningTime()
    if (now - 上次回報 < 失聯毫秒) {
        led.plot(2, 2)
    } else {
        if (now % 600 < 300) { led.plot(2, 2) } else { led.unplot(2, 2) }
        if (now - 上次警告 > 警告間隔) {
            震動(150)
            上次警告 = now
        }
    }

    basic.pause(送出週期)
})
