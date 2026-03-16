/**
 * 부품/공임 테이블 위젯 - 탭 전환 및 행 클릭 토글
 */
document.addEventListener('DOMContentLoaded', function () {
    const widget = document.querySelector('.parts-table-widget');
    if (!widget) return;



    // ── 행 클릭으로 체크박스 토글 ──
    const rows = widget.querySelectorAll('.parts-row');
    rows.forEach(function (row) {
        row.addEventListener('click', function (e) {
            // 체크박스 직접 클릭 시에는 이벤트 무시 (더블 토글 방지)
            if (e.target.type === 'checkbox') return;

            const cb = this.querySelector('input[type="checkbox"]');
            if (cb) {
                cb.checked = !cb.checked;
                this.classList.toggle('selected-row', cb.checked);
            }
        });

        // 체크박스 직접 클릭 시에도 행 스타일 동기화
        const cb = row.querySelector('input[type="checkbox"]');
        if (cb) {
            cb.addEventListener('change', function () {
                row.classList.toggle('selected-row', this.checked);
            });
        }
    });
});
