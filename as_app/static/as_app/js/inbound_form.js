document.addEventListener("DOMContentLoaded", function () {
  /**
   * 사내 AS & 툴 입출고 관리 시스템: 입고 등록 스크립트 (Inbound Fast Form)
   * 1. 품목 바코드(TOOL-1-20 등) 연속 스캔 시:
   *    - 포커스 이동을 비동기 콜백이 아닌 0ms 동기식으로 처리하여 타건 갈라짐(L-1-20 잔류) 원천 차단
   *    - 시리얼이 비어 있는 행이 있으면 100% 일관되게 해당 행의 품목을 변경하고,
   *      시리얼이 입력된 행만 있을 때는 100% 일관되게 새 티켓(행)을 추가
   * 2. 박스 품목명(모델명) 바코드 오스캔 방어:
   *    - 시리얼 번호 근처의 품목명 바코드(예: 18ESE17Q, MPRO300GCD 등)가 찍히면
   *      시리얼 번호에서 즉시 제외하고 품목 자동 선택 또는 안내 토스트 표시
   * 3. 한글(IME) 100% 영문 QWERTY 자동 치환 및 연속 시리얼 쉼표(,) 분리 누적
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

  // ── 2. 품목 마스터 바코드(TOOL-1-20 등) 완전 분석 및 찌꺼기 제거기 ──
  function parseToolMasterBarcode(rawStr) {
    if (!rawStr) return { found: false };
    let s = convertHangulToEnglish(rawStr).toUpperCase().trim();
    s = s.replace(/[;_\-]/g, ':');

    // 쉼표로 구분된 토큰들 중 가장 마지막에 찍힌 마스터 바코드 탐색 (앞글자 T, TO, TOO 누락까지 모두 포착)
    const regexFull = /(?:T?O?O?L):(\d+):(\d+)/g;
    let match;
    let lastMatch = null;
    while ((match = regexFull.exec(s)) !== null) {
      lastMatch = match;
    }
    if (lastMatch) {
      return {
        found: true,
        brandId: lastMatch[1],
        toolId: lastMatch[2],
      };
    }

    const matchToolOnly = s.match(/(?:TOOL|OOL):(\d+)(?!:)/);
    if (matchToolOnly) {
      return {
        found: true,
        brandId: null,
        toolId: matchToolOnly[1],
      };
    }

    return { found: false };
  }

  function stripMasterBarcodeTokens(rawStr) {
    if (!rawStr) return '';
    const converted = convertHangulToEnglish(rawStr).toUpperCase();
    const tokens = converted.split(',').map(t => t.trim()).filter(Boolean);
    const cleanTokens = tokens.filter(tok => {
      const norm = tok.replace(/[;_\-]/g, ':');
      if (/^(?:T?O?O?L)?:?\d+:\d+$/.test(norm)) return false;
      if (/^(?:T?O?O?L):\d+$/.test(norm)) return false;
      if (/(?:T?O?O?L):\d+:\d+/.test(norm)) return false;
      return true;
    });
    return cleanTokens.join(', ');
  }

  // ── 3. 사운드 및 토스트 알림 ──
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
      gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
      osc.start();
      osc.stop(audioCtx.currentTime + duration);
    } catch (_) {}
  }

  function showToastNotification(msg, isWarning = false) {
    let toast = document.getElementById("barcode-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "barcode-toast";
      toast.style.cssText = "position:fixed; top:24px; right:24px; z-index:999999; color:#fff; font-weight:700; font-size:14px; padding:12px 20px; border-radius:8px; box-shadow:0 4px 16px rgba(0,0,0,0.2); transition:opacity 0.25s ease; pointer-events:none;";
      document.body.appendChild(toast);
    }
    toast.style.background = isWarning ? "#dc2626" : "#059669";
    toast.textContent = msg;
    toast.style.opacity = "1";
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
      toast.style.opacity = "0";
    }, 3000);
  }

  // ── 4. 브랜드 -> 툴 목록 비동기 동적 갱신 ──
  function updateToolOptions(brandSelect, targetToolId = null, callback = null) {
    const row = brandSelect.closest("tr");
    if (!row) return;

    const toolSelect = row.querySelector("select[name$='-tool']");
    if (!toolSelect) return;

    const brandId = brandSelect.value;
    if (!brandId) {
      toolSelect.innerHTML = '<option value="">---------</option>';
      if (callback) callback();
      return;
    }

    fetch(`/api/tools-by-brand/?brand_id=${brandId}`)
      .then((response) => response.json())
      .then((data) => {
        const currentToolId = targetToolId || toolSelect.value;
        toolSelect.innerHTML = '<option value="">---------</option>';

        if (data.tools && Array.isArray(data.tools)) {
          data.tools.forEach((tool) => {
            const option = document.createElement("option");
            option.value = tool.id;
            option.textContent = tool.model_name;
            if (String(tool.id) === String(currentToolId)) {
              option.selected = true;
            }
            toolSelect.appendChild(option);
          });
        }
        if (targetToolId) {
          toolSelect.value = String(targetToolId);
        }
        if (callback) callback();
      })
      .catch((err) => {
        console.error("Error fetching tools:", err);
        if (callback) callback();
      });
  }

  function getActiveInboundRows() {
    return Array.from(
      document.querySelectorAll("tr.form-row:not(.empty-form), tr.has_original:not(.empty-form), tr.dynamic-inventories:not(.empty-form)")
    );
  }

  function scrubAllSerialInputs() {
    document.querySelectorAll("input[name$='-serial'], input[name$='-serial_number']").forEach(inp => {
      const cleaned = stripMasterBarcodeTokens(inp.value);
      if (cleaned !== inp.value.replace(/^[, ]+|[, ]+$/g, '').trim()) {
        inp.value = cleaned ? cleaned + ', ' : '';
      }
    });
  }

  // ── 5. 품목 마스터 바코드 자동 선택 핸들러 (100% 일관된 행 선택 보장) ──
  function handleToolMasterBarcode(brandId, toolId) {
    if (!toolId) return;

    // 모든 시리얼 입력창에서 마스터 바코드 찌꺼기(TOOL-1-20 등) 즉시 청소
    scrubAllSerialInputs();

    let targetRow = null;
    const allRows = getActiveInboundRows();

    // 1순위: 이미 동일한 품목(toolId)이 선택된 행이 있다면 그 행으로 포커스
    targetRow = allRows.find(r => {
      const tSel = r.querySelector("select[name$='-tool']");
      return (tSel && String(tSel.value) === String(toolId)) || r.dataset.pendingToolId === String(toolId);
    });

    // 2순위: 시리얼 번호가 아직 비어있고 '시리얼번호 없음'도 체크되지 않은 행이 있다면 무조건 그 행의 품목을 변경!
    // (시리얼을 안 찍고 품목 바코드만 연속으로 찍을 때 빈 행이 증식하거나 랜덤하게 동작하는 현상 100% 해결)
    if (!targetRow) {
      targetRow = allRows.find(r => {
        const sInp = r.querySelector("input[name$='-serial'], input[name$='-serial_number']");
        const noSerialCb = r.querySelector("input[name$='-no_serial_number'], input[name$='-no_serial']");
        const hasNoSerialChecked = noSerialCb && noSerialCb.checked;
        const cleanVal = sInp ? stripMasterBarcodeTokens(sInp.value) : '';
        return !hasNoSerialChecked && !cleanVal;
      });
    }

    // 3순위: 모든 기존 행에 이미 시리얼이 입력되어 있거나 '시리얼번호 없음'이 체크되어 있다면 -> 새 티켓(행) 추가!
    if (!targetRow) {
      const addRowBtn = document.querySelector(".add-row a, tr.add-row a, .inline-related .add-row a");
      if (addRowBtn) {
        addRowBtn.click();
        const updatedRows = getActiveInboundRows();
        targetRow = updatedRows[updatedRows.length - 1];
      } else if (allRows.length > 0) {
        targetRow = allRows[allRows.length - 1];
      }
    }

    if (!targetRow) return;

    targetRow.dataset.pendingToolId = String(toolId);
    const brandSelect = targetRow.querySelector("select[name$='-brand']");
    const toolSelect = targetRow.querySelector("select[name$='-tool']");
    const serialInput = targetRow.querySelector("input[name$='-serial'], input[name$='-serial_number']");

    // 포커스를 비동기 fetch 완료 후가 아니라 지금 즉시(0ms 동기식) 이동시켜 다음 스캔 시 타건이 쪼개지지 않게 방어!
    if (serialInput) {
      const cleanVal = stripMasterBarcodeTokens(serialInput.value);
      serialInput.value = cleanVal ? cleanVal + ', ' : '';
      serialInput.focus();
    }

    function applySelection(bId, tId) {
      if (brandSelect && bId) {
        brandSelect.value = String(bId);
      }
      if (bId) {
        updateToolOptions(brandSelect, tId, function () {
          delete targetRow.dataset.pendingToolId;
          playBeep(2000, 0.08);

          const bText = brandSelect ? (brandSelect.options[brandSelect.selectedIndex]?.text || '') : '';
          const tText = toolSelect ? (toolSelect.options[toolSelect.selectedIndex]?.text || '') : '';
          showToastNotification(`품목 선택: ${bText} > ${tText}`);
        });
      }
    }

    if (brandId) {
      applySelection(brandId, toolId);
    } else {
      fetch(`/inventory/barcode-api/tool-info/?tool_id=${toolId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.success && data.brand_id) {
            applySelection(data.brand_id, toolId);
          } else {
            delete targetRow.dataset.pendingToolId;
          }
        })
        .catch((err) => {
          delete targetRow.dataset.pendingToolId;
          console.error("Error fetching tool info:", err);
        });
    }
  }

  // ── 5.1. 페이지 내 모든 시리얼 중복 검사 헬퍼 ──
  function isSerialAlreadyEnteredOnPage(serial, currentField = null) {
    const s = serial.trim().toUpperCase();
    if (!s) return false;
    const inputs = document.querySelectorAll("input[name$='-serial'], input[name$='-serial_number']");
    for (const inp of inputs) {
      if (inp === currentField) continue;
      const tokens = stripMasterBarcodeTokens(inp.value).split(',').map(t => t.trim()).filter(Boolean);
      if (tokens.includes(s)) {
        return true;
      }
    }
    return false;
  }

  // ── 6. 시리얼 검증 및 필드 누적 헬퍼 ──
  function validateAndAppendSerial(field, targetSerial, existingTokens) {
    const row = field.closest("tr");

    // 1) 마스터 바코드 조각인지 한 번 더 검증
    const parsed = parseToolMasterBarcode(targetSerial);
    if (parsed.found) {
      field.value = existingTokens.length > 0 ? existingTokens.join(', ') + ', ' : '';
      handleToolMasterBarcode(parsed.brandId, parsed.toolId);
      return;
    }

    // 2) 현재 입력란 내부 중복 검사
    if (existingTokens.includes(targetSerial)) {
      field.value = existingTokens.length > 0 ? existingTokens.join(', ') + ', ' : '';
      showToastNotification(`중복 시리얼: [${targetSerial}]은 이미 입력되어 있습니다.`, true);
      playBeep(400, 0.25);
      return;
    }

    // 3) 페이지 전체 다른 행 중복 검사
    if (isSerialAlreadyEnteredOnPage(targetSerial, field)) {
      field.value = existingTokens.length > 0 ? existingTokens.join(', ') + ', ' : '';
      showToastNotification(`중복 시리얼: [${targetSerial}]은 다른 행에 이미 입력되어 있습니다.`, true);
      playBeep(400, 0.25);
      return;
    }

    // 4) 백엔드 조회: 품목명(모델명) 바코드 오스캔 여부 및 기존 재고 여부 검증
    fetch(`/inventory/barcode-api/lookup/?serial=${encodeURIComponent(targetSerial)}`)
      .then(res => res.json())
      .then(data => {
        // [핵심] 박스에 적힌 품목명(모델명) 바코드가 찍힌 경우 시리얼란에서 즉시 제거!
        if (data.is_tool_model) {
          field.value = existingTokens.length > 0 ? existingTokens.join(', ') + ', ' : '';
          const toolSelect = row ? row.querySelector("select[name$='-tool']") : null;
          if (toolSelect && !toolSelect.value && data.brand_id && data.tool_id) {
            // 아직 품목이 선택되지 않은 행이었다면 해당 품목을 자동 선택해 줌
            handleToolMasterBarcode(data.brand_id, data.tool_id);
          } else {
            playBeep(400, 0.25);
            showToastNotification(`품목명 바코드 제외: [${data.tool_name}]은 품목명이므로 시리얼에서 제외되었습니다.`, true);
          }
          return;
        }

        if (data.found && data.is_stock) {
          field.value = existingTokens.length > 0 ? existingTokens.join(', ') + ', ' : '';
          showToastNotification(`재고 확인: [${targetSerial}] 출고 등록 화면으로 이동합니다.`, true);
          playBeep(1000, 0.15);
          setTimeout(() => {
            window.location.href = `/inventory/tool_inventory/outboundbatch/add/?serial=${encodeURIComponent(targetSerial)}`;
          }, 600);
          return;
        }

        // 정상 신규 시리얼 누적
        const updated = [...existingTokens, targetSerial];
        const finalVal = updated.join(', ') + ', ';
        field.value = finalVal;
        field.focus();
        field.setSelectionRange(finalVal.length, finalVal.length);
        playBeep(1400, 0.08);
      })
      .catch(() => {
        const updated = [...existingTokens, targetSerial];
        const finalVal = updated.join(', ') + ', ';
        field.value = finalVal;
        playBeep(1400, 0.08);
      });
  }

  // ── 7. 글로벌 & 시리얼 인풋 통합 스캔 버퍼 ──
  let scanBuffer = [];
  let lastKeyTime = 0;
  const SCAN_INTERVAL = 70;

  document.body.addEventListener("input", function (e) {
    if (e.target.matches("input[name$='-serial'], input[name$='-serial_number']")) {
      const raw = e.target.value;
      const converted = convertHangulToEnglish(raw).toUpperCase();
      if (raw !== converted) {
        const start = e.target.selectionStart;
        const end = e.target.selectionEnd;
        e.target.value = converted;
        try {
          e.target.setSelectionRange(start, end);
        } catch (_) {}
      }
    }
  });

  document.body.addEventListener("compositionend", function (e) {
    if (e.target.matches("input[name$='-serial'], input[name$='-serial_number']")) {
      e.target.value = convertHangulToEnglish(e.target.value).toUpperCase();
    }
  });

  document.body.addEventListener("keydown", function (e) {
    if (e.target.matches("input[name$='-serial'], input[name$='-serial_number']")) {
      if (e.key === "Enter") {
        e.preventDefault();
        e.stopPropagation();

        // 만약 포커스 이동 직전 window scanBuffer에 앞글자가 찍혔다면 복원 결합
        const now = performance.now();
        let prefix = "";
        if (scanBuffer.length > 0 && (now - lastKeyTime) < 150) {
          prefix = scanBuffer.join("");
        }
        scanBuffer = [];

        const raw = (prefix + e.target.value).trim();
        const converted = convertHangulToEnglish(raw).toUpperCase();

        // 1) 품목 마스터 바코드(TOOL-1-20 등) 감지
        const parsed = parseToolMasterBarcode(converted);
        if (parsed.found) {
          const cleaned = stripMasterBarcodeTokens(converted);
          e.target.value = cleaned ? cleaned + ', ' : '';
          handleToolMasterBarcode(parsed.brandId, parsed.toolId);
          return;
        }

        // 2) 일반 시리얼 번호 처리
        if (converted) {
          const cleanStr = stripMasterBarcodeTokens(converted);
          const serialTokens = cleanStr.split(',').map(s => s.trim()).filter(Boolean);
          if (serialTokens.length === 0) {
            e.target.value = '';
            return;
          }
          const targetSerial = serialTokens[serialTokens.length - 1];
          const existingTokens = serialTokens.slice(0, -1);
          validateAndAppendSerial(e.target, targetSerial, existingTokens);
        }
      }
    }
  });

  // ── 8. 글로벌 바코드 인터셉터 (포커스가 시리얼 인풋에 없을 때) ──
  window.addEventListener("keydown", function (e) {
    const activeEl = document.activeElement;
    if (activeEl && activeEl.matches && activeEl.matches("input[name$='-serial'], input[name$='-serial_number']")) {
      return;
    }
    if (activeEl && ['TEXTAREA'].includes(activeEl.tagName)) {
      return;
    }

    const now = performance.now();
    const gap = now - lastKeyTime;
    lastKeyTime = now;

    if (e.key === "Enter") {
      if (scanBuffer.length >= 3) {
        const rawScanned = scanBuffer.join("").trim();
        scanBuffer = [];
        e.preventDefault();
        e.stopPropagation();

        const converted = convertHangulToEnglish(rawScanned).toUpperCase();
        const parsed = parseToolMasterBarcode(converted);
        if (parsed.found) {
          handleToolMasterBarcode(parsed.brandId, parsed.toolId);
          return;
        }

        // 현재 포커스 가능한 시리얼 인풋 탐색
        const allInputs = Array.from(
          document.querySelectorAll("tr:not(.empty-form) input[name$='-serial']:not([disabled]), tr:not(.empty-form) input[name$='-serial_number']:not([disabled])")
        );
        const targetInput = allInputs[allInputs.length - 1];
        if (targetInput) {
          const existingTokens = stripMasterBarcodeTokens(targetInput.value).split(',').map(s => s.trim()).filter(Boolean);
          validateAndAppendSerial(targetInput, converted, existingTokens);
        }
      } else {
        scanBuffer = [];
      }
    } else if (e.key.length === 1) {
      if (gap <= SCAN_INTERVAL || scanBuffer.length === 0) {
        scanBuffer.push(e.key);
      } else {
        scanBuffer = [e.key];
      }
    }
  });

  // ── 9. 시리얼 없음 체크박스 제어 및 URL 파라미터 처리 ──
  function toggleSerialFields(row) {
    if (!row) return;
    const noSerialCheckbox = row.querySelector("input[name$='-no_serial_number'], input[name$='-no_serial']");
    const quantityField = row.querySelector("input[name$='-quantity']");
    const serialField = row.querySelector("input[name$='-serial_number'], input[name$='-serial']");

    if (noSerialCheckbox && quantityField && serialField) {
      const isChecked = noSerialCheckbox.checked;
      if (isChecked) {
        quantityField.disabled = false;
        quantityField.readOnly = false;
        quantityField.style.opacity = "1";
        quantityField.style.pointerEvents = "auto";
        quantityField.style.backgroundColor = "";

        serialField.disabled = true;
        serialField.readOnly = true;
        serialField.style.opacity = "0.3";
        serialField.style.pointerEvents = "none";
        serialField.value = "";
      } else {
        quantityField.disabled = false;
        quantityField.readOnly = true;
        quantityField.style.opacity = "0.5";
        quantityField.style.pointerEvents = "none";
        quantityField.style.backgroundColor = "#f3f4f6";
        quantityField.value = "1";

        serialField.disabled = false;
        serialField.readOnly = false;
        serialField.style.opacity = "1";
        serialField.style.pointerEvents = "auto";
      }
    }
  }

  document.querySelectorAll("tr.form-row, tr.dynamic-inventories").forEach(row => {
    toggleSerialFields(row);
  });

  document.body.addEventListener("change", function (e) {
    if (e.target.matches("select[name$='-brand']")) {
      const row = e.target.closest("tr");
      const toolSelect = row.querySelector("select[name$='-tool']");
      if (toolSelect) toolSelect.value = "";
      updateToolOptions(e.target);
    } else if (e.target.matches("input[name$='-no_serial_number'], input[name$='-no_serial']")) {
      const row = e.target.closest("tr");
      toggleSerialFields(row);
    }
  });

  document.addEventListener("formset:added", function (event) {
    toggleSerialFields(event.target);
  });

  // URL 파라미터(?serial=..., ?initial_master=...) 처리
  const urlParams = new URLSearchParams(window.location.search);
  const initialMaster = urlParams.get('initial_master');
  const initialSerial = urlParams.get('serial');

  if (initialMaster) {
    const parsed = parseToolMasterBarcode(initialMaster);
    if (parsed.found) {
      setTimeout(() => {
        handleToolMasterBarcode(parsed.brandId, parsed.toolId);
      }, 100);
    }
  }

  if (initialSerial) {
    const firstSerialInput = document.querySelector("input[name$='-serial'], input[name$='-serial_number']");
    if (firstSerialInput) {
      setTimeout(() => {
        validateAndAppendSerial(firstSerialInput, convertHangulToEnglish(initialSerial).trim().toUpperCase(), []);
      }, 150);
    }
  }
});
