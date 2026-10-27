# 예산 맞춤형 식단·장보기 추천 서비스

공공 식품·영양·가격 데이터를 결합해 예산과 영양 조건에 맞는 식단 및 예상 장보기 비용을 계산하는 Streamlit MVP입니다.

## 기능
- 메뉴젠 레시피와 국가표준식품성분DB·KAMIS·참가격 데이터 결합 및 품질 검증
- 직접 일치하는 A등급 가격만 구매비 계산에 사용 (불확실한 B/C 등급 가격 제외)
- SciPy MILP 기반 예산·영양·메뉴 반복 제약조건 최적화
- 보유재료 반영, 구매 목록 및 예상 비용 확인, CSV 다운로드
- 조건 불충족·입력 오류 등 경계 상황에 대한 예외 처리

## 로컬 실행
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 자동 테스트
```bash
python -m unittest discover -s tests -v
python demo.py
```

로컬 추천 엔진 자동 테스트 11개 통과(2026-10-15). 웹 UI 및 공개 URL은 배포 후 별도 확인이 필요합니다.

## Streamlit Cloud 배포
저장소 최상위에 `app.py`, `core.py`, `demo.py`, `requirements.txt`, `runtime.txt`, `.streamlit/config.toml`, `data/`, `tests/`가 모두 있는지 확인하세요.

1. https://share.streamlit.io/ 접속 후 **Create app** → **Deploy a public app from GitHub**
2. Repository: `rlaqhfla0917-bit/budget-meal-planner`
3. Branch: `main`, Main file path: `app.py`
4. 공개 URL에서 5끼·7끼 추천, 보유재료 없음, 엄격한 조건, CSV 다운로드 등 재검증

## 범위·한계
- 엄격한 가격 검증을 통과한 **36개 메뉴 / 2,916개 조합**을 대상으로 하는 MVP입니다.
- 전체 원자료의 3,220개 메뉴 중 2,929개가 5종 영양소 계산 가능(91.0%)하다는 수치는 별도 원자료 감사 결과입니다.
- 공공가격으로 계산한 **예상 장보기비**이며 실제 마트 결제액과 다를 수 있습니다.
- 일부 식재료 보유 가정이나 중량 단가가 적용될 수 있습니다.
- 의료·영양 처방용 서비스가 아니며 사용자가 선택한 조건을 계산합니다.
- Streamlit Cloud 공개 배포를 2026-10-15에 완료했습니다. 현재 저장소의 추천 범위는 가격 검증을 통과한 36개 메뉴와 2,916개 조합입니다.
