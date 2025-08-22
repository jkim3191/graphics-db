# Graphics-DB

## Instructions

### Commands

To re-build the Docker image (e.g., modified `pip` dependencies):

```bash
docker compose --profile setup up --build
```

To reset DB table and ingest data:

```bash
docker compose --profile setup up
```

To start API service

```bash
docker compose --profile api up
```
