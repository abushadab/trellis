# Seam Kinds

A seam is a place where two parts meet. Defects hide there, because each side can look correct on its own.

This file defines shared vocabulary only. How each role uses it is in that role's guidance.

1. **Process or service boundary:** one service calls another, or a client calls a runner.
2. **Durable state:** a saved phase, marker, or intent, or a pair of writes that must agree.
3. **Shared hold:** a lock, claim, pin, lease, or pooled connection.
4. **Changed shared mechanism:** a check, record, parser, or helper that existing flows also use.
5. **Caller input:** a query key, header, path segment, or body field.
6. **Inherited state:** anything copied in, such as a cloned database, that can act before checks run.
7. **Test expected result:** an assertion that claims to prove a boundary.

A seam may have unchanged code or code from an earlier slice on its other side.
