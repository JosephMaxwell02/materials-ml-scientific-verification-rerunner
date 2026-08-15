# v1.0.1 repository maintenance receipt

## Scope

- Repository: `JosephMaxwell02/materials-ml-scientific-verification-rerunner`
- Base tag and commit: `v1.0.0` / `b1661bc6e51b835609eb33785faf58bb2b7bb5b6`
- Historical sealed archive: `MATERIALS_ML_SCIENTIFIC_VERIFICATION_RERUNNER_V1_0_0_20260814.zip`
- Historical archive SHA-256: `79296314a170db9edc611e5bf9312d681279b86f2e9c614264cbbbccaabd7a1c`

## Maintenance changes

- Declared canonical LF text and explicit binary handling in `.gitattributes`.
- Regenerated `MANIFEST.sha256` for the canonical v1.0.1 Git tree.
- Added clean-checkout manifest verification, automated tests and the existing deterministic
  mechanism smoke check to CI.
- Added a short quick-verification path to `README.md`.
- Added exact instructions for correcting creator ORCID and affiliation on the existing
  Zenodo record without creating a new file version.

The v1.0.0 clean-clone discrepancy was newline normalisation only. It did not affect
scientific values, verification outputs or the integrity of the sealed v1.0.0 ZIP.

## Verification

- Canonical Git-tree manifest: `39` files, PASS.
- Automated unit suite: `4 passed`.
- Deterministic mechanism smoke check: PASS.
- Frozen expected outputs, receipts, protocols and scientific code changed: `0`.
- Secret/private-path scan: PASS.
- Historical v1.0.0 archive SHA-256 recheck: PASS.

## Claim boundary

CI exercises tests and a synthetic mechanism smoke check. It does not reproduce the full
publication campaigns and requires no Materials Project credentials or large external data.

No scientific claims or archived v1.0.0 scientific objects were changed.
