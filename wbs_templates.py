# Standard WBS Templates

# Categories
CAT_BABY = "A. 유아용품 (Baby Products)"
CAT_CONST = "B. 건축자재 (Construction Materials)"
CAT_COMMON = "C. 공통 (Common)"

TEMPLATES = {
    # --- A. Baby Products ---
    "baby_npd": {
        "name": "1. 유아용품 신제품 개발 (Stage-Gate)",
        "category": CAT_BABY,
        "description": "아이디어부터 런칭까지의 Stage-Gate 프로세스 (젖병/유모차 등)",
        "phases": [
            {"phase_name": "Stage 1: 아이디어/기획", "tasks": [
                {"title": "시장 트렌드 및 VOC 분석", "description": "기존 제품 불만사항 및 경쟁사 리뷰 분석", "estimated_days": 5, "is_core": True, "checklist": ["맘카페 키워드 분석", "경쟁사 스펙 비교표"]},
                {"title": "컨셉 정의 및 스코핑", "description": "핵심 USP 도출 및 타겟 페르소나 설정", "estimated_days": 3, "is_core": True, "checklist": ["USP 정의서", "타겟 고객 정의"]}
            ]},
            {"phase_name": "Stage 2: 사업성/요구사항", "tasks": [
                {"title": "PRD (제품 요구사항) 작성", "description": "기능, 디자인, 소재, 안전 기준 명세", "estimated_days": 5, "is_core": True, "checklist": ["PRD 초안", "원가 목표 설정"]},
                {"title": "사업성 검토", "description": "예상 판매량 및 수익성 시뮬레이션", "estimated_days": 2, "is_core": True, "checklist": ["손익분기점(BEP) 분석"]}
            ]},
            {"phase_name": "Stage 3: 개발/샘플", "tasks": [
                {"title": "1차 프로토타입 제작", "description": "형상 및 기본 기능 구현", "estimated_days": 10, "is_core": True, "checklist": ["3D 목업", "작동 테스트"]},
                {"title": "개선 및 2차 샘플 (Golden Sample)", "description": "양산 직전 최종 사양 확정", "estimated_days": 7, "is_core": True, "checklist": ["금형 수정 사항 반영", "최종 스펙 확정"]}
            ]},
            {"phase_name": "Stage 4: 시험/검증", "tasks": [
                {"title": "사용자 테스트 (FGI)", "description": "타겟 고객 대상 실사용 테스트", "estimated_days": 5, "is_core": False, "checklist": ["체험단 피드백 수집", "사용성 개선"]},
                {"title": "KC 안전 시험 의뢰", "description": "공인 기관 시험 접수", "estimated_days": 1, "is_core": True, "checklist": ["시료 준비", "시험 신청서"]}
            ]},
            {"phase_name": "Stage 5: 런칭", "tasks": [
                {"title": "패키징 및 라벨링 확정", "description": "표시사항 검수 및 패키지 디자인", "estimated_days": 3, "is_core": True, "checklist": ["법적 표시사항 체크", "바코드 생성"]},
                {"title": "출고 및 판매 개시", "description": "초도 물량 입고 및 판매 채널 오픈", "estimated_days": 1, "is_core": True, "checklist": ["상세페이지 오픈", "재고 등록"]}
            ]}
        ]
    },
    "baby_kc": {
        "name": "2. 유아용품 KC 대응 (안전확인/인증)",
        "category": CAT_BABY,
        "description": "어린이제품 안전 특별법 대응 프로세스",
        "phases": [
            {"phase_name": "준비 (Preparation)", "tasks": [
                {"title": "대상 품목 분류 및 확인", "description": "안전인증/안전확인/공급자적합성 대상 여부 확인", "estimated_days": 1, "is_core": True, "checklist": ["KTR/KATRI 문의", "HS코드 확인"]},
                {"title": "시험 신청 서류 준비", "description": "사업자등록증, 제품설명서, 물질안전보건자료(MSDS)", "estimated_days": 2, "is_core": True, "checklist": ["신청서 작성", "부품 리스트 정리"]}
            ]},
            {"phase_name": "시험 (Testing)", "tasks": [
                {"title": "시료 발송 및 시험 접수", "description": "시험용 샘플 기관 발송", "estimated_days": 1, "is_core": True, "checklist": ["샘플 3개 준비", "접수비 납부"]},
                {"title": "시험 진행 및 보완", "description": "유해물질(프탈레이트 등) 및 물리적 안전성 테스트", "estimated_days": 15, "is_core": True, "checklist": ["시험 진행상황 체크", "보완 요청 대응"]}
            ]},
            {"phase_name": "인증/신고 (Certification)", "tasks": [
                {"title": "시험 성적서 수령", "description": "적합 판정 성적서 원본 확보", "estimated_days": 1, "is_core": True, "checklist": ["성적서 PDF 저장"]},
                {"title": "안전확인 신고 (해당 시)", "description": "제품안전관리원 신고 및 번호 발급", "estimated_days": 3, "is_core": True, "checklist": ["신고 필증 수령"]}
            ]},
            {"phase_name": "표시 (Labeling)", "tasks": [
                {"title": "KC 마크 및 표시사항 부착", "description": "제품 및 포장에 법적 표시사항 인쇄", "estimated_days": 2, "is_core": True, "checklist": ["도안 적용", "가독성 확인"]}
            ]}
        ]
    },
    "baby_sourcing": {
        "name": "3. ODM/OEM 소싱 & 제조사 선정",
        "category": CAT_BABY,
        "description": "중국 제조 등 외주 생산 파트너 발굴 및 계약",
        "phases": [
            {"phase_name": "소싱 (Sourcing)", "tasks": [
                {"title": "후보 제조사 리스트업 (Long-list)", "description": "알리바바, 전시회 등을 통한 후보군 10곳 발굴", "estimated_days": 5, "is_core": True, "checklist": ["공장 규모 확인", "주요 레퍼런스 체크"]},
                {"title": "RFQ (견적요청) 발송", "description": "스펙, 수량, 포장 조건을 포함한 견적 요청", "estimated_days": 2, "is_core": True, "checklist": ["RFQ 패키지 작성", "목표가 제시"]}
            ]},
            {"phase_name": "평가 (Evaluation)", "tasks": [
                {"title": "견적 비교 및 Short-list 선정", "description": "단가, 납기, MOQ 비교 후 3곳 선정", "estimated_days": 3, "is_core": True, "checklist": ["비교표 작성", "샘플 요청"]},
                {"title": "샘플 품질 평가", "description": "마감, 내구성, 기능 테스트", "estimated_days": 7, "is_core": True, "checklist": ["샘플 평가 리포트"]}
            ]},
            {"phase_name": "계약 (Contract)", "tasks": [
                {"title": "공장 심사 (Audit)", "description": "생산 설비 및 QC 시스템 현장/화상 점검", "estimated_days": 3, "is_core": False, "checklist": ["공장 심사 체크리스트"]},
                {"title": "계약 체결", "description": "공급 계약서 날인 (품질, 납기, 결제조건)", "estimated_days": 5, "is_core": True, "checklist": ["금형비 조건", "불량 페널티 조항"]}
            ]},
            {"phase_name": "양산 (Mass Production)", "tasks": [
                {"title": "Pilot 생산 (PP)", "description": "소량 시생산 및 문제점 점검", "estimated_days": 7, "is_core": True, "checklist": ["작업 표준서 확인"]},
                {"title": "양산 승인 (PSA)", "description": "양산 제품 최종 승인 및 선적 허가", "estimated_days": 1, "is_core": True, "checklist": ["Golden Sample 보관"]}
            ]}
        ]
    },
    "baby_packaging": {
        "name": "4. 패키징/라벨/설명서 표준화",
        "category": CAT_BABY,
        "description": "CS/규정 준수를 위한 패키지 및 동봉물 제작",
        "phases": [
            {"phase_name": "기획 (Planning)", "tasks": [
                {"title": "표시사항 요건 정의", "description": "국가별/품목별 필수 표기 항목 정리", "estimated_days": 2, "is_core": True, "checklist": ["KC 표시사항", "경고 문구"]},
                {"title": "패키지 구조 설계", "description": "박스 형태, 내부 트레이, 보호재 설계", "estimated_days": 3, "is_core": True, "checklist": ["지기구조 도면", "낙하 테스트 고려"]}
            ]},
            {"phase_name": "제작 (Production)", "tasks": [
                {"title": "다국어 매뉴얼 작성", "description": "한/영/중 사용 설명서 및 보증서", "estimated_days": 5, "is_core": True, "checklist": ["QR코드 삽입", "CS 연락처 포함"]},
                {"title": "디자인 및 감리", "description": "패키지 그래픽 디자인 및 인쇄 감리", "estimated_days": 3, "is_core": True, "checklist": ["색상 교정", "오타 점검"]}
            ]},
            {"phase_name": "물류 (Logistics)", "tasks": [
                {"title": "박스 규격 및 팔레타이징 최적화", "description": "물류비 절감을 위한 적재 효율 검토", "estimated_days": 1, "is_core": True, "checklist": ["CBM 계산", "바코드 부착 위치 지정"]}
            ]}
        ]
    },
    "baby_global": {
        "name": "5. 아마존/글로벌 이커머스 런칭",
        "category": CAT_BABY,
        "description": "해외 마켓플레이스 입점 및 판매 프로세스",
        "phases": [
            {"phase_name": "준비 (Preparation)", "tasks": [
                {"title": "채널 입점 요건 확인", "description": "카테고리 승인 및 필요 서류 준비", "estimated_days": 3, "is_core": True, "checklist": ["CPC 인증(미국)", "사업자 정보 등록"]},
                {"title": "리스팅 콘텐츠 제작", "description": "영문 상세페이지(A+ Content), 썸네일", "estimated_days": 7, "is_core": True, "checklist": ["키워드 분석", "영문 카피라이팅"]}
            ]},
            {"phase_name": "물류 (Logistics)", "tasks": [
                {"title": "FBA/3PL 입고", "description": "해외 창고 발송 및 입고 처리", "estimated_days": 10, "is_core": True, "checklist": ["Shipping Label 부착", "통관 진행"]},
                {"title": "재고 반영 확인", "description": "판매 가능 상태 전환 확인", "estimated_days": 1, "is_core": True, "checklist": ["재고 수량 체크"]}
            ]},
            {"phase_name": "마케팅 (Marketing)", "tasks": [
                {"title": "리뷰 시딩 (VINE)", "description": "초기 리뷰 확보 프로그램 신청", "estimated_days": 1, "is_core": True, "checklist": ["VINE 등록"]},
                {"title": "PPC 광고 캠페인", "description": "키워드 광고 세팅", "estimated_days": 3, "is_core": True, "checklist": ["자동 캠페인", "수동 타겟팅"]}
            ]}
        ]
    },
    "baby_recall": {
        "name": "6. 리콜/클레임 대응 (품질 이슈)",
        "category": CAT_BABY,
        "description": "불량/안전 이슈 발생 시 체계적인 대응 절차",
        "phases": [
            {"phase_name": "접수/분석 (Analysis)", "tasks": [
                {"title": "이슈 분류 및 긴급도 판단", "description": "안전/성능/외관 유형 분류 및 심각도 평가", "estimated_days": 1, "is_core": True, "checklist": ["피해 사례 수집", "안전위해성 평가"]},
                {"title": "원인 분석 (8D Report)", "description": "근본 원인 파악 및 유출 경로 추적", "estimated_days": 2, "is_core": True, "checklist": ["LOT 추적", "4M(Man,Machine,Material,Method) 분석"]}
            ]},
            {"phase_name": "조치 (Action)", "tasks": [
                {"title": "고객 공지 및 대응안 수립", "description": "교환/환불/리콜 정책 결정 및 안내", "estimated_days": 1, "is_core": True, "checklist": ["공지문 작성", "CS 스크립트 배포"]},
                {"title": "개선 대책 적용", "description": "설계 변경 또는 부품 교체", "estimated_days": 5, "is_core": True, "checklist": ["재발방지 대책", "검사 기준 강화"]}
            ]}
        ]
    },

    # --- B. Construction Materials ---
    "const_import": {
        "name": "7. 해외 건축자재 수입/총판 론칭",
        "category": CAT_CONST,
        "description": "해외 브랜드 자재 국내 도입 및 유통망 구축",
        "phases": [
            {"phase_name": "소싱/계약 (Sourcing)", "tasks": [
                {"title": "공급 계약 체결", "description": "독점권, MOQ, 가격, 리드타임 확정", "estimated_days": 7, "is_core": True, "checklist": ["Distributorship Agreement", "단가표 확정"]},
                {"title": "샘플 및 데모 자재 확보", "description": "영업용 샘플북 및 목업 수입", "estimated_days": 5, "is_core": True, "checklist": ["샘플 통관", "카탈로그 국문화"]}
            ]},
            {"phase_name": "물류/가격 (Logistics & Pricing)", "tasks": [
                {"title": "수입 통관 프로세스", "description": "HS코드 분류 및 관세 납부", "estimated_days": 3, "is_core": True, "checklist": ["원산지 증명서", "운송사 배차"]},
                {"title": "가격 정책 및 마진 구조 수립", "description": "소비자가/대리점가/특판가 설정", "estimated_days": 2, "is_core": True, "checklist": ["마진뮬 시뮬레이션", "할인율 정책"]}
            ]},
            {"phase_name": "영업 준비 (Sales Prep)", "tasks": [
                {"title": "국내 A/S 체계 구축", "description": "부품 확보 및 수리 매뉴얼", "estimated_days": 5, "is_core": True, "checklist": ["워런티 정책", "A/S 접수 채널"]},
                {"title": "대리점 모집/교육", "description": "지역 거점 유통망 확보", "estimated_days": 10, "is_core": False, "checklist": ["대리점 계약서", "제품 교육"]}
            ]}
        ]
    },
    "const_specin": {
        "name": "8. 건축자재 스펙인 (설계/시공 영업)",
        "category": CAT_CONST,
        "description": "설계 단계에서 자재를 반영시키는 영업 프로세스",
        "phases": [
            {"phase_name": "영업 (Sales)", "tasks": [
                {"title": "타겟 프로젝트 리스트업", "description": "고급 주거, 호텔 등 타겟 현장 발굴", "estimated_days": 3, "is_core": True, "checklist": ["건축사사무소 컨택", "시공사 협력업체 등록"]},
                {"title": "설계 지원 (Spec-in)", "description": "도면 블록(CAD/BIM) 및 디테일 도면 제공", "estimated_days": 5, "is_core": True, "checklist": ["시방서 제공", "상세도 지원"]}
            ]},
            {"phase_name": "제안 (Proposal)", "tasks": [
                {"title": "기술 자료 패키징", "description": "시험성적서, 친환경 인증, 구조 검토서 제출", "estimated_days": 2, "is_core": True, "checklist": ["자재승인서류", "성적서 유효기간 확인"]},
                {"title": "견적 및 VE 대응", "description": "예산 맞춤형 견적 제안", "estimated_days": 3, "is_core": True, "checklist": ["VE(Value Engineering) 제안서", "물량 산출"]}
            ]},
            {"phase_name": "시공 (Construction)", "tasks": [
                {"title": "현장 기술 미팅", "description": "시공 상세 협의 및 문제점 사전 체크", "estimated_days": 1, "is_core": True, "checklist": ["샘플 시공", "마감 상세 협의"]}
            ]}
        ]
    },
    "const_manual": {
        "name": "9. 현장 시공 표준화 (매뉴얼+교육)",
        "category": CAT_CONST,
        "description": "시공 품질 확보를 위한 표준 가이드 및 교육",
        "phases": [
            {"phase_name": "표준화 (Standardization)", "tasks": [
                {"title": "시공 프로세스 맵핑", "description": "자재 반입부터 마감까지 단계 정의", "estimated_days": 3, "is_core": True, "checklist": ["단계별 체크포인트", "소요 시간 산출"]},
                {"title": "위험 포인트(Risk) 정의", "description": "누수, 결로, 전기 합선 등 주요 하자 유형 분석", "estimated_days": 2, "is_core": True, "checklist": ["하자 사례집", "예방 대책"]}
            ]},
            {"phase_name": "교육자료 (Materials)", "tasks": [
                {"title": "시공 매뉴얼/체크리스트 제작", "description": "현장 휴대용 가이드북 및 점검표", "estimated_days": 5, "is_core": True, "checklist": ["사진 기준서", "합격/불합격 기준"]},
                {"title": "교육 커리큘럼 개발", "description": "시공팀 교육용 교재 및 실습 계획", "estimated_days": 3, "is_core": True, "checklist": ["동영상 강의", "실습 키트"]}
            ]},
            {"phase_name": "적용 (Implementation)", "tasks": [
                {"title": "파일럿 현장 적용", "description": "시범 현장 적용 및 피드백", "estimated_days": 5, "is_core": True, "checklist": ["현장 검수", "매뉴얼 개정"]}
            ]}
        ]
    },
    "const_ce": {
        "name": "10. CE/CPR 문서 패키징",
        "category": CAT_CONST,
        "description": "유럽 규격(Construction Products Regulation) 대응 문서화",
        "phases": [
            {"phase_name": "규격 확인 (Standards)", "tasks": [
                {"title": "적용 표준(hEN) 확인", "description": "해당 자재의 조화 표준 확인", "estimated_days": 1, "is_core": True, "checklist": ["EN 규격 번호 확인", "필수 특성 파악"]},
                {"title": "DoP (성능선언서) 확보", "description": "제조사의 Declaration of Performance 수취", "estimated_days": 2, "is_core": True, "checklist": ["DoP 번호 매칭", "서명 확인"]}
            ]},
            {"phase_name": "문서화 (Documentation)", "tasks": [
                {"title": "영문 스펙시트/성능표 작성", "description": "DoP 기반 기술 데이터 정리", "estimated_days": 2, "is_core": True, "checklist": ["내화 성능", "단열 성능", "내구성 등급"]},
                {"title": "CE 마킹 부착 관리", "description": "제품/포장에 CE 라벨 규정 준수 확인", "estimated_days": 1, "is_core": True, "checklist": ["로고 비율", "식별 번호"]}
            ]}
        ]
    },
    "const_showroom": {
        "name": "11. 샘플룸/쇼룸 구축",
        "category": CAT_CONST,
        "description": "고객 체험을 위한 오프라인 전시 공간 조성",
        "phases": [
            {"phase_name": "기획 (Planning)", "tasks": [
                {"title": "전시 컨셉 및 동선 기획", "description": "타겟 고객 경험 시나리오 설계", "estimated_days": 5, "is_core": True, "checklist": ["평면도 레이아웃", "조명 계획"]},
                {"title": "전시 SKU 선정", "description": "주력 제품 및 신제품 라인업 확정", "estimated_days": 2, "is_core": True, "checklist": ["샘플 발주", "컬러칩 준비"]}
            ]},
            {"phase_name": "시공 (Construction)", "tasks": [
                {"title": "인테리어 시공", "description": "벽체, 바닥, 조명, 집기 설치", "estimated_days": 14, "is_core": True, "checklist": ["전기 배선", "마감 검수"]},
                {"title": "제품 디스플레이", "description": "샘플 배치 및 설명물(VMD) 부착", "estimated_days": 3, "is_core": True, "checklist": ["가격표 부착", "QR 설명서"]}
            ]},
            {"phase_name": "운영 (Operation)", "tasks": [
                {"title": "운영 매뉴얼 수립", "description": "방문 예약, 상담 스크립트, 리드 관리 프로세스", "estimated_days": 3, "is_core": True, "checklist": ["예약 시스템", "고객 방명록"]}
            ]}
        ]
    },
    "const_project": {
        "name": "12. 견적/수주/납기 (프로젝트 영업)",
        "category": CAT_CONST,
        "description": "건설 프로젝트 단위 계약 및 납품 관리",
        "phases": [
            {"phase_name": "견적 (Estimation)", "tasks": [
                {"title": "도면 접수 및 물량 산출", "description": "현장 도면 기반 필요 자재 수량 계산", "estimated_days": 2, "is_core": True, "checklist": ["로스율 적용", "부자재 포함"]},
                {"title": "견적서 제출", "description": "단가, 납기, 결제 조건 제안", "estimated_days": 1, "is_core": True, "checklist": ["유효기간 명시", "특기사항 기재"]}
            ]},
            {"phase_name": "계약/발주 (Contract)", "tasks": [
                {"title": "최종 옵션 확정 및 계약", "description": "컬러, 규격, 수량 확정", "estimated_days": 2, "is_core": True, "checklist": ["계약이행보증", "선수금 수령"]},
                {"title": "자재 발주", "description": "공장 생산 의뢰 또는 재고 할당", "estimated_days": 1, "is_core": True, "checklist": ["납기 일정 픽스"]}
            ]},
            {"phase_name": "납품 (Delivery)", "tasks": [
                {"title": "현장 반입 일정 조율", "description": "현장 공정에 맞춘 분할 납품 협의", "estimated_days": 1, "is_core": True, "checklist": ["양중 장비 확인", "하차 공간 확보"]},
                {"title": "검수 및 인수증", "description": "현장 반입 확인 및 서명 날인", "estimated_days": 1, "is_core": True, "checklist": ["거래명세서", "인수증 회수"]}
            ]}
        ]
    },
    "const_as": {
        "name": "13. A/S 및 부품 운영 체계",
        "category": CAT_CONST,
        "description": "지속적인 유지보수 및 고객 만족 관리 시스템",
        "phases": [
            {"phase_name": "체계 수립 (Setup)", "tasks": [
                {"title": "주요 고장 모드 및 부품 정의", "description": "빈발 하자와 필요 예비 부품 식별", "estimated_days": 3, "is_core": True, "checklist": ["부품 SKU 코드화", "안전재고 설정"]},
                {"title": "A/S 비용 및 보증 정책", "description": "유/무상 기준 및 출장비 책정", "estimated_days": 2, "is_core": True, "checklist": ["보증서 약관", "수가표"]}
            ]},
            {"phase_name": "운영 (Operation)", "tasks": [
                {"title": "접수 및 원격 진단 프로세스", "description": "전화/채팅 1차 응대 및 자가조치 안내", "estimated_days": 2, "is_core": True, "checklist": ["상담 매뉴얼", "고장 증상 사진 요청"]},
                {"title": "현장 방문 SOP", "description": "기사 방문 절차 및 복장/태도 규정", "estimated_days": 2, "is_core": True, "checklist": ["수리 키트 점검", "고객 확인서"]}
            ]}
        ]
    },

    # --- C. Common ---
    "comm_ve": {
        "name": "14. 원가절감/리디자인 (VE)",
        "category": CAT_COMMON,
        "description": "수익성 개선을 위한 가치 공학 (Value Engineering) 프로젝트",
        "phases": [
            {"phase_name": "분석 (Analysis)", "tasks": [
                {"title": "원가 구조 분해", "description": "재료비, 가공비, 물류비 등 원가 요소 파악", "estimated_days": 2, "is_core": True, "checklist": ["원가 테이블", "Pareto 분석"]},
                {"title": "고비용 요인 식별", "description": "상위 5개 원가 상승 요인 도출", "estimated_days": 1, "is_core": True, "checklist": ["타겟 부품 선정"]}
            ]},
            {"phase_name": "제안/검증 (Proposal)", "tasks": [
                {"title": "대체 소재/공법 발굴", "description": "동등 이상 성능의 저렴한 대안 모색", "estimated_days": 5, "is_core": True, "checklist": ["공급사 제안 요청", "샘플 테스트"]},
                {"title": "품질 영향 평가", "description": "변경 시 내구성/디자인 영향 검토", "estimated_days": 3, "is_core": True, "checklist": ["신뢰성 테스트", "승인원 갱신"]}
            ]},
            {"phase_name": "적용 (Implementation)", "tasks": [
                {"title": "재견적 및 단가 합의", "description": "변경된 사양으로 최종 단가 확정", "estimated_days": 2, "is_core": True, "checklist": ["단가 변경 합의서"]},
                {"title": "양산 적용", "description": "VE 적용 제품 생산 투입", "estimated_days": 1, "is_core": True, "checklist": ["BOM 수정"]}
            ]}
        ]
    },
    "comm_renewal": {
        "name": "15. 브랜드/제품군 라인업 리뉴얼",
        "category": CAT_COMMON,
        "description": "포트폴리오 최적화 및 브랜드 재정비",
        "phases": [
            {"phase_name": "진단 (Diagnosis)", "tasks": [
                {"title": "라인업 맵 (Positioning Map)", "description": "가격대별/기능별 제품 분포 분석", "estimated_days": 2, "is_core": True, "checklist": ["시장 포지셔닝 맵", "판매량/이익 분석"]},
                {"title": "단종/유지/강화 결정", "description": "SKU 효율화 의사결정", "estimated_days": 2, "is_core": True, "checklist": ["단종 예고", "재고 소진 계획"]}
            ]},
            {"phase_name": "기획 (Planning)", "tasks": [
                {"title": "네이밍 및 패키지 가이드", "description": "브랜드 통일성을 위한 디자인 언어 재정립", "estimated_days": 5, "is_core": True, "checklist": ["BI 가이드라인", "시리즈 네이밍"]},
                {"title": "분기별 론칭 캘린더", "description": "신제품 출시 로드맵 수립", "estimated_days": 2, "is_core": True, "checklist": ["시즌성 고려", "마케팅 일정 연동"]}
            ]}
        ]
    }
}
