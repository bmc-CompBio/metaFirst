# metaFirst

A metadata-first Research Data Management system for life sciences. Metadata is collected centrally via RDMP-guided forms; raw data remains on user machines and lab storage.

## Core Ideas

- **Metadata-first, sample-centric** — samples are the unit of organization; metadata is captured before or during data acquisition
- **RDMPs as enforceable schemas** — Research Data Management Plans define fields, roles, permissions, and visibility
- **No central control of raw data** — files stay where they are; the system tracks references, not copies
- **Event-driven ingest** — file watchers detect new data and prompt for metadata entry in the browser
- **Federated discovery** — cross-project search operates on metadata only; raw data is never exposed

## Status

Active proof-of-principle. Core functionality is implemented; some features (releases, discovery UI) are planned.

## Quick Start

### Supervisor (group leader / lab admin)

```bash
# Clone and set up
git clone <repository-url>
cd metaFirst/supervisor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Seed demo data
python ../demo/seed.py

# Start backend API
uvicorn supervisor.main:app --reload --port 8000

# Start web UI (in a new terminal)
cd ../supervisor-ui
npm install
npm run dev
```

- API docs: http://localhost:8000/docs
- Web UI: http://localhost:5173
- Demo users: alice, bob, carol, david, eve (password: `demo123`)

### User (researcher / data steward)

The ingest helper is optional. It watches local folders and creates pending ingests when new files appear. Raw data stays on your machine.

```bash
cd ingest_helper
pip install -r requirements.txt
cp config.example.yaml config.yaml
# Edit config.yaml with your supervisor URL, credentials, and watch paths
python metafirst_ingest.py config.yaml
```

See [ingest_helper/README.md](ingest_helper/README.md) for configuration details.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — system design, components, interaction flows
- [ingest_helper/README.md](ingest_helper/README.md) — ingest helper configuration and usage
- [supervisor/supervisor/discovery/](supervisor/supervisor/discovery/) — federated discovery index module
