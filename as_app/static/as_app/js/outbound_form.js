document.addEventListener("DOMContentLoaded", function () {
  /**
   * 인라인 폼셋에서 "브랜드 선택 -> 툴 목록 갱신" 
   * "툴 선택 -> 재고(시리얼) 목록 & 현재 재고(수량) 갱신"
   */

  function updateToolOptions(row, brandId) {
    const toolSelect = row.querySelector("select[name$='-tool']");
    if (!toolSelect) return;

    if (!brandId) {
      toolSelect.innerHTML = '<option value="">---------</option>';
      return;
    }

    fetch(`/api/tools-by-brand/?brand_id=${brandId}`)
      .then((response) => response.json())
      .then((data) => {
        const currentToolId = toolSelect.value;
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
      })
      .catch((err) => console.error("Error fetching tools:", err));
  }

  function updateInventoryOptions(row, toolId) {
    // CheckboxSelectMultiple 위젯이 있는 컨테이너 찾기
    const inventoryTd = row.querySelector(".field-inventories");
    if (!inventoryTd) return;

    const currentStockInput = row.querySelector("input[name$='-current_stock']");

    // 행의 prefix 파악 (e.g. "tickets-0")
    let rowPrefix = "";
    if (row.id) {
      rowPrefix = row.id;
    }

    if (!toolId) {
      // 선택된 대상 장비가 없으면 재고 목록도 비움
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
        // 기존에 선택된게 있다면 값 기억하기
        const existingCheckboxes = Array.from(inventoryTd.querySelectorAll('input[type="checkbox"]'));
        const checkedValues = existingCheckboxes.filter(cb => cb.checked).map(cb => cb.value);

        // 기존 렌더링된 체크박스 모두 삭제
        existingCheckboxes.forEach(cb => {
          const wrapperDiv = cb.closest('div');
          if (wrapperDiv) wrapperDiv.remove();
        });

        const count = data.inventory.length;
        if (currentStockInput) currentStockInput.value = count;

        // 컨테이너가 복잡하게 래핑되어 있을 수 있으므로 찾아서 넣는다
        // 안쪽 빈 공간에 넣기 위해 div를 하나 만들어서 append 한다
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

          const cb = document.createElement("input");
          cb.type = "checkbox";
          cb.name = rowPrefix + "-inventories";
          cb.value = inv.id;
          cb.id = rowPrefix + "-inventories_" + index;

          if (checkedValues.includes(String(inv.id))) {
            cb.checked = true;
          }

          const lbl = document.createElement("label");
          lbl.htmlFor = cb.id;
          lbl.textContent = inv.serial ? ` S/N: ${inv.serial}` : ` S/N: 없음 (${inv.id.substring(0, 8)}...)`;
          lbl.style.marginLeft = "8px";
          lbl.style.fontSize = "0.875rem"; // tailwind text-sm
          lbl.style.cursor = "pointer";

          wrapper.appendChild(cb);
          wrapper.appendChild(lbl);
          container.appendChild(wrapper);
        });

        updateQuantityLogic(row);
      })
      .catch((err) => console.error("Error fetching inventory:", err));
  }

  function updateQuantityLogic(row) {
    const quantityInput = row.querySelector("input[name$='-quantity']");
    if (!quantityInput) return;

    // 현재 목록에 진짜 시리얼이 있는지 확인 ("S/N: 없음"이 아닌 레이블 존재 여부)
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

    // 체크된 체크박스 개수 세기
    const checkedBoxes = row.querySelectorAll("input[type='checkbox'][name$='-inventories']:checked");
    const selectedCount = checkedBoxes.length;

    // 공통: 하얗게 변하는 현상(inline style) 완전 제거하여 주변 디자인과 통일
    quantityInput.style.backgroundColor = 'transparent'; // 다른 필드와 같은 색상 유지
    quantityInput.style.color = 'inherit';

    if (!hasItems || hasSerial) {
      // 1. 선택된 툴이 없거나 시리얼이 있는 품목: 클릭 및 입력 원천 불가 (선택된 박스 수로만 제어)
      quantityInput.readOnly = true;
      quantityInput.style.pointerEvents = 'none';
      quantityInput.style.opacity = '0.5';

      if (hasSerial) {
        // 시리얼이 있는 품목은 체크박스 활성화
        row.querySelectorAll("input[type='checkbox'][name$='-inventories']").forEach(cb => {
          cb.disabled = false;
        });
      }

      if (selectedCount > 0) {
        quantityInput.value = selectedCount;
      } else {
        if (!quantityInput.value || quantityInput.value === '0') {
          quantityInput.value = 1; // 기본값
        }
      }
    } else {
      // 2. 시리얼이 없는 품목: 수동 입력 활성화 및 체크박스 잠금
      quantityInput.readOnly = false;
      quantityInput.style.pointerEvents = 'auto';
      quantityInput.style.opacity = '1';

      // 시리얼이 없는 품목은 체크박스 선택 불가토록 강제 잠금 및 해제
      row.querySelectorAll("input[type='checkbox'][name$='-inventories']").forEach(cb => {
        cb.checked = false;
        cb.disabled = true;
      });

      if (!quantityInput.value || quantityInput.value === '0') {
        quantityInput.value = selectedCount > 0 ? selectedCount : 1;
      }
    }
  }

  // 초기 렌더링 검사
  document.querySelectorAll(".field-inventories").forEach(td => {
    const row = td.closest("tr");
    if (row && !row.classList.contains('empty-form')) {
      // 이미 Django 폼에서 렌더링된 체크박스들에 대해 이벤트 붙이기 위함
      const toolSelect = row.querySelector("select[name$='-tool']");
      if (toolSelect && toolSelect.value) {
        updateInventoryOptions(row, toolSelect.value);
      }
      updateQuantityLogic(row);
    }
  });

  document.body.addEventListener("change", function (e) {
    // 브랜드를 선택하면 툴 초기화, 재고 목록 초기화
    if (e.target.matches("select[name$='-brand']")) {
      const row = e.target.closest("tr");
      const toolSelect = row.querySelector("select[name$='-tool']");

      if (toolSelect) toolSelect.value = "";

      updateToolOptions(row, e.target.value);
      updateInventoryOptions(row, null);
    }

    // 대장 장비(툴)를 선택하면 재고 목록 갱신
    if (e.target.matches("select[name$='-tool']")) {
      const row = e.target.closest("tr");
      updateInventoryOptions(row, e.target.value);
    }

    // 아무 체크박스나 클릭하면 수량 계산 다시
    if (e.target.matches("input[type='checkbox'][name$='-inventories']")) {
      const row = e.target.closest("tr");
      updateQuantityLogic(row);
    }
  });
});
