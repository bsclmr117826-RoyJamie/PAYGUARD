# Decision log

One line per decision, newest first. A change to any contract in the design document (sections 4 and 5)
needs the code change, the edit to `docs/design.md` and a line here in the same pull request.

Format: `date | id | decision | why | sections touched | agreed by`

2026-11 | R3-CHANGE | VCS-001 pattern now also matches daraja_key and daraja_secret variable names | QA report BUG-001 example used daraja_secret and the scanner missed it | 5.1 | (fill in)
2026-11 | REBUILD | Repository restructured to the layout in design section 3.5; `scanner/` is the only rule engine; old top-level `payguard_backend/`, loose zips and the Django default CI file removed | Parts did not fit together (three data models, three severity spellings, two scoring methods) | 3, 4, 5, 7 | (fill in)
2026-11 | D5 | CI runs on GitHub Actions instead of CircleCI | Repository already on GitHub, no extra account; actions pinned to commit SHAs | 1.4, 7.6 | (fill in)
2026-11 | BUG-001 | RULE-IDE-01 retired; EP-001 in `scanner` (project level, once per folder) replaces it | Regex fired on every ordinary line; scanner version has tests | 5.1 | (fill in)
2026-11 | D1-D4, D6-D10 | Defaults from design section 1.4 adopted | Nobody blocked while the team reviews | 1.4 | (fill in)
