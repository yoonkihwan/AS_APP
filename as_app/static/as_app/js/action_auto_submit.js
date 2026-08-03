/**
 * 상태 등록 화면 — 액션 드롭다운 자동 제출(auto-submit)
 * 
 * Unfold admin에서 changelist 체크박스 기반 액션을 사용할 때,
 * 드롭다운(select[name="action"])에서 항목을 선택하면
 * 사용자가 별도로 "Run" 버튼을 클릭하지 않아도 즉시 폼이 제출됩니다.
 * 
 * 이를 통해 "액션이 선택되지 않았습니다" 오류를 방지합니다.
 */
(function () {
    'use strict';

    function initAutoSubmit() {
        const actionSelect = document.querySelector('select[name="action"]');
        if (!actionSelect) return;

        actionSelect.addEventListener('change', function () {
            const selectedValue = this.value;
            if (!selectedValue) return;  // "Select action" (빈 값)은 무시

            // changelist-form을 찾아서 index 값과 함께 제출
            const form = document.getElementById('changelist-form');
            if (!form) return;

            // Django admin이 "index" POST 파라미터를 요구하므로 hidden input 추가
            let indexInput = form.querySelector('input[name="index"]');
            if (!indexInput) {
                indexInput = document.createElement('input');
                indexInput.type = 'hidden';
                indexInput.name = 'index';
                indexInput.value = '0';
                form.appendChild(indexInput);
            }

            form.submit();
        });
    }

    // DOM이 로드된 후 초기화
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAutoSubmit);
    } else {
        initAutoSubmit();
    }
})();
