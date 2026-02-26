/**
 * 수리 세트 등록/편집 폼에서 "브랜드 → 적용 장비" 캐스케이딩 필터
 * 브랜드를 선택하면, filter_horizontal 위젯의 적용 장비 목록을
 * 해당 브랜드에 속한 장비만 보여주도록 필터링합니다.
 */
document.addEventListener("DOMContentLoaded", function () {
  // Unfold의 autocomplete_fields에서 브랜드는 select2 위젯으로 렌더링됨
  // 따라서 change 이벤트를 select2:select 이벤트로 보완해야 함

  const brandField = document.querySelector("#id_brand");
  if (!brandField) return;

  function filterToolsByBrand(brandId) {
    if (!brandId) return;

    // API 호출하여 해당 브랜드 장비 목록 가져오기
    fetch(`api/tools-for-brand/${brandId}/`)
      .then((res) => res.json())
      .then((data) => {
        const toolIds = new Set(data.tools.map((t) => String(t.id)));

        // filter_horizontal 위젯의 "선택 가능" 목록(from 박스) 필터링
        const fromBox = document.querySelector("#id_tools_from");
        if (fromBox) {
          Array.from(fromBox.options).forEach((opt) => {
            opt.style.display = toolIds.has(opt.value) ? "" : "none";
          });
        }
      })
      .catch((err) => console.error("브랜드별 장비 필터링 오류:", err));
  }

  // 일반 select의 change 이벤트
  brandField.addEventListener("change", function () {
    filterToolsByBrand(this.value);
  });

  // Select2 이벤트 (autocomplete_fields 사용 시)
  if (typeof django !== "undefined" && typeof django.jQuery !== "undefined") {
    django.jQuery(brandField).on("select2:select", function (e) {
      filterToolsByBrand(e.params.data.id);
    });
    django.jQuery(brandField).on("select2:clear", function () {
      // 브랜드 클리어 시 모든 옵션 다시 보이기
      const fromBox = document.querySelector("#id_tools_from");
      if (fromBox) {
        Array.from(fromBox.options).forEach((opt) => {
          opt.style.display = "";
        });
      }
    });
  }

  // 페이지 로드 시 이미 브랜드가 선택되어 있으면 필터링 적용
  const initialBrandId = brandField.value;
  if (initialBrandId) {
    filterToolsByBrand(initialBrandId);
  }
});
