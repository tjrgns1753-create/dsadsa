"""D2a: DEVSIM으로 DRAM 저장 노드(n+/p 웰) 1D 접합의 역방향 누설을 계산한다.

단위 예외: DEVSIM 관례에 따라 농도 cm^-3, 길이 cm, 전류밀도 A/cm².

사전 조사로 확정한 처리(계획서 M2 참고):
- simple_physics는 n_i를 온도와 무관한 상수로 두므로 n_i, n1, p1을 온도의 함수로 덮어쓴다.
- 단자 전류를 그대로 읽으면 다수 캐리어 항의 상쇄로 정밀도 오차가 신호를 덮는다. 대신
  J = |q·Σ USRH·NodeVolume| + |Jn(p 단자)| + |Jp(n+ 단자)| 로 정밀도가 좋은 성분만 더한다.
- solve는 메모리의 모든 소자를 함께 풀기 때문에 계산마다 reset_devsim()으로 비운다.
- 바이어스는 0.1 V씩 올린다. DEVSIM의 C 수준 출력은 파일 디스크립터 단위로 막는다.
"""
import contextlib
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass

from memdev.colab import DEVSIM_MATH_LIBS
from memdev.silicon import depletion_width_cm, ni_silicon
from memdev.units import Q, celsius_to_kelvin

RAMP_STEP_V = 0.1
REACH_THROUGH_FRACTION = 0.8  # 공핍층이 중성 영역 길이의 이 비율을 넘으면 거부


class JunctionSimError(RuntimeError):
    pass


@dataclass(frozen=True)
class JunctionResult:
    temp_c: float
    na: float
    nd: float
    tau: float
    biases_v: list[float]
    j_total: list[float]  # [A/cm²]
    j_gen: list[float]  # 소자 안 SRH 생성 성분
    j_diff: list[float]  # 단자에서 들어오는 소수 캐리어 성분 (구조 길이에 의존)


@contextlib.contextmanager
def _quiet():
    """DEVSIM의 반복 로그를 막는다. DEVSIM은 파이썬 sys.stdout으로 쓰고(Jupyter에서는 셀 출력),
    라이브러리 로딩 메시지 등은 C 수준 fd 1·2로 쓰므로 둘 다 막는다."""
    sys.stdout.flush()
    sys.stderr.flush()
    saved = [os.dup(1), os.dup(2)]
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            yield
    finally:
        os.dup2(saved[0], 1)
        os.dup2(saved[1], 2)
        for fd in (*saved, devnull):
            os.close(fd)


def simulate_junction(*, temp_c: float, na: float, nd: float, tau: float, biases_v: Sequence[float],
                      length_cm: float = 2.5e-4, xj_cm: float = 0.5e-4, fine_cm: float = 1e-8,
                      max_iterations: int = 60) -> JunctionResult:
    biases = [float(v) for v in biases_v]
    if any(v < 0 for v in biases):
        raise ValueError(f"역방향 바이어스(>= 0)만 지원합니다: {biases}")
    if any(b < a for a, b in zip(biases, biases[1:])):
        raise ValueError(f"바이어스는 오름차순이어야 합니다: {biases}")
    for name, value in (("na", na), ("nd", nd), ("tau", tau)):
        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value}")
    _check_reach_through(temp_c, na, nd, max(biases, default=0.0), length_cm, xj_cm)
    os.environ.setdefault("DEVSIM_MATH_LIBS", DEVSIM_MATH_LIBS)
    condition = f"{temp_c:g}°C, NA={na:.2g}, ND={nd:.2g}, τ={tau:.2g} s"
    try:
        with _quiet():
            return _run(temp_c, na, nd, tau, biases, length_cm, xj_cm, fine_cm, max_iterations)
    except Exception as e:  # DEVSIM은 수렴 실패를 일반 예외로 던진다
        if isinstance(e, (ValueError, JunctionSimError)):
            raise
        raise JunctionSimError(f"DEVSIM이 수렴하지 못했습니다 ({condition}, 바이어스 {biases} V): {e}") from e


def _check_reach_through(temp_c, na, nd, reverse_v, length_cm, xj_cm) -> None:
    """공핍층이 단자에 닿으면(reach-through) 단자가 소수 캐리어를 직접 공급해 누설이 구조 탓으로 부풀려진다."""
    w = depletion_width_cm(temp_c, na, nd, reverse_v)
    x_p, x_n = w * nd / (na + nd), w * na / (na + nd)
    p_len, n_len = length_cm - xj_cm, xj_cm
    if x_p >= REACH_THROUGH_FRACTION * p_len or x_n >= REACH_THROUGH_FRACTION * n_len:
        raise ValueError(
            f"공핍층이 단자에 거의 닿습니다(p쪽 {x_p * 1e4:.2f} µm / 영역 {p_len * 1e4:.2f} µm, "
            f"n쪽 {x_n * 1e4:.3f} µm / 영역 {n_len * 1e4:.2f} µm). 구조를 길게 하거나 도핑을 높이세요.")


def _run(temp_c, na, nd, tau, biases, length_cm, xj_cm, fine_cm, max_iterations) -> JunctionResult:
    import devsim as ds
    from devsim.python_packages.simple_physics import (
        CreateSiliconDriftDiffusion, CreateSiliconDriftDiffusionAtContact, CreateSiliconPotentialOnly,
        CreateSiliconPotentialOnlyContact, CreateSolution, GetContactBiasName, SetSiliconParameters)

    ds.reset_devsim()
    m = d = "junction"
    r = "si"
    ds.create_1d_mesh(mesh=m)
    ds.add_1d_mesh_line(mesh=m, pos=0.0, ps=length_cm / 50, tag="top")
    ds.add_1d_mesh_line(mesh=m, pos=xj_cm, ps=fine_cm, tag="mid")
    ds.add_1d_mesh_line(mesh=m, pos=length_cm, ps=length_cm / 50, tag="bot")
    ds.add_1d_contact(mesh=m, name="top", tag="top", material="metal")
    ds.add_1d_contact(mesh=m, name="bot", tag="bot", material="metal")
    ds.add_1d_region(mesh=m, material="Si", region=r, tag1="top", tag2="bot")
    ds.finalize_mesh(mesh=m)
    ds.create_device(mesh=m, device=d)

    SetSiliconParameters(d, r, celsius_to_kelvin(temp_c))
    ni = ni_silicon(temp_c)
    for name in ("n_i", "n1", "p1"):
        ds.set_parameter(device=d, region=r, name=name, value=ni)
    ds.set_parameter(device=d, region=r, name="taun", value=tau)
    ds.set_parameter(device=d, region=r, name="taup", value=tau)
    # 위쪽(top) = n+ 저장 노드, 아래쪽(bot) = p 웰
    ds.node_model(device=d, region=r, name="Donors", equation=f"{nd}*step({xj_cm}-x)")
    ds.node_model(device=d, region=r, name="Acceptors", equation=f"{na}*step(x-{xj_cm})")
    ds.node_model(device=d, region=r, name="NetDoping", equation="Donors-Acceptors")

    CreateSolution(d, r, "Potential")
    CreateSiliconPotentialOnly(d, r)
    for contact in ("top", "bot"):
        ds.set_parameter(device=d, name=GetContactBiasName(contact), value=0.0)
        CreateSiliconPotentialOnlyContact(d, r, contact)
    ds.solve(type="dc", absolute_error=1.0, relative_error=1e-12, maximum_iterations=max_iterations)

    CreateSolution(d, r, "Electrons")
    CreateSolution(d, r, "Holes")
    ds.set_node_values(device=d, region=r, name="Electrons", init_from="IntrinsicElectrons")
    ds.set_node_values(device=d, region=r, name="Holes", init_from="IntrinsicHoles")
    CreateSiliconDriftDiffusion(d, r)
    for contact in ("top", "bot"):
        CreateSiliconDriftDiffusionAtContact(d, r, contact)

    def solve():
        ds.solve(type="dc", absolute_error=1e10, relative_error=1e-12, maximum_iterations=max_iterations)

    solve()
    j_gen, j_diff = [], []
    v_now = 0.0
    for v in biases:
        while v_now < v - 1e-12:
            v_now = min(v, v_now + RAMP_STEP_V)
            ds.set_parameter(device=d, name=GetContactBiasName("top"), value=v_now)
            solve()
        usrh = ds.get_node_model_values(device=d, region=r, name="USRH")
        volume = ds.get_node_model_values(device=d, region=r, name="NodeVolume")
        j_gen.append(abs(Q * sum(u * vol for u, vol in zip(usrh, volume))))
        j_diff.append(abs(ds.get_contact_current(device=d, contact="bot", equation="ElectronContinuityEquation"))
                      + abs(ds.get_contact_current(device=d, contact="top", equation="HoleContinuityEquation")))
    ds.reset_devsim()
    return JunctionResult(temp_c=temp_c, na=na, nd=nd, tau=tau, biases_v=biases,
                          j_total=[g + f for g, f in zip(j_gen, j_diff)], j_gen=j_gen, j_diff=j_diff)
