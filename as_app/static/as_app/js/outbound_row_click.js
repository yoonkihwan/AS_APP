/**
 * 출고 등록 목록 - 행 클릭 시 체크박스 토글
 * 테이블 행을 클릭하면 해당 행의 체크박스가 토글됩니다.
 * (링크 클릭, 체크박스 직접 클릭 시는 기본 동작 유지)
 */
(function () {
    "use strict";

    function init() {
        const table = document.querySelector("#result_list table");
        if (!table) return;

        table.addEventListener("click", function (e) {
            const target = e.target;

            // 링크, 체크박스, 버튼 클릭은 무시
            if (
                target.tagName === "A" ||
                target.tagName === "INPUT" ||
                target.tagName === "BUTTON" ||
                target.closest("a") ||
                target.closest("button")
            ) {
                return;
            }

            // 가장 가까운 tr 찾기
            const row = target.closest("tr");
            if (!row) return;

            // 체크박스 찾기
            const checkbox = row.querySelector('input[type="checkbox"]');
            if (!checkbox) return;

            // 체크박스 토글
            checkbox.checked = !checkbox.checked;

            // change 이벤트 발생 (Django/Unfold의 전체 선택 등 연동)
            checkbox.dispatchEvent(new Event("change", { bubbles: true }));

            // 행 선택 스타일
            row.classList.toggle("selected", checkbox.checked);
        });

        // 선택된 행 스타일링
        const style = document.createElement("style");
        style.textContent = `
            #result_list table tbody tr {
                cursor: pointer;
                transition: background 0.1s ease;
            }
            #result_list table tbody tr:hover {
                background: rgba(99, 102, 241, 0.04) !important;
            }
            #result_list table tbody tr.selected,
            #result_list table tbody tr.selected:hover {
                background: rgba(99, 102, 241, 0.08) !important;
            }
            .dark #result_list table tbody tr:hover {
                background: rgba(99, 102, 241, 0.1) !important;
            }
            .dark #result_list table tbody tr.selected,
            .dark #result_list table tbody tr.selected:hover {
                background: rgba(99, 102, 241, 0.18) !important;
            }
        `;
        document.head.appendChild(style);

        // 페이지 로드 시 이미 체크된 행에 selected 클래스 적용
        table.querySelectorAll('tbody tr').forEach(function (row) {
            const cb = row.querySelector('input[type="checkbox"]');
            if (cb && cb.checked) {
                row.classList.add("selected");
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
