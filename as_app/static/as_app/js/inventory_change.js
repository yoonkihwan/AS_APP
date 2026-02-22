document.addEventListener("DOMContentLoaded", function () {
    // 모든 텍스트 요소를 순회하면서 '삭제 통합 재고 리스트' 관련 문구를 강제로 '삭제'로 교체
    const linksAndButtons = document.querySelectorAll('a, button');
    linksAndButtons.forEach(el => {
        if (el.textContent.includes('삭제') && el.textContent.includes('통합') && el.textContent.includes('재고')) {
            el.textContent = '삭제';
            el.style.visibility = 'visible';
        }
    });
});
