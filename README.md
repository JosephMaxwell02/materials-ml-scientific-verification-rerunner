# Materials ML Failure Analysis — Publication-Specific Scientific Verification Rerunner

Version **1.0.0** · DOI **10.5281/zenodo.21939447**

This standalone publication-specific implementation recomputes representative
claim-bearing scientific kernels. It does not rerun every unit in the sealed
campaigns. The accepted papers, evidence and headline readouts are preserved in
the related research compendium at <https://doi.org/10.5281/zenodo.21919563>.

The package excludes the production Systemica/Geatomica runtime, recovery
controller, policy engine, private estate paths, credentials and commercial
connectors.

## Quick verification

```bash
git clone https://github.com/JosephMaxwell02/materials-ml-scientific-verification-rerunner.git
cd materials-ml-scientific-verification-rerunner
python tools/install_reference_environment.py
python -m pip install pytest==8.4.2
python tools/verify_manifest.py
python -m pytest -q
python run.py smoke
```

This path checks repository integrity, automated tests and deterministic scientific
mechanisms. It does not rerun the complete publication campaigns. Real-data acquisition and
bounded fitting instructions remain in [INPUTS.md](INPUTS.md).

The installer preserves every version in `environment/requirements.txt`. It installs
`matbench==0.6` and `matminer==0.10.1` without dependency resolution because their
historical metadata conflict with the frozen, receipted `matminer==0.10.1` and
`pandas==3.0.2` versions. Their public runtime dependencies are installed separately.

## Routes

| Route | Publication relationship | Bounded computation |
|---|---|---|
| `matbench-importance` | Supports Paper 1 | Official Matbench fold, fixed MLP baseline and genuine retrained feature removal |
| `mp-viability` | Supports Paper 2 | Frozen Materials Project cell, Ridge baseline and 30 target-permutation null fits |
| `spatial-gil` | Supports the wider compendium and monograph; it is **not Paper 3** | Frozen JARVIS cohort, structural features, four-fold Ridge and paired null fits |

Paper 3 of the trilogy concerns evidence availability, admission, replay and
bounded authority. It is not misrepresented here as the Spatial GIL experiment.

## Executable states

There are two executable scientific modes and one explicit unavailable state:

```powershell
python run.py smoke
python run.py compute --route ROUTE [--cache PATH | --dataset PATH]
python run.py verify --receipt outputs\COMPUTED_RECEIPT.json
python run.py full --route ROUTE
```

- `smoke` runs small deterministic mechanism checks; it is not a published-claim rerun.
- `compute` performs a bounded fitting calculation without loading frozen expected outputs.
- `verify` separately compares a previously computed receipt with accepted evidence.
- `full` writes a structured `FULL_PUBLICATION_CAMPAIGN_NOT_BOUND` refusal receipt.

This separation makes the anti-circularity boundary visible: the expected tables
are unnecessary during computation and are consulted only by `verify`.

## Inputs and environment

See `INPUTS.md` for exact acquisition and verification commands. Third-party
provider data remain outside the package; receipts record only filename, byte
count and SHA-256 identity. No credentials are stored.

The frozen reference environment is recorded in `environment/requirements.txt`.
Observed agreement on the reference workstation was exact at `1e-12`; the
portable declared scientific acceptance tolerance is `1e-10`.

## Rights and claim boundary

The included publication-specific code may be inspected and executed for
non-commercial scientific verification under `LICENSE.md`. The licence does not
cover the private production runtime, third-party data, commercial reuse or
deployment. Computational agreement is not external replication, peer review,
physical validation or engineering authority.
