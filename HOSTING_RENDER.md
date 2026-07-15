# Host the dashboard publicly with Render

This repository is deployment-ready for a public Render URL.

## Fast free deployment

1. Create a GitHub repository.
2. Upload every file in this project folder to the repository root.
3. Sign in to Render and select **New → Blueprint**.
4. Connect the GitHub repository.
5. Render detects `render.yaml`; select **Apply**.
6. Wait for the Docker build and health check to complete.
7. Open the generated `onrender.com` URL.

The included Blueprint creates one free Docker web service in the Virginia region.

## Important free-tier behavior

- The service can sleep after 15 minutes without inbound traffic.
- The first visitor after sleep might wait roughly one minute.
- The SQLite database is ephemeral on the free plan.
- On a restart, the app automatically rebuilds its synthetic history and resumes the live feed.

This is acceptable for a public portfolio demonstration because the project intentionally uses synthetic data.

## Persistent always-on option

Upgrade the Render service to a paid instance and attach a persistent disk:

- Mount path: `/app/data`
- Environment variable: `DATA_DIR=/app/data`
- Keep instance count at one because SQLite and the in-process simulator are single-instance components.

## Manual Render service settings

If you do not use the Blueprint:

- Service type: Web Service
- Runtime: Docker
- Dockerfile path: `./Dockerfile`
- Health check path: `/healthz`
- Environment variable: `START_SIMULATOR=1`
- Environment variable: `SIM_INTERVAL=2`

## Production command

The Docker image runs:

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:server
```
