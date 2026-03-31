"""GDS-based schematic for grail switched-cap topology.

Renders the circuit topology as KLayout-viewable GDS geometry:
rectangles for components, paths for wires, text for labels.
Not a physical layout — a visual schematic in GDS form.

    V_in ──[SW1]── +C_fly- ──[SW_a]──┐
                                       ├── L ── V_out ──[C_out]── GND
    GND  ──[SW2]── C_fly- ──[SW_b]──┘
"""

import klayout.db as kdb


# Layer assignments (arbitrary, chosen for visual contrast in KLayout)
L_WIRE    = kdb.LayerInfo(1, 0)   # wires
L_COMP    = kdb.LayerInfo(2, 0)   # component bodies (switches, caps)
L_LABEL   = kdb.LayerInfo(3, 0)   # text labels
L_SUPPLY  = kdb.LayerInfo(4, 0)   # supply rails (V_in, GND)
L_CTRL    = kdb.LayerInfo(5, 0)   # controller block
L_ANNO    = kdb.LayerInfo(6, 0)   # annotations / phase labels

# Coordinate scale: 1 unit = 1 nm in GDS, we work in um * 1000
S = 1000  # scale: 1 um = 1000 database units


def _um(x):
    """Convert um to database units."""
    return int(x * S)


def _box(cell, layer_idx, x, y, w, h):
    """Insert a rectangle (x,y = center, w,h = size, all in um)."""
    cell.shapes(layer_idx).insert(kdb.DBox(x - w/2, y - h/2, x + w/2, y + h/2))


def _path(cell, layer_idx, points, width=0.3):
    """Insert a path through a list of (x,y) points in um."""
    pts = [kdb.DPoint(x, y) for x, y in points]
    cell.shapes(layer_idx).insert(kdb.DPath(pts, width))


def _text(cell, layer_idx, x, y, txt, size=2.0):
    """Insert a text label."""
    t = kdb.DText(txt, kdb.DTrans(kdb.DPoint(x, y)))
    t.size = size
    cell.shapes(layer_idx).insert(t)


def _switch_sym(cell, l_comp, l_label, x, y, name, vertical=True):
    """Draw a switch symbol as a thin rectangle with label."""
    if vertical:
        _box(cell, l_comp, x, y, 3, 8)
    else:
        _box(cell, l_comp, x, y, 8, 3)
    _text(cell, l_label, x + 2, y + 2, name, size=1.5)


def _cap_sym(cell, l_comp, l_label, x, y, name, w=6, h=12):
    """Draw a capacitor symbol (two parallel plates)."""
    # Top plate
    cell.shapes(l_comp).insert(kdb.DBox(x - w/2, y + 0.8, x + w/2, y + 1.5))
    # Bottom plate
    cell.shapes(l_comp).insert(kdb.DBox(x - w/2, y - 1.5, x + w/2, y - 0.8))
    _text(cell, l_label, x + w/2 + 1, y, name, size=1.8)


def _inductor_sym(cell, l_comp, l_label, x, y, name, horizontal=True):
    """Draw an inductor symbol (zigzag approximation)."""
    if horizontal:
        # Three bumps as small boxes
        for i in range(3):
            cx = x - 3 + i * 3
            _box(cell, l_comp, cx, y, 2.5, 2)
        _text(cell, l_label, x, y + 2.5, name, size=1.8)
    else:
        for i in range(3):
            cy = y - 3 + i * 3
            _box(cell, l_comp, x, cy, 2, 2.5)
        _text(cell, l_label, x + 2.5, y, name, size=1.8)


def generate_schematic(v_in, v_core, process, gds_path):
    """Generate a GDS schematic of the grail topology.

    Returns the path to the written GDS file.
    """
    layout = kdb.Layout()
    layout.dbu = 0.001  # 1 nm database unit

    top = layout.create_cell("GRAIL_SCHEMATIC")

    # Layer indices
    li_wire  = layout.layer(L_WIRE)
    li_comp  = layout.layer(L_COMP)
    li_label = layout.layer(L_LABEL)
    li_supply = layout.layer(L_SUPPLY)
    li_ctrl  = layout.layer(L_CTRL)
    li_anno  = layout.layer(L_ANNO)

    # ================================================================
    # Coordinates (um) — Y increases upward in GDS
    # ================================================================
    y_vin  = 80    # V_in rail
    y_gnd  = -80   # GND rail
    y_plus = 50    # + plate wire
    y_minus = -50  # - plate wire
    y_mid  = 0     # junction to L

    x_sw1  = -40   # SW1
    x_sw2  = -40   # SW2
    x_cfly = 0     # C_fly
    x_xbar = 40    # crossbar switches
    x_L    = 65    # inductor
    x_vout = 90    # V_out / C_out

    # ================================================================
    # Supply rails
    # ================================================================
    _path(top, li_supply, [(-60, y_vin), (0, y_vin)], width=0.8)
    _text(top, li_label, -62, y_vin, f"V_in ({v_in}V)", size=2.5)

    _path(top, li_supply, [(-60, y_gnd), (x_vout, y_gnd)], width=0.8)
    _text(top, li_label, -62, y_gnd, "GND", size=2.5)

    # ================================================================
    # SW1: V_in → +C_fly
    # ================================================================
    _path(top, li_wire, [(x_sw1, y_vin), (x_sw1, y_plus + 5)], width=0.3)
    _switch_sym(top, li_comp, li_label, x_sw1, (y_vin + y_plus) / 2, "SW1")
    _path(top, li_wire, [(x_sw1, y_plus - 5), (x_sw1, y_plus)], width=0.3)
    _text(top, li_anno, x_sw1 + 3, (y_vin + y_plus) / 2 - 2, "Ph1", size=1.2)

    # ================================================================
    # SW2: GND → C_fly-
    # ================================================================
    _path(top, li_wire, [(x_sw2, y_gnd), (x_sw2, y_minus - 5)], width=0.3)
    _switch_sym(top, li_comp, li_label, x_sw2, (y_gnd + y_minus) / 2, "SW2")
    _path(top, li_wire, [(x_sw2, y_minus + 5), (x_sw2, y_minus)], width=0.3)
    _text(top, li_anno, x_sw2 + 3, (y_gnd + y_minus) / 2 - 2, "Ph2", size=1.2)

    # ================================================================
    # C_fly (+ on top, - on bottom)
    # ================================================================
    # Horizontal wires to cap
    _path(top, li_wire, [(x_sw1, y_plus), (x_cfly, y_plus)], width=0.3)
    _path(top, li_wire, [(x_sw2, y_minus), (x_cfly, y_minus)], width=0.3)

    # Vertical wires to cap plates
    _path(top, li_wire, [(x_cfly, y_plus), (x_cfly, 3)], width=0.3)
    _path(top, li_wire, [(x_cfly, y_minus), (x_cfly, -3)], width=0.3)

    # Cap symbol
    _cap_sym(top, li_comp, li_label, x_cfly, 0, "C_fly", w=8)

    # Plate labels
    _text(top, li_label, x_cfly - 3, 4, "+", size=2.0)
    _text(top, li_label, x_cfly - 3, -5, "-", size=2.0)

    # ================================================================
    # Continue + and - wires to crossbar
    # ================================================================
    _path(top, li_wire, [(x_cfly, y_plus), (x_xbar, y_plus)], width=0.3)
    _path(top, li_wire, [(x_cfly, y_minus), (x_xbar, y_minus)], width=0.3)

    # ================================================================
    # SW_a: + plate → mid junction (Ph2)
    # ================================================================
    _path(top, li_wire, [(x_xbar, y_plus), (x_xbar, y_mid + 5)], width=0.3)
    _switch_sym(top, li_comp, li_label, x_xbar, (y_plus + y_mid) / 2, "SW_a")
    _text(top, li_anno, x_xbar + 3, (y_plus + y_mid) / 2 - 2, "Ph2", size=1.2)

    # ================================================================
    # SW_b: - plate → mid junction (Ph1)
    # ================================================================
    _path(top, li_wire, [(x_xbar, y_minus), (x_xbar, y_mid - 5)], width=0.3)
    _switch_sym(top, li_comp, li_label, x_xbar, (y_minus + y_mid) / 2, "SW_b")
    _text(top, li_anno, x_xbar + 3, (y_minus + y_mid) / 2 - 2, "Ph1", size=1.2)

    # Junction at mid
    _box(top, li_wire, x_xbar, y_mid, 1, 1)

    # ================================================================
    # L: inductor from crossbar junction → V_out
    # ================================================================
    _path(top, li_wire, [(x_xbar, y_mid), (x_L - 6, y_mid)], width=0.3)
    _inductor_sym(top, li_comp, li_label, x_L, y_mid, "L (bond wire)")
    _path(top, li_wire, [(x_L + 6, y_mid), (x_vout, y_mid)], width=0.3)

    # ================================================================
    # V_out node + C_out to GND
    # ================================================================
    _box(top, li_wire, x_vout, y_mid, 1.5, 1.5)  # junction dot
    _text(top, li_label, x_vout + 2, y_mid + 2, f"V_out ({v_core}V)", size=2.0)

    # Output wire to the right
    _path(top, li_wire, [(x_vout, y_mid), (x_vout + 20, y_mid)], width=0.3)
    _text(top, li_label, x_vout + 22, y_mid, f"V_core", size=2.0)

    # C_out vertical
    _path(top, li_wire, [(x_vout, y_mid), (x_vout, y_mid - 10)], width=0.3)
    _cap_sym(top, li_comp, li_label, x_vout, y_mid - 15, "C_out", w=6)
    _path(top, li_wire, [(x_vout, y_mid - 20), (x_vout, y_gnd)], width=0.3)

    # ================================================================
    # 1-bit controller
    # ================================================================
    _box(top, li_ctrl, x_L, y_gnd + 18, 30, 12)
    _text(top, li_label, x_L, y_gnd + 18, "1-bit Controller", size=1.8)
    _text(top, li_label, x_L, y_gnd + 14, "(bang-bang)", size=1.2)

    # SETTLED input
    _path(top, li_wire, [(x_L + 20, y_gnd + 18), (x_L + 30, y_gnd + 18)],
          width=0.3)
    _text(top, li_label, x_L + 32, y_gnd + 18, "SETTLED", size=1.5)

    # Ph1/Ph2 output arrows (just labeled wires)
    _path(top, li_ctrl, [(x_L - 15, y_gnd + 18), (x_L - 25, y_gnd + 18)],
          width=0.3)
    _text(top, li_label, x_L - 28, y_gnd + 20, "Ph1,Ph2", size=1.2)

    # ================================================================
    # Title
    # ================================================================
    _text(top, li_label, -60, y_vin + 15,
          f"grail -- 2:1 Resonant SC Converter  |  {process}", size=3.0)
    _text(top, li_anno, -60, y_vin + 10,
          "Ph1: SW1+SW_b  (series charge)    "
          "Ph2: SW_a+SW2  (parallel discharge)", size=1.5)

    layout.write(gds_path)
    return gds_path
