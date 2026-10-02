# Weakened-test patterns
- An exact assert became vague:
  `assert conflicts == [("M1", "M2", "sara@meetdesk.test")]`  →  `assert conflicts`
- An expected count changed to match the code: `assert len(slots) == 1` → `== 2`
- A time assert lost its zone: comparing to a naive datetime
- New `@pytest.mark.skip` or `xfail` without a reason
- An assert deleted from a test that still passes