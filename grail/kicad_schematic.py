"""KiCad schematic generator for grail switched-cap topology.

Generates a .kicad_sch file with NMOS switches, capacitors, inductor,
and wiring for the 2:1 resonant SC converter:

    V_in ──[SW1]── +C_fly- ──[SW_a]──┐
                                       ├── L ── V_out ──[C_out]── GND
    GND  ──[SW2]── C_fly- ──[SW_b]──┘
"""

import os
import uuid as _uuid


def uid():
    return str(_uuid.uuid4())


# ── lib_symbol generators ──

def _nmos_lib(name="NMOS_SW"):
    """NMOS switch symbol: G left, D top, S bottom."""
    ef = "(effects (font (size 1.27 1.27)))"
    efh = "(effects (font (size 1.27 1.27)) (hide yes))"
    efl = "(effects (font (size 1.27 1.27)) (justify left))"
    return f"""\t\t(symbol "grail:{name}"
\t\t\t(pin_names (offset 0.254) (hide yes))
\t\t\t(pin_numbers (hide yes))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "M"
\t\t\t\t(at 5.08 1.27 0)
\t\t\t\t{efl}
\t\t\t)
\t\t\t(property "Value" "{name}"
\t\t\t\t(at 5.08 -1.27 0)
\t\t\t\t{efl}
\t\t\t)
\t\t\t(property "Footprint" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t{efh}
\t\t\t)
\t\t\t(property "Datasheet" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t{efh}
\t\t\t)
\t\t\t(property "Description" "NMOS power switch"
\t\t\t\t(at 0 0 0)
\t\t\t\t{efh}
\t\t\t)
\t\t\t(symbol "{name}_0_1"
\t\t\t\t(polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy -0.508 1.27) (xy -0.508 -1.27))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy -0.508 0.762) (xy 0 0.762) (xy 0 2.54))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy -0.508 -0.762) (xy 0 -0.762) (xy 0 -2.54))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy -0.508 0) (xy 2.54 0))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy -2.54 0) (xy -1.27 0))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy -0.254 0.508) (xy 0.254 0) (xy -0.254 -0.508))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t)
\t\t\t(symbol "{name}_1_1"
\t\t\t\t(pin passive line (at -5.08 0 0) (length 2.54)
\t\t\t\t\t(name "G" {ef}) (number "1" {ef}))
\t\t\t\t(pin passive line (at 0 5.08 270) (length 2.54)
\t\t\t\t\t(name "D" {ef}) (number "2" {ef}))
\t\t\t\t(pin passive line (at 0 -5.08 90) (length 2.54)
\t\t\t\t\t(name "S" {ef}) (number "3" {ef}))
\t\t\t)
\t\t\t(embedded_fonts no)
\t\t)"""


def _cap_lib(name="CAP"):
    """Capacitor symbol: pin 1 top, pin 2 bottom."""
    ef = "(effects (font (size 1.27 1.27)))"
    efh = "(effects (font (size 1.27 1.27)) (hide yes))"
    efl = "(effects (font (size 1.27 1.27)) (justify left))"
    return f"""\t\t(symbol "grail:{name}"
\t\t\t(pin_names (offset 0.254) (hide yes))
\t\t\t(pin_numbers (hide yes))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "C"
\t\t\t\t(at 2.54 0 0)
\t\t\t\t{efl}
\t\t\t)
\t\t\t(property "Value" "{name}"
\t\t\t\t(at 2.54 -2.54 0)
\t\t\t\t{efl}
\t\t\t)
\t\t\t(property "Footprint" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t{efh}
\t\t\t)
\t\t\t(property "Datasheet" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t{efh}
\t\t\t)
\t\t\t(property "Description" "Capacitor"
\t\t\t\t(at 0 0 0)
\t\t\t\t{efh}
\t\t\t)
\t\t\t(symbol "{name}_0_1"
\t\t\t\t(polyline (pts (xy -1.27 0.508) (xy 1.27 0.508))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy -1.27 -0.508) (xy 1.27 -0.508))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 0 0.508) (xy 0 2.54))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 0 -0.508) (xy 0 -2.54))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t)
\t\t\t(symbol "{name}_1_1"
\t\t\t\t(pin passive line (at 0 5.08 270) (length 2.54)
\t\t\t\t\t(name "1" {ef}) (number "1" {ef}))
\t\t\t\t(pin passive line (at 0 -5.08 90) (length 2.54)
\t\t\t\t\t(name "2" {ef}) (number "2" {ef}))
\t\t\t)
\t\t\t(embedded_fonts no)
\t\t)"""


def _ind_lib(name="IND"):
    """Inductor symbol: pin 1 left, pin 2 right (horizontal)."""
    ef = "(effects (font (size 1.27 1.27)))"
    efh = "(effects (font (size 1.27 1.27)) (hide yes))"
    efl = "(effects (font (size 1.27 1.27)) (justify left))"
    # Three arcs approximated as polylines
    arcs = ""
    for i in range(3):
        cx = -2.0 + i * 2.0
        arcs += f"""\t\t\t\t(arc (start {cx - 1.0} 0) (mid {cx} -1.0) (end {cx + 1.0} 0)
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
"""
    return f"""\t\t(symbol "grail:{name}"
\t\t\t(pin_names (offset 0.254) (hide yes))
\t\t\t(pin_numbers (hide yes))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "L"
\t\t\t\t(at 0 2.54 0)
\t\t\t\t{efl}
\t\t\t)
\t\t\t(property "Value" "{name}"
\t\t\t\t(at 0 -2.54 0)
\t\t\t\t{efl}
\t\t\t)
\t\t\t(property "Footprint" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t{efh}
\t\t\t)
\t\t\t(property "Datasheet" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t{efh}
\t\t\t)
\t\t\t(property "Description" "Inductor (bond wire)"
\t\t\t\t(at 0 0 0)
\t\t\t\t{efh}
\t\t\t)
\t\t\t(symbol "{name}_0_1"
{arcs}\t\t\t\t(polyline (pts (xy -3.0 0) (xy -2.54 0))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 3.0 0) (xy 2.54 0))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t)
\t\t\t(symbol "{name}_1_1"
\t\t\t\t(pin passive line (at -5.08 0 0) (length 2.54)
\t\t\t\t\t(name "1" {ef}) (number "1" {ef}))
\t\t\t\t(pin passive line (at 5.08 0 180) (length 2.54)
\t\t\t\t\t(name "2" {ef}) (number "2" {ef}))
\t\t\t)
\t\t\t(embedded_fonts no)
\t\t)"""


# ── placement helpers ──

def _sym(lib_id, ref, value, at, pins_n=3, mirror=None):
    """Place a symbol instance."""
    ax, ay, ar = round(at[0], 4), round(at[1], 4), at[2]
    u = uid()
    ef = "(effects (font (size 1.0 1.0)) (justify left))"
    efh = "(effects (font (size 1.27 1.27)) (hide yes))"
    mirror_line = f"\n\t\t(mirror {mirror})" if mirror else ""
    pins = "\n".join(f'\t\t(pin "{n}" (uuid "{uid()}"))' for n in range(1, pins_n + 1))
    return f"""\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {ax} {ay} {ar}){mirror_line}
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{u}")
\t\t(property "Reference" "{ref}"
\t\t\t(at {ax + 3.81} {ay - 1.27} 0)
\t\t\t{ef}
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at {ax + 3.81} {ay + 1.27} 0)
\t\t\t{ef}
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at {ax} {ay} 0)
\t\t\t{efh}
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at {ax} {ay} 0)
\t\t\t{efh}
\t\t)
\t\t(property "Description" ""
\t\t\t(at {ax} {ay} 0)
\t\t\t{efh}
\t\t)
{pins}
\t\t(instances
\t\t\t(project "grail")
\t\t)
\t)"""


def _wire(x1, y1, x2, y2):
    x1, y1, x2, y2 = round(x1, 4), round(y1, 4), round(x2, 4), round(y2, 4)
    return f"""\t(wire
\t\t(pts (xy {x1} {y1}) (xy {x2} {y2}))
\t\t(stroke (width 0) (type solid))
\t\t(uuid "{uid()}")
\t)"""


def _label(name, x, y, angle=0):
    x, y = round(x, 4), round(y, 4)
    return f"""\t(label "{name}"
\t\t(at {x} {y} {angle})
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{uid()}")
\t)"""


def _junction(x, y):
    x, y = round(x, 4), round(y, 4)
    return f"""\t(junction
\t\t(at {x} {y})
\t\t(diameter 1.016)
\t\t(color 0 0 0 0)
\t\t(uuid "{uid()}")
\t)"""


def _text(txt, x, y, sz=2.0):
    return f"""\t(text "{txt}"
\t\t(exclude_from_sim no)
\t\t(at {x} {y} 0)
\t\t(effects (font (size {sz} {sz})) (justify left bottom))
\t\t(uuid "{uid()}")
\t)"""


def _pwr_flag(name, x, y):
    """Power flag (global label)."""
    x, y = round(x, 4), round(y, 4)
    return f"""\t(global_label "{name}"
\t\t(shape passive)
\t\t(at {x} {y} 0)
\t\t(effects (font (size 1.27 1.27)))
\t\t(uuid "{uid()}")
\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"
\t\t\t(at 0 0 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t)"""


# ── main generator ──

def generate(v_in, v_core, process):
    """Generate KiCad schematic S-expression for the grail topology."""

    g = 2.54  # KiCad grid

    # NMOS pin offsets (no mirror): G at x-p, D at y-p (up), S at y+p (down)
    p = 2 * g  # 5.08

    # ── Coordinates (KiCad Y increases downward) ──
    # Vertical layout: V_in at top, GND at bottom

    VIN_Y = 8 * g       # V_in rail
    GND_Y = 52 * g      # GND rail

    # SW1 column (V_in → +C_fly)
    SW1_X = 20 * g
    SW1_Y = 16 * g      # D at y-p=VIN_Y+p, S at y+p

    # SW2 column (GND → C_fly-)
    SW2_X = 20 * g
    SW2_Y = 44 * g      # D at y-p, S at y+p=GND_Y-p

    # C_fly (vertical cap, pin1=top=+, pin2=bot=-)
    CFLY_X = 32 * g
    CFLY_Y = 30 * g     # center; pin1 at y-p (top), pin2 at y+p (bottom)

    # Horizontal wires from switches to cap
    PLUS_Y = SW1_Y + p      # + plate wire (SW1 source level)
    MINUS_Y = SW2_Y - p     # - plate wire (SW2 drain level)

    # Crossbar switches (SW_a and SW_b)
    XBAR_X = 44 * g
    # SW_a: connects + plate to mid junction
    SWA_Y = 24 * g      # between PLUS_Y and MID_Y
    # SW_b: connects - plate to mid junction
    SWB_Y = 36 * g      # between MID_Y and MINUS_Y

    MID_Y = 30 * g      # junction where SW_a and SW_b meet → L

    # Inductor (horizontal)
    IND_X = 56 * g      # center; pin1 at x-p (left), pin2 at x+p (right)
    IND_Y = MID_Y

    # V_out / C_out
    VOUT_X = IND_X + p + 4 * g  # past inductor pin2
    VOUT_Y = MID_Y
    COUT_X = VOUT_X
    COUT_Y = 40 * g     # pin1 at y-p, pin2 at y+p

    parts = []
    wires = []
    juncs = set()
    labels = []

    def W(x1, y1, x2, y2):
        wires.append(_wire(x1, y1, x2, y2))

    def J(x, y):
        juncs.add((round(x, 2), round(y, 2)))

    def L(name, x, y, angle=0):
        labels.append(_label(name, x, y, angle))

    # ── Place symbols ──

    # SW1: NMOS, D=top(toward V_in), S=bottom(toward + plate)
    parts.append(_sym("grail:NMOS_SW", "M1", "SW1", (SW1_X, SW1_Y, 0)))

    # SW2: NMOS, D=top(toward - plate), S=bottom(toward GND)
    parts.append(_sym("grail:NMOS_SW", "M2", "SW2", (SW2_X, SW2_Y, 0)))

    # SW_a: NMOS, D=top(toward + plate), S=bottom(toward mid)
    parts.append(_sym("grail:NMOS_SW", "M3", "SW_a", (XBAR_X, SWA_Y, 0)))

    # SW_b: NMOS, D=top(toward mid), S=bottom(toward - plate)
    parts.append(_sym("grail:NMOS_SW", "M4", "SW_b", (XBAR_X, SWB_Y, 0)))

    # C_fly: vertical cap, pin1=top(+), pin2=bottom(-)
    parts.append(_sym("grail:CAP", "C1", "C_fly", (CFLY_X, CFLY_Y, 0), pins_n=2))

    # C_out: vertical cap
    parts.append(_sym("grail:CAP", "C2", "C_out", (COUT_X, COUT_Y, 0), pins_n=2))

    # L: horizontal inductor
    parts.append(_sym("grail:IND", "L1", "L (bond wire)", (IND_X, IND_Y, 0), pins_n=2))

    # ── Wiring ──

    # V_in rail
    W(SW1_X - 6 * g, VIN_Y, SW1_X + 4 * g, VIN_Y)

    # SW1 drain to V_in
    W(SW1_X, SW1_Y - p, SW1_X, VIN_Y)

    # SW1 source to + plate wire
    W(SW1_X, SW1_Y + p, SW1_X, PLUS_Y)

    # + plate horizontal wire: SW1 → C_fly pin1 → SW_a
    W(SW1_X, PLUS_Y, CFLY_X, PLUS_Y)
    W(CFLY_X, PLUS_Y, CFLY_X, CFLY_Y - p)  # down to cap pin1
    W(CFLY_X, PLUS_Y, XBAR_X, PLUS_Y)       # continue to crossbar
    W(XBAR_X, PLUS_Y, XBAR_X, SWA_Y - p)    # down to SW_a drain
    J(CFLY_X, PLUS_Y)

    # - plate horizontal wire: SW2 → C_fly pin2 → SW_b
    W(SW2_X, SW2_Y - p, SW2_X, MINUS_Y)
    W(SW2_X, MINUS_Y, CFLY_X, MINUS_Y)
    W(CFLY_X, MINUS_Y, CFLY_X, CFLY_Y + p)  # up to cap pin2
    W(CFLY_X, MINUS_Y, XBAR_X, MINUS_Y)     # continue to crossbar
    W(XBAR_X, MINUS_Y, XBAR_X, SWB_Y + p)   # up to SW_b source
    J(CFLY_X, MINUS_Y)

    # SW_a source to mid junction
    W(XBAR_X, SWA_Y + p, XBAR_X, MID_Y)

    # SW_b drain to mid junction
    W(XBAR_X, SWB_Y - p, XBAR_X, MID_Y)
    J(XBAR_X, MID_Y)

    # Mid junction to inductor pin1
    W(XBAR_X, MID_Y, IND_X - p, MID_Y)

    # Inductor pin2 to V_out
    W(IND_X + p, MID_Y, VOUT_X, MID_Y)

    # V_out to C_out pin1
    W(VOUT_X, MID_Y, VOUT_X, COUT_Y - p)
    J(VOUT_X, MID_Y)

    # C_out pin2 to GND
    W(COUT_X, COUT_Y + p, COUT_X, GND_Y)

    # SW2 source to GND
    W(SW2_X, SW2_Y + p, SW2_X, GND_Y)

    # GND rail
    W(SW2_X, GND_Y, COUT_X, GND_Y)
    J(SW2_X, GND_Y)
    J(COUT_X, GND_Y)

    # ── Gate drive labels ──
    L("Ph1", SW1_X - p - 4 * g, SW1_Y)
    W(SW1_X - p - 4 * g, SW1_Y, SW1_X - p, SW1_Y)

    L("Ph2", SW2_X - p - 4 * g, SW2_Y)
    W(SW2_X - p - 4 * g, SW2_Y, SW2_X - p, SW2_Y)

    L("Ph2", XBAR_X - p - 4 * g, SWA_Y)
    W(XBAR_X - p - 4 * g, SWA_Y, XBAR_X - p, SWA_Y)

    L("Ph1", XBAR_X - p - 4 * g, SWB_Y)
    W(XBAR_X - p - 4 * g, SWB_Y, XBAR_X - p, SWB_Y)

    # ── Net labels ──
    L("+C_fly", CFLY_X + 2 * g, PLUS_Y)
    L("C_fly-", CFLY_X + 2 * g, MINUS_Y)
    L("V_out", VOUT_X + 2 * g, MID_Y)

    # V_out output wire to the right
    W(VOUT_X, MID_Y, VOUT_X + 6 * g, MID_Y)
    L(f"V_core ({v_core}V)", VOUT_X + 2 * g, MID_Y - 2 * g)

    # ── Power labels ──
    L(f"V_in ({v_in}V)", SW1_X - 6 * g, VIN_Y - 2 * g)
    L("GND", SW2_X - 2 * g, GND_Y + 2 * g)

    # ── Title ──
    title = _text(
        f"grail \\u2014 2:1 Resonant SC Converter  |  "
        f"V_in={v_in}V  V_core={v_core}V  |  {process}",
        4 * g, 4 * g, 2.5
    )

    phase_note = _text(
        "Ph1: SW1+SW_b (series charge)    Ph2: SW_a+SW2 (parallel discharge)",
        4 * g, 6 * g, 1.5
    )

    # Plate annotations near C_fly
    plus_label = _text("+", CFLY_X - 3 * g, CFLY_Y - 2 * g, 2.0)
    minus_label = _text("-", CFLY_X - 3 * g, CFLY_Y + 1 * g, 2.0)

    # ── Assemble ──
    junctions_str = "\n".join(_junction(x, y) for x, y in sorted(juncs))
    lib_syms = "\n".join([_nmos_lib(), _cap_lib(), _ind_lib()])

    sch = f"""(kicad_sch
\t(version 20250114)
\t(generator "python")
\t(generator_version "10.0")
\t(uuid "{uid()}")
\t(paper "A3")
\t(lib_symbols
{lib_syms}
\t)
{title}
{phase_note}
{plus_label}
{minus_label}
{junctions_str}
{chr(10).join(wires)}
{chr(10).join(labels)}
{chr(10).join(parts)}
)
"""
    return sch


def _kicad_pro(sch_uuid):
    """Generate a minimal .kicad_pro project file."""
    import json
    return json.dumps({
        "board": {
            "3dviewports": [],
            "design_settings": {
                "defaults": {
                    "board_outline_line_width": 0.1,
                    "copper_line_width": 0.2,
                    "copper_text_size_h": 1.5,
                    "copper_text_size_v": 1.5,
                    "copper_text_thickness": 0.3,
                    "other_line_width": 0.15,
                    "silk_line_width": 0.15,
                    "silk_text_size_h": 1.0,
                    "silk_text_size_v": 1.0,
                    "silk_text_thickness": 0.15,
                },
                "diff_pair_dimensions": [],
                "drc_exclusions": [],
                "rules": {
                    "solder_mask_clearance": 0.0,
                    "solder_mask_min_width": 0.0,
                },
                "track_widths": [],
                "via_dimensions": [],
            },
            "layer_pairs": [],
            "layer_presets": [],
            "viewports": [],
        },
        "boards": [],
        "cvpcb": {"equivalence_files": []},
        "erc": {
            "erc_exclusions": [],
            "meta": {"version": 0},
            "pin_map": [],
            "rule_severities": {
                "bus_definition_conflict": "error",
                "bus_entry_needed": "error",
                "bus_label_syntax": "error",
                "bus_to_bus_conflict": "error",
                "bus_to_net_conflict": "error",
                "different_unit_footprint": "error",
                "different_unit_net": "error",
                "duplicate_reference": "error",
                "duplicate_sheet_names": "error",
                "endpoint_off_grid": "warning",
                "extra_units": "error",
                "footprint_filter": "ignore",
                "footprint_link_issues": "warning",
                "four_way_junction": "ignore",
                "global_label_dangling": "warning",
                "hier_label_mismatch": "error",
                "label_dangling": "error",
                "label_multiple_wires": "warning",
                "lib_symbol_issues": "ignore",
                "lib_symbol_mismatch": "ignore",
                "missing_bidi_pin": "warning",
                "missing_input_pin": "warning",
                "missing_power_pin": "ignore",
                "missing_unit": "warning",
                "multiple_net_names": "warning",
                "net_not_bus_member": "warning",
                "no_connect_connected": "warning",
                "no_connect_dangling": "warning",
                "pin_not_connected": "ignore",
                "pin_not_driven": "ignore",
                "pin_to_pin": "ignore",
                "power_pin_not_driven": "ignore",
                "same_local_global_label": "warning",
                "similar_label_and_power": "warning",
                "similar_labels": "warning",
                "similar_power": "warning",
                "simulation_model_issue": "ignore",
                "single_global_label": "ignore",
                "unannotated": "error",
                "unconnected_wire_endpoint": "warning",
                "unit_value_mismatch": "error",
                "unresolved_variable": "error",
                "wire_dangling": "warning",
            },
        },
        "libraries": {
            "pinned_footprint_libs": [],
            "pinned_symbol_libs": [],
        },
        "meta": {
            "filename": "grail_schematic.kicad_pro",
            "version": 3,
        },
        "net_settings": {
            "classes": [
                {
                    "bus_width": 12,
                    "clearance": 0.2,
                    "diff_pair_gap": 0.25,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.2,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "Default",
                    "pcb_color": "rgba(0, 0, 0, 0.000)",
                    "priority": 2147483647,
                    "schematic_color": "rgba(0, 0, 0, 0.000)",
                    "track_width": 0.25,
                    "via_diameter": 0.8,
                    "via_drill": 0.4,
                    "wire_width": 6,
                }
            ],
            "meta": {"version": 4},
            "net_colors": None,
            "netclass_assignments": None,
            "netclass_patterns": [],
        },
        "pcbnew": {
            "last_paths": {
                "gencad": "", "idf": "", "netlist": "", "plot": "",
                "pos_files": "", "specctra_dsn": "", "step": "",
                "svg": "", "vrml": "",
            },
            "page_layout_descr_file": "",
        },
        "schematic": {
            "annotate_start_num": 0,
            "bom_export_filename": "${PROJECTNAME}.csv",
            "bom_fmt_presets": [],
            "bom_fmt_settings": {
                "field_delimiter": ",",
                "keep_line_breaks": False,
                "keep_tabs": False,
                "name": "CSV",
                "ref_delimiter": ",",
                "ref_range_delimiter": "",
                "string_delimiter": "\"",
            },
            "bom_presets": [],
            "bom_settings": {
                "exclude_dnp": False,
                "fields_ordered": [],
                "filter_string": "",
                "group_symbols": True,
                "include_excluded_from_bom": True,
                "name": "Default Editing",
                "sort_asc": True,
                "sort_field": "Reference",
            },
            "connection_grid_size": 50.0,
            "drawing": {
                "dashed_lines_dash_length_ratio": 12.0,
                "dashed_lines_gap_length_ratio": 3.0,
                "default_bus_thickness": 12.0,
                "default_junction_size": 40.0,
                "default_line_thickness": 6.0,
                "default_text_size": 50.0,
                "default_wire_thickness": 6.0,
                "field_names": [],
                "intersheets_ref_own_page": False,
                "intersheets_ref_prefix": "",
                "intersheets_ref_short": False,
                "intersheets_ref_show": False,
                "intersheets_ref_suffix": "",
                "junction_size_choice": 3,
                "label_size_ratio": 0.3,
                "pin_symbol_size": 25.0,
                "text_offset_ratio": 0.3,
            },
            "legacy_lib_dir": "",
            "legacy_lib_list": [],
            "meta": {"version": 1},
            "net_format_name": "",
            "page_layout_descr_file": "",
            "plot_directory": "",
            "spice_adjust_passive_values": False,
            "spice_current_sheet_as_root": False,
            "spice_external_command": "spice \"%I\"",
            "spice_model_current_sheet_as_root": True,
            "spice_save_all_currents": False,
            "spice_save_all_dissipations": False,
            "spice_save_all_voltages": False,
            "subpart_first_id": 65,
            "subpart_id_separator": 0,
        },
        "sheets": [[sch_uuid, "Root"]],
        "text_variables": {},
    }, indent=2)


def emit_kicad_sch(v_in, v_core, process, output_dir):
    """Generate KiCad project (schematic + project file). Returns list of paths."""
    os.makedirs(output_dir, exist_ok=True)
    sch = generate(v_in, v_core, process)
    files = []

    sch_path = os.path.join(output_dir, "grail_schematic.kicad_sch")
    with open(sch_path, 'w') as f:
        f.write(sch)
    files.append(sch_path)

    # Extract the schematic UUID for the project file
    import re
    m = re.search(r'\(uuid "([^"]+)"\)', sch)
    sch_uuid = m.group(1) if m else uid()

    pro_path = os.path.join(output_dir, "grail_schematic.kicad_pro")
    with open(pro_path, 'w') as f:
        f.write(_kicad_pro(sch_uuid))
    files.append(pro_path)

    return files
