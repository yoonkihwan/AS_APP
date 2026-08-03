/**
 * Multi-Select Filter Bar — AS 관리 복합 필터 JavaScript
 *
 * 기능:
 * 1. 다중 선택 드롭다운 (체크박스 방식)
 * 2. 검색 가능한 드롭다운 (매출처 등)
 * 3. 날짜 범위 선택기 (빠른 선택 포함)
 * 4. 선택 Pill 태그 개별 삭제
 * 5. [적용] / [초기화] 버튼
 */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        initFilterBar();
    });

    function initFilterBar() {
        const filterBar = document.getElementById("multi-filter-bar");
        if (!filterBar) return;

        // body에 필터 바 활성 클래스 추가 (사이드바 필터 숨김)
        document.body.classList.add("filter-bar-active");

        initDropdowns(filterBar);
        initSearchableDropdowns(filterBar);
        initDatePresets(filterBar);
        initApplyButton(filterBar);
        initResetButton(filterBar);
        initPillRemove();
        initClickOutside();
    }

    // ── 드롭다운 토글 ──
    function initDropdowns(container) {
        const triggers = container.querySelectorAll(".filter-dropdown__trigger");
        triggers.forEach(function (trigger) {
            trigger.addEventListener("click", function (e) {
                e.stopPropagation();
                const dropdown = trigger.closest(".filter-dropdown");

                // 다른 드롭다운 닫기
                container.querySelectorAll(".filter-dropdown--open").forEach(function (d) {
                    if (d !== dropdown) d.classList.remove("filter-dropdown--open");
                });

                dropdown.classList.toggle("filter-dropdown--open");
            });
        });

        // 옵션 클릭 (체크박스 토글)
        const options = container.querySelectorAll(".filter-dropdown__option");
        options.forEach(function (option) {
            option.addEventListener("click", function (e) {
                e.preventDefault();
                e.stopPropagation();
                const checkbox = option.querySelector('input[type="checkbox"]');
                if (checkbox) {
                    checkbox.checked = !checkbox.checked;
                    option.classList.toggle("filter-dropdown__option--selected", checkbox.checked);
                }

                // Trigger 텍스트 업데이트
                updateTriggerText(option.closest(".filter-dropdown"));
            });

            // 직접 체크박스 클릭 시 이벤트 버블링 방지
            const cb = option.querySelector('input[type="checkbox"]');
            if (cb) {
                cb.addEventListener("click", function (e) {
                    e.stopPropagation();
                    option.classList.toggle("filter-dropdown__option--selected", cb.checked);
                    updateTriggerText(option.closest(".filter-dropdown"));
                });
            }
        });
    }

    // Trigger 텍스트 동적 업데이트
    function updateTriggerText(dropdown) {
        if (!dropdown) return;
        const trigger = dropdown.querySelector(".filter-dropdown__trigger");
        const checked = dropdown.querySelectorAll('input[type="checkbox"]:checked');
        const defaultText = trigger.dataset.placeholder || "전체";

        if (checked.length === 0) {
            trigger.querySelector(".filter-dropdown__trigger-text").textContent = defaultText;
            trigger.classList.remove("filter-dropdown__trigger--active");
        } else if (checked.length === 1) {
            const label = checked[0].closest(".filter-dropdown__option")
                .querySelector(".filter-dropdown__option-text").textContent;
            trigger.querySelector(".filter-dropdown__trigger-text").textContent = label;
            trigger.classList.add("filter-dropdown__trigger--active");
        } else {
            trigger.querySelector(".filter-dropdown__trigger-text").textContent =
                checked.length + "개 선택";
            trigger.classList.add("filter-dropdown__trigger--active");
        }
    }

    // ── 검색 가능한 드롭다운 ──
    function initSearchableDropdowns(container) {
        const searchInputs = container.querySelectorAll(".filter-dropdown__search input");
        searchInputs.forEach(function (input) {
            input.addEventListener("input", function () {
                const keyword = input.value.toLowerCase().trim();
                const panel = input.closest(".filter-dropdown__panel");
                const options = panel.querySelectorAll(".filter-dropdown__option");
                options.forEach(function (opt) {
                    const text = opt.querySelector(".filter-dropdown__option-text").textContent.toLowerCase();
                    if (keyword === "" || text.includes(keyword)) {
                        opt.classList.remove("filter-dropdown__option--hidden");
                    } else {
                        opt.classList.add("filter-dropdown__option--hidden");
                    }
                });
            });

            // 검색 인풋 클릭 시 드롭다운 닫히지 않도록
            input.addEventListener("click", function (e) {
                e.stopPropagation();
            });
        });
    }

    // ── 날짜 빠른 선택 프리셋 ──
    function initDatePresets(container) {
        const presetBtns = container.querySelectorAll(".filter-date-range__preset-btn");
        presetBtns.forEach(function (btn) {
            btn.addEventListener("click", function (e) {
                e.preventDefault();
                const range = btn.dataset.range;
                const dateGroup = btn.closest(".filter-bar__item--date");
                const fromInput = dateGroup.querySelector('input[name$="_from"]');
                const toInput = dateGroup.querySelector('input[name$="_to"]');

                const today = new Date();
                let from = new Date();

                // 같은 그룹 내 활성 프리셋 초기화
                dateGroup.querySelectorAll(".filter-date-range__preset-btn--active")
                    .forEach(function (b) { b.classList.remove("filter-date-range__preset-btn--active"); });

                switch (range) {
                    case "1w":
                        from.setDate(today.getDate() - 7);
                        break;
                    case "1m":
                        from.setMonth(today.getMonth() - 1);
                        break;
                    case "3m":
                        from.setMonth(today.getMonth() - 3);
                        break;
                    case "6m":
                        from.setMonth(today.getMonth() - 6);
                        break;
                    case "1y":
                        from.setFullYear(today.getFullYear() - 1);
                        break;
                    default:
                        return;
                }

                fromInput.value = formatDate(from);
                toInput.value = formatDate(today);
                btn.classList.add("filter-date-range__preset-btn--active");
            });
        });
    }

    function formatDate(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, "0");
        const d = String(date.getDate()).padStart(2, "0");
        return y + "-" + m + "-" + d;
    }

    // ── [적용] 버튼 ──
    function initApplyButton(container) {
        const applyBtn = container.querySelector(".filter-bar__btn--apply");
        if (!applyBtn) return;

        applyBtn.addEventListener("click", function (e) {
            e.preventDefault();
            const form = container.querySelector("#filter-bar-form");
            if (form) {
                form.submit();
            }
        });
    }

    // ── [초기화] 버튼 ──
    function initResetButton(container) {
        const resetBtn = container.querySelector(".filter-bar__btn--reset");
        if (!resetBtn) return;

        resetBtn.addEventListener("click", function () {
            // 현재 URL에서 모든 mf_ 파라미터와 q= 제거
            const url = new URL(window.location.href);
            const keysToRemove = [];
            url.searchParams.forEach(function (val, key) {
                if (key.startsWith("mf_") || key === "q") {
                    keysToRemove.push(key);
                }
            });
            keysToRemove.forEach(function (key) {
                url.searchParams.delete(key);
            });
            window.location.href = url.toString();
        });
    }

    // ── Pill 삭제 버튼 ──
    function initPillRemove() {
        const pillRemoves = document.querySelectorAll(".filter-pill__remove");
        pillRemoves.forEach(function (btn) {
            btn.addEventListener("click", function () {
                const key = btn.dataset.key;
                const value = btn.dataset.value;
                const url = new URL(window.location.href);

                if (value === "__date_range__") {
                    // 날짜 범위: 시작일/종료일 모두 제거
                    url.searchParams.delete("mf_" + key + "_from");
                    url.searchParams.delete("mf_" + key + "_to");
                } else {
                    // 다중 선택: 해당 값만 제거
                    const paramName = "mf_" + key;
                    const currentValues = url.searchParams.getAll(paramName);
                    url.searchParams.delete(paramName);
                    currentValues.forEach(function (v) {
                        if (v !== value) {
                            url.searchParams.append(paramName, v);
                        }
                    });
                }

                window.location.href = url.toString();
            });
        });
    }

    // ── 외부 클릭 시 드롭다운 닫기 ──
    function initClickOutside() {
        document.addEventListener("click", function (e) {
            const openDropdowns = document.querySelectorAll(".filter-dropdown--open");
            openDropdowns.forEach(function (d) {
                if (!d.contains(e.target)) {
                    d.classList.remove("filter-dropdown--open");
                }
            });
        });
    }
})();
