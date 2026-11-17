#!/usr/bin/env bash
#
# 機關王 R4M 程式說明站 (r4m-guide) 一鍵部署腳本
# 流程：本機編譯與驗證 → rsync 同步內容 → 重啟 r4m 容器 → 線上路由驗證
#
# 說明：
# 1. 本站為純靜態網站，透過 rsync 增量同步檔案至 NAS 的 /volume1/docker/r4m-guide
# 2. 容器定義在 ccmtc-official 的 docker-compose.yml（服務名 r4m）
# 3. 本腳本走 SSH 金鑰驗證與限定指令 sudo NOPASSWD，不需輸入密碼
# 4. 本站公開（2026-11 起），路徑與存取設定見 ccmtc-portal/src/config/sites.mjs
#
# 注意：本腳本嚴禁在此工作流中直接執行。

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

REMOTE_USER="kevinkid"
# 預設走 Tailscale（公網 22 埠已關閉）。在家可改走內網：export NAS_HOST=192.168.68.113
REMOTE_HOST="${NAS_HOST:-100.96.102.35}"
HOST="${REMOTE_USER}@${REMOTE_HOST}"
SSH_OPTS=(-o StrictHostKeyChecking=no -o ConnectTimeout=20)
DOCKER_BIN="/var/packages/ContainerManager/target/usr/bin"
REMOTE_DIR="/volume1/docker/r4m-guide"
COMPOSE_DIR="/volume1/docker/ccmtc-official"
SITE_URL="https://ccmtc.mooo.com/r4m/"

echo "=== 步驟 1：連線檢查 ==="
if ! ssh "${SSH_OPTS[@]}" -o BatchMode=yes "${HOST}" true 2>/dev/null; then
    echo "❌ 金鑰登入失敗（${HOST}）。"
    echo "   公網 22 埠已關，請確認 Tailscale 已連線，"
    echo "   或改走內網：export NAS_HOST=192.168.68.113"
    exit 1
fi
echo "✅ 金鑰登入正常"

echo
echo "=== 步驟 2：（已取消）本站自 2026-11 起公開，不再檢查通行碼 ==="

echo
echo "=== 步驟 3：本機編譯、驗證與同步站台內容 ==="
echo ">> 由原稿產生頁面..."
python3 "${SCRIPT_DIR}/build/pages_src.py"
echo ">> 執行本機靜態建置..."
python3 "${SCRIPT_DIR}/build/build_site.py"

echo ">> 執行本機靜態驗證..."
python3 "${SCRIPT_DIR}/build/verify_site.py" --quick

echo ">> 同步檔案至 NAS..."
ssh "${SSH_OPTS[@]}" "${HOST}" "mkdir -p '${REMOTE_DIR}'"
rsync -az --delete --stats \
      -e "ssh ${SSH_OPTS[*]}" \
      --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r \
      --exclude '.DS_Store' \
      ./site/ "${HOST}:${REMOTE_DIR}/site/"
rsync -az --inplace -e "ssh ${SSH_OPTS[*]}" --chmod=Fu=rw,Fgo=r ./nginx.conf "${HOST}:${REMOTE_DIR}/nginx.conf"
ssh "${SSH_OPTS[@]}" "${HOST}" "chmod -R a+rX '${REMOTE_DIR}'"
echo "✅ 靜態檔案同步完成"

echo
echo "=== 步驟 4：重啟 r4m 容器 ==="
# 輸出寫入臨時日誌檔再判斷退出碼，避免 pipe 吃掉錯誤碼（規範 05 鐵則）
ssh "${SSH_OPTS[@]}" "${HOST}" "
set -e
cd '${COMPOSE_DIR}'
LOG=/tmp/r4m-compose.log
sudo ${DOCKER_BIN}/docker-compose up -d r4m > \"\$LOG\" 2>&1 || {
  echo '❌ docker-compose 失敗，最後 30 行：'; tail -30 \"\$LOG\"; rm -f \"\$LOG\"; exit 1; }
tail -10 \"\$LOG\"; rm -f \"\$LOG\"
sudo ${DOCKER_BIN}/docker exec r4m-guide nginx -t
sudo ${DOCKER_BIN}/docker exec r4m-guide nginx -s reload
" < /dev/null
echo "✅ 容器啟動成功且 nginx 設定測試通過"

echo
echo "=== 步驟 5：線上路由驗證（公開站） ==="
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "${SITE_URL}" || echo 000)
echo "${SITE_URL} -> HTTP ${code}"
case "${code}" in
  200)
    echo "✅ 正常：公開站可直接瀏覽"
    ;;
  302|307|503)
    echo "❌ 仍在要求通行碼（${code}）：請確認 ccmtc-portal 已部署 sites.mjs 公開設定"
    exit 1
    ;;
  *)
    echo "⚠️  非預期的回應狀態碼 (${code})，請檢查 portal 與 r4m-guide 容器日誌"
    exit 1
    ;;
esac
