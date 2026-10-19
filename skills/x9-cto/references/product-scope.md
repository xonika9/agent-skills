# Product scope and supporting machinery

The accepted outcome and constraints come from the user and owning canon, not
from the chosen implementation or qualification method. Supporting
infrastructure belongs in scope only when it implements that outcome or is
necessary for an accepted security, data-integrity, recovery, or resource
boundary. State that property independently of the mechanism and connect the
work to evidence of the need; "the monitor must pass" is not such a property.

When supporting machinery blocks progress, distinguish a failed product
property from missing evidence. Before repairing or extending it, compare the
repair with omitting optional machinery or obtaining the required evidence by a
simpler existing means. State sufficient evidence and its limits; convenience
does not establish safety. Distinguish effective technical controls from tools
that only observe them: failure of an observer alone proves neither failure nor
safety of the protected property. A mechanism that actively enforces protection
must not be discarded as mere observation.

If the user or owning contract explicitly requires the mechanism or evidence
method, propose a scoped change without waiving it. Otherwise a method change
within existing authority is an implementation choice, not a new approval gate.
Security boundaries require effective technical controls, not instructions or
hoped-for behavior. Criticism and acceptance stay scoped to the accepted outcome
and constraints; unrelated improvements do not become release blockers. These
rules do not resume frozen work, reset budgets, waive required evidence, or grant
authority to build supporting machinery.
