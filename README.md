# r4m-guide — 機關王 R4M 程式說明站

> **2026-11-23 部署方式變更：本站已併入官網共用容器 `ccmtc-guides`（網址不變）。**
> 改完內容後先在本專案建置出 `site/`，再到 `../ccmtc-guides` 執行 `./deploy_nas.sh`。
> 本專案的 `deploy_nas.sh` 與獨立容器已停用。

> **2026-11 存取方式變更：本站已改為公開，不需通行碼。**
> 存取設定統一在 `ccmtc-official/ccmtc-portal/src/config/sites.mjs`（`auth: null`）。
> 下文的通行碼相關章節保留作為紀錄；日後要恢復，在該檔把 `auth` 改回註解中的設定，並在 NAS 的 `.env` 補回環境變數即可。

2027 世界機關王 R4M 基礎組 A／B／C 三車的程式說明網站，掛在 `https://ccmtc.mooo.com/r4m/`，公開瀏覽。

- A／B 車：KSB 搖桿（micro:bit radio）或手機 V7RC 遙控，同一支程式靠開機選單切換車編號
- C 車：程式自主循跡取料
- 內容只寫目前的功能與操作，不放版本修正歷程

## 頁面

| 檔案 | 內容 | 對象 |
|---|---|---|
| `index.html` | 三車一覽、入口、檔案下載 | 全部 |
| `prepare.html` | 燒錄哪支程式、擴充套件、燒錄步驟、賽前檢查清單、規則重點 | 選手 |
| `pairing.html` | 車子設定、KSB 配對、燈號圖鑑、四項驗收、決賽模式 | 選手 |
| `ksb.html` | KSB 搖桿按鍵、對位技巧、燈號與震動、訊號隔離 | 選手 |
| `v7rc.html` | 手機 V7RC 設定、連線、Game ADV 按鍵、常見問題 | 選手 |
| `ccar.html` | C 車任務計分、路線、按鍵與燈號、參數表、校正方法 | 選手 |
| `faq.html` | A／B 車、V7RC、C 車、燒錄的常見問題 | 選手 |
| `tech.html` | 腳位、方向預設值、可調常數、決賽鎖定、訊號隔離、封包探測器 | 老師 |

## 目錄

```
build/
  pages_src.py      頁面內容原稿（改內容改這裡）
  page-template.html
  nav.html          共用導覽列
  build_site.py     注入導覽列／頁尾、快取雜湊、離線壓縮包
  verify_site.py    靜態驗證（--quick）與線上回歸（--url）
site/               產出的靜態網站（nginx 直接提供）
  downloads/        .ts 程式原始碼、離線壓縮包
  assets/img/       場地底圖縮圖
nginx.conf          .ts 以純文字附件下載（避免被當成 video/mp2t）
docker-compose.yml  本機獨立測試用（3090）
deploy_nas.sh       部署腳本
```

## 更新流程

```bash
python3 build/pages_src.py      # 由原稿產生 site/*.html
python3 build/build_site.py     # 注入導覽列、頁尾、雜湊，重建離線包
python3 build/verify_site.py --quick
```

程式檔更新時，把 `機關王/2026_遙控程式_v2/` 與 `R4M_C車_循跡取料_2027.ts` 的新檔複製到 `site/downloads/`，再跑上面三步。

## 部署

- 容器定義在 `ccmtc-official/ccmtc-portal/docker-compose.yml` 的 `r4m` 服務（`r4m-guide`，只在 Docker 內網 expose 80）
- 通行碼由 portal 的 middleware 驗證（`src/lib/siteAuth.js` 的 `SITES.r4m`，cookie `r4m_pass`）
- 通行碼放在 NAS 的 `/volume1/docker/ccmtc-official/.env`：`R4M_PASS=$R4M_PASS`，由管理者手動填寫；沒填時 `/r4m/` 回 503，不會公開
- 首次上線需要同時部署 portal（新增 `/r4m` 路由與登入頁）
