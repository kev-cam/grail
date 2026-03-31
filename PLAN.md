\# \*grail — On-Chip Switched-Cap Power Pad Generator



\## Overview



\*grail is a pad-level power management generator that produces on-chip switched-cap voltage step-down cells for integration with async logic designs. It wraps kestrel's existing generator infrastructure (gdsfactory, open PDK device models, layout pipeline) and adds a hybrid LC switched-cap topology with a 1-bit adaptive controller driven directly by the async pipeline's SETTLED signal.



The name implies what it is: the long-sought on-chip power management primitive that eliminates the external PMIC, board-level regulation complexity, and the synchronous timing sensitivity to supply noise — in a single generated pad cell.



\---



\## Problem Statement



Conventional on-chip power delivery assumes synchronous logic:



\- V\_DD must be held stiff — droop violates setup/hold margins

\- DVFS requires a dedicated controller, ADC, PLL reference, and μs-scale transition time

\- Near-threshold operation requires tight regulation — exactly where board regulators are least efficient

\- Per-stage voltage domains are impractical — too many feedback loops



Async logic with current-sense completion changes all the constraints. V\_DD noise translates to latency jitter, not logical error. The pipeline finds its own operating point. The SETTLED signal already carries all the information a power controller needs.



\*grail exploits this: the completion detector and the power manager are the same circuit.



\---



\## Architecture



\### Topology: Hybrid LC Switched-Cap, 2:1



```

V\_in (2 × V\_core) ──\[SW1]──┬── V\_out (V\_core)

&#x20;                           │

&#x20;                        \[C\_fly]    ← on-chip MIM or MOS cap

&#x20;                           │

&#x20;                          \[L]      ← bond wire + package/SMD inductor

&#x20;                           │

&#x20;                         \[SW2]

&#x20;                           │

&#x20;                          GND

```



The 2:1 ratio is fixed by topology — not by a control loop. This is the efficiency maximum for series-parallel switched-cap: zero charge redistribution loss at the natural conversion ratio.



The inductor in series with SW2 enforces zero-current switching (ZCS): the LC resonant current naturally reaches zero at the end of each transfer half-cycle, eliminating switching loss without requiring precise timing control.



Board supply targets 2× V\_core. For near-threshold operation at \~0.6V, board delivers 1.2V — a much more efficient buck converter operating point than regulating 0.6V directly. Bond wire and trace I²R losses drop by 75% (half the current at twice the voltage).



\### Adaptive Controller: 1-Bit Bang-Bang



```

SETTLED early  →  slow down  (reduce SW1 on-time, V\_out sags slightly)

SETTLED late   →  go faster  (increase SW1 on-time, V\_out rises slightly)

```



No ADC. No DAC. No PLL reference. No latency measurement. One bit in, one bit out, acting once per pipeline fire event. The system hunts to the natural equilibrium of the pipeline — the quiescent operating point emerges from the physics rather than being programmed in.



Controller implemented in heron async cells (C-elements + toggle counter). The power manager is async logic managed by async logic.



\### Self-Aligning Thresholds



The comparator reference that generates the SETTLED signal uses a replica sense transistor biased at the leakage floor. It tracks process corner, temperature, and V\_DD automatically. No explicit threshold calibration at any operating point.



\---



\## Inputs / Outputs



\### Generator Inputs



| Parameter | Description |

|---|---|

| `V\_in` | External supply (nominally 2 × V\_core) |

| `V\_core\_target` | Desired on-chip V\_DD (near-threshold: \~0.5–0.7V) |

| `I\_avg` | Average pipeline switching current (from swift energy budget) |

| `f\_fire\_min` | Minimum pipeline firing interval (sets resonant frequency floor) |

| `PDK` | Target process (SKY130, GF180, GF22FDX...) |



\### Generator Outputs



| Output | Description |

|---|---|

| C\_fly sizing | MIM/MOS cap dimensions, DRC-clean |

| SW1/SW2 sizing | Wide NMOS switch transistors, ZCS-optimized |

| L specification | Target inductance for off-chip component (bond wire contribution included) |

| SETTLED interface | Timing constraints for heron handshake connection |

| LVS-clean layout | gdsfactory-generated pad cell, ready for OpenROAD pad ring integration |

| Spice netlist | For NVC+Xyce co-simulation and Monte Carlo sign-off |



\---



\## Relationship to Existing Projects



| \*grail component | Existing foundation |

|---|---|

| Generator framework | kestrel (PLL generator, gdsfactory, open PDK plumbing) |

| SETTLED signal source | heron (async cell library, current-sense comparator) |

| Energy budget input | swift (RTL→async synthesis, per-stage switching energy) |

| Per-stage distribution | petrel (fine-grain on-chip supply, C reservoir) |

| Analog sign-off | NVC+Xyce federated flow, Monte Carlo PVT |



\*grail is a wrapper, not a ground-up build. The hard infrastructure — PDK DRC rules, MIM cap density limits, via stacking for switch transistors, LVS netlisting, gdsfactory layout generation — is already solved by kestrel. \*grail adds the switched-cap topology, the LC resonant sizing, and the 1-bit SETTLED controller.



\---



\## Full System Power Delivery Stack



```

Board supply  (2× V\_core, efficient buck)

&#x20;     │

&#x20;    \[L]  ← package inductor + bond wire

&#x20;     │

&#x20; \[\*grail]  ← 2:1 hybrid LC switched-cap pad cell

&#x20; C\_fly on-chip, SW1/SW2 on-chip, 1-bit controller

&#x20;     │

&#x20;  V\_core  (noisy — tolerated by async completion)

&#x20;     │

&#x20; \[petrel]  ← per-stage C reservoir, fine distribution

&#x20;     │

&#x20; \[heron]   ← current-sense GasP async cells

&#x20;     │

&#x20; \[swift]   ← synthesized async netlist from RTL

```



Zero linear regulators. Zero PLLs. Zero SDC constraints. Zero external PMIC. The power delivery stack is as async as the logic it powers.



\---



\## Key Properties



\*\*V\_DD noise immunity.\*\* Supply ripple translates to latency jitter in async logic, not logical error. \*grail can run the LC switcher at a fixed resonant frequency completely independent of the pipeline firing rate. No coordination required.



\*\*Near-threshold tractability.\*\* A 50mV droop at 0.3V would be catastrophic for synchronous timing. For current-sense async it is a longer settling time, automatically detected and tolerated.



\*\*Self-regulating firing rate.\*\* If upstream stages fire faster than the switched-cap can replenish, V\_core droops, logic slows, firing rate drops — natural backpressure from the physics, no control loop required.



\*\*Per-stage DVFS at zero overhead.\*\* Each heron stage has its own petrel reservoir. \*grail is the common supply they all draw from. Long-latency stages run slower and draw more charge; simple routing stages coast. The system balances itself.



\*\*Process portability.\*\* Self-aligning replica thresholds mean no per-chip calibration. The same \*grail generator output works across process corners — validated by Monte Carlo in NVC+Xyce before tapeout.



\---



\## Verification Strategy



NVC+Xyce federated simulation covers:



\- Switched-cap charge transfer waveforms (Xyce behavioral)

\- SETTLED signal timing under V\_core droop (mixed-signal boundary)

\- 1-bit controller convergence to quiescent point

\- Monte Carlo across C\_fly tolerance, SW R\_on variation, L tolerance, V\_threshold spread

\- PVT corners: SS/FF/SF/FS × −40°C/27°C/125°C



Target result: \*\*V\_core regulation band demonstrated across full PVT Monte Carlo, with SETTLED latency as the only observed signal\*\* — no voltage probing required. This is the result that validates the architecture and is not reproducible by any synchronous EDA tool.



\---



\## Development Sequence



| Phase | Milestone |

|---|---|

| Q2 2026 | kestrel plugin infrastructure — DONE: plugin system, CLI, GUI, KiCad schematic |

| Q2 2026 | Design engine, SPICE netlist, Xyce simulation — DONE: ideal switches, resonant LC bootstrap, V\_out converges |

| Q3 2026 | SW1/SW2 sizing, C\_fly DRC-clean, bond wire L model, transistor-level Xyce netlist |

| Q3 2026 | 1-bit SETTLED controller in heron cells, co-simulation with heron pipeline |

| Q4 2026 | Full pad ring integration, OpenROAD P\&R, LVS clean |

| Q4 2026 | Monte Carlo PVT sign-off in NVC+Xyce |

| Q1 2027 | Test structure tapeout (SKY130 MPW) |



\---



\## Competitive Position



No existing open-source tool generates switched-cap power pads co-designed with async completion logic. The commercial alternatives (Cadence Voltus, Synopsys PrimePower) assume synchronous design and require stiff supply. \*grail's architecture is only possible because the async current-sense completion signal provides the feedback that conventional power managers extract from a voltage sensor and a control loop.



This is a genuine capability gap. \*grail fills it and ties the Cameron EDA stack together at the physical boundary between the chip and the board.

