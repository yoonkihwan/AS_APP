# 🔧 사내용 AS 관리 시스템 (Internal AS Management System)

AS 입고부터 수리, 출고, 이력 관리까지의 전 과정을 전산화하여 업무 효율성을 높이고 데이터 누락을 방지하는 사내 웹 애플리케이션입니다.

> **핵심 가치:** 쉽고 빠른 입력(드롭다운, 일괄 입고) · 정확한 이력 추적 · 마스터 데이터 기반의 체계적 관리

- [프로그램 매뉴얼 보기](./GEMINI.MD)

---

## 📋 목차

- [기술 스택](#-기술-스택)
- [주요 기능](#-주요-기능)
- [프로젝트 구조](#-프로젝트-구조)
- [설치 및 실행](#-설치-및-실행)
- [사용 가이드](#-사용-가이드)
- [데이터베이스 설계](#-데이터베이스-설계)
- [개발 로드맵](#-개발-로드맵)

---

## 🛠 기술 스택

| 구분 | 기술 | 설명 |
|:-----|:-----|:-----|
| **Language** | Python 3.x | 전체 비즈니스 로직 처리 및 백엔드 구현 |
| **Framework** | Django 5.x | 웹 애플리케이션 프레임워크 (MVT 패턴, ORM 활용) |
| **Database** | PostgreSQL | 로컬 개발 및 운영 배포용 PostgreSQL |
| **Frontend/UI** | Django Unfold | Django Admin을 현대적인 UI로 커스터마이징하여 대시보드 구축 |
| **Import/Export** | django-import-export | 데이터 일괄 가져오기/내보내기 지원 |
| **Hosting** | Render | 운영 환경 호스팅 (WhiteNoise 정적 파일 서빙) |

---

## ✨ 주요 기능

### ✅ P0 — 핵심 기능 (구현 완료)

| 카테고리 | 기능 | 설명 |
|:---------|:-----|:-----|
| **마스터 관리** | 업체관리 | 매출처업체 / 의뢰업체를 탭 네비게이션으로 통합 관리 |
| **마스터 관리** | 브랜드 & 툴 관리 | 브랜드별 장비/툴 통합 관리 (autocomplete 검색) |
| **마스터 관리** | 수리부품 관리 | 부품명, 부품코드, 단가, 구분(전용/공용/공임), 적용 장비(다중) |
| **마스터 관리** | 수리 세트 | 자주 사용하는 부품 조합을 프리셋으로 등록 · 원클릭 적용 |
| **AS 입고** | 일괄 입고 등록 | 공통 정보 1회 입력 + 인라인 품목별 다중 추가, 쉼표 시리얼 자동 분리 |
| **AS 수리** | 수리 기록 등록 | 체크박스로 부품 선택 → 비용 자동 계산 · 수리완료 자동 상태 변경 |
| **AS 출고** | 다중 출고 처리 | 수리완료 장비 선택 → 오늘 출고 / 날짜 선택 출고 |
| **AS 이력** | 통합 이력 조회 | 입고~출고 전체 이력 읽기 전용 조회 |
| **추출** | 견적서 발행 (데모) | 수리완료/출고 상태 장비만 조회 및 데모용 PDF 추출 |
| **추출** | 세금계산서 등록 | 출고 완료(SHIPPED) 장비의 세금계산서 발행 여부 마킹 (내부 조회용) |
| **대시보드** | KPI 카드 | 수리 대기 · 이번 달 입고 · 수리 완료(미출고) · 이번 달 출고 |
| **UI/UX** | 상태별 행 색상 | 뱃지 대신 전체 행(Row)에 입고(노랑), 수리완료(초록), 출고(파랑), 폐기(빨강) 등의 색상을 적용해 직관성 극대화 |
| **UI/UX** | 네비게이션 일관성 | 대시보드 중심의 빵부스러기(Breadcrumb), 검색/필터 버튼 한국어 최적화 |

### ⬜ P1 — 고도화 기능 (예정)

- 단가 그룹별 차등 가격 관리
- 분해도 이미지 연동 (이미지 클릭 → 부품 정보 기입)
- 엑셀 견적서 생성 및 추출 (수리 완료/가견적서)
- 모바일 반응형 최적화

---

## 📁 프로젝트 구조

```
AS_APP/
├── as_project/                       # Django 프로젝트 설정
│   ├── settings.py                   #   Unfold, DB, SIDEBAR 네비게이션 설정
│   ├── urls.py                       #   URL 라우팅
│   ├── wsgi.py                       #   WSGI 설정
│   └── asgi.py                       #   ASGI 설정
├── as_app/                           # 핵심 애플리케이션
│   ├── models.py                     #   데이터 모델 (마스터 + AS 프로세스 + 프록시)
│   ├── admin.py                      #   Django Admin 커스터마이징 (전체 UI 로직)
│   ├── forms.py                      #   커스텀 폼 (ASTicketForm 등)
│   ├── dashboard.py                  #   대시보드 KPI 콜백 함수
│   ├── apps.py                       #   앱 설정
│   ├── static/as_app/               #   정적 파일
│   │   ├── css/                      #     인라인 수정 CSS, FAB 숨김 CSS
│   │   └── js/                       #     입고 폼 JS, 출고 행 클릭 JS
│   └── migrations/                   #   DB 마이그레이션 파일
├── templates/                        # 커스텀 템플릿
│   └── admin/as_app/                 #   Admin 템플릿 오버라이드
│       ├── company_tabs.html         #     업체관리 탭 네비게이션 (공통)
│       ├── company/change_list.html  #     매출처업체 목록 (탭 포함)
│       ├── outsourcecompany/         #     의뢰업체 목록 (탭 포함)
│       ├── part/change_list.html     #     수리부품 목록 (세트 관리 버튼)
│       ├── repairticket/             #     수리 기록 폼 (프리셋 관리)
│       └── outbound_date_select.html #     출고 날짜 선택 중간 페이지
├── (db.sqlite3)                      # (구형 SQLite 데이터베이스 백업, 미사용)
├── manage.py                         # Django 관리 명령어
├── requirements.txt                  # Python 의존성 패키지
├── build.sh                          # Render 빌드 스크립트
├── .cursorrules                      # 개발 지침 (AI 및 개발자용)
├── GEMINI.MD                         # 개발 명세서 (기능 상세)
└── README.md                         # 이 문서
```

---

## 🚀 설치 및 실행

### 사전 요구사항

- **Python** 3.10 이상
- **pip** (Python 패키지 매니저)

### 1. 저장소 클론

```bash
git clone https://github.com/yoonkihwan/AS_APP.git
cd AS_APP
```

### 2. 가상 환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 데이터베이스 마이그레이션

```bash
python manage.py migrate
```

### 5. 관리자 계정 생성

```bash
python manage.py createsuperuser
```

### 6. 개발 서버 실행

```bash
python manage.py runserver
```

브라우저에서 **http://127.0.0.1:8000/admin/** 으로 접속합니다.

---

## 📖 사용 가이드

### 사이드바 메뉴 구성

| 섹션 | 메뉴 | 설명 |
|:-----|:-----|:-----|
| **대시보드** | 대시보드 | KPI 카드 + 수리 대기 목록 + 최근 출고 목록 |
| **AS 관리** | 통합 이력 | 전체 AS 이력 읽기 전용 조회 |
| | 입고 등록 | 공통 정보 + 인라인 품목 일괄 입고 |
| | 수리 기록 등록 | 입고/수리대기 상태 장비의 수리 내역 입력 |
| | 출고 등록 | 수리완료 장비 선택 후 일괄 출고 |
| | 세금계산서 등록 | 출고된 티켓들의 세금계산서 발행 여부를 리스트 뷰에서 체크 |
| **추출** | 견적서 발행 (데모) | 수리완료/출고 건에 대한 견적서 PDF 파일 다운로드 |
| **기준 정보** | 업체관리 | 탭 전환: 매출처업체 / 의뢰업체 |
| | 수리부품 관리 | 부품 등록 + 수리 세트 관리 바로가기 |
| | 브랜드 & 툴 관리 | 브랜드별 장비/툴 관리 |

### AS 처리 흐름

```
📦 입고 등록  →  🔩 수리 기록 등록  →  🚚 출고 처리
   (입고)         (입고/수리대기)       (수리완료 → 출고)
                      ↓
               📋 통합 이력 조회
```

1. **입고 등록** — 업체·날짜·담당자를 입력하고, 인라인으로 장비(브랜드→툴/시리얼)를 추가합니다. 쉼표로 시리얼 구분 시 다건 자동 생성.
2. **수리 기록** — 입고된 장비의 "🔧 수리 기록 등록" 버튼 클릭 → 부품 체크박스 선택 또는 수리 세트 적용 → 저장 시 비용 자동 계산 + 수리완료 상태 자동 변경.
3. **출고 처리** — 수리 완료된 장비를 체크박스로 선택 → "오늘 날짜 출고" 또는 "날짜 선택 출고" 액션으로 일괄 출고 처리.
4. **통합 이력** — 모든 AS 이력을 상태·업체·날짜·브랜드 등으로 필터링/검색하여 조회 (읽기 전용).

---

## 🗄 데이터베이스 설계

### 마스터 데이터 (Master Data)

```
CompanyCategory (단가 그룹)
  └─ name: 단가 그룹명

Company (매출처)
  ├─ name: 업체명
  ├─ price_group → CompanyCategory (FK)
  ├─ region: 지역/국가
  └─ address: 주소

OutsourceCompany (의뢰업체)
  ├─ name: 의뢰업체명
  ├─ contact: 연락처
  └─ memo: 메모

Brand (브랜드)
  └─ name: 브랜드명

Tool (장비/툴)
  ├─ brand → Brand (FK)
  └─ model_name: 모델명

Part (부품/공임)
  ├─ tools → Tool (M2M, 다중 적용)
  ├─ name: 부품명
  ├─ code: 부품코드
  ├─ price: 단가
  └─ part_type: 구분 (전용/공용/공임)

RepairPreset (수리 세트)
  ├─ name: 세트명
  ├─ tools → Tool (M2M, 적용 장비)
  └─ parts → Part (M2M, 포함 부품)
```

### AS 프로세스 데이터 (Transaction Data)

```
InboundBatch (입고 배치)
  ├─ inbound_date: 입고 날짜
  ├─ company → Company (FK)
  ├─ manager: 담당자
  ├─ memo: 메모
  └─ created_at: 생성일 (자동)

ASTicket (AS 티켓)
  ├─ [입고] inbound_batch → InboundBatch (FK)
  ├─ [입고] inbound_date, company, manager, tool, serial_number, symptom
  ├─ [수리] repair_content, used_parts → Part (M2M), repair_cost (자동)
  ├─ [의뢰] outsource_company → OutsourceCompany (FK)
  ├─ [상태] status: 입고 → 수리대기 → 수리완료/수리의뢰/자체폐기 → 출고
  └─ [출고] outbound_date, estimate_status, tax_invoice
```

### 프록시 모델 (Admin 뷰 분리)

| 프록시 모델 | 용도 | 표시 상태 |
|:-----------|:-----|:---------|
| `InboundTicket` | 입고 등록 전용 | 입고 |
| `RepairTicket` | 수리 기록 전용 | 입고/수리대기/수리의뢰 |
| `OutboundTicket` | 출고 처리 전용 | 수리완료 |
| `ASHistory` | 통합 이력 조회 | 전체 (읽기 전용) |
| `EstimateTicket` | 견적서 조회용 | 수리완료/출고 |
| `TaxInvoiceTicket` | 세금계산서 등록 | 출고 (내부 확인용) |

---

## 🗺 개발 로드맵

- [x] 환경 설정 — Django 프로젝트 생성, Unfold 설치, PostgreSQL 연동
- [x] 마스터 모델 구현 — Company, Brand, Tool, Part 모델 정의 및 Admin 등록
- [x] 핵심 로직 구현 (P0) — ASTicket, InboundBatch, 입고/수리/출고 로직
- [x] UI 개선 — Django Unfold 테마 적용 및 사이드바 구성
- [x] 대시보드 — KPI 통계 카드 + 수리 대기/최근 출고 목록
- [x] 수리 세트 (RepairPreset) — 자주 사용하는 부품 조합 프리셋
- [x] 업체관리 통합 — 매출처/의뢰업체 탭 네비게이션으로 통합
- [x] UI/UX 고도화 — 상태 컬러 뱃지 적용, 대시보드 네비게이션 일치 및 한국어 최적화
- [x] Render 배포 — WhiteNoise + PostgreSQL 운영 환경 구성
- [x] **툴 입출고 관리 (신규 앱)** — 기존 `inventory.db`의 텍스트 기반 관리를 체계적인 RDBMS 기반 관리로 이전. 일괄 입고, 다중 시리얼 출고, 현재 재고 연동 UI 적용 완료.
- [x] **시스템 계정 관리** — 시스템 관리 권한 제어 및 일반 권한 일괄 부여 기능 적용 완료.
- [ ] 단가 그룹별 가격 관리
- [ ] 엑셀 견적서 출력
- [ ] 분해도 이미지 매핑
- [ ] 모바일 반응형 최적화

---

## 📜 라이선스

사내 전용 프로젝트 — 내부 사용 목적으로 개발되었습니다.
