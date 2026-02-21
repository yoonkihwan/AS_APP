document.addEventListener("DOMContentLoaded", function () {
    /**
     * 인라인 폼셋에서 "브랜드 선택 -> 툴 목록 갱신" 로직 처리
     * Django Admin의 TabularInline 구조에 맞춰 작성됨.
     */
  
    function updateToolOptions(brandSelect) {
      // brandSelect: <select name="...-brand">
      const row = brandSelect.closest("tr");
      if (!row) return;
  
      const toolSelect = row.querySelector("select[name$='-tool']");
      if (!toolSelect) return;
  
      const brandId = brandSelect.value;
  
      // 2. 브랜드 선택이 없으면 툴 목록 초기화
      if (!brandId) {
        toolSelect.innerHTML = '<option value="">---------</option>';
        return;
      }
  
      // 3. API 호출
      fetch(`/api/tools-by-brand/?brand_id=${brandId}`)
        .then((response) => response.json())
        .then((data) => {
          const currentToolId = toolSelect.value;
          
          // 옵션 초기화
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
  
    // 이벤트 위임
    document.body.addEventListener("change", function (e) {
      if (e.target.matches("select[name$='-brand']")) {
        const row = e.target.closest("tr");
        const toolSelect = row.querySelector("select[name$='-tool']");
        
        // 브랜드를 변경하면 툴 선택 초기화
        toolSelect.value = "";
        
        updateToolOptions(e.target);
      }
    });
  
    // 페이지 로드 시, "이미 브랜드는 선택되어 있는데 툴 목록이 비어있는 경우" 처리
    // (보통 폼 에러로 리로드되었을 때, 또는 Form __init__에서 처리가 안 된 예외적 케이스)
    // 하지만 우리가 forms.py에서 __init__으로 QuerySet을 잘 처리했다면, 
    // 여기서는 굳이 API를 다시 부를 필요가 없음.
    // 만약 "POST 요청 후 폼 에러 시" 자바스크립트로 다시 채워야 한다면 아래 로직 사용.
    
    // const brandSelects = document.querySelectorAll("select[name$='-brand']");
    // brandSelects.forEach(select => {
    //     if (select.value && !select.closest('.empty-form')) {
    //         const row = select.closest("tr");
    //         const toolSelect = row.querySelector("select[name$='-tool']");
    //         if (toolSelect && toolSelect.options.length <= 1) {
    //             updateToolOptions(select);
    //         }
    //     }
    // });
  });
