document.addEventListener("DOMContentLoaded", function () {
  /**
   * 인라인 폼셋에서 "브랜드 선택 -> 툴 목록 갱신" 
   * "툴 선택 -> 재고(시리얼) 목록 & 현재 재고(수량) 갱신"
   * "바코드 스캔 -> 시리얼 체크박스 자동 선택 & 수량 자동 카운트"
   */

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

  function updateToolOptions(row, brandId, targetToolId = null, onComplete = null) {
    const toolSelect = row.querySelector("select[name$='-tool']");
    if (!toolSelect) return;

    if (!brandId) {
      toolSelect.innerHTML = '<option value="">---------</option>';
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
          toolSelect.value = targetToolId;
        }

        if (onComplete) onComplete();
      })
      .catch((err) => console.error("Error fetching tools:", err));
  }

  function updateInventoryOptions(row, toolId, targetSerial = null) {
    const inventoryTd = row.querySelector(".field-inventories");
    if (!inventoryTd) return;

    const currentStockInput = row.querySelector("input[name$='-current_stock']");

    let rowPrefix = "";
    if (row.id) {
      rowPrefix = row.id;
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
        const existingCheckboxes = Array.from(inventoryTd.querySelectorAll('input[type="checkbox"]'));
        const checkedValues = existingCheckboxes.filter(cb => cb.checked).map(cb => cb.value);

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
          cb.setAttribute('data-serial', (inv.serial || '').trim());

          // 기존 체크 상태 복원 또는 타겟 시리얼 자동 체크
          if (checkedValues.includes(String(inv.id)) || (targetSerial && inv.serial && inv.serial.trim() === targetSerial.trim())) {
            cb.checked = true;
            wrapper.style.backgroundColor = "rgba(16, 185, 129, 0.2)";
          }

          const lbl = document.createElement("label");
          lbl.htmlFor = cb.id;
          // [피드백 반영] 품목명은 이미 선택되어 있으므로 시리얼 번호만 깔끔하게 노출
          lbl.textContent = inv.serial ? ` ${inv.serial}` : ` S/N: 없음 (${inv.id.substring(0, 8)}...)`;
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
      .catch((err) => console.error("Error fetching inventory:", err));
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

  // ── 🚀 바코드 스캔 처리 핵심 함수 ──
  function handleScannedSerial(serial) {
    serial = serial.trim();
    if (!serial) return;

    // 1. 현재 화면에 이미 렌더링된 체크박스 중 시리얼 일치 항목 검색
    const allCbs = Array.from(document.querySelectorAll("input[type='checkbox'][name$='-inventories']"));
    const matchedCb = allCbs.find(cb => {
      const s = cb.getAttribute('data-serial');
      if (s && s.toLowerCase() === serial.toLowerCase()) return true;
      const lbl = document.querySelector(`label[for='${cb.id}']`);
      return lbl && lbl.textContent.trim().toLowerCase() === serial.toLowerCase();
    });

    if (matchedCb) {
      matchedCb.checked = true;
      const row = matchedCb.closest("tr");
      if (row) updateQuantityLogic(row);

      const wrapper = matchedCb.closest("div");
      if (wrapper) {
        wrapper.style.backgroundColor = "rgba(16, 185, 129, 0.25)";
        wrapper.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      playBeep(1800, 0.1);
      return;
    }

    // 2. 화면에 없다면 -> API로 품목 정보 조회 후 인라인 자동 세팅
    fetch(`/inventory/barcode-api/lookup/?serial=${encodeURIComponent(serial)}`)
      .then(res => res.json())
      .then(data => {
        if (!data.success || !data.found) {
          playBeep(300, 0.25);
          if (confirm(`시리얼 [${serial}]은 미등록 장비입니다.\n[입고 등록] 화면으로 이동하여 신규 입고하시겠습니까?`)) {
            window.location.href = `/inventory/tool_inventory/inventorybatch/add/?serial=${encodeURIComponent(serial)}`;
          }
          return;
        }

        if (!data.is_stock) {
          playBeep(300, 0.25);
          alert(`시리얼 [${serial}]은 이미 '${data.status}' 처리된 장비입니다.`);
          return;
        }

        // 비어있는 행 찾기
        const rows = Array.from(document.querySelectorAll("tr.form-row:not(.empty-form)"));
        let targetRow = rows.find(r => {
          const toolSel = r.querySelector("select[name$='-tool']");
          return toolSel && !toolSel.value;
        });

        if (!targetRow && rows.length > 0) {
          targetRow = rows[rows.length - 1];
        }

        if (targetRow) {
          const brandSelect = targetRow.querySelector("select[name$='-brand']");
          if (brandSelect && data.brand_id) {
            brandSelect.value = data.brand_id;
            updateToolOptions(targetRow, data.brand_id, data.tool_id, () => {
              updateInventoryOptions(targetRow, data.tool_id, serial);
            });
          } else {
            updateInventoryOptions(targetRow, data.tool_id, serial);
          }
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
    }, 400);
  }

  // ── [출고날짜 오염 방어] 페이지 진입 시 release_date 자동 포커스 해제 ──
  const releaseDateInput = document.querySelector("input[name='release_date']");
  if (releaseDateInput && document.activeElement === releaseDateInput) {
    releaseDateInput.blur();
  }
  let initialReleaseDate = releaseDateInput ? releaseDateInput.value : "";

  // 글로벌 바코드 스캐너 리스너 (40ms 이하 스캔)
  let scanBuffer = [];
  let lastKeyTime = 0;
  const SCAN_INTERVAL = 40;

  window.addEventListener("keydown", function(e) {
    const activeEl = document.activeElement;
    if (activeEl && ['TEXTAREA'].includes(activeEl.tagName)) return;

    const now = performance.now();
    const gap = now - lastKeyTime;
    lastKeyTime = now;

    if (e.key === "Enter") {
      if (scanBuffer.length >= 4) {
        const scanned = scanBuffer.join("").trim();
        scanBuffer = [];
        e.preventDefault();
        e.stopPropagation();

        // 출고날짜(release_date) 필드에 바코드 찌꺼기가 들어갔다면 즉시 복원
        if (releaseDateInput && releaseDateInput.value !== initialReleaseDate) {
          releaseDateInput.value = initialReleaseDate;
        }

        handleScannedSerial(scanned);
      } else {
        scanBuffer = [];
      }
    } else if (e.key.length === 1) {
      if (gap <= SCAN_INTERVAL) {
        // 스캐너 고속 스트림 중: 포커스된 인풋(특히 release_date)에 문자가 찍히는 것을 원천 차단!
        if (activeEl && activeEl.matches && activeEl.matches("input[name='release_date'], input[type='text'], input[type='search']")) {
          e.preventDefault();
        }
        scanBuffer.push(e.key);
      } else {
        // 새로운 입력 시작
        scanBuffer = [e.key];
      }
    }
  });

  // 이벤트 위임
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
