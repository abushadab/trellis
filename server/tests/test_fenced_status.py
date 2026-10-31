from trellis_mcp.sessions import parse_decisions, parse_turn_status


FENCED = """Done.

```text
## Turn Status
Status: needs_decision
Summary: one question
Artifacts: /tmp/a.md

## Decision needed
Q1: Pick one?
Options: A) x B) y
Recommendation: A
Kind: technical
```
"""


def test_fenced_turn_status_and_decision_parse_cleanly():
    status = parse_turn_status(FENCED)
    assert status["status"] == "needs_decision"
    assert status["artifacts"] == ["/tmp/a.md"]
    assert parse_decisions(FENCED)[0]["kind"] == "technical"
