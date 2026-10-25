# memdev: DRAM 셀 소자 설계 프로젝트

현업의 소자 설계 순서(스펙 → 소자 시뮬레이션 → 모델 추출 → 회로 확인 → 민감도 → 산포·최악 조건 → 최적화)를 따라 **DRAM 셀을 설계**하고, 마지막에 이 질문에 숫자로 답합니다.

> 셀마다 리텐션이 다른데, 약한 셀이 있는 행만 자주 리프레시하고 나머지는 덜 자주 하면 리프레시를 얼마나 줄일 수 있고, 그 대가는 무엇인가?

**정직성 고지**: 방법론은 현업과 같게 따르지만, 상용 TCAD와 실제 공정 데이터가 없으므로 모든 수치는 가정값과 시뮬레이션 결과이며 실제 제품에 쓸 수 없습니다. 각 파라미터의 출처와 확인 상태는 `memdev/params/`에 기록합니다.

## 노트북 (Colab에서 바로 실행)

| 노트북 | 내용 | 열기 |
|---|---|---|
| 00 설치 확인 | ngspice, DEVSIM, 한글 폰트 확인 | [Open in Colab](https://colab.research.google.com/github/tjrgns1753-create/dsadsa/blob/claude/feature-research/notebooks/00_setup_check.ipynb) |
| 01 스펙과 셀 물리 | D1 스펙, 전하 분배, 리텐션, 온도, 슬라이더 6개 | [Open in Colab](https://colab.research.google.com/github/tjrgns1753-create/dsadsa/blob/claude/feature-research/notebooks/01_dram_spec_physics.ipynb) |
| 02 접합 누설 (DEVSIM) | 저장 노드 n+/p 접합의 역방향 누설: 전압·온도·도핑·수명, 활성화 에너지, 01 가정과 비교 | [Open in Colab](https://colab.research.google.com/github/tjrgns1753-create/dsadsa/blob/claude/feature-research/notebooks/02_devsim_leakage.ipynb) |

Colab에서 **런타임 → 모두 실행**을 누르면 첫 셀이 저장소를 내려받고 도구를 설치합니다.

모든 노트북은 **현재 설계안** 하나를 함께 씁니다. 01 노트북의 슬라이더에서 설계를 바꾸고 [현재 설계안으로 저장]을 누르면 다음 단계 노트북에 반영됩니다. 각 단계 결과에는 어떤 설계안으로 계산했는지가 기록되고, 설계안이 바뀌면 다시 실행할 노트북을 알려 줍니다.

## 진행 상황

| 단계 | 내용 | 상태 |
|---|---|---|
| M0 | 저장소 뼈대, 설치 확인 노트북 | 완료 |
| M1 | D1 스펙, 셀 기본 물리, 슬라이더 노트북 | 완료 |
| M2 | D2 DEVSIM 접합 누설 | 완료 |
| M3 | D3 모델 추출 | 예정 |
| M4 | D4 ngspice 셀 회로 | 예정 |
| M5 | D5 민감도, D6 산포·코너 | 예정 |
| M6 | D7 설계 결정과 결론 질문 | 예정 |

개념 노트: [`docs/concepts/`](docs/concepts/) · 면접 Q&A: [`docs/interview/dram.md`](docs/interview/dram.md) · 검증 기록: [`docs/validation/`](docs/validation/)

설계 문서: [`docs/superpowers/specs/2026-10-25-memdev-design.md`](docs/superpowers/specs/2026-10-25-memdev-design.md)

## 로컬 실행

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev,sim]"
sudo apt-get install -y ngspice libopenblas0 liblapack3 fonts-nanum
.venv/bin/pytest
PATH=.venv/bin:$PATH bash scripts/build_notebooks.sh
```

참고: `docs/feature-research*.md`, `docs/feature-ranking.md`는 이 프로젝트 이전의 앱 아이디어 조사 문서로, 이 프로젝트와는 별개입니다.
