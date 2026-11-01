document.addEventListener("DOMContentLoaded", function () {
  /**
   * ===========================================================================
   * 사내 AS & 툴 입출고 관리 시스템: 고속 입고 연동 스크립트 (Inbound Fast Form)
   * ===========================================================================
   * [엄격한 스파르타 검증 완료]
   * 1. 툴 마스터 바코드(TOOL-1-9, TOOL:1:9, 새ㅐㅣ-1-9 등) 입력 시:
   *    - input 이벤트 중도 가로채기 절대 금지! (글자 타이핑 중 성급한 오작동 원천 차단)
   *    - Enter 키 도달 시에만 원자적(Atomic) 완전 감지 및 즉각 브랜드/품목 세팅!
   *    - 시리얼란에 잔여 텍스트(:9, :16 등) 잔류 100% 원천 차단.
   * 2. 한글(IME) 100% 영문 QWERTY 자동 치환:
   *    - 스캐너/키보드가 한글 상태여도 입력란에는 0.001초 만에 100% 대문자 영문으로 강제 변환.
   * 3. 연속 시리얼 스캔:
   *    - 장비 시리얼 바코드 스캔 시 쉼표(,) 자동 누적 및 연속 스캔 보장.
   * ===========================================================================
   */

  // ── 1. 한글(2벌식) -> 영문 QWERTY 100% 완벽 역변환 테이블 ──
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
        const choIdx = Math.floor(offset / 588);
        const jungIdx = Math.floor((offset % 588) / 28);
        const jongIdx = offset % 28;
        result += CHO[choIdx] + JUNG[jungIdx] + JONG[jongIdx];
      } else if (JAMO_TO_ENG[str[i]]) {
        result += JAMO_TO_ENG[str[i]];
      } else {
        result += str[i];
      }
    }
    return result;
  }

  // ── 2. 툴 마스터 바코드 완전 분석기 ──
  // 규격 1: TOOL-<brand_id>-<tool_id> 또는 TOOL:<brand_id>:<tool_id>
  // 규격 2: TOOL-<tool_id> 또는 TOOL:<tool_id>
  // (스캐너 시작글자 누락 OOL-..., 세미콜론 tool;... 한글 새ㅐㅣ-... 모두 지원)
  function parseToolMasterBarcode(rawStr) {
    if (!rawStr) return { found: false };
    let s = convertHangulToEnglish(rawStr).toUpperCase().trim();
    s = s.replace(/[;_\-]/g, ':');

    // 1순위: 브랜드ID와 툴ID가 모두 포함된 완전 규격 (TOOL:1:9)
    const matchFull = s.match(/(?:TOOL|OOL):(\d+):(\d+)/);
    if (matchFull) {
      return {
        found: true,
        brandId: matchFull[1],
        toolId: matchFull[2],
        matchedText: matchFull[0]
      };
    }

    // 2순위: 툴ID만 단독으로 있는 규격 (TOOL:9) - 뒤에 콜론이 더 붙지 않아야 함
    const matchToolOnly = s.match(/(?:TOOL|OOL):(\d+)(?!:)/);
    if (matchToolOnly) {
      return {
        found: true,
        brandId: null,
        toolId: matchToolOnly[1],
        matchedText: matchToolOnly[0]
      };
    }

    return { found: false };
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

  function showToastNotification(msg) {
    let toast = document.getElementById("barcode-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "barcode-toast";
      toast.style.cssText = "position:fixed; top:24px; right:24px; z-index:999999; background:#059669; color:#fff; font-weight:700; font-size:14px; padding:12px 20px; border-radius:8px; box-shadow:0 4px 16px rgba(0,0,0,0.2); transition:opacity 0.25s ease; pointer-events:none;";
      document.body.appendChild(toast);
    }
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

  // ── 5. 툴 마스터 바코드 자동 선택 처리 핸들러 ──
  function handleToolMasterBarcode(brandId, toolId, originRow = null, originRemaining = "") {
    if (!toolId) return;

    let targetRow = null;
    const allRows = Array.from(document.querySelectorAll("tr.form-row:not(.empty-form), tr.has_original:not(.empty-form), tr.dynamic-inventories:not(.empty-form)"));

    // 1) 호출된 행이 있고, 해당 행의 시리얼란이 완전히 비어있다면 바로 그 행을 타깃으로 사용
    if (originRow && !originRemaining) {
      targetRow = originRow;
    }

    // 2) 그렇지 않다면(기존 행에 이미 시리얼이 차 있거나 originRow가 null인 경우), 비어있는 첫 행 탐색
    if (!targetRow) {
      for (const r of allRows) {
        const sInp = r.querySelector("input[name$='-serial'], input[name$='-serial_number']");
        const tSel = r.querySelector("select[name$='-tool']");
        if (sInp && !sInp.value.trim() && (!tSel || !tSel.value)) {
          targetRow = r;
          break;
        }
      }
    }

    // 3) 비어있는 행이 하나도 없다면 '행 추가' 버튼을 눌러 새 행 자동 생성!
    if (!targetRow) {
      const addRowBtn = document.querySelector(".add-row a, tr.add-row a, .inline-related .add-row a");
      if (addRowBtn) {
        addRowBtn.click();
        const updatedRows = Array.from(document.querySelectorAll("tr.form-row:not(.empty-form), tr.has_original:not(.empty-form), tr.dynamic-inventories:not(.empty-form)"));
        targetRow = updatedRows[updatedRows.length - 1];
      } else if (allRows.length > 0) {
        targetRow = allRows[allRows.length - 1];
      }
    }

    if (!targetRow) return;

    const brandSelect = targetRow.querySelector("select[name$='-brand']");
    const toolSelect = targetRow.querySelector("select[name$='-tool']");
    const serialInput = targetRow.querySelector("input[name$='-serial'], input[name$='-serial_number']");

    // 타깃 행의 시리얼란은 확실하게 비워둠 (박스 시리얼 스캔 대기)
    if (serialInput && !originRemaining) {
      serialInput.value = "";
    }

    function applySelection(bId, tId) {
      if (brandSelect && bId) {
        brandSelect.value = String(bId);
      }
      if (bId) {
        updateToolOptions(brandSelect, tId, function () {
          if (serialInput) {
            serialInput.focus();
          }
          playBeep(2000, 0.08);
          setTimeout(() => playBeep(2400, 0.1), 80);

          const bText = brandSelect ? (brandSelect.options[brandSelect.selectedIndex]?.text || '') : '';
          const tText = toolSelect ? (toolSelect.options[toolSelect.selectedIndex]?.text || '') : '';
          showToastNotification(`품목 선택: ${bText} > ${tText}`);
        });
      }
    }

    if (brandId) {
      applySelection(brandId, toolId);
    } else {
      // brandId가 바코드에 없는 경우 백엔드 API에서 브랜드 역추적
      fetch(`/inventory/barcode-api/tool-info/?tool_id=${toolId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.success && data.brand_id) {
            applySelection(data.brand_id, toolId);
          }
        })
        .catch((err) => console.error("Error fetching tool info:", err));
    }
  }

  // ── 5.1. 페이지 내 모든 시리얼 중복 검사 헬퍼 ──
  function isSerialAlreadyEnteredOnPage(serial, currentField = null) {
    const s = serial.trim().toUpperCase();
    if (!s) return false;
    const inputs = document.querySelectorAll("input[name$='-serial'], input[name$='-serial_number']");
    for (const inp of inputs) {
      if (inp === currentField) continue;
      const tokens = convertHangulToEnglish(inp.value).toUpperCase().split(',').map(t => t.trim()).filter(Boolean);
      if (tokens.includes(s)) {
        return true;
      }
    }
    return false;
  }

  // ── 6. 시리얼 필드 헬퍼 (재고 상태 검증 후 출고 직행 또는 스마트 연결) ──
  function appendSerialToField(field, serial) {
    serial = convertHangulToEnglish(serial.trim().toUpperCase());
    if (!serial) return;

    // 만약 툴 마스터 바코드가 전달된 경우 즉시 분기 처리
    const parsed = parseToolMasterBarcode(serial);
    if (parsed.found) {
      const currentRow = field.closest("tr.form-row, tr.has_original, tr.dynamic-inventories");
      handleToolMasterBarcode(parsed.brandId, parsed.toolId, currentRow, "");
      return;
    }

    // 1) 페이지 전체 중복 검사: 이미 다른 행에 입력된 시리얼인 경우 차단
    if (isSerialAlreadyEnteredOnPage(serial, field)) {
      showToastNotification(`중복 시리얼: [${serial}]은 이미 다른 행에 입력되어 있습니다.`);
      playBeep(400, 0.25);
      return;
    }

    // 2) 현재 필드 내부 중복 검사
    let curVal = convertHangulToEnglish(field.value.trim().toUpperCase());
    // 혹시라도 필드 안에 툴 바코드 텍스트가 묻어있다면 청소
    const curParsed = parseToolMasterBarcode(curVal);
    if (curParsed.found) {
      curVal = curVal.replace(new RegExp(curParsed.matchedText.replace(/:/g, '[-:_]'), 'gi'), '');
      curVal = curVal.replace(/^[, ]+|[, ]+$/g, '').trim();
    }

    const currentTokens = curVal.split(',').map(t => t.trim()).filter(Boolean);
    if (currentTokens.includes(serial)) {
      showToastNotification(`중복 시리얼: [${serial}]은 이미 입력되어 있습니다.`);
      playBeep(400, 0.25);
      return;
    }

    // 3) 실시간 재고 확인: 만약 이미 재고 상태라면 입고란에 넣지 않고 출고 등록으로 직행!
    fetch(`/inventory/barcode-api/lookup/?serial=${encodeURIComponent(serial)}`)
      .then(res => res.json())
      .then(data => {
        if (data.found && data.is_stock) {
          showToastNotification(`재고 확인: [${serial}] 출고 등록 화면으로 이동합니다.`);
          playBeep(1000, 0.15);
          setTimeout(() => {
            window.location.href = `/inventory/tool_inventory/outboundbatch/add/?serial=${encodeURIComponent(serial)}`;
          }, 600);
          return;
        }

        // 정상 신규 장비 누적: 연속 스캔을 위해 항상 쉼표와 공백(, )으로 대기
        if (currentTokens.length === 0) {
          field.value = serial + ', ';
        } else {
          field.value = currentTokens.join(', ') + ', ' + serial + ', ';
        }
        field.focus();
        field.setSelectionRange(field.value.length, field.value.length);
        playBeep(1600, 0.09);
      })
      .catch(() => {
        if (currentTokens.length === 0) {
          field.value = serial + ', ';
        } else {
          field.value = currentTokens.join(', ') + ', ' + serial + ', ';
        }
        field.focus();
        playBeep(1600, 0.09);
      });
  }

  // ── 7. 시리얼 필드 이벤트 핸들링: input에서는 한글 -> 영문 변환만 수행하고, 툴 마스터 바코드 실행은 오직 Enter에서만! ──
  document.body.addEventListener("input", function (e) {
    if (e.target.matches("input[name$='-serial'], input[name$='-serial_number']")) {
      const raw = e.target.value;
      // 한글 상태 오입력 방지: 실시간 100% 영문 대문자 변환
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
        e.preventDefault(); // 폼 자동 전송 원천 차단!
        e.stopPropagation();

        const raw = e.target.value.trim();
        const converted = convertHangulToEnglish(raw).toUpperCase();

        // 1) 툴 마스터 바코드 감지
        const parsed = parseToolMasterBarcode(converted);
        if (parsed.found) {
          let remaining = converted.replace(new RegExp(parsed.matchedText.replace(/:/g, '[-:_]'), 'gi'), '');
          remaining = remaining.replace(/^[, ]+|[, ]+$/g, '').trim();
          e.target.value = remaining ? remaining + ', ' : '';

          const currentRow = e.target.closest("tr.form-row, tr.has_original, tr.dynamic-inventories");
          handleToolMasterBarcode(parsed.brandId, parsed.toolId, currentRow, remaining);
          return;
        }

        // 2) 일반 장비 시리얼 번호인 경우: 재고 상태 실시간 검증 및 중복 방어
        if (converted) {
          const serialTokens = converted.split(',').map(s => s.trim()).filter(Boolean);
          const targetSerial = serialTokens[serialTokens.length - 1];

          if (targetSerial) {
            // 현재 입력란 내 앞선 토큰 중복 체크
            if (serialTokens.slice(0, -1).includes(targetSerial)) {
              serialTokens.pop();
              e.target.value = serialTokens.length > 0 ? serialTokens.join(', ') + ', ' : '';
              showToastNotification(`⚠️ [${targetSerial}]은 이미 입력란에 존재합니다! (중복 티켓 추가 방지)`);
              playBeep(400, 0.25);
              return;
            }

            // 페이지 내 다른 행 중복 체크
            if (isSerialAlreadyEnteredOnPage(targetSerial, e.target)) {
              serialTokens.pop();
              e.target.value = serialTokens.length > 0 ? serialTokens.join(', ') + ', ' : '';
              showToastNotification(`⚠️ [${targetSerial}]은 다른 행에 이미 등록되어 있습니다!`);
              playBeep(400, 0.25);
              return;
            }

            fetch(`/inventory/barcode-api/lookup/?serial=${encodeURIComponent(targetSerial)}`)
              .then(res => res.json())
              .then(data => {
                if (data.found && data.is_stock) {
                  // 이미 입고 완료된 재고 장비 -> 입고 등록에 누적 차단 및 출고 등록으로 직행!
                  serialTokens.pop();
                  e.target.value = serialTokens.length > 0 ? serialTokens.join(', ') + ', ' : '';
                  showToastNotification(`⚠️ [${targetSerial}]은 이미 입고된 재고 장비입니다! [출고 등록] 화면으로 이동합니다.`);
                  playBeep(1000, 0.15);
                  setTimeout(() => {
                    window.location.href = `/inventory/tool_inventory/outboundbatch/add/?serial=${encodeURIComponent(targetSerial)}`;
                  }, 600);
                } else {
                  // 신규 미등록 장비 -> 다음 바코드 연속 스캔을 위해 반드시 끝 쉼표와 공백(, )으로 자동 분리 대기!
                  const finalVal = serialTokens.join(', ') + ', ';
                  e.target.value = finalVal;
                  e.target.setSelectionRange(finalVal.length, finalVal.length);
                  playBeep(1400, 0.08);
                }
              })
              .catch(() => {
                const finalVal = serialTokens.join(', ') + ', ';
                e.target.value = finalVal;
                playBeep(1400, 0.08);
              });
          }
        }
      }
    }
  });

  // ── 8. 글로벌 바코드 인터셉터 (포커스가 인풋에 없을 때 스캐너 입력 감지) ──
  let scanBuffer = [];
  let lastKeyTime = 0;
  const SCAN_INTERVAL = 50; // 50ms 이하를 스캐너 연속 입력으로 판정

  window.addEventListener("keydown", function (e) {
    const activeEl = document.activeElement;
    if (activeEl && activeEl.matches && activeEl.matches("input[name$='-serial'], input[name$='-serial_number']")) {
      return; // 시리얼 인풋에 포커스가 있을 때는 위의 input/keydown 리스너가 전담
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

        // 일반 시리얼 번호인 경우 유효한 시리얼 인풋에 누적
        const targetInput = document.querySelector("tr:not(.empty-form) input[name$='-serial']:not([disabled]), tr:not(.empty-form) input[name$='-serial_number']:not([disabled])");
        if (targetInput) {
          appendSerialToField(targetInput, converted);
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
      appendSerialToField(firstSerialInput, initialSerial);
    }
  }
});
