# Scientific verification rerunner v1.0.0 — test receipt

Date: 2026-08-14  
Software DOI: `10.5281/zenodo.21939447`  
Related compendium DOI: `10.5281/zenodo.21919563`

## Result

The standalone publication-specific implementation passed its deterministic
smoke suite and all three bounded real-data fitting routes. Computed results are
written before frozen expected evidence is loaded by the separate verification
command.

| Route | Real computation | Reference result |
|---|---|---|
| `matbench-importance` | Full Matbench band-gap fold; fixed MLP baseline and genuine retrained removal of feature 0 | Reference differences were zero at `1e-12` |
| `mp-viability` | Frozen Materials Project bulk/common-lane cell; Ridge baseline plus 30 target-permutation null refits | Reference differences were zero at `1e-12` |
| `spatial-gil` | Frozen 256-record JARVIS cohort; four folds of BASE+C Ridge plus three paired null refits per fold | Reference differences were zero at `1e-12` |

The portable declared scientific acceptance tolerance is `1e-10`. The tighter
`1e-12` statement describes the observed reference workstation result; it is not
the cross-platform pass threshold.

Automated unit suite: `4 passed`.

## Standalone input test

The acquisition helper was exercised from an empty working directory:

- Matbench regenerated all 106,113 rows of the 142-feature cache. Source, input,
  feature-array and feature-name identities matched the frozen values exactly.
- JARVIS downloaded 40,811,489 bytes from the fixed official Figshare endpoint,
  matched the declared archive hash and passed the four-fold Spatial GIL route.
- The Materials Project helper verified the snapshot, cohort-membership and
  split-membership hashes before computation.

No route required a private code path, stored credential or production
Systemica/Geatomica component.

## Input identities

- Materials Project snapshot:
  `e02083989c5f0dc029408eaf4b8634fe5557241a06e8e3ebd10c27693fa26b62`
- JARVIS archive:
  `d4c64660e9e1fa45c82bd8868a96ec10162195eed69636445972c05550d8d0d6`
- Matbench feature array:
  `6cdf69d17d086b14b7a4a54637bc731ba2fdc26f2c8a136956e9b3fd649db8b2`

Third-party provider inputs are not included in the release archive.

## Claim boundary

This receipt establishes that the public kernels recompute selected frozen
fitted results without the private production runtime. It does not establish a
full re-execution of every published scientific unit, external replication,
peer review, physical qualification or engineering authority.
