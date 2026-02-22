# TOOL_INVENTORY 개발 명세서 (기존 프로그램 웹 전환)

## 1. 개요
*   **시스템 명:** 장비/툴 입출고 관리 시스템 (Tool & Inventory Management)
*   **목적:** 기존 데스크톱 파이썬 프로그램(`TOOL 입출고 관리.exe`)과 `inventory.db`의 데이터를 웹 애플리케이션으로 전환하여 AS 프로젝트와 같은 서버에서 작동하도록 함.
*   **주요 특징:** 
    * AS 시스템(`as_app`)과는 데이터와 화면을 완전히 격리 (다중 Admin Site 구조).
    * 기존 SQLite 데이터 모델을 장고(Django) 모델로 매핑하고 데이터 무결성을 유지하며 마이그레이션.

---

## 2. 기존 데이터베이스 분석 및 테이블 매핑
기존 프로그램(`inventory.db`)은 매우 직관적인 텍스트 기반의 데이터 구조를 가지고 있습니다. 이것을 장고의 관계형 데이터베이스(PostgreSQL) 형태로 변환하여 구현합니다.

### 2.1 마스터 테이블
기존 데이터베이스엔 단순히 이름만 관리되는 목록들이 있습니다.
*   **Supplier (입고처/매입처):** 기존 `suppliers` 테이블.
    *   `name`: 업체명 (Primary Key)
*   **ReleaseSupplier (출고처/현장):** 기존 `release_suppliers` 테이블.
    *   `name`: 업체명 (Primary Key)
*   **ItemName (품목 이름):** 기존 `item_names` 테이블.
    *   `name`: 품목명 (Primary Key)

*장고 모델화 방향:*
유연한 조회를 위해 장고에서는 자동 생성되는 `id` (정수형 PK)를 사용하고, `name`을 고유(Unique) 필드로 갖게끔 마이그레이션 할 예정입니다.

### 2.2 메인 테이블 (입출고 내역)
*   **Inventory (재고/입출고 상태):** 기존 `inventory` 테이블.
    *   `id`: `UUID` 형태의 기존 고유값. 장고에서도 `UUIDField(primary_key=True)`를 사용하여 기존 ID 유지.
    *   `supplier`: 입고처 (Supplier 모델 Foreign Key 연동)
    *   `date`: 입고일 (`DateField`)
    *   `name`: 품목명 (ItemName 모델 Foreign Key 연동)
    *   `serial`: 시리얼 번호 (`CharField`, 선택 입력 가능)
    *   `release_date`: 출고일 (`DateField`, nullable)
    *   `release_supplier`: 출고처 (ReleaseSupplier 모델 Foreign Key 연동, nullable)
    *   `status`: 상태 (`CharField` 선택값 - 예: '재고', '출고')

---

## 3. 화면 구성 및 분리 원칙 (Admin Site 분리)
AS 관리와 툴 인벤토리 관리를 하나의 사이트에서 운영하되, 사용자가 작업 도중 헷갈리지 않게 **접속 경로와 관리자 화면 전체를 분리**합니다.

*   `as.yoursite.com/admin/`: **AS 관리 시스템** (AS 업무 관련 기능만 노출)
*   `as.yoursite.com/inventory/`: **툴/장비 관리 시스템** (본 앱 관련 기능만 노출)

본 앱(Tool Inventory)의 Admin 화면은 다음을 충족합니다:
*   **대시보드:** 별도의 독립적인 대시보드를 구성. (예: 현재 남은 재고 건수, 이 달의 입/출고 건수 등)
*   **마스터 관리:** 입고처, 출고처, 품목명 각각의 텍스트 추가/수정용 간이 화면.
*   **메인 관리 화면:**
    *   기존 프로그램을 본떠서 "입고 등록", "출고 등록" 버튼이나 액션이 직관적이어야 함.
    *   목록에서 시리얼 번호, 품목명 기반의 강력한 필터링/검색 기능 제공.

---

## 4. 데이터 마이그레이션 전략 (기존 DB 살리기)
새로운 모델이 구축되면, 기존 `inventory.db` 파일의 데이터를 읽어와서 `tool_inventory`의 PostgreSQL 테이블에 그대로 이식하는 전용 1회성 마이그레이션 스크립트를 작성하여 100% 복구합니다.

## 5. 단계별 개발 목표 (개발 프로세스)
1. **장고 모델 생성 (models.py):** 위 명세대로 데이터베이스 구조를 짭니다.
2. **독립된 Admin 등록 (admin.py):** AS 시스템과 섞이지 않도록 `ToolInventoryAdminSite`를 커스텀으로 만들고 연동합니다.
3. **데이터 인서트 스크립트 작성:** 파이썬으로 기존 SQLite를 열어서 장고 ORM을 사용해 새 DB에 복제합니다.
4. **UI 편의성 작업:** 기존 데스크톱 exe만큼 빠르고 편하게 쓸 수 있도록 Django Unfold를 사용해 가독성과 접근성을 높입니다.
