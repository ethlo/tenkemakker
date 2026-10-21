# Connected fraction learning — verification

Date: 21 October 2026. Implemented on `codex/fraction-connected-learning`, based
on PR #5 head `a0b1eeb`; current main `d212a3d` was merged into the review branch.
PR #5 remained open during validation. Its integration fixes are included here.
No user work in the original checkout was changed.

## Local checks

- `node tests/worker-fraction.cjs`: Worker capability, unchanged sequence contract,
  default auth requirement, language, task bounds and legacy route pass.
- `node tests/fraction-integration.cjs`: 178 checks pass, including main tasks,
  isolated lab scores, parent/teacher scope, delayed replies, old/new/mismatched
  Worker responses, artifact fallback and local speech adapters.
- `node tests/fraction-connected.cjs`: 561 checks pass, including all 2–24
  denominator choices, unchanged quantities, keyboard linkage, support snapshots,
  unresolved progression, independent transfer, version 2 export and isolated print.
- Norwegian and English, 390px dark and desktop light; no horizontal overflow or
  runtime errors. Model, parent and print screenshots were visually reviewed.
- Chrome 155 discovers installed local voices including Nora (nb-NO) and English
  voices. The real read action was exercised; audio quality was not independently
  listened to or rated. Missing/remote/wrong-language voices and speech errors are
  tested with adapters. No microphone was accessed.
- The localhost preview was opened in the Codex browser and the Brøkverksted tab
  selected. Code and Worker checks do not establish production deployment.

Existing Playwright and Chrome were used; no dependencies or browser were installed.
Commands use NODE_PATH for the bundled runtime and CHROMIUM_CHANNEL=chrome.

## Still open

- Human review of the preview and code.
- The facilitated 4–6 participant pilot and later task (PILOT.md); no participants
  were tested and no learning effects are claimed.
- Live Claude response quality, publication, Worker rollout and authenticated
  production checks. There was no push to main and no change to access settings.
