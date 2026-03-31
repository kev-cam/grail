"""Grail design engine — sizes a 2:1 resonant SC converter.

Topology:
    V_in ──[SW1]── +C_fly- ──[SW_a]──┐
                                       ├── L ── V_out ──[C_out]── GND
    GND  ──[SW2]── C_fly- ──[SW_b]──┘

    Ph1: SW1 + SW_b on  (series charge)
    Ph2: SW_a + SW2 on  (parallel discharge)

Design targets ZCS: switching frequency = LC resonant frequency
so inductor current naturally reaches zero each half-cycle.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from kestrel.process import _PROCESS_PARAMS, get_process_params, format_eng


@dataclass
class GrailSpec:
    """User-facing specification for grail SC converter."""
    v_in: float              # V — external supply (2x V_core for 2:1)
    v_core: float            # V — target on-chip VDD
    i_avg: float             # A — average load current
    f_fire_min: float        # Hz — minimum pipeline firing rate
    process: str = "sky130"


@dataclass
class GrailDesign:
    """Computed grail design parameters."""
    spec: GrailSpec

    # Conversion
    ratio: float = 0.0       # V_in / V_core

    # Gate drive boost (auxiliary LC resonant doubler)
    v_gate: float = 0.0      # V — boosted gate drive rail
    l_boot: float = 0.0      # H — bootstrap inductor
    c_boot: float = 0.0      # F — bootstrap capacitor (holds V_gate)

    # Resonant tank
    f_sw: float = 0.0        # Hz — switching frequency (= f_resonant)
    c_fly: float = 0.0       # F — flying capacitor
    l_bond: float = 0.0      # H — bond wire inductance
    f_res: float = 0.0       # Hz — actual LC resonant frequency
    t_half: float = 0.0      # s — half-cycle (one phase duration)
    z0: float = 0.0          # ohm — characteristic impedance sqrt(L/C)

    # Output
    c_out: float = 0.0       # F — output decoupling capacitor
    r_load: float = 0.0      # ohm — equivalent load resistance
    v_ripple: float = 0.0    # V — estimated output ripple

    # Switch sizing
    sw_w: float = 0.0        # m — NMOS switch width (all 4 identical)
    sw_l: float = 0.0        # m — NMOS switch length
    r_on: float = 0.0        # ohm — switch on-resistance
    i_peak: float = 0.0      # A — peak resonant current

    # Efficiency
    eta_cond: float = 0.0    # conduction efficiency (R_on losses)
    eta_est: float = 0.0     # overall estimated efficiency

    # Status
    warnings: list = field(default_factory=list)


def design_grail(spec: GrailSpec) -> GrailDesign:
    """Compute all grail parameters from a specification."""
    d = GrailDesign(spec=spec)
    proc = get_process_params(spec.process)

    d.ratio = spec.v_in / spec.v_core
    if abs(d.ratio - 2.0) > 0.1:
        d.warnings.append(
            f"V_in/V_core = {d.ratio:.2f}, not 2:1 — "
            f"topology only supports 2:1 conversion"
        )

    # --- Load ---
    d.r_load = spec.v_core / spec.i_avg

    # --- Switching frequency ---
    # Target: match the pipeline firing rate for natural synchronization
    d.f_sw = spec.f_fire_min

    # --- Flying capacitor ---
    # Each cycle transfers Q = C_fly * V_core charge to the output.
    # I_avg = Q * f_sw = C_fly * V_core * f_sw
    # → C_fly = I_avg / (V_core * f_sw)
    d.c_fly = spec.i_avg / (spec.v_core * d.f_sw)

    # --- Bond wire inductance ---
    # For ZCS: f_res = f_sw = 1 / (2*pi*sqrt(L*C_fly))
    # → L = 1 / ((2*pi*f_sw)^2 * C_fly)
    omega_sw = 2 * math.pi * d.f_sw
    d.l_bond = 1.0 / (omega_sw * omega_sw * d.c_fly)

    # Verify L is in bond-wire range (0.5–10 nH)
    if d.l_bond < 0.5e-9:
        d.warnings.append(
            f"L = {format_eng(d.l_bond, 'H')} too small for bond wire "
            f"— consider lower f_sw"
        )
    if d.l_bond > 10e-9:
        d.warnings.append(
            f"L = {format_eng(d.l_bond, 'H')} — may need package inductor "
            f"in addition to bond wire"
        )

    # --- Resonant parameters ---
    d.f_res = 1.0 / (2 * math.pi * math.sqrt(d.l_bond * d.c_fly))
    d.t_half = 1.0 / (2 * d.f_sw)  # each phase is one half-cycle
    d.z0 = math.sqrt(d.l_bond / d.c_fly)

    # Peak resonant current: I_peak = V_core / Z0
    # (voltage step across LC tank is V_core for both phases)
    d.i_peak = spec.v_core / d.z0

    # --- Output cap ---
    # Size for < 5% ripple: delta_V = I_avg * t_half / C_out
    # C_out = I_avg * t_half / (0.05 * V_core)
    target_ripple = 0.05 * spec.v_core
    d.c_out = spec.i_avg * d.t_half / target_ripple
    # Ensure C_out >> C_fly (at least 10x)
    if d.c_out < 10 * d.c_fly:
        d.c_out = 10 * d.c_fly

    d.v_ripple = spec.i_avg * d.t_half / d.c_out

    # --- Gate drive boost (auxiliary LC resonant doubler) ---
    # A small L_boot + C_boot tank, driven by the existing Ph1/Ph2
    # switches, resonates at f_sw.  The LC rings the voltage on
    # C_boot up to ~2*V_in (ideal lossless half-cycle resonant swing).
    # No extra switches — just taps the existing phase clocks.
    #
    # Size L_boot and C_boot to resonate at f_sw.  C_boot must be
    # large enough to hold the gate charge of all 4 switches without
    # significant droop.  L_boot follows from the resonance constraint.
    d.v_gate = 2 * spec.v_in

    # C_boot: must supply gate charge for 4 switches per cycle
    # with < 10% droop.  Q_gate = C_gate_total * V_gate.
    # C_boot > 10 * C_gate_total.  We'll finalize after switch sizing.
    # For now, seed with 10x C_fly (small relative to main path).
    c_boot_min = d.c_fly  # initial seed, tightened after switch sizing

    # L_boot from resonance: f_sw = 1/(2*pi*sqrt(L_boot*C_boot))
    d.c_boot = c_boot_min
    d.l_boot = 1.0 / (omega_sw * omega_sw * d.c_boot)

    # --- Switch sizing ---
    # Trade-off: wider switches → lower R_on but higher gate cap.
    # P_cond = 2 * R_on * I_rms^2 ∝ 1/W
    # P_gate = 4 * C_gate * V_gate^2 * f_sw ∝ W
    # Optimal W minimizes P_cond + P_gate.
    # d(P_total)/dW = 0 → W_opt = sqrt(P_cond_coeff / P_gate_coeff)

    kpn = proc["kpn"]
    vtn = proc["vtn"]
    lmin = proc["lmin"]

    # Worst-case Vgs: SW_a source at V_core during Ph2
    vgs = d.v_gate - spec.v_core
    vov = vgs - vtn
    if vov < 0.1:
        vov = 0.1
        d.warnings.append(
            f"V_gate-V_core ({vgs:.2f}V) close to Vtn ({vtn}V) — "
            f"switch R_on will be high, consider higher pump ratio"
        )

    d.sw_l = lmin
    i_rms = d.i_peak / math.sqrt(2)

    # Gate capacitance per unit width: ~1 fF/um (Cox * L)
    c_gate_per_w = 1e-15 / 1e-6  # F/m — ~1 fF per um of width

    # P_cond = 2 * (1 / (kpn * W/L * Vov)) * I_rms^2
    #        = 2 * L / (kpn * Vov * W) * I_rms^2
    # P_gate = 4 * c_gate_per_w * W * V_gate^2 * f_sw
    # d(P_cond + P_gate)/dW = 0:
    # W_opt = sqrt(2 * L * I_rms^2 / (kpn * Vov * 4 * c_gate_per_w * V_gate^2 * f_sw))
    num = 2 * d.sw_l * i_rms * i_rms
    den = kpn * vov * 4 * c_gate_per_w * d.v_gate * d.v_gate * d.f_sw
    w_opt = math.sqrt(num / den)
    d.sw_w = max(lmin * 4, w_opt)

    d.r_on = 1.0 / (kpn * (d.sw_w / d.sw_l) * vov)

    # --- Finalize bootstrap C_boot ---
    # C_boot must hold gate charge of 4 switches with < 10% droop:
    #   Q_gate = 4 * C_gate_per_switch * V_gate
    #   C_boot > Q_gate / (0.1 * V_gate) = 40 * C_gate_per_switch
    c_gate_total = c_gate_per_w * d.sw_w  # per switch
    c_boot_needed = 40 * c_gate_total
    d.c_boot = max(c_boot_needed, d.c_fly)  # at least C_fly
    d.l_boot = 1.0 / (omega_sw * omega_sw * d.c_boot)

    # --- Efficiency ---
    # The bootstrap LC is resonant — energy sloshes back and forth,
    # only the resistive losses in L_boot matter (small).
    # Gate charge is recycled through the resonant tank, not dissipated.
    # Net gate drive loss ≈ Q_gate * V_gate * f_sw / Q_factor_boot
    # With Q ~ 10 for bond wire, effective gate loss is ~10% of naive.
    p_cond = 2 * d.r_on * i_rms * i_rms  # 2 switches in path per phase
    p_gate_naive = 4 * c_gate_total * d.v_gate * d.v_gate * d.f_sw
    q_boot = 10  # typical Q for on-chip LC at this frequency
    p_gate = p_gate_naive / q_boot  # resonant recycling
    p_out = spec.v_core * spec.i_avg
    if p_out > 0:
        d.eta_cond = 1.0 - p_cond / p_out
        d.eta_est = 1.0 - (p_cond + p_gate) / p_out
        d.eta_est = max(0, min(1.0, d.eta_est))

    return d


def summarize(d: GrailDesign) -> str:
    """Return a human-readable design summary."""
    lines = [
        "grail Design Summary",
        "=" * 50,
        f"  V_in:            {d.spec.v_in} V",
        f"  V_core:          {d.spec.v_core} V  (ratio {d.ratio:.1f}:1)",
        f"  I_avg:           {format_eng(d.spec.i_avg, 'A')}",
        f"  R_load:          {format_eng(d.r_load, 'ohm')}",
        "",
        "  Resonant Tank",
        f"    f_sw:          {format_eng(d.f_sw, 'Hz')}",
        f"    C_fly:         {format_eng(d.c_fly, 'F')}",
        f"    L (bond wire): {format_eng(d.l_bond, 'H')}",
        f"    f_res:         {format_eng(d.f_res, 'Hz')}",
        f"    Z0:            {format_eng(d.z0, 'ohm')}",
        f"    I_peak:        {format_eng(d.i_peak, 'A')}",
        f"    t_half:        {format_eng(d.t_half, 's')}",
        "",
        "  Output",
        f"    C_out:         {format_eng(d.c_out, 'F')}",
        f"    V_ripple:      {format_eng(d.v_ripple, 'V')} ({d.v_ripple/d.spec.v_core*100:.1f}%)",
        "",
        "  Gate Drive (resonant LC bootstrap)",
        f"    V_gate:        {d.v_gate}V  (2x V_in via LC resonance)",
        f"    L_boot:        {format_eng(d.l_boot, 'H')}",
        f"    C_boot:        {format_eng(d.c_boot, 'F')}",
        f"    Vgs worst:     {d.v_gate - d.spec.v_core:.2f}V",
        "",
        "  Switches (all 4 identical NMOS)",
        f"    W/L:           {d.sw_w*1e6:.1f}u / {d.sw_l*1e6:.2f}u",
        f"    R_on:          {format_eng(d.r_on, 'ohm')}",
        "",
        "  Efficiency (estimated)",
        f"    Conduction:    {d.eta_cond*100:.1f}%",
        f"    Overall:       {d.eta_est*100:.1f}%",
    ]
    if d.warnings:
        lines.append("")
        lines.append("  Warnings:")
        for w in d.warnings:
            lines.append(f"    - {w}")
    return "\n".join(lines)
