<<<<<<< HEAD
# 🔧 사내용 AS 관리 시스템 (Internal AS Management System)

AS 입고부터 수리, 출고, 이력 관리까지의 전 과정을 전산화하여 업무 효율성을 높이고 데이터 누락을 방지하는 사내 웹 애플리케이션입니다.

> **핵심 가치:** 쉽고 빠른 입력(드롭다운, 일괄 입고) · 정확한 이력 추적 · 마스터 데이터 기반의 체계적 관리

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
| **Language** | Python | 전체 비즈니스 로직 처리 및 백엔드 구현 |
| **Framework** | Django 5.2 | 웹 애플리케이션 프레임워크 (MVT 패턴, ORM 활용) |
| **Database** | SQLite (초기) | 개발 및 초기 단계용 내장 DB (추후 PostgreSQL 마이그레이션 고려) |
| **Frontend/UI** | Django Unfold | Django Admin을 현대적인 UI로 커스터마이징하여 대시보드 구축 |
| **Import/Export** | django-import-export | 데이터 일괄 가져오기/내보내기 지원 |

---

## ✨ 주요 기능

### ✅ P0 — 핵심 기능 (MVP, 구현 완료)

| 카테고리 | 기능 | 설명 |
|:---------|:-----|:-----|
| **마스터 관리** | 업체 관리 | 업체명, 구분(매출처/의뢰처), 단가 그룹, 지역/국가, 주소 |
| **마스터 관리** | 브랜드 & 툴 관리 | 브랜드별 장비/툴 통합 관리 (인라인 편집) |
| **마스터 관리** | 부품 관리 | 부품명, 부품코드, 단가, 구분(전용/공용), 적용 장비(다중) |
| **AS 입고** | 일괄 입고 등록 | 공통 정보 1회 입력 후 품목별 인라인 다중 추가 |
| **AS 수리** | 수리 내역 입력 | 입고된 장비 필터링 후 수리 내용·사용 부품 기록 |
| **AS 출고** | 다중 출고 처리 | '수리 완료' 상태 장비를 선택하여 일괄 출고 |
| **AS 이력** | 통합 이력 조회 | 입고~출고 전체 이력 읽기 전용 조회, 필드별 검색 |
| **대시보드** | KPI 카드 | 수리 대기 · 금일 입고 · 이번 달 입고 실시간 통계 |

### ⬜ P1 — 고도화 기능 (예정)

- 단가 그룹별 차등 가격 관리
- 분해도 이미지 연동 (이미지 클릭 → 부품 정보 기입)
- 엑셀 견적서 생성 및 추출 (수리 완료/가견적서)

---

## 📁 프로젝트 구조

```
AS_APP/
├── as_project/            # Django 프로젝트 설정
│   ├── settings.py        #   Unfold, DB, 앱 설정
│   ├── urls.py            #   URL 라우팅
│   ├── wsgi.py            #   WSGI 설정
│   └── asgi.py            #   ASGI 설정
├── as_app/                # 핵심 애플리케이션
│   ├── models.py          #   데이터 모델 (마스터 + AS 프로세스)
│   ├── admin.py           #   Django Admin 커스터마이징
│   ├── dashboard.py       #   대시보드 KPI 콜백 함수
│   ├── apps.py            #   앱 설정
│   └── migrations/        #   DB 마이그레이션 파일
├── templates/             # 커스텀 템플릿
│   └── admin/             #   Admin 템플릿 오버라이드
├── db.sqlite3             # SQLite 데이터베이스
├── manage.py              # Django 관리 명령어
├── requirements.txt       # Python 의존성 패키지
├── GEMINI.MD              # 개발 명세서
├── URL_LIST.md            # URL 목록 문서
└── README.md              # 이 문서
```

---

## 🚀 설치 및 실행

### 사전 요구사항

- **Python** 3.10 이상
- **pip** (Python 패키지 매니저)

### 1. 저장소 클론

```bash
git clone <repository-url>
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
| **대시보드** | 대시보드 | KPI 카드 (수리 대기 / 금일 입고 / 이번 달 입고) |
| **AS 관리** | 입고 등록 | 공통 정보 + 인라인 품목 일괄 입고 |
| | 수리 기록 | 입고/수리대기 상태 장비의 수리 내역 입력 |
| | 출고 처리 | 수리완료 장비 선택 후 일괄 출고 |
| | 통합 이력 | 전체 AS 이력 읽기 전용 조회 |
| **기준 정보** | 업체 관리 | 매출처/의뢰처 업체 등록 및 수정 |
| | 브랜드 & 툴 관리 | 브랜드별 장비/툴 관리 |
| | 부품 관리 | 수리 부품 등록 및 적용 장비 매핑 |

### AS 처리 흐름

```
📦 입고 등록  →  🔩 수리 기록  →  🚚 출고 처리
   (입고)         (수리대기)        (수리완료 → 출고)
                     ↓
              📋 통합 이력 조회
```

1. **입고 등록** — 업체·날짜·담당자를 입력하고, 인라인으로 장비(툴/시리얼/증상)를 추가합니다.
2. **수리 기록** — 입고된 장비를 선택하여 수리 내용, 사용 부품, AS 비용을 기록합니다.
3. **출고 처리** — 수리 완료된 장비를 체크박스로 선택하여 일괄 출고 처리합니다.
4. **통합 이력** — 모든 AS 이력을 검색·필터링하여 조회합니다 (읽기 전용).

---

## 🗄 데이터베이스 설계

### 마스터 데이터 (Master Data)

```
CompanyCategory (단가 그룹)
  └─ name: 단가 그룹명

Company (업체)
  ├─ name: 업체명
  ├─ company_type: 업체 구분 (매출처/의뢰처/양쪽)
  ├─ price_group → CompanyCategory (FK)
  ├─ region: 지역/국가
  └─ address: 주소

Brand (브랜드)
  └─ name: 브랜드명

Tool (장비/툴)
  ├─ brand → Brand (FK)
  └─ model_name: 모델명

Part (부품)
  ├─ tools → Tool (M2M, 다중 적용)
  ├─ name: 부품명
  ├─ code: 부품코드
  ├─ price: 단가
  └─ part_type: 구분 (전용/공용)
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
  ├─ [수리] repair_content, used_parts → Part (M2M), repair_cost
  ├─ [상태] status: 입고 → 수리대기 → 수리완료 → 출고
  └─ [출고] outbound_date, estimate_status, tax_invoice
```

### 프록시 모델 (Admin 뷰 분리)

| 프록시 모델 | 용도 | 표시 상태 |
|:-----------|:-----|:---------|
| `InboundTicket` | 입고 등록 전용 | 입고 |
| `RepairTicket` | 수리 기록 전용 | 입고/수리대기 |
| `OutboundTicket` | 출고 처리 전용 | 수리완료 |
| `ASHistory` | 통합 이력 조회 | 전체 (읽기 전용) |

---

## 🗺 개발 로드맵

- [x] 환경 설정 — Django 프로젝트 생성, Unfold 설치, SQLite 연동
- [x] 마스터 모델 구현 — Company, Brand, Tool, Part 모델 정의 및 Admin 등록
- [x] 핵심 로직 구현 (P0) — ASTicket, InboundBatch, 입고/수리/출고 로직
- [x] UI 개선 — Django Unfold 테마 적용 및 사이드바 구성
- [x] 대시보드 — KPI 통계 카드 (수리 대기, 금일/월간 입고)
- [ ] 단가 그룹별 가격 관리
- [ ] 엑셀 견적서 출력
- [ ] 분해도 이미지 매핑

---

## 📜 라이선스

사내 전용 프로젝트 — 내부 사용 목적으로 개발되었습니다.
=======
- [프로그램 메뉴얼 보기](./GEMINI.MD)
>>>>>>> 68a2be91931e42b097617ccdb9be5f5469400432
