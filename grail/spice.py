"""SPICE netlist emitter for grail 2:1 resonant SC converter.

Generates a Xyce-compatible testbench with:
- Smooth B-source conductance switches (tanh transition, solver-friendly)
- Bootstrap LC for gate drive boost
- Ideal L, C_fly, C_out
- Non-overlapping Ph1/Ph2 clock
- Resistive load
"""

import os
from kestrel.process import format_eng
from .engine import GrailDesign


def _eng(val):
    """SPICE engineering notation."""
    if val == 0:
        return "0"
    prefixes = [
        (1e12, "T"), (1e9, "G"), (1e6, "MEG"), (1e3, "K"),
        (1, ""), (1e-3, "M"), (1e-6, "U"), (1e-9, "N"),
        (1e-12, "P"), (1e-15, "F"),
    ]
    for scale, prefix in prefixes:
        if abs(val) >= scale * 0.999:
            return f"{val/scale:.4g}{prefix}"
    return f"{val:.4g}"


def emit_spice(design: GrailDesign, output_dir: str) -> list:
    """Generate Xyce SPICE netlist for the grail converter."""
    os.makedirs(output_dir, exist_ok=True)
    files = []

    d = design
    s = d.spec

    # Timing
    t_half = d.t_half
    t_period = 2 * t_half
    t_dead = 0.10 * t_half   # 10% dead time
    t_rise = 0.10 * t_half   # 10% rise/fall
    t_stop = 200 * t_period
    t_step = t_period / 50

    # Switch conductances
    g_on = 1.0 / d.r_on
    g_off = 1e-8  # 100 Mohm off — small leakage for solver

    # Smooth switch: G = G_off + (G_on - G_off) * 0.5*(1 + tanh(k*(V_ctrl - V_th)))
    # k sets transition sharpness; V_th = half of clock swing
    v_th = s.v_in * 0.5
    # k = 20/V_in gives a smooth-enough transition over ~10% of swing
    k_smooth = 20.0 / s.v_in

    netlist = f"""\
* grail — 2:1 Resonant SC Converter
* V_in = {s.v_in}V, V_core = {s.v_core}V, I_avg = {_eng(s.i_avg)}A
* f_sw = {_eng(d.f_sw)}Hz, C_fly = {_eng(d.c_fly)}F, L = {_eng(d.l_bond)}H
* Process: {s.process}
*
*   V_in ──[SW1]── +C_fly- ──[SW_a]──┐
*                                      ├── L ── V_out ──[C_out]── GND
*   GND  ──[SW2]── C_fly- ──[SW_b]──┘
*
*   Ph1: SW1 + SW_b on  (series charge)
*   Ph2: SW_a + SW2 on  (parallel discharge)
*
* Switches modeled as smooth B-source conductances (tanh transition)
* to avoid VSWITCH convergence issues at GHz switching rates.

* ── Supply ──
Vvin  v_in  0  {s.v_in}

* ── Phase clocks (non-overlapping) ──
Vph1 ph1 0 PULSE({s.v_in} 0 0 {_eng(t_rise)} {_eng(t_rise)} {_eng(t_half - 2*t_dead)} {_eng(t_period)})
Vph2 ph2 0 PULSE(0 {s.v_in} {_eng(t_half)} {_eng(t_rise)} {_eng(t_rise)} {_eng(t_half - 2*t_dead)} {_eng(t_period)})

* ── Smooth switch macro ──
* B-source current: I = G(V_ctrl) * (V_a - V_b)
* G(V_ctrl) = {_eng(g_off)} + ({_eng(g_on)} - {_eng(g_off)}) * 0.5 * (1 + tanh({k_smooth:.1f} * (V_ctrl - {v_th})))
.PARAM G_on  = {g_on:.6g}
.PARAM G_off = {g_off:.6g}
.PARAM K_sw  = {k_smooth:.4g}
.PARAM V_th  = {v_th:.4g}

* ── SW1: V_in → +C_fly (Ph1) ──
B_SW1  v_in  cfly_p  I = {{(G_off + (G_on - G_off) * 0.5 * (1 + tanh(K_sw * (V(ph1) - V_th)))) * (V(v_in) - V(cfly_p))}}

* ── SW_b: C_fly- → L junction (Ph1) ──
B_SWb  cfly_n  jct  I = {{(G_off + (G_on - G_off) * 0.5 * (1 + tanh(K_sw * (V(ph1) - V_th)))) * (V(cfly_n) - V(jct))}}

* ── SW_a: +C_fly → L junction (Ph2) ──
B_SWa  cfly_p  jct  I = {{(G_off + (G_on - G_off) * 0.5 * (1 + tanh(K_sw * (V(ph2) - V_th)))) * (V(cfly_p) - V(jct))}}

* ── SW2: C_fly- → GND (Ph2) ──
B_SW2  cfly_n  0  I = {{(G_off + (G_on - G_off) * 0.5 * (1 + tanh(K_sw * (V(ph2) - V_th)))) * V(cfly_n)}}

* ── Flying capacitor ──
C_fly  cfly_p  cfly_n  {_eng(d.c_fly)}

* ── Bond wire inductor ──
L_bond  jct  v_out  {_eng(d.l_bond)}

* ── Output decoupling ──
C_out  v_out  0  {_eng(d.c_out)}

* ── Load ──
R_load  v_out  0  {_eng(d.r_load)}

* ── Bootstrap LC gate drive (resonant doubler) ──
* L_boot + C_boot resonate at f_sw.  Driven by Ph1/Ph2 through
* smooth switches.  Rings C_boot up to ~2*V_in = {d.v_gate:.2g}V.
L_boot  boot_sw  boot_cap  {_eng(d.l_boot)}
C_boot  boot_cap  0  {_eng(d.c_boot)}
R_boot  boot_cap  0  100K
B_boot1  v_in  boot_sw  I = {{(1E-3 + (1.0 - 1E-3) * 0.5 * (1 + tanh(K_sw * (V(ph1) - V_th)))) * (V(v_in) - V(boot_sw))}}
B_boot2  boot_sw  0  I = {{(1E-3 + (1.0 - 1E-3) * 0.5 * (1 + tanh(K_sw * (V(ph2) - V_th)))) * V(boot_sw)}}

* ── Initial conditions ──
.IC V(cfly_p)={s.v_core} V(cfly_n)=0 V(v_out)={s.v_core} V(boot_cap)={s.v_in}

* ── Solver options ──
.OPTIONS TIMEINT METHOD=GEAR MAXORD=2 RELTOL=1E-3 ABSTOL=1E-9
+ DELMAX={_eng(t_period/10)}
.OPTIONS NONLIN MAXSTEP=40 ABSTOL=1E-9 RELTOL=1E-3

* ── Analysis ──
.TRAN {_eng(t_step)} {_eng(t_stop)}

* ── Output ──
.PRINT TRAN V(v_out) V(boot_cap) V(cfly_p) V(cfly_n) V(jct) I(L_bond) V(ph1) V(ph2)

.END
"""

    path = os.path.join(output_dir, "grail_tb.cir")
    with open(path, 'w') as f:
        f.write(netlist)
    files.append(path)

    return files
