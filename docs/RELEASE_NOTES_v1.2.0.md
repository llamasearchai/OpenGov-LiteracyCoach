# OpenGov-Literacy Coach v1.2.0

Author: Nik Jois

## Highlights

- Mock Mode: offline deterministic behavior via `LITCOACH_MOCK` for transcription, TTS, chat, and embeddings.
- Gateway short-circuits in mock mode for agent/assessment and provides stable stubbed results.
- CI pipeline (GitHub Actions) to run tests on PRs/pushes.
- Release workflow for PyPI and Docker (secrets-driven).
- Developer tooling: Makefile targets, test requirements, release script.
- Visual polish: Logo prominently added to README; `.env.example` for safe configuration.

## Breaking Changes

- None.

## Upgrade Notes

- If using mock mode, set `LITCOACH_MOCK=true` to run the gateway offline.
- Review `.env.example` for recommended configuration placeholders.

## Thanks

Thanks to contributors and reviewers for testing and feedback.

