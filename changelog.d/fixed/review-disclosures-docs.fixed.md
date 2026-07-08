Disclosed previously silent simplifications surfaced by the 2026-07 external
review: the dual reading of the `salaire_brut` input (declared salary for the
IR chain vs gross salary for CSG/CRDS), CSG déductible computed but not
deducted from `revenu_net_imposable`, the missing AF complément dégressif
(hard modulation cliffs), family benefits paid gross of CRDS, the AF age-14
majoration timing, and the veuf/veuve quotient-familial case — all now named
in `modelled_policies.yaml`, `docs/coverage.md` and the variable docstrings.
Also fixed stale documentation: test counts and MVP status in CLAUDE.md,
ASF/pensions alimentaires missing from README and docs/index.md, the AF
plafond parameter descriptions (the stored base is a zero-child base), the
pyproject Homepage URL, and docs/_toc.yml now publishes the coverage map.
