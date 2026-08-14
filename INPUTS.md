# Input acquisition and verification

Keep all third-party inputs outside the extracted package. The helper stores no
API keys or credentials.

## Matbench importance route

```powershell
python tools/acquire_inputs.py matbench-cache --output ..\inputs\matbench
python run.py compute --route matbench-importance --cache ..\inputs\matbench
python run.py verify --receipt outputs\MATBENCH_IMPORTANCE_COMPUTED_RECEIPT.json
```

The helper obtains the Matbench v0.1 task through the official package and
generates the declared 142-feature cache locally. The reference task contains
106,113 rows. First-time feature generation may take several minutes.

## Materials Project viability route

Exact replay requires the three historical files used by the sealed campaign:

- `materials_project_snapshot.csv`
- `COHORT_MEMBERSHIP.csv`
- `SPLIT_MEMBERSHIP.csv`

The historical freeze is not redistributed. An outside researcher may request
author-facilitated access where Materials Project terms permit, obtain a matching
archived provider object if one becomes available, or conduct a new non-identical
study through the current Materials Project API. A current API download must not
be described as an exact replay of the historical snapshot.

```powershell
python tools/acquire_inputs.py verify-mp-viability --directory ..\inputs\mp
python run.py compute --route mp-viability --dataset ..\inputs\mp\materials_project_snapshot.csv
python run.py verify --receipt outputs\MP_VIABILITY_COMPUTED_RECEIPT.json
```

## Spatial GIL route

```powershell
python tools/acquire_inputs.py spatial-gil --output ..\inputs\jarvis
python run.py compute --route spatial-gil --dataset ..\inputs\jarvis\jdft_3d-12-12-2022.json.zip
python run.py verify --receipt outputs\SPATIAL_GIL_COMPUTED_RECEIPT.json
```

The helper downloads the fixed 12 December 2022 JARVIS-DFT 3D archive from the
official NIST/JARVIS Figshare endpoint. Expected SHA-256:
`d4c64660e9e1fa45c82bd8868a96ec10162195eed69636445972c05550d8d0d6`.

Provider pages:

- Matbench: <https://github.com/materialsproject/matbench>
- Materials Project: <https://docs.materialsproject.org/downloading-data/how-do-i-download-the-materials-project-database>
- JARVIS: <https://pages.nist.gov/jarvis/>
- JARVIS-DFT 3D DOI: <https://doi.org/10.6084/m9.figshare.6815699>
