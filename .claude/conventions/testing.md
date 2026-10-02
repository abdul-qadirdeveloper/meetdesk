
# Testing conventions

- Put shared fixtures in tests/conftest.py.
- Small hand-written CSV fixtures live in tests/fixtures/.
- Test names describe behaviour: test_back_to_back_meetings_do_not_conflict.
- Use fixed dates in the week of 2026-09-28; never datetime.now() in tests.