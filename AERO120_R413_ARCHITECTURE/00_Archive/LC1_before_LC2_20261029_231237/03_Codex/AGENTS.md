# AERO120 Codex — R4.13 Modular Architecture

Read ../02_Design_Brief/R413_产品架构与接口冻结草案.md before modifying CAD. Keep R4.12 files immutable as baseline. This R4.13 folder is a design/interface proposal, not CAD release.

## Non-negotiables
- No giant fan box. Bottom-mounted 120mm fan, 105mm fan hole pitch, direct 124mm flange.
- Real 90-degree sealed elbow. Do not conceal unsealed side/rear gaps under decorative surfaces.
- STRIKE slash-cut aesthetic: center spine proud, upper/lower recessed slots; FRONT MASK is removable with concealed fasteners.
- At least one low-cost outlet-direction adjustment. Baseline ±12 degrees pitch with one small moveable louver core.
- Main duct stays fixed while outlet turns. Two installation modes via independent brackets on the SAME main duct. No slider system.
- Mount bracket out of fan/flange gasket stack: only one closed-cell gasket at fan interface, no blockage of inlet.
- Allow 120x25/38/50/55mm fan depths; 38mm design default.
- Protect the airpath; do not add open decorative vents through the sidewalls.
- Right/left mirror for two independent simulator cockpit sides. No center bridge.

## Engineering workflow
1. Parametric master drawing and fan/access clearance geometry.
2. Build main duct A, removable mask B, adjustable core C, upright bracket D1 and crossbar bracket D2.
3. Confirm all STEP solids valid and STL meshes watertight as appropriate; each physical part separate.
4. CAD collisions for all assembled orientations, support placement, fan thickness variants, tool access.
5. Test the A-B seam, inlet gasket, mounting bosses. Do not claim airtightness without a leak test.
6. Actual print slicing and vendor quote before promises about costs.
7. Use labeled images from REAL CAD, not conceptual renders, for manufacturing release.

## Acceptance
No production-ready label until screw/inserts, ventilation behavior, material strength, support removal, and measured cockpit constraints are checked. Preserve categorized folders for source, STEP, STL, assembly reference, QA, previews, and BOM.
