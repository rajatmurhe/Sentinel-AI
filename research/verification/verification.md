# Integration and research verification — 20 October 2026

## Completed locally

- Built the React frontend with npm's lockfile.
- Seven tests passed against an isolated PostgreSQL 14 database, including a legacy-schema upgrade that preserved existing records and was safe to run twice.
- The same integration flow passed on SQLite (PostgreSQL-only test excluded).
- Authenticated exact-vector submissions preserve all entered features in ResearchInteraction.
- Eight-turn adaptive simulation records previous defence and previous/current behaviour consistently.
- Tested authorization for research routes, saved tables, PNG downloads, invalid inputs and nonexistent artifacts.
- Browser login, SOC dashboard and eight-turn action-conditioned attack completed against the built frontend and real PostgreSQL backend. Screenshot: adaptive-dashboard.png.
- Browser controls were disabled in Work settings before visual research-page/hosted verification finished; API verification continues separately.
- Direct dependency pins resolve from the package index and match locally tested Python 3.11 libraries. The deployment CI builds and tests independently on Linux.

## Research results

Five enhanced-protocol seeds completed on all 61,473 CERT test rows per seed. All five selected log-transformed features plus frozen training-user deviations using validation average precision. Thresholds maximize validation F1 within a validation FPR ceiling. No test-label fitting or per-test threshold selection is performed.

Full-model F1 changed from 0.006721 to 0.020362 and ROC-AUC from 0.754084 to 0.798708. However, enhanced Static SentinelAI F1 is 0.020725 and enhanced IF ROC-AUC is 0.833692. Absolute performance remains weak. No consistent or statistically significant superiority is established. The independent synthetic response environment is unchanged and its repeated outcomes must not be credited to the CERT preprocessing change.

Original and enhanced outputs are preserved separately. Updated figures are derived from the saved CSVs. The original test period had already been inspected, so this is exploratory follow-up, not independent confirmatory evaluation.

## Scope limits

The live session detector remains a clearly labelled synthetic demonstration detector. Saved CERT joblib models expect the user-day schema and are research artifacts, not automatically interchangeable session models. Application actions are decisions/recommendations; endpoint enforcement is simulated. Existing cryptography modules are placeholders, not validated ML-KEM/ML-DSA implementations.

Frontend npm audit still reports inherited development-tool dependencies requiring breaking upgrades (Tailwind/Vite); these were not force-upgraded in this research change. Deployment only serves built static assets, not the Vite dev server.
