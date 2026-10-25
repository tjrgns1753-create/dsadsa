# 검증 기록

각 항목이 무엇과 비교했는지, 맞았는지, 그리고 그 비교가 무엇을 보장하고 무엇은 보장하지 않는지 기록합니다.

| 단계 | 항목 | 기준 | 결과 | 일치 | 의미와 한계 | 테스트 |
|---|---|---|---|---|---|---|
| M0 | ngspice RC 감쇠 (10 fF, 100 TΩ, 1.1→0.85 V) | 해석해 ln(1.1/0.85)×τ = 0.2578 s | 0.2578 s | 일치 (1% 이내) | 회로 시뮬레이터 실행·측정 파이프라인 확인. 소자 모델 검증은 아님 | `tests/crosscheck/test_ngspice_rc.py` |
| M1 | 전하 분배의 전하량 보존 | C_s V_cell + C_bl V_dd/2 = (C_s + C_bl)(V_dd/2 + ΔV) | 성립 | 일치 | 수식 구현 확인 | `tests/invariants/test_cell.py` |
| M1 | 기준 설계 리텐션 (85°C) | 손계산 C_s(V_dd − V_fail)/I = 10 fF × 0.25 V / 2.5 fA = 1.0 s | 1.0 s | 일치 | 구현 확인. 1초라는 값 자체는 가정값에서 나온 것 | `tests/invariants/test_cell.py` |
| M1 | 아레니우스 10°C 비율 (80→90°C, E_a 0.6 eV) | 시험작 계산 1.72 | 1.72 | 일치 | 모델 내부 일관성일 뿐 **실측 검증 아님**. E_a 값의 근거 확인 필요 | `tests/invariants/test_leakage.py` |
| M2 | DEVSIM 0 V 전류 (85°C) | 평형에서 0 | 1.6e-21 A/cm² (1.5 V 전류의 2e-15배) | 일치 | 정밀도 안전 전류 계산 확인. 원래 단자 전류로는 p 단자에 약 2e-11 A/cm² 잔류(리뷰 측정, 자동 테스트 없음) | `tests/devsim/test_junction.py` |
| M2 | 격자 수렴 (접합 격자 1e-7 vs 1e-9 cm) | 차이 1% 이내 | 0.05% | 일치 | 격자에 따른 수치 오차가 작음 | `tests/devsim/test_junction.py` |
| M2 | 생성 성분 vs 공식 상한 q·n_i·W/(2τ) (85°C, 1.5 V) | 상한 이하, 0.3배 초과 | 0.50배 | 일치 | 공핍층 가장자리에서 생성이 줄어드는 효과. 상한식 자체의 정확도 검증은 아님 | `tests/devsim/test_junction.py` |
| M2 | 생성 성분의 τ 의존 (1 µs → 0.1 µs) | 10배 | 10.0배 | 일치 | SRH 모델 구현 확인 | `tests/devsim/test_junction.py` |
| M2 | 전체 누설 활성화 에너지 (65–95°C, 1.1 V) | 생성·확산 값 사이 | 0.71 eV | 일치 | 생성과 확산의 혼합. 확산 크기는 구조 길이에 의존 | `tests/devsim/test_d2.py` |
| M2 | 성분별 활성화 에너지 (0–95°C, 1.1 V) | n_i 겉보기 Ea 0.65 eV, 확산 2·Ea+kT 1.33 eV | 생성 0.65, 확산 1.31 eV | 일치 | 교과서 근사 Eg/2, Eg보다 큰 이유(밴드갭 온도 의존, T^1.5)를 확인 | `tests/test_silicon.py`, 노트북 02 3절 |
| M2 | 공핍층 reach-through 검사 (NA 1e16, p 0.5 µm, 1.5 V) | 거부 | ValueError | 일치 | 짧은 구조에서 NA 1e16 누설이 기준의 27배(실제 약 4배)로 나오던 문제 차단. 기본 p 영역 2 µm | `tests/devsim/test_junction.py` |
| M2 | n_i(300 K) | 약 1.0e10 cm⁻³ (교과서) | 1.07e10 | 일치 (10% 이내) | 물성 상수는 기억에 의존, 원문 미확인 | `tests/test_silicon.py` |
| M2 | 셀당 누설 vs 01 가정값 (85°C, 1.1 V) | 2.5 fA (가정) | 0.004 fA | **불일치 (약 640배)** | 1D SRH 생성·확산만으로는 부족. GIDL·모서리 전계·TAT 미포함, τ 가정. τ ≈ 1.4 ns면 일치. D3에서 다룸 | `notebooks/02_devsim_leakage.ipynb` 5절 |
