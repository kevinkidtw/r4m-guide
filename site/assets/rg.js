/* ==========================================================================
   智創機器人程式說明站 (robot-guide) — 全站共用腳本 (rg.js)
   包含：深淺色模式切換 (rg-theme)、流體字級 A-/A/A+ (rg-fs)、賽前檢查清單記憶、OLED 模擬器共用
   所有 localStorage 讀寫皆包在 try/catch 中，無痕或 file:// 下也能正常運作。
   ========================================================================== */
(function () {
  var root = document.documentElement;

  function safeGet(key, fallback) {
    try {
      var v = localStorage.getItem(key);
      return v !== null ? v : fallback;
    } catch (e) {
      return fallback;
    }
  }

  function safeSet(key, val) {
    try {
      localStorage.setItem(key, val);
    } catch (e) {}
  }

  /* --- 1. 深淺色模式切換 (light / dark / auto) --- */
  var themeBtns = Array.prototype.slice.call(
    document.querySelectorAll('.rg-tool-btn[data-rg-theme]')
  );

  function applyTheme(t) {
    if (t === 'light' || t === 'dark') {
      root.setAttribute('data-theme', t);
    } else {
      t = 'auto';
      root.removeAttribute('data-theme');
    }
    themeBtns.forEach(function (btn) {
      var active = btn.getAttribute('data-rg-theme') === t;
      btn.setAttribute('aria-pressed', String(active));
      btn.classList.toggle('is-current', active);
    });
    safeSet('rg-theme', t);
  }

  if (themeBtns.length > 0) {
    themeBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        applyTheme(btn.getAttribute('data-rg-theme'));
      });
    });
    applyTheme(safeGet('rg-theme', 'auto'));
  }

  /* --- 2. 字級切換 (A- = 0.92, A = 1, A+ = 1.12) --- */
  var fsBtns = Array.prototype.slice.call(
    document.querySelectorAll('.rg-tool-btn[data-rg-fs]')
  );

  function applyFontSize(fs) {
    var allowed = { '0.92': '0.92', '1': '1', '1.12': '1.12' };
    var val = allowed[String(fs)] || '1';
    root.style.setProperty('--fs-user', val);
    fsBtns.forEach(function (btn) {
      var active = btn.getAttribute('data-rg-fs') === val;
      btn.setAttribute('aria-pressed', String(active));
      btn.classList.toggle('is-current', active);
    });
    safeSet('rg-fs', val);
  }

  if (fsBtns.length > 0) {
    fsBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        applyFontSize(btn.getAttribute('data-rg-fs'));
      });
    });
    applyFontSize(safeGet('rg-fs', '1'));
  }

  /* --- 3. 賽前檢查清單勾選記憶 (match/checklist.html) --- */
  var checkItems = Array.prototype.slice.call(
    document.querySelectorAll('.rg-check-item input[type="checkbox"][data-rg-check]')
  );

  if (checkItems.length > 0) {
    var savedChecks = {};
    try {
      var raw = safeGet('rg-checklist-r4m', '{}');
      savedChecks = JSON.parse(raw) || {};
    } catch (e) {
      savedChecks = {};
    }

    function syncCheckUI(input) {
      var label = input.closest('.rg-check-item');
      if (label) {
        label.classList.toggle('is-checked', !!input.checked);
      }
    }

    checkItems.forEach(function (input) {
      var id = input.getAttribute('data-rg-check');
      if (savedChecks[id] === true) {
        input.checked = true;
      }
      syncCheckUI(input);
      input.addEventListener('change', function () {
        savedChecks[id] = !!input.checked;
        syncCheckUI(input);
        safeSet('rg-checklist-r4m', JSON.stringify(savedChecks));
      });
    });

    var resetBtn = document.getElementById('rg-checklist-reset');
    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        savedChecks = {};
        checkItems.forEach(function (input) {
          input.checked = false;
          syncCheckUI(input);
        });
        safeSet('rg-checklist-r4m', '{}');
      });
    }
  }
})();
