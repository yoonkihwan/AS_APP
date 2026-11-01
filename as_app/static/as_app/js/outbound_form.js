document.addEventListener("DOMContentLoaded", function () {
  /**
   * 출고 등록 인라인 폼셋 스크립트 (Outbound Fast Form)
   * 1. 브랜드 선택 -> 품목 목록 갱신 -> 재고(시리얼) 목록 및 현재 재고량 갱신
   * 2. 바코드 스캔 시:
   *    - 동일 품목 행이 이미 있으면 해당 행에 시리얼 체크 추가
   *    - 빈 행이 있으면 빈 행에 품목/시리얼 세팅
   *    - 다른 품목이 이미 선택되어 빈 행이 없으면 자동으로 새 티켓(행)을 추가하여 동시 출고 지원
   * 3. 박스에 인쇄된 품목명 바코드나 마스터 바코드(TOOL-...) 오스캔 시 시리얼로 오인식하지 않고 자동 차단
   */

  // ── 1. 한글(2벌식) -> 영문 QWERTY 역변환 ──
  const CHO = ['r', 'R', 's', 'e', 'E', 'f', 'a', 'q', 'Q', 't', 'T', 'd', 'w', 'W', 'c', 'z', 'x', 'v', 'g'];
  const JUNG = ['k', 'o', 'i', 'O', 'j', 'p', 'u', 'P', 'h', 'hk', 'ho', 'hl', 'y', 'n', 'nj', 'np', 'nl', 'b', 'm', 'ml', 'l'];
  const JONG = ['', 'r', 'R', 'rt', 's', 'sw', 'sg', 'e', 'f', 'fr', 'fa', 'fq', 'ft', 'fx', 'fv', 'fg', 'a', 'q', 'qt', 't', 'T', 'd', 'w', 'c', 'z', 'x', 'v', 'g'];
  const JAMO_TO_ENG = {
    'ㄱ': 'r', 'ㄲ': 'R', 'ㄴ': 's', 'ㄷ': 'e', 'ㄸ': 'E', 'ㄹ': 'f',
    'ㅁ': 'a', 'ㅂ': 'q', 'ㅃ': 'Q', 'ㅅ': 't', 'ㅆ': 'T', 'ㅇ': 'd',
    'ㅈ': 'w', 'ㅉ': 'W', 'ㅊ': 'c', 'ㅋ': 'z', 'ㅌ': 'x', 'ㅍ': 'v', 'ㅎ': 'g',
    'ㅏ': 'k', 'ㅐ': 'o', 'ㅑ': 'i', 'ㅒ': 'O', 'ㅓ': 'j', 'ㅔ': 'p',
    'ㅕ': 'u', 'ㅖ': 'P', 'ㅗ': 'h', 'ㅘ': 'hk', 'ㅙ': 'ho', 'ㅚ': 'hl',
    'ㅛ': 'y', 'ㅜ': 'n', 'ㅝ': 'nj', 'ㅞ': 'np', 'ㅟ': 'nl', 'ㅠ': 'b',
    'ㅡ': 'm', 'ㅢ': 'ml', 'ㅣ': 'l',
    'ㄳ': 'rt', 'ㄵ': 'sw', 'ㄶ': 'sg', 'ㄺ': 'fr', 'ㄻ': 'fa',
    'ㄼ': 'fq', 'ㄽ': 'ft', 'ㄾ': 'fx', 'ㄿ': 'fv', 'ㅀ': 'fg', 'ㅄ': 'qt'
  };

  function convertHangulToEnglish(str) {
    if (!str) return '';
    let result = '';
    for (let i = 0; i < str.length; i++) {
      const code = str.charCodeAt(i);
      if (code >= 0xAC00 && code <= 0xD7A3) {
        const offset = code - 0xAC00;
        result += CHO[Math.floor(offset / 588)] + JUNG[Math.floor((offset % 588) / 28)] + JONG[offset % 28];
      } else if (JAMO_TO_ENG[str[i]]) {
        result += JAMO_TO_ENG[str[i]];
      } else {
        result += str[i];
      }
    }
    return result;
  }

  function isMasterBarcode(str) {
    const norm = str.replace(/[;_\-]/g, ':').toUpperCase();
    return /^(?:T?O?O?L)?:?\d+:\d+$/.test(norm) || norm.startsWith("TOOL:") || norm.startsWith("OOL:");
  }

  // ── 2. 사운드 및 토스트 알림 ──
  let audioCtx = null;
  function playBeep(freq = 1500, duration = 0.08) {
    try {
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      if (audioCtx.state === 'suspended') audioCtx.resume();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.frequency.value = freq;
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
      osc.start();
      osc.stop(audioCtx.currentTime + duration);
    } catch (e) {}
  }

  function showToast(msg, isWarning = false) {
    let toast = document.getElementById("outbound-barcode-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "outbound-barcode-toast";
      toast.style.cssText = "position:fixed; top:24px; right:24px; z-index:999999; color:#fff; font-weight:700; font-size:14px; padding:12px 20px; border-radius:8px; box-shadow:0 4px 16px rgba(0,0,0,0.2); transition:opacity 0.25s ease; pointer-events:none;";
      document.body.appendChild(toast);
    }
    toast.style.background = isWarning ? "#dc2626" : "#4f46e5";
    toast.textContent = msg;
    toast.style.opacity = "1";
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
      toast.style.opacity = "0";
    }, 3000);
  }

  // ── 3. 브랜드 -> 툴 -> 시리얼 목록 로드 ──
  function updateToolOptions(row, brandId, targetToolId = null, onComplete = null) {
    const toolSelect = row.querySelector("select[name$='-tool']");
    if (!toolSelect) return;

    if (!brandId) {
      toolSelect.innerHTML = '<option value="">---------</option>';
      if (onComplete) onComplete();
      return;
    }

    fetch(`/api/tools-by-brand/?brand_id=${brandId}`)
      .then((response) => response.json())
      .then((data) => {
        const currentToolId = targetToolId || toolSelect.value;
        toolSelect.innerHTML = '<option value="">---------</option>';

        data.tools.forEach((tool) => {
          const option = document.createElement("option");
          option.value = tool.id;
          option.textContent = tool.model_name;
          if (String(tool.id) === String(currentToolId)) {
            option.selected = true;
          }
          toolSelect.appendChild(option);
        });

        if (targetToolId) {
          toolSelect.value = String(targetToolId);
        }

        if (onComplete) onComplete();
      })
      .catch((err) => {
        console.error("Error fetching tools:", err);
        if (onComplete) onComplete();
      });
  }

  function updateInventoryOptions(row, toolId, targetSerial = null) {
    const inventoryTd = row.querySelector(".field-inventories");
    if (!inventoryTd) return;

    const currentStockInput = row.querySelector("input[name$='-current_stock']");
    const rowPrefix = row.id || "";

    if (targetSerial) {
      if (!row._pendingSerials) row._pendingSerials = new Set();
      row._pendingSerials.add(targetSerial.trim().toUpperCase());
    }

    if (!toolId) {
      Array.from(inventoryTd.querySelectorAll('input[type="checkbox"]')).forEach(cb => {
        const wrapperDiv = cb.closest('div');
        if (wrapperDiv) wrapperDiv.remove();
      });
      if (currentStockInput) currentStockInput.value = "0";
      updateQuantityLogic(row);
      return;
    }

    fetch(`/api/inventory-by-tool/?tool_id=${toolId}`)
      .then((response) => response.json())
      .then((data) => {
        delete row.dataset.pendingToolId;

        const existingCheckboxes = Array.from(inventoryTd.querySelectorAll('input[type="checkbox"]'));
        const checkedValues = existingCheckboxes.filter(cb => cb.checked).map(cb => String(cb.value));
        const checkedSerials = existingCheckboxes
          .filter(cb => cb.checked && cb.getAttribute('data-serial'))
          .map(cb => cb.getAttribute('data-serial').trim().toUpperCase());

        if (row._pendingSerials) {
          row._pendingSerials.forEach(s => {
            if (!checkedSerials.includes(s)) checkedSerials.push(s);
          });
          row._pendingSerials.clear();
        }

        existingCheckboxes.forEach(cb => {
          const wrapperDiv = cb.closest('div');
          if (wrapperDiv) wrapperDiv.remove();
        });

        const count = data.inventory.length;
        if (currentStockInput) currentStockInput.value = count;

        let container = inventoryTd.querySelector('.dynamic-checkbox-container');
        if (!container) {
          container = document.createElement('div');
          container.className = 'dynamic-checkbox-container';
          container.style.marginTop = '8px';
          container.style.maxHeight = '150px';
          container.style.overflowY = 'auto';
          inventoryTd.appendChild(container);
        } else {
          container.innerHTML = '';
        }

        data.inventory.forEach((inv, index) => {
          const wrapper = document.createElement("div");
          wrapper.style.display = "flex";
          wrapper.style.alignItems = "center";
          wrapper.style.marginBottom = "4px";
          wrapper.style.padding = "2px 4px";
          wrapper.style.borderRadius = "4px";
          wrapper.style.transition = "background-color 0.3s ease";

          const cb = document.createElement("input");
          cb.type = "checkbox";
          cb.name = rowPrefix + "-inventories";
          cb.value = inv.id;
          cb.id = rowPrefix + "-inventories_" + index;
          const invSerial = (inv.serial || '').trim();
          cb.setAttribute('data-serial', invSerial);

          if (
            checkedValues.includes(String(inv.id)) ||
            (invSerial && checkedSerials.includes(invSerial.toUpperCase()))
          ) {
            cb.checked = true;
            wrapper.style.backgroundColor = "rgba(16, 185, 129, 0.2)";
          }

          const lbl = document.createElement("label");
          lbl.htmlFor = cb.id;
          lbl.textContent = invSerial ? ` ${invSerial}` : ` S/N: 없음 (${inv.id.substring(0, 8)}...)`;
          lbl.style.marginLeft = "8px";
          lbl.style.fontSize = "0.875rem";
          lbl.style.cursor = "pointer";

          wrapper.appendChild(cb);
          wrapper.appendChild(lbl);
          container.appendChild(wrapper);
        });

        updateQuantityLogic(row);

        if (targetSerial) {
          playBeep(1800, 0.12);
        }
      })
      .catch((err) => {
        delete row.dataset.pendingToolId;
        console.error("Error fetching inventory:", err);
      });
  }

  function updateQuantityLogic(row) {
    const quantityInput = row.querySelector("input[name$='-quantity']");
    if (!quantityInput) return;

    let hasSerial = false;
    let hasItems = false;
    const allLabels = row.querySelectorAll(".field-inventories label");
    if (allLabels.length > 0) {
      hasItems = true;
      allLabels.forEach(lbl => {
        if (!lbl.textContent.includes("S/N: 없음")) {
          hasSerial = true;
        }
      });
    }

    const checkedBoxes = row.querySelectorAll("input[type='checkbox'][name$='-inventories']:checked");
    const selectedCount = checkedBoxes.length;

    quantityInput.style.backgroundColor = 'transparent';
    quantityInput.style.color = 'inherit';

    if (!hasItems || hasSerial) {
      quantityInput.readOnly = true;
      quantityInput.style.pointerEvents = 'none';
      quantityInput.style.opacity = '0.5';

      if (hasSerial) {
        row.querySelectorAll("input[type='checkbox'][name$='-inventories']").forEach(cb => {
          cb.disabled = false;
        });
      }

      if (selectedCount > 0) {
        quantityInput.value = selectedCount;
      } else {
        quantityInput.value = 1;
      }
    } else {
      quantityInput.readOnly = false;
      quantityInput.style.pointerEvents = 'auto';
      quantityInput.style.opacity = '1';

      row.querySelectorAll("input[type='checkbox'][name$='-inventories']").forEach(cb => {
        cb.disabled = true;
        cb.checked = false;
      });
    }
  }

  function getActiveTicketRows() {
    return Array.from(
      document.querySelectorAll("tr.form-row:not(.empty-form), tr.dynamic-tickets:not(.empty-form)")
    );
  }

  // ── 4. 바코드 스캔 처리 핵심 함수 (다중 품목 자동 행 추가 지원) ──
  function handleScannedSerial(rawSerial) {
    const serial = convertHangulToEnglish(rawSerial).trim().toUpperCase();
    if (!serial) return;

    // 0. 마스터 바코드(TOOL-1-20 등)가 출고 화면에서 찍힌 경우 무시
    if (isMasterBarcode(serial)) {
      playBeep(400, 0.2);
      showToast("품목 바코드입니다. 출고할 장비의 시리얼 번호 바코드를 스캔하십시오.", true);
      return;
    }

    // 1. 현재 화면에 이미 렌더링된 체크박스 중 시리얼 일치 항목 검색
    const allCbs = Array.from(document.querySelectorAll("input[type='checkbox'][name$='-inventories']"));
    const matchedCb = allCbs.find(cb => {
      const s = (cb.getAttribute('data-serial') || '').trim().toUpperCase();
      if (s && s === serial) return true;
      const lbl = document.querySelector(`label[for='${cb.id}']`);
      return lbl && lbl.textContent.trim().toUpperCase() === serial;
    });

    if (matchedCb) {
      const wasChecked = matchedCb.checked;
      matchedCb.checked = true;
      const row = matchedCb.closest("tr");
      if (row) updateQuantityLogic(row);

      const wrapper = matchedCb.closest("div");
      if (wrapper) {
        wrapper.style.backgroundColor = "rgba(16, 185, 129, 0.25)";
        wrapper.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      playBeep(1800, 0.1);
      showToast(wasChecked ? `이미 선택된 시리얼입니다: ${serial}` : `출고 선택 완료: ${serial}`);
      return;
    }

    // 2. 화면에 없다면 -> API로 품목 정보 조회 후 행 탐색 또는 새 티켓(행) 추가
    fetch(`/inventory/barcode-api/lookup/?serial=${encodeURIComponent(serial)}`)
      .then(res => res.json())
      .then(data => {
        // 박스의 품목명(모델명) 바코드가 찍힌 경우 시리얼로 오인식하지 않고 즉시 차단!
        if (data.is_tool_model) {
          playBeep(400, 0.25);
          showToast(`품목명 바코드 제외: [${data.tool_name}]은 품목명입니다. 시리얼 바코드를 스캔하십시오.`, true);
          return;
        }

        if (!data.success || !data.found) {
          playBeep(300, 0.25);
          showToast(`미등록 시리얼: [${serial}]은 재고에 등록되지 않은 번호입니다.`, true);
          return;
        }

        if (!data.is_stock) {
          playBeep(300, 0.25);
          showToast(`출고 불가: [${serial}]은 이미 '${data.status}' 처리된 장비입니다.`, true);
          return;
        }

        const targetToolId = String(data.tool_id);
        let rows = getActiveTicketRows();

        // (A) 이미 동일한 품목(tool_id)이 선택되어 있거나 로딩 중인 행이 있는지 확인
        let targetRow = rows.find(r => {
          const toolSel = r.querySelector("select[name$='-tool']");
          return (toolSel && String(toolSel.value) === targetToolId) || r.dataset.pendingToolId === targetToolId;
        });

        if (targetRow) {
          updateInventoryOptions(targetRow, data.tool_id, data.serial);
          showToast(`출고 추가: [${data.tool_name}] S/N: ${data.serial}`);
          return;
        }

        // (B) 아직 브랜드/품목이 선택되지 않은 완전히 비어있는 행 찾기
        targetRow = rows.find(r => {
          const brandSel = r.querySelector("select[name$='-brand']");
          const toolSel = r.querySelector("select[name$='-tool']");
          return toolSel && !toolSel.value && (!brandSel || !brandSel.value) && !r.dataset.pendingToolId;
        });

        // (C) 비어있는 행이 없다면(이전 품목이 이미 들어있다면) -> 절대 덮어쓰지 않고 '새 티켓(행) 추가' 클릭!
        if (!targetRow) {
          const addRowBtn = document.querySelector(".add-row a, tr.add-row a, .inline-related .add-row a");
          if (addRowBtn) {
            addRowBtn.click();
            rows = getActiveTicketRows();
            targetRow = rows[rows.length - 1];
          }
        }

        if (targetRow) {
          targetRow.dataset.pendingToolId = targetToolId;
          if (!targetRow._pendingSerials) targetRow._pendingSerials = new Set();
          targetRow._pendingSerials.add(data.serial.trim().toUpperCase());

          const brandSelect = targetRow.querySelector("select[name$='-brand']");
          if (brandSelect && data.brand_id) {
            brandSelect.value = String(data.brand_id);
            updateToolOptions(targetRow, data.brand_id, data.tool_id, () => {
              updateInventoryOptions(targetRow, data.tool_id, data.serial);
            });
          } else {
            updateInventoryOptions(targetRow, data.tool_id, data.serial);
          }
          showToast(`티켓 추가: [${data.tool_name}] S/N: ${data.serial}`);
        }
      })
      .catch(err => console.error("Error looking up scanned serial:", err));
  }

  // URL 파라미터(?serial=...) 처리
  const urlParams = new URLSearchParams(window.location.search);
  const initialSerial = urlParams.get('serial');
  if (initialSerial) {
    setTimeout(() => {
      handleScannedSerial(initialSerial);
    }, 300);
  }

  // ── 5. 출고날짜 오염 방어 ──
  const releaseDateInput = document.querySelector("input[name='release_date']");
  if (releaseDateInput && document.activeElement === releaseDateInput) {
    releaseDateInput.blur();
  }
  let initialReleaseDate = releaseDateInput ? releaseDateInput.value : "";

  // ── 6. 글로벌 바코드 스캐너 리스너 (70ms 이하 스캔) ──
  let scanBuffer = [];
  let lastKeyTime = 0;
  const SCAN_INTERVAL = 70;

  window.addEventListener("keydown", function(e) {
    const activeEl = document.activeElement;
    if (activeEl && ['TEXTAREA'].includes(activeEl.tagName)) return;
    if (activeEl && activeEl.matches && activeEl.matches("input[name$='-usage_process']")) return;

    const now = performance.now();
    const gap = now - lastKeyTime;
    lastKeyTime = now;

    if (e.key === "Enter") {
      if (scanBuffer.length >= 3) {
        const scanned = scanBuffer.join("").trim();
        scanBuffer = [];
        e.preventDefault();
        e.stopPropagation();

        if (releaseDateInput && releaseDateInput.value !== initialReleaseDate) {
          releaseDateInput.value = initialReleaseDate;
        }

        handleScannedSerial(scanned);
      } else {
        scanBuffer = [];
      }
    } else if (e.key.length === 1) {
      if (gap <= SCAN_INTERVAL) {
        if (activeEl && activeEl.matches && activeEl.matches("input[name='release_date'], input[type='text'], input[type='search']")) {
          e.preventDefault();
        }
        scanBuffer.push(e.key);
      } else {
        scanBuffer = [e.key];
      }
    }
  });

  // ── 7. 수동 드롭다운 및 수량 변경 이벤트 위임 ──
  document.body.addEventListener("change", function (e) {
    if (e.target.matches("select[name$='-brand']")) {
      const row = e.target.closest("tr");
      const toolSelect = row.querySelector("select[name$='-tool']");
      if (toolSelect) toolSelect.value = "";
      updateToolOptions(row, e.target.value);
      updateInventoryOptions(row, null);
    }

    if (e.target.matches("select[name$='-tool']")) {
      const row = e.target.closest("tr");
      updateInventoryOptions(row, e.target.value);
    }

    if (e.target.matches("input[type='checkbox'][name$='-inventories']")) {
      const row = e.target.closest("tr");
      updateQuantityLogic(row);
    }

    if (e.target.matches("input[name$='-quantity']")) {
      const row = e.target.closest("tr");
      const currentStockInput = row.querySelector("input[name$='-current_stock']");
      if (currentStockInput && currentStockInput.value) {
        const maxStock = parseInt(currentStockInput.value, 10) || 0;
        let val = parseInt(e.target.value, 10);
        if (!isNaN(val) && maxStock > 0 && val > maxStock) {
          e.target.value = maxStock;
          alert("입력한 수량이 현재 재고(" + maxStock + "개)를 초과하여 자동 조정되었습니다.");
        }
      }
    }
  });

  document.body.addEventListener("input", function (e) {
    if (e.target.matches("input[name$='-quantity']")) {
      const row = e.target.closest("tr");
      const currentStockInput = row.querySelector("input[name$='-current_stock']");
      if (currentStockInput && currentStockInput.value) {
        const maxStock = parseInt(currentStockInput.value, 10) || 0;
        let val = parseInt(e.target.value, 10);
        if (!isNaN(val) && maxStock > 0 && val > maxStock) {
          e.target.value = maxStock;
        }
      }
    }
  });
});
