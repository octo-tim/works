# 코드 리뷰 보고서

**저장소**: [octo-tim/works](https://github.com/octo-tim/works)  
**분석 일자**: 2026년 1월 12일  
**분석 도구**: Flake8, Bandit, Radon, 수동 코드 리뷰

---

## 1. 프로젝트 개요

### 1.1 프로젝트 설명

이 프로젝트는 **비즈니스 일정 공유 시스템**으로, FastAPI 기반의 웹 애플리케이션입니다. 주요 기능으로는 프로젝트 관리, 업무(Task) 관리, 일정 공유, 회의록 관리, 업무 템플릿, AI 기반 업무 분석 등이 포함되어 있습니다.

### 1.2 기술 스택

| 구분 | 기술 |
|------|------|
| **백엔드 프레임워크** | FastAPI |
| **데이터베이스** | SQLite (개발) / PostgreSQL (프로덕션) |
| **ORM** | SQLAlchemy |
| **템플릿 엔진** | Jinja2 |
| **프론트엔드** | TailwindCSS (CDN) |
| **인증** | JWT (python-jose) |
| **AI 통합** | Google Gemini API |
| **배포** | Docker, Render |

### 1.3 프로젝트 구조

```
works/
├── main.py              # 메인 애플리케이션 (2,356 라인)
├── models.py            # SQLAlchemy 모델 정의 (253 라인)
├── config.py            # 설정 관리 (47 라인)
├── database.py          # 데이터베이스 연결 (18 라인)
├── utils.py             # 유틸리티 함수 (67 라인)
├── wbs_templates.py     # WBS 템플릿 데이터 (294 라인)
├── templates/           # Jinja2 HTML 템플릿 (16개 파일)
├── static/              # 정적 파일
├── Dockerfile           # Docker 설정
└── requirements.txt     # Python 의존성
```

---

## 2. 코드 품질 분석

### 2.1 정적 분석 결과 요약

| 분석 항목 | 결과 | 평가 |
|----------|------|------|
| **총 코드 라인 (LOC)** | 2,356 | - |
| **논리적 코드 라인 (LLOC)** | 1,258 | - |
| **주석 비율** | 8% | ⚠️ 낮음 |
| **평균 순환 복잡도** | B (5.23) | ⚠️ 보통 |
| **유지보수성 지수** | C (0.00) | ❌ 매우 낮음 |
| **Flake8 경고** | 200+ | ❌ 개선 필요 |
| **보안 이슈 (Bandit)** | 5건 | ⚠️ 검토 필요 |

### 2.2 Flake8 주요 이슈

#### 미사용 Import
```python
# main.py:1, 4, 20
from fastapi import status  # 미사용
import shutil               # 미사용
import re                   # 미사용
```

#### 코드 스타일 위반
- **E302/E303**: 함수/클래스 사이 빈 줄 규칙 위반 (다수)
- **W293**: 공백만 있는 빈 줄 (다수)
- **W291**: 줄 끝 공백 (다수)
- **E501**: 150자 초과 라인 (2건)

#### 코드 중복
```python
# main.py:1013-1014 - 동일한 키로 딕셔너리 중복 할당
"users": users,
"users": users,  # 중복
```

```python
# main.py:660-661 - 중복된 return 문
return RedirectResponse(url="/", status_code=303)
return RedirectResponse(url="/", status_code=303)  # 도달 불가
```

### 2.3 순환 복잡도 (Cyclomatic Complexity)

**높은 복잡도 함수 (개선 필요)**:

| 함수명 | 복잡도 | 등급 | 권장 조치 |
|--------|--------|------|-----------|
| `read_root` | 44 | F | 분리 필수 |
| `process_event_from_ai` | 26 | D | 분리 권장 |
| `create_meeting_minute` | 19 | C | 리팩토링 권장 |
| `generate_work_report_endpoint` | 17 | C | 리팩토링 권장 |
| `get_project_tasks` | 14 | C | 검토 필요 |
| `create_project` | 12 | C | 검토 필요 |

> **권장사항**: 복잡도 10 이상인 함수는 더 작은 단위로 분리하여 테스트 용이성과 유지보수성을 향상시켜야 합니다.

---

## 3. 보안 취약점 분석

### 3.1 발견된 보안 이슈

#### 🔴 Medium: SQL Injection 위험 (3건)

**위치**: `main.py:213-215`

```python
# 문제 코드
for eng, kor in config.DEPARTMENT_MAPPING.items():
    db.execute(text(f"UPDATE users SET department = '{kor}' WHERE department = '{eng}'"))
```

**위험성**: 현재는 `config.DEPARTMENT_MAPPING`의 값이 하드코딩되어 있어 즉각적인 위험은 낮지만, 향후 동적 입력을 받게 될 경우 SQL Injection 공격에 취약해질 수 있습니다.

**권장 수정**:
```python
# 파라미터 바인딩 사용
db.execute(
    text("UPDATE users SET department = :kor WHERE department = :eng"),
    {"kor": kor, "eng": eng}
)
```

#### 🟡 Low: 하드코딩된 비밀 키

**위치**: `config.py:23`

```python
SECRET_KEY = "dev-secret-key-change-in-production"  # 개발용 기본값
```

**권장사항**: 프로덕션 환경에서는 반드시 환경 변수를 통해 강력한 비밀 키를 설정해야 합니다. 현재 경고 메시지는 출력되지만, 애플리케이션 시작을 차단하지는 않습니다.

#### 🟡 Low: 빈 except 블록

**위치**: `main.py:1416-1417`

```python
except:
    pass
```

**권장사항**: 최소한 로깅을 추가하여 디버깅이 가능하도록 해야 합니다.

### 3.2 추가 보안 권장사항

| 항목 | 현재 상태 | 권장 조치 |
|------|----------|-----------|
| **CSRF 보호** | 미구현 | FastAPI-CSRF 또는 토큰 기반 보호 추가 |
| **Rate Limiting** | 미구현 | slowapi 등을 통한 요청 제한 추가 |
| **입력 검증** | 부분적 | Pydantic 모델을 통한 체계적 검증 |
| **에러 메시지** | 상세 노출 | 프로덕션에서 상세 에러 숨김 처리 |
| **HTTPS 강제** | 미구현 | 프로덕션 환경에서 HTTPS 리다이렉트 |

---

## 4. 아키텍처 및 설계 평가

### 4.1 장점

1. **명확한 기술 스택 선택**: FastAPI + SQLAlchemy 조합은 현대적이고 효율적입니다.

2. **AI 통합**: Google Gemini API를 활용한 자연어 업무 처리, WBS 생성, 회의록 분석 등 혁신적인 기능을 제공합니다.

3. **유연한 데이터베이스 지원**: SQLite(개발)와 PostgreSQL(프로덕션) 간 전환이 용이합니다.

4. **반응형 UI**: TailwindCSS를 활용한 모바일 친화적 인터페이스를 제공합니다.

5. **다중 담당자 지원**: 업무와 프로젝트에 여러 담당자를 할당할 수 있는 유연한 구조입니다.

### 4.2 개선이 필요한 영역

#### 4.2.1 단일 파일 구조 (God Object 안티패턴)

**문제점**: `main.py`가 2,356 라인으로 모든 라우트, 비즈니스 로직, AI 헬퍼 클래스를 포함하고 있습니다.

**권장 구조**:
```
app/
├── __init__.py
├── main.py              # FastAPI 앱 초기화만
├── routers/
│   ├── auth.py          # 인증 관련 라우트
│   ├── projects.py      # 프로젝트 관련 라우트
│   ├── tasks.py         # 업무 관련 라우트
│   ├── calendar.py      # 일정 관련 라우트
│   ├── meetings.py      # 회의록 관련 라우트
│   └── ai.py            # AI 관련 라우트
├── services/
│   ├── ai_service.py    # AIHelper 클래스
│   └── report_service.py
├── schemas/             # Pydantic 스키마
├── models.py
├── config.py
└── utils.py
```

#### 4.2.2 비즈니스 로직과 라우트 혼재

현재 라우트 핸들러 내에 비즈니스 로직이 직접 구현되어 있어 테스트와 재사용이 어렵습니다.

**현재 코드**:
```python
@app.post("/tasks/create")
def create_task(...):
    # 비즈니스 로직이 라우트에 직접 구현
    new_task = models.Task(...)
    db.add(new_task)
    db.commit()
```

**권장 패턴**:
```python
# services/task_service.py
class TaskService:
    def create_task(self, db: Session, task_data: TaskCreate, user: User) -> Task:
        # 비즈니스 로직
        ...

# routers/tasks.py
@router.post("/create")
def create_task(..., service: TaskService = Depends()):
    return service.create_task(db, task_data, current_user)
```

#### 4.2.3 에러 처리 일관성 부족

일부 함수는 예외를 발생시키고, 일부는 리다이렉트를 반환하며, 일부는 조용히 실패합니다.

```python
# 일관성 없는 에러 처리 예시
if not current_user:
    return RedirectResponse(url="/login")  # 리다이렉트

if not current_user:
    raise HTTPException(status_code=401)   # 예외 발생
```

---

## 5. 데이터 모델 평가

### 5.1 모델 구조

현재 13개의 데이터 모델이 정의되어 있으며, 전반적으로 잘 설계되어 있습니다.

| 모델 | 용도 | 평가 |
|------|------|------|
| User | 사용자 관리 | ✅ 양호 |
| Project | 프로젝트 관리 | ✅ 양호 |
| Task | 업무 관리 | ⚠️ 레거시 필드 존재 |
| Event | 일정 관리 | ✅ 양호 |
| MeetingMinutes | 회의록 | ✅ 양호 |
| WorkTemplate | 업무 템플릿 | ✅ 양호 |
| WorkReport | 업무 리포트 | ✅ 양호 |

### 5.2 개선 권장사항

#### 레거시 필드 정리

```python
# models.py - Task 모델
assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 레거시
assignees = relationship("User", secondary=task_assignees, ...)       # 신규

# 권장: 마이그레이션 후 assignee_id 제거
```

#### 인덱스 최적화

자주 조회되는 필드에 인덱스 추가를 권장합니다:

```python
class Task(Base):
    status = Column(String, default="Todo", index=True)  # 인덱스 추가
    due_date = Column(Date, nullable=True, index=True)   # 인덱스 추가
```

---

## 6. 프론트엔드 평가

### 6.1 장점

- **TailwindCSS 활용**: 일관된 디자인 시스템 적용
- **반응형 디자인**: 모바일/데스크톱 대응
- **사용자 친화적 UI**: 직관적인 네비게이션과 카드 기반 레이아웃

### 6.2 개선 권장사항

| 항목 | 현재 상태 | 권장 조치 |
|------|----------|-----------|
| **TailwindCSS** | CDN 사용 | 빌드 시스템 도입 (성능 최적화) |
| **JavaScript** | 인라인 스크립트 | 별도 파일로 분리 |
| **에러 표시** | 일부만 구현 | 통일된 에러/성공 메시지 시스템 |
| **로딩 상태** | 미구현 | AI 요청 시 로딩 인디케이터 추가 |

---

## 7. 테스트 및 문서화

### 7.1 현재 상태

| 항목 | 상태 | 평가 |
|------|------|------|
| **단위 테스트** | 없음 | ❌ 심각 |
| **통합 테스트** | 없음 | ❌ 심각 |
| **API 문서** | FastAPI 자동 생성 | ✅ 양호 |
| **코드 주석** | 8% | ⚠️ 부족 |
| **README** | 없음 | ❌ 필요 |

### 7.2 권장 테스트 전략

```python
# tests/test_tasks.py 예시
import pytest
from fastapi.testclient import TestClient

def test_create_task(client: TestClient, auth_headers: dict):
    response = client.post(
        "/tasks/create",
        data={"title": "테스트 업무", "status": "Todo"},
        headers=auth_headers
    )
    assert response.status_code == 303
```

---

## 8. 성능 고려사항

### 8.1 잠재적 성능 이슈

1. **N+1 쿼리 문제**: 관계 데이터 로딩 시 발생 가능
   ```python
   # 문제 코드
   tasks = db.query(models.Task).all()
   for task in tasks:
       print(task.assignees)  # 각 태스크마다 추가 쿼리 발생
   
   # 해결책: eager loading
   tasks = db.query(models.Task).options(joinedload(models.Task.assignees)).all()
   ```

2. **대량 데이터 처리**: 페이지네이션 미구현으로 대량 데이터 시 성능 저하 우려

3. **AI API 호출**: 동기 방식으로 구현되어 응답 지연 발생 가능

### 8.2 권장 최적화

- 데이터베이스 쿼리에 페이지네이션 적용
- AI API 호출을 비동기 처리로 전환
- Redis 등을 활용한 캐싱 도입 검토

---

## 9. 종합 평가

### 9.1 점수 요약

| 평가 항목 | 점수 (10점 만점) | 비고 |
|----------|-----------------|------|
| **기능 완성도** | 8 | 다양한 기능 구현 |
| **코드 품질** | 5 | 리팩토링 필요 |
| **보안** | 6 | 기본 보안 구현, 개선 필요 |
| **아키텍처** | 4 | 구조 개선 시급 |
| **테스트** | 2 | 테스트 부재 |
| **문서화** | 4 | 문서화 부족 |
| **성능** | 6 | 최적화 여지 있음 |
| **종합** | **5.0** | 개선 필요 |

### 9.2 우선순위별 개선 권장사항

#### 🔴 즉시 개선 (High Priority)

1. **main.py 분리**: 라우터별로 파일 분리하여 유지보수성 향상
2. **SQL Injection 수정**: 파라미터 바인딩 적용
3. **테스트 코드 작성**: 핵심 기능에 대한 테스트 추가
4. **README 작성**: 프로젝트 설명, 설치 방법, 사용법 문서화

#### 🟡 단기 개선 (Medium Priority)

1. **Pydantic 스키마 도입**: 요청/응답 데이터 검증 강화
2. **에러 처리 통일**: 일관된 에러 처리 패턴 적용
3. **코드 스타일 정리**: Flake8 경고 해결
4. **CSRF 보호 추가**: 폼 제출 보안 강화

#### 🟢 장기 개선 (Low Priority)

1. **프론트엔드 빌드 시스템**: Vite 등 도입
2. **캐싱 레이어**: Redis 도입
3. **모니터링**: 로깅 및 APM 도입
4. **CI/CD 파이프라인**: 자동화된 테스트 및 배포

---

## 10. 결론

이 프로젝트는 **기능적으로 풍부하고 실용적인 비즈니스 도구**입니다. 특히 AI 통합 기능은 혁신적이며, 사용자 경험을 크게 향상시킵니다. 그러나 코드 구조와 품질 측면에서 상당한 개선이 필요합니다.

가장 시급한 과제는 **main.py의 분리**입니다. 2,300줄 이상의 단일 파일은 유지보수를 어렵게 하고, 팀 협업 시 충돌을 유발합니다. FastAPI의 라우터 기능을 활용하여 도메인별로 코드를 분리하면 코드 품질과 개발 생산성이 크게 향상될 것입니다.

또한 **테스트 코드 부재**는 장기적으로 큰 기술 부채가 될 수 있습니다. 핵심 비즈니스 로직에 대한 테스트를 우선적으로 작성하여 코드 변경 시 안정성을 확보해야 합니다.

---

**작성자**: AI Code Reviewer  
**검토 버전**: 최신 커밋 기준  
**다음 검토 예정**: 주요 리팩토링 완료 후
