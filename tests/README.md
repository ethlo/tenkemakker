# Fraction integration regression checks

Run from the repository using Node.js 18+:

```sh
node tests/worker-fraction.cjs
node tests/fraction-integration.cjs
```

The browser suite needs an **existing** Playwright package and browser. It does not
install dependencies or browsers. If Playwright lives outside the repository, set
`NODE_PATH` to that installation's `node_modules` directory. Set
`CHROMIUM_CHANNEL=chrome` to use an existing Chrome installation; otherwise the
suite uses Playwright's existing Chromium. Set `TEST_SCREENSHOTS` to an output
directory for screenshots; no screenshot files are generated in the repo by default.

The suite opens the standalone HTML and also starts/stops a temporary loopback HTTP
server on an automatically assigned port. Health/model responses, artifact sampling
and browser speech are simulated. There are no live AI calls, credentials, microphone
recordings or persistent pupil records. External Google Fonts may load as in the app.

Coverage:

- Optional lab / Task start screen; original three tasks and additional local task bank.
- Exact fraction answers across both flows; model amounts and independent transfer task.
- Stale equivalent-feedback regression; conversation reading position and new replies.
- Parent/teacher scope, no duplicated points or main-task activity, restart and export.
- Missing/old/future/disabled Worker capability, valid response version, mismatched
  response, failure/timeout, original backend hints, and artifact fallback.
- Late health and model responses preserve input/focus across views.
- Explicit speech with automatic read-aloud off; missing, remote or wrong-language
  voices; local speech errors displayed in the active lab.
- Norwegian/English × light desktop/dark 390px mobile; runtime errors and overflow.
- Worker auth requirement, capabilities, sequence response version, prompt language,
  task bounds, missing key and legacy hint route (model mocked).

These checks do not prove live-model quality, real microphone behavior, learning
outcomes, production deployment or CI success. The PR does not configure hosted CI.
