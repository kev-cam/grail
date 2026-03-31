"""Grail generator plugin for Kestrel.

Switched-cap power pad generator for DVFS with async completion logic.
Topology: 2:1 hybrid LC switched-cap with 1-bit bang-bang controller
driven by the async pipeline's SETTLED signal.
"""


def add_arguments(parser):
    """Add grail-specific CLI arguments."""
    parser.add_argument("--v-in", required=True,
                        help="External supply voltage (e.g. 2.4)")
    parser.add_argument("--v-core", required=True,
                        help="Target on-chip VDD (e.g. 0.6)")
    parser.add_argument("--i-avg", required=True,
                        help="Average switching current (e.g. 10m)")
    parser.add_argument("--f-fire-min", required=True,
                        help="Min pipeline firing interval freq (e.g. 500M)")
    parser.add_argument("--process", default="sky130",
                        choices=["sky130", "gf180", "sg13g2"])
    parser.add_argument("--output", "-o", default="./grail_out",
                        help="Output directory")


def run(args):
    """Execute grail generation from parsed CLI args."""
    from kestrel.spec import parse_freq
    from .engine import GrailSpec, design_grail, summarize
    from .spice import emit_spice
    from .schematic import emit_schematics
    from .kicad_schematic import emit_kicad_sch

    spec = GrailSpec(
        v_in=float(args.v_in),
        v_core=float(args.v_core),
        i_avg=_parse_current(args.i_avg),
        f_fire_min=parse_freq(args.f_fire_min),
        process=args.process,
    )
    design = design_grail(spec)
    print(summarize(design))
    print()

    files = emit_spice(design, args.output)
    for f in files:
        print(f"  wrote {f}")

    files = emit_schematics(spec.v_in, spec.v_core, spec.process, args.output)
    for f in files:
        print(f"  wrote {f}")

    files = emit_kicad_sch(spec.v_in, spec.v_core, spec.process, args.output)
    for f in files:
        print(f"  wrote {f}")


def _parse_current(text):
    """Parse a current string with SI suffix (e.g. '10m', '100u')."""
    from kestrel.spec import parse_freq
    return parse_freq(text)  # same SI prefix logic


def gui_fields():
    """Return grail GUI field definitions."""
    return {
        "entries": [
            {"label": "V_in:",        "key": "v_in",       "default": "2.4",  "hint": "V (external supply, 2x V_core)"},
            {"label": "V_core:",      "key": "v_core",     "default": "0.6",  "hint": "V (on-chip VDD target)"},
            {"label": "I_avg:",       "key": "i_avg",      "default": "10m",  "hint": "A (average switching current)"},
            {"label": "f_fire_min:",  "key": "f_fire_min", "default": "500M", "hint": "Hz (min firing freq)"},
        ],
        "combos": [
            {"label": "Process:", "key": "process", "default": "sky130", "choices": ["sky130", "gf180", "sg13g2"]},
        ],
        "extras": [],
    }


def register():
    """Register the grail generator with Kestrel."""
    return {
        "name": "grail",
        "version": "0.1.0",
        "description": "Switched-cap power pad generator for DVFS",
        "add_arguments": add_arguments,
        "run": run,
        "gui_fields": gui_fields,
    }
