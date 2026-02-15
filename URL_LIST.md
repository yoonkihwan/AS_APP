# AS 관리 시스템 - URL 목록

> 삭제할 URL 그룹이 있으면 체크 해제해 주세요.

---

## 🔧 시스템 공통 URL

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/` | `index` | **대시보드** (메인 페이지, KPI 카드 표시) |
| `admin/login/` | `login` | 로그인 페이지 |
| `admin/logout/` | `logout` | 로그아웃 |
| `admin/password_change/` | `password_change` | 비밀번호 변경 |
| `admin/password_change/done/` | `password_change_done` | 비밀번호 변경 완료 |
| `admin/autocomplete/` | `autocomplete` | 드롭다운 자동완성 (업체/툴 검색에 사용) |
| `admin/jsi18n/` | `jsi18n` | Django Admin 다국어 JS (내부용) |
| `admin/search/` | `search` | Unfold 전역 검색 (사이드바 검색 삭제했으나 URL은 존재) |
| `admin/r/<content_type_id>/<object_id>/` | `view_on_site` | 객체 사이트에서 보기 (미사용) |

---

## 📦 입고 배치 (InboundBatch) - 일괄 입고 등록

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/as_app/inboundbatch/` | `changelist` | 입고 배치 목록 |
| `admin/as_app/inboundbatch/add/` | `add` | **입고 등록** (사이드바 메뉴에서 연결) |
| `admin/as_app/inboundbatch/<id>/change/` | `change` | 입고 배치 수정 |
| `admin/as_app/inboundbatch/<id>/delete/` | `delete` | 입고 배치 삭제 |
| `admin/as_app/inboundbatch/<id>/history/` | `history` | 입고 배치 변경 이력 |

---

## 🔩 수리 기록 (RepairTicket) - 프록시 모델

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/as_app/repairticket/` | `changelist` | **수리 기록 목록** (입고/수리대기 상태만 표시) |
| `admin/as_app/repairticket/add/` | `add` | 수리 티켓 개별 추가 |
| `admin/as_app/repairticket/<id>/change/` | `change` | 수리 내역 입력/수정 |
| `admin/as_app/repairticket/<id>/delete/` | `delete` | 수리 티켓 삭제 |
| `admin/as_app/repairticket/<id>/history/` | `history` | 수리 티켓 변경 이력 |

---

## 🚚 출고 처리 (OutboundTicket) - 프록시 모델

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/as_app/outboundticket/` | `changelist` | **출고 처리 목록** (수리완료 상태만 표시) |
| `admin/as_app/outboundticket/add/` | `add` | 출고 티켓 개별 추가 |
| `admin/as_app/outboundticket/<id>/change/` | `change` | 출고 정보 수정 |
| `admin/as_app/outboundticket/<id>/delete/` | `delete` | 출고 티켓 삭제 |
| `admin/as_app/outboundticket/<id>/history/` | `history` | 출고 티켓 변경 이력 |

---

## 📋 통합 이력 (ASHistory) - 프록시 모델 (Read-Only)

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/as_app/ashistory/` | `changelist` | **AS 통합 이력 조회** (전체 티켓 읽기 전용) |
| `admin/as_app/ashistory/add/` | `add` | ~~추가~~ (권한 차단됨) |
| `admin/as_app/ashistory/<id>/change/` | `change` | ~~수정~~ (권한 차단됨) |
| `admin/as_app/ashistory/<id>/delete/` | `delete` | ~~삭제~~ (권한 차단됨) |
| `admin/as_app/ashistory/<id>/history/` | `history` | 변경 이력 조회 |

---

## 📝 입고 티켓 (InboundTicket) - 프록시 모델 (사이드바 숨김)

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/as_app/inboundticket/` | `changelist` | 개별 입고 티켓 목록 (사이드바 미노출) |
| `admin/as_app/inboundticket/add/` | `add` | 개별 입고 티켓 추가 |
| `admin/as_app/inboundticket/<id>/change/` | `change` | 개별 입고 티켓 수정 |
| `admin/as_app/inboundticket/<id>/delete/` | `delete` | 개별 입고 티켓 삭제 |
| `admin/as_app/inboundticket/<id>/history/` | `history` | 변경 이력 |

---

## 🏢 업체 관리 (Company) - 마스터 데이터

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/as_app/company/` | `changelist` | **업체 목록** |
| `admin/as_app/company/add/` | `add` | 업체 추가 |
| `admin/as_app/company/<id>/change/` | `change` | 업체 수정 |
| `admin/as_app/company/<id>/delete/` | `delete` | 업체 삭제 |
| `admin/as_app/company/<id>/history/` | `history` | 업체 변경 이력 |

---

## 💰 단가 그룹 (CompanyCategory) - 마스터 데이터 (사이드바 숨김)

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/as_app/companycategory/` | `changelist` | 단가 그룹 목록 (사이드바 미노출, 업체에서 통합 관리) |
| `admin/as_app/companycategory/add/` | `add` | 단가 그룹 추가 |
| `admin/as_app/companycategory/<id>/change/` | `change` | 단가 그룹 수정 |
| `admin/as_app/companycategory/<id>/delete/` | `delete` | 단가 그룹 삭제 |
| `admin/as_app/companycategory/<id>/history/` | `history` | 변경 이력 |

---

## 🏭 브랜드 (Brand) - 마스터 데이터 (사이드바 숨김)

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/as_app/brand/` | `changelist` | 브랜드 목록 (사이드바 미노출, 툴에서 통합 관리) |
| `admin/as_app/brand/add/` | `add` | 브랜드 추가 |
| `admin/as_app/brand/<id>/change/` | `change` | 브랜드 수정 |
| `admin/as_app/brand/<id>/delete/` | `delete` | 브랜드 삭제 |
| `admin/as_app/brand/<id>/history/` | `history` | 변경 이력 |

---

## 🔧 장비/툴 (Tool) - 마스터 데이터

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/as_app/tool/` | `changelist` | **브랜드 & 툴 목록** |
| `admin/as_app/tool/add/` | `add` | 툴 추가 |
| `admin/as_app/tool/<id>/change/` | `change` | 툴 수정 |
| `admin/as_app/tool/<id>/delete/` | `delete` | 툴 삭제 |
| `admin/as_app/tool/<id>/history/` | `history` | 변경 이력 |

---

## ⚙️ 부품 (Part) - 마스터 데이터

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/as_app/part/` | `changelist` | **부품 목록** |
| `admin/as_app/part/add/` | `add` | 부품 추가 |
| `admin/as_app/part/<id>/change/` | `change` | 부품 수정 |
| `admin/as_app/part/<id>/delete/` | `delete` | 부품 삭제 |
| `admin/as_app/part/<id>/history/` | `history` | 변경 이력 |

---

## 👥 인증/권한 (Django Auth) - 사용자 관리

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/auth/user/` | `changelist` | 사용자 목록 |
| `admin/auth/user/add/` | `add` | 사용자 추가 |
| `admin/auth/user/<id>/change/` | `change` | 사용자 수정 |
| `admin/auth/user/<id>/delete/` | `delete` | 사용자 삭제 |
| `admin/auth/user/<id>/password/` | `password_change` | 사용자 비밀번호 변경 |
| `admin/auth/user/<id>/history/` | `history` | 사용자 변경 이력 |
| `admin/auth/group/` | `changelist` | 그룹(권한 묶음) 목록 |
| `admin/auth/group/add/` | `add` | 그룹 추가 |
| `admin/auth/group/<id>/change/` | `change` | 그룹 수정 |
| `admin/auth/group/<id>/delete/` | `delete` | 그룹 삭제 |
| `admin/auth/group/<id>/history/` | `history` | 그룹 변경 이력 |

---

## 📊 앱 목록

| URL | URL Name | 용도 |
|:----|:---------|:-----|
| `admin/^(?P<app_label>auth\|as_app)/$` | `app_list` | 앱별 모델 목록 페이지 (대시보드 하단에 표시) |
| `admin/(?P<url>.*)$` | _(catch-all)_ | 잘못된 URL 처리 (404 표시) |
