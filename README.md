# vehicle-recall-early-warning
Early-warning model that predicts vehicle recalls from NHTSA consumer complaints, LLM-scored symptoms, and manufacturer technical service bulletins.

> **Status:** 초기 단계. 데이터 전처리 · EDA 진행 중이며, `docs/`의 기준 문서는 초안이다 (LLM 점수화 실행 전에 동결한다).

## 개요

소비자 결함신고의 **양**(얼마나 늘었나)과 **내용**(어떤 증상인가), 제조사 **기술공지**를 함께 분석해 "이 차종 · 부품이 몇 달 안에 리콜될까?"를 예측한다. 리콜 가능성이 높은 차종 · 부품의 순위와 근거 신고 요약을 제공해, 결함 차량이 리콜 전까지 도로에 노출되는 기간을 줄이는 것이 목표다.

- 범위: 현대 · 기아, 2015–2025
- 분석 단위: 차종 × 연식 × 부품 × 월
- 예측 대상: N개월(기본 6, 3 · 12 비교) 안에 해당 단위가 리콜되는가 (0 / 1)
- 국내 적용성: 미국 신고 기반 예측을 한국 리콜로 재확인

## 접근: 입력을 하나씩 추가하는 어블레이션

같은 데이터 · 같은 시간 분할에서 입력만 추가해 각 정보의 효과를 분리한다.

| 실험 | 모델 | 입력 |
|---|---|---|
| A (대조군) | 로지스틱 회귀 | 월별 신고 건수 |
| B (대조군) | XGBoost | 정형 정보 (Li et al., 2025 방식) |
| C | XGBoost | B + LLM 신고 글 점수 |
| D | XGBoost | C + 제조사 기술공지 |

단순 기준선(신고 건수 상위 k개)을 못 이기면 모델을 쓸 이유가 없으므로 반드시 함께 비교한다.

## 평가

- 시간 순서 분할: 학습 2015–2020 / 검증 2021 / 평가 2022–2025 (무작위 섞기 없음, `configs/split.yaml`)
- 매월 시점 재현: 그달까지의 신고만 보고 순위를 매기고, 이후 6개월의 리콜로 채점
- 지표: Precision@k, Recall@k, 선행기간, PR-AUC (Accuracy는 리콜 비율이 낮아 사용하지 않음)
- 위험 리콜(화재 · 동력 상실 등)은 선행기간을 별도 보고
- 누수 방지: 리콜 발표 이후 신고 제외, 반복 리콜은 첫 리콜만 사용
- LLM 점수 신뢰도: 신고 약 200건을 사람이 판단해 일치도 확인

## 데이터

데이터 파일은 레포에 포함되지 않는다. 출처 · 규칙은 [`data/README.md`](data/README.md)를 본다.

| 이름 | 출처 | 용도 |
|---|---|---|
| 미국 결함신고 | NHTSA | 예측 입력 (신고 추이 · 증상 글) |
| 미국 리콜 | NHTSA | 정답 |
| 제조사 기술공지 | NHTSA | 추가 신호 |
| 국내 리콜 | 한국교통안전공단 (공공데이터포털) | 국내 적용성 검증 |

## 레포 구조

```
data/          # raw · interim · processed는 gitignore, README.md와 manifest.json만 추적
notebooks/     # 번호_이름.ipynb (예: 01_eda_complaints.ipynb), 출력은 nbstripout으로 제거
src/           # 전처리 · 라벨링 · 피처 · 평가 코드
scripts/       # download_data.py 등 실행 스크립트
configs/       # data_sources.yaml, split.yaml (실험 설정은 코드가 아니라 여기서 바꾼다)
docs/          # filter-criteria.md, llm-codebook.md, matching-rules.md
reports/       # 그림, 발표자료
DECISIONS.md   # 설계 결정과 문제 해결 기록
```

## 시작하기

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
nbstripout --install              # 노트북 출력 자동 제거 (클론 후 최초 1회)
copy .env.example .env            # macOS / Linux: cp .env.example .env  → LLM 키 입력 (커밋 금지)
python scripts/download_data.py --dry-run
```

## 문서

| 문서 | 내용 |
|---|---|
| [`docs/filter-criteria.md`](docs/filter-criteria.md) | 텍스트 사용 · 제외 기준과 단계별 잔존 건수표 |
| [`docs/llm-codebook.md`](docs/llm-codebook.md) | LLM 점수 항목 · 척도 · 앵커 · 검증 프로토콜 |
| [`docs/matching-rules.md`](docs/matching-rules.md) | 신고 ↔ 리콜 · 기술공지 매칭과 라벨 생성 규칙 |
| [`DECISIONS.md`](DECISIONS.md) | 설계 결정 기록 |

## 진행 상태

- [x] 주제 확정
- [x] 레포 템플릿
- [ ] 데이터 다운로드 · 기술공지 / 국내 리콜 URL 확정
- [ ] EDA (라벨 양성 개수, 신고 희소성, 텍스트 점검)
- [ ] 필터 기준 v1 동결
- [ ] LLM 코드북 v1 동결
- [ ] 라벨 생성 · 실험 A / B
- [ ] LLM 점수화 · 실험 C / D
- [ ] 평가 · 한국 리콜 검증

## 라이선스

MIT (`LICENSE`)
