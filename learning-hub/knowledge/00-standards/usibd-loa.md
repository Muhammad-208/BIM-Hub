---
title: USIBD Level of Accuracy (LOA) — scan-to-BIM accuracy
tags: [scan-to-bim, point-cloud, loa, as-built, accuracy, survey]
source: USIBD Level of Accuracy (LOA) Specification Guide (summary; check the current edition before contractual use)
---
# USIBD Level of Accuracy (LOA)

LOA states **how accurate** existing-conditions data is — separate from LOD, which states **how developed** an element is.
Two values are specified per element class:

- **Measured accuracy** — of the survey/scan data itself (registration + instrument error).
- **Represented accuracy** — of the model/drawing made from that data (always ≤ the measured accuracy).

Ranges are stated at the **95 % confidence level (2σ)**:

| LOA | Range (upper – lower) | Typical use |
|---|---|---|
| LOA 10 | user defined, > 5 cm | massing, rough planning |
| LOA 20 | 5 cm – 15 mm | general architectural as-built |
| LOA 30 | 15 mm – 5 mm | detailed architecture, MEP routing, structure |
| LOA 40 | 5 mm – 1 mm | fabrication interfaces, plant/industrial |
| LOA 50 | 1 mm – 0 | high-precision / metrology |

## How the hub uses it
- `project.yaml → params.loa_measured / loa_represented` (scan-to-bim projects).
- Scope matrix assigns an LOA per element class and zone — e.g. walls/slabs LOA 30, ceilings LOA 20, plant LOA 40.
- Deviation analysis (stage P4) checks the represented LOA: % of checked surfaces within the upper range, target ≥ 95 %.
- Every modelled element carries a verification state (Scanned / Assumed / From drawings) — LOA applies only to Scanned.
- The handover includes an accuracy & limitations statement (occlusions, areas not scanned, assumed elements).
