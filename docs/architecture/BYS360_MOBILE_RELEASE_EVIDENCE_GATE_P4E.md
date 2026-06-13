# BYS360 P4E Mobile Release Evidence Gate

P4E combines the P3 mobile response-suite evidence and P4 mobile security evidence into a single CI/handover release gate.

It validates:

- P3F mobile response suite report exists and passed.
- P4D mobile security evidence report exists and passed.
- P3 response coverage includes the main mobile feature surface.
- P4 security evidence covers the expected feature surface.
- Security probe count is at least 97.
- No secret findings exist in the evidence reports.
- Mobile API facade remains small and route decorators stay in domain modules.
- Compile, app factory, secret gate, and targeted pytest can pass.

The gate is read-only and does not create users, mutate live data, or require a real database.
