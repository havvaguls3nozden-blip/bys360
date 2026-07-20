# BYS360 Corporate Information Center services

## Canonical public entry point

New production code must import CIC operations from:

```python
from app.services.cic.service import send_task
```

`app.services.cic.service` intentionally exposes only the 13 operations used by
active production consumers. The exact contract is protected by
`tests/architecture/test_cic_service_entrypoint_v1.py`.

## Historical compatibility facade

`app.services.cic.facade` is compatibility-only. It preserves the historical
100-name import surface for possible out-of-tree callers, but active BYS360
production code must not import it. The facade must not receive new operations
or become a production dependency again.

Removing the facade is a separate compatibility decision. It requires explicit
approval and evidence that no supported out-of-tree caller still imports the
historical module.

## Canonical implementation ownership

Implementations remain in focused owner modules such as `mail_service.py`,
`scheduler_service.py`, `query_service.py`, `template_service.py`,
`celebration_service.py`, `config_context.py`, `misc_context.py`, and
`cic_context.py`. Neither `service.py` nor `facade.py` should contain duplicate
business logic.
