# metaFirst

A proof-of-principle "metadata-first" Research Data Management system for life sciences.

## Core Ideas

- **Metadata is centralized** — a single supervisor service is the source of truth
- **Raw data stays distributed** — files remain on user machines, referenced by path
- **RDMPs govern everything** — fields, roles, permissions, and visibility are RDMP-defined
- **Federation via metadata** — cross-project discovery indexes metadata only, never data

## Status

This is an active proof-of-concept. Core functionality is implemented; some features (releases, discovery UI) are planned.

## Quick Start

```bash
cd supervisor && pip install -e ".[dev]"
python demo/seed.py
uvicorn supervisor.main:app --reload --port 8000
```

API docs at http://localhost:8000/docs. Demo users: alice, bob, carol, david, eve (password: `demo123`).

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — system design, components, and interaction flows
- [ingest_helper/README.md](ingest_helper/README.md) — file watcher setup and usage
- [supervisor/supervisor/discovery/](supervisor/supervisor/discovery/) — federated discovery index module
