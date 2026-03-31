"""SVG schematic generator for grail switched-cap power pad.

Draws the 2:1 hybrid LC switched-cap topology:

    V_in ──[SW1]── +C_fly ──[SW_a]──┐
                                      ├── L ── V_out ──[C_out]── GND
    GND  ──[SW2]── C_fly- ──[SW_b]──┘

    Ph1: SW1 + SW_b on  (charge: V_in → C_fly → L → V_out, series)
    Ph2: SW_a + SW2 on  (discharge: C_fly → L → V_out, C_fly- → GND, parallel)

C_fly is NMOS in isolated well (gate = + plate, channel = - plate).
L provides ZCS — resonant half-cycle brings current to zero naturally.
"""

import os
from kestrel.schematic import (
    SVG, arrow, block, nmos, pmos, resistor, capacitor, inductor,
    gnd, vdd, dot, wire_label, switch,
)
from kestrel.process import format_eng


def draw_topology(v_in, v_core, process, path):
    """Draw the 2:1 hybrid LC switched-cap block diagram."""
    svg = SVG(860, 620)

    # Title
    svg.text(430, 28, "grail -- 2:1 Resonant SC Converter",
             size=15, weight="bold")
    svg.text(430, 48,
             f"V_in = {v_in}V  ->  V_core = {v_core}V  |  {process}",
             size=11, color="#555")

    # ================================================================
    # Layout coordinates
    # ================================================================
    y_vin = 100        # V_in rail
    y_gnd = 440        # GND rail

    x_sw1 = 140        # SW1 (V_in to +C_fly)
    x_sw2 = 140        # SW2 (GND to C_fly-)
    x_cfly = 300       # C_fly (vertical, A on top, B on bottom)
    x_xbar = 460       # crossbar switches SW_a / SW_b
    x_L = 560          # inductor
    x_vout = 680       # V_out node

    y_a = 180           # C_fly + plate wire
    y_b = 360           # C_fly - plate wire
    y_mid = 270         # junction where SW_a and SW_b meet -> L

    # ================================================================
    # Rails
    # ================================================================
    svg.line(60, y_vin, 220, y_vin, color="#c00", width=2)
    svg.text(50, y_vin + 4, f"V_in ({v_in}V)", size=10, color="#c00",
             anchor="end")

    svg.line(60, y_gnd, 220, y_gnd, color="#00c", width=2)
    svg.text(50, y_gnd + 4, "GND", size=10, color="#00c", anchor="end")

    # ================================================================
    # SW1: V_in → +C_fly
    # ================================================================
    svg.line(x_sw1, y_vin, x_sw1, y_a - 34)
    # switch symbol (vertical, open)
    svg.line(x_sw1, y_a - 34, x_sw1, y_a - 26)
    svg.circle(x_sw1, y_a - 26, 2, fill="#222", stroke="none")
    svg.line(x_sw1, y_a - 26, x_sw1 + 10, y_a - 8)  # open arm
    svg.circle(x_sw1, y_a - 8, 2, fill="#222", stroke="none")
    svg.line(x_sw1, y_a - 8, x_sw1, y_a)
    svg.text(x_sw1 + 16, y_a - 20, "SW1", size=10, anchor="start",
             color="#555", weight="bold")
    svg.text(x_sw1 + 16, y_a - 8, "(Ph1)", size=8, anchor="start",
             color="#888")

    # ================================================================
    # SW2: GND → C_fly-
    # ================================================================
    svg.line(x_sw2, y_gnd, x_sw2, y_b + 34)
    svg.line(x_sw2, y_b + 34, x_sw2, y_b + 26)
    svg.circle(x_sw2, y_b + 26, 2, fill="#222", stroke="none")
    svg.line(x_sw2, y_b + 26, x_sw2 + 10, y_b + 8)  # open arm
    svg.circle(x_sw2, y_b + 8, 2, fill="#222", stroke="none")
    svg.line(x_sw2, y_b + 8, x_sw2, y_b)
    svg.text(x_sw2 + 16, y_b + 22, "SW2", size=10, anchor="start",
             color="#555", weight="bold")
    svg.text(x_sw2 + 16, y_b + 34, "(Ph2)", size=8, anchor="start",
             color="#888")

    # ================================================================
    # C_fly (vertical, + plate top, - plate bottom)
    # ================================================================
    # Horizontal wires to cap
    svg.line(x_sw1, y_a, x_cfly, y_a)
    svg.line(x_sw2, y_b, x_cfly, y_b)

    # Cap symbol (larger than normal — it's a power cap)
    cfly_top = y_a + 50
    cfly_bot = y_b - 50
    svg.line(x_cfly, y_a, x_cfly, cfly_top)
    svg.line(x_cfly - 20, cfly_top, x_cfly + 20, cfly_top, width=2.5)
    svg.line(x_cfly - 20, cfly_bot, x_cfly + 20, cfly_bot, width=2.5)
    svg.line(x_cfly, cfly_bot, x_cfly, y_b)
    svg.text(x_cfly + 26, (cfly_top + cfly_bot) / 2 + 4, "C_fly",
             size=11, anchor="start", color="#222", weight="bold")
    svg.text(x_cfly + 26, (cfly_top + cfly_bot) / 2 + 18, "(MIM/MOS)",
             size=8, anchor="start", color="#888")

    # Plate labels
    svg.text(x_cfly - 8, cfly_top - 4, "+", size=11, anchor="end",
             color="#666", weight="bold")
    svg.text(x_cfly - 8, cfly_bot + 12, "-", size=11, anchor="end",
             color="#666", weight="bold")

    # ================================================================
    # Crossbar: SW_a (+ plate → L), SW_b (- plate → L)
    # ================================================================
    # Extend A and B wires to crossbar
    svg.line(x_cfly, y_a, x_xbar, y_a)
    dot(svg, x_cfly, y_a)
    svg.line(x_cfly, y_b, x_xbar, y_b)
    dot(svg, x_cfly, y_b)

    # SW_a: from + plate wire down to mid junction
    svg.circle(x_xbar, y_a, 2, fill="#222", stroke="none")
    svg.line(x_xbar, y_a, x_xbar + 10, y_mid - 4)  # open arm angled down
    svg.circle(x_xbar, y_mid, 2, fill="#222", stroke="none")
    svg.text(x_xbar + 14, y_a + 12, "SW_a", size=10, anchor="start",
             color="#555", weight="bold")
    svg.text(x_xbar + 14, y_a + 24, "(Ph2)", size=8, anchor="start",
             color="#888")

    # SW_b: from - plate wire up to mid junction
    svg.circle(x_xbar, y_b, 2, fill="#222", stroke="none")
    svg.line(x_xbar, y_b, x_xbar + 10, y_mid + 4)  # open arm angled up
    svg.text(x_xbar + 14, y_b - 8, "SW_b", size=10, anchor="start",
             color="#555", weight="bold")
    svg.text(x_xbar + 14, y_b + 4, "(Ph1)", size=8, anchor="start",
             color="#888")

    # Junction dot at mid
    dot(svg, x_xbar, y_mid)

    # ================================================================
    # L: inductor from crossbar junction to V_out
    # ================================================================
    svg.line(x_xbar, y_mid, x_L, y_mid)
    # inductor symbol (horizontal)
    svg.line(x_L, y_mid, x_L + 5, y_mid)
    for i in range(4):
        cx = x_L + 10 + i * 10
        svg.elements.append(
            f'<path d="M {cx-4},{y_mid} A 5,5 0 0,0 {cx+6},{y_mid}" '
            f'fill="none" stroke="#222" stroke-width="1.5"/>')
    svg.line(x_L + 42, y_mid, x_vout, y_mid)
    svg.text(x_L + 22, y_mid - 12, "L", size=11, color="#222",
             weight="bold")
    svg.text(x_L + 22, y_mid + 18, "(bond wire", size=8, color="#888")
    svg.text(x_L + 22, y_mid + 28, " + pkg)", size=8, color="#888")

    # ================================================================
    # V_out node + C_out (decoupling to GND)
    # ================================================================
    dot(svg, x_vout, y_mid)
    wire_label(svg, x_vout, y_mid - 12, "V_out")

    # Output wire to the right
    svg.line(x_vout, y_mid, x_vout + 70, y_mid)
    wire_label(svg, x_vout + 78, y_mid + 4, f"V_core ({v_core}V)",
               anchor="start")

    # C_out to GND
    svg.line(x_vout, y_mid, x_vout, y_mid + 20)
    svg.line(x_vout - 14, y_mid + 20, x_vout + 14, y_mid + 20, width=2)
    svg.line(x_vout - 14, y_mid + 26, x_vout + 14, y_mid + 26, width=2)
    svg.line(x_vout, y_mid + 26, x_vout, y_gnd)
    svg.text(x_vout + 18, y_mid + 26, "C_out", size=10, anchor="start",
             color="#555")
    # GND connection at bottom
    svg.line(x_vout, y_gnd, x_vout, y_gnd + 6)
    svg.line(x_vout - 8, y_gnd + 6, x_vout + 8, y_gnd + 6)
    svg.line(x_vout - 5, y_gnd + 10, x_vout + 5, y_gnd + 10)
    svg.line(x_vout - 2, y_gnd + 14, x_vout + 2, y_gnd + 14)

    # Extend GND rail to C_out
    svg.line(220, y_gnd, x_vout, y_gnd, color="#00c", width=2)

    # ================================================================
    # 1-bit controller
    # ================================================================
    x_ctrl = 560
    y_ctrl = y_gnd + 50
    block(svg, x_ctrl - 10, y_ctrl, 180, 60,
          "1-bit Controller", "bang-bang", fill="#f3e8fd")

    # SETTLED input
    arrow(svg, x_ctrl + 200, y_ctrl + 30, x_ctrl + 170, y_ctrl + 30)
    wire_label(svg, x_ctrl + 208, y_ctrl + 34, "SETTLED", anchor="start")
    svg.text(x_ctrl + 208, y_ctrl + 48, "(from async pipe)", size=7,
             anchor="start", color="#888")

    # Controller outputs
    svg.line(x_ctrl - 10, y_ctrl + 20, x_ctrl - 40, y_ctrl + 20)
    svg.text(x_ctrl - 46, y_ctrl + 24, "Ph1, Ph2", size=8, anchor="end",
             color="#555")

    # ================================================================
    # Phase annotations
    # ================================================================
    y_note = y_gnd + 130
    svg.rect(30, y_note, 800, 72, fill="#f8f9fa", stroke="#ccc", rx=4)

    svg.text(50, y_note + 18,
             "Ph1: SW1 + SW_b on    V_in -> +C_fly- -> L -> V_out",
             size=9, anchor="start", color="#d93025", family="monospace")
    svg.text(50, y_note + 34,
             "                      C_fly charges in series with C_out   "
             "  (current: V_in -> + -> - -> L -> C_out -> GND)",
             size=8, anchor="start", color="#888", family="monospace")

    svg.text(50, y_note + 52,
             "Ph2: SW_a + SW2 on    +C_fly -> L -> V_out,  C_fly- -> GND",
             size=9, anchor="start", color="#1a73e8", family="monospace")
    svg.text(50, y_note + 66,
             "                      C_fly discharges parallel with C_out "
             "  (voltage on C_fly reverses)       ZCS via LC resonance",
             size=8, anchor="start", color="#888", family="monospace")

    with open(path, "w") as f:
        f.write(svg.render())
    return path


def draw_phases(v_in, v_core, process, path):
    """Draw the two phases side by side with current flow."""
    svg = SVG(860, 480)

    svg.text(430, 28, "Phase Operation — Current Flow",
             size=15, weight="bold")

    for phase, x_off, color, title in [
        (1, 0, "#d93025", "Phase 1: Charge (series)"),
        (2, 430, "#1a73e8", "Phase 2: Discharge (parallel)"),
    ]:
        xo = x_off
        svg.text(xo + 215, 60, title, size=12, weight="bold", color=color)

        # Simplified circuit for each phase
        y_top = 100
        y_bot = 340
        y_mid = 220
        x_left = xo + 60
        x_cap = xo + 160
        x_L = xo + 260
        x_out = xo + 360

        if phase == 1:
            # V_in → SW1(closed) → A ──C_fly── B → L → V_out → C_out → GND
            # SW1 closed
            svg.line(x_left, y_top, x_left, y_top + 20)
            vdd(svg, x_left, y_top, label=f"V_in ({v_in}V)")
            svg.line(x_left, y_top + 20, x_left, y_top + 50)
            svg.text(x_left + 8, y_top + 38, "SW1", size=8, anchor="start",
                     color=color)
            # wire to plate A
            svg.line(x_left, y_top + 50, x_left, y_mid - 40)
            svg.line(x_left, y_mid - 40, x_cap, y_mid - 40)
            svg.text(x_cap - 20, y_mid - 48, "+", size=11, color="#666",
                     anchor="end", weight="bold")

            # C_fly
            svg.line(x_cap, y_mid - 40, x_cap, y_mid - 10)
            svg.line(x_cap - 16, y_mid - 10, x_cap + 16, y_mid - 10,
                     width=2.5)
            svg.line(x_cap - 16, y_mid + 10, x_cap + 16, y_mid + 10,
                     width=2.5)
            svg.line(x_cap, y_mid + 10, x_cap, y_mid + 40)
            svg.text(x_cap + 20, y_mid + 4, "C_fly", size=9,
                     anchor="start", color="#555")
            svg.text(x_cap - 20, y_mid + 48, "-", size=11, color="#666",
                     anchor="end", weight="bold")

            # - plate → SW_b(closed) → L
            svg.line(x_cap, y_mid + 40, x_L, y_mid + 40)
            svg.text((x_cap + x_L) / 2, y_mid + 36, "SW_b", size=8,
                     color=color)
            svg.line(x_L, y_mid + 40, x_L, y_mid + 10)
            # L symbol
            svg.line(x_L, y_mid + 10, x_L, y_mid + 5)
            for i in range(3):
                cy = y_mid + 5 - i * 6
                svg.elements.append(
                    f'<path d="M {x_L},{cy+2} A 3,3 0 0,1 {x_L},{cy-4}" '
                    f'fill="none" stroke="#222" stroke-width="1.2"/>')
            svg.line(x_L, y_mid - 13, x_L, y_mid - 30)
            svg.text(x_L + 8, y_mid - 2, "L", size=9, anchor="start",
                     color="#555")
            # → V_out
            svg.line(x_L, y_mid - 30, x_out, y_mid - 30)
            wire_label(svg, x_out + 4, y_mid - 34, "V_out", anchor="start")

            # C_out to GND
            svg.line(x_out, y_mid - 30, x_out, y_mid - 10)
            svg.line(x_out - 10, y_mid - 10, x_out + 10, y_mid - 10,
                     width=2)
            svg.line(x_out - 10, y_mid + 6, x_out + 10, y_mid + 6,
                     width=2)
            svg.line(x_out, y_mid + 6, x_out, y_bot)
            svg.text(x_out + 14, y_mid, "C_out", size=8, anchor="start",
                     color="#555")
            gnd(svg, x_out, y_bot)

            # Current flow arrow (dashed)
            arrow(svg, x_left - 20, y_top + 80, x_left - 20, y_mid - 40,
                  color=color, width=1)
            svg.text(x_left - 28, y_top + 100, "I", size=10, color=color,
                     anchor="end")

        else:
            # +C_fly → SW_a(closed) → L → V_out → C_out → GND
            # C_fly- → SW2(closed) → GND

            # + plate
            svg.text(x_cap - 20, y_mid - 48, "+", size=11, color="#666",
                     anchor="end", weight="bold")
            svg.line(x_cap, y_mid - 40, x_cap, y_mid - 10)
            svg.line(x_cap - 16, y_mid - 10, x_cap + 16, y_mid - 10,
                     width=2.5)
            svg.line(x_cap - 16, y_mid + 10, x_cap + 16, y_mid + 10,
                     width=2.5)
            svg.line(x_cap, y_mid + 10, x_cap, y_mid + 40)
            svg.text(x_cap + 20, y_mid + 4, "C_fly", size=9,
                     anchor="start", color="#555")
            svg.text(x_cap - 20, y_mid + 48, "-", size=11, color="#666",
                     anchor="end", weight="bold")

            # A → SW_a(closed) → L → V_out
            svg.line(x_cap, y_mid - 40, x_L, y_mid - 40)
            svg.text((x_cap + x_L) / 2, y_mid - 48, "SW_a", size=8,
                     color=color)
            svg.line(x_L, y_mid - 40, x_L, y_mid - 13)
            # L symbol
            for i in range(3):
                cy = y_mid - 13 + i * 6
                svg.elements.append(
                    f'<path d="M {x_L},{cy-2} A 3,3 0 0,1 {x_L},{cy+4}" '
                    f'fill="none" stroke="#222" stroke-width="1.2"/>')
            svg.line(x_L, y_mid + 5, x_L, y_mid + 20)
            svg.text(x_L + 8, y_mid - 2, "L", size=9, anchor="start",
                     color="#555")

            svg.line(x_L, y_mid + 20, x_out, y_mid + 20)
            wire_label(svg, x_out + 4, y_mid + 16, "V_out", anchor="start")

            # C_out
            svg.line(x_out, y_mid + 20, x_out, y_mid + 40)
            svg.line(x_out - 10, y_mid + 40, x_out + 10, y_mid + 40,
                     width=2)
            svg.line(x_out - 10, y_mid + 56, x_out + 10, y_mid + 56,
                     width=2)
            svg.line(x_out, y_mid + 56, x_out, y_bot)
            svg.text(x_out + 14, y_mid + 50, "C_out", size=8,
                     anchor="start", color="#555")
            gnd(svg, x_out, y_bot)

            # B → SW2(closed) → GND
            svg.line(x_cap, y_mid + 40, x_left, y_mid + 40)
            svg.line(x_left, y_mid + 40, x_left, y_bot)
            svg.text(x_left + 8, y_mid + 58, "SW2", size=8,
                     anchor="start", color=color)
            gnd(svg, x_left, y_bot)

            # Current flow arrow
            arrow(svg, x_cap - 20, y_mid - 40, x_cap - 20, y_mid + 40,
                  color=color, width=1)
            svg.text(x_cap - 28, y_mid, "I", size=10, color=color,
                     anchor="end")

    # Separator
    svg.line(430, 70, 430, 400, color="#ddd", width=1, dash="4,4")

    # ZCS note
    svg.rect(30, 410, 800, 55, fill="#f8f9fa", stroke="#ccc", rx=4)
    svg.text(50, 430,
             "Both phases: LC resonant half-cycle (C_fly + L) "
             "brings current to zero naturally",
             size=9, anchor="start", color="#444", family="monospace")
    svg.text(50, 448,
             f"f_res = 1 / (2*pi*sqrt(L*C_fly))    |    "
             f"Fixed 2:1 ratio: V_core = V_in/2 = {v_in/2:.2g}V    |    "
             f"C_fly voltage reverses each cycle",
             size=8, anchor="start", color="#888", family="monospace")

    with open(path, "w") as f:
        f.write(svg.render())
    return path


def emit_schematics(v_in, v_core, process, output_dir):
    """Generate all grail schematic SVGs.  Returns list of paths."""
    os.makedirs(output_dir, exist_ok=True)
    files = []

    p = os.path.join(output_dir, "grail_topology.svg")
    draw_topology(v_in, v_core, process, p)
    files.append(p)

    p = os.path.join(output_dir, "grail_phases.svg")
    draw_phases(v_in, v_core, process, p)
    files.append(p)

    return files
