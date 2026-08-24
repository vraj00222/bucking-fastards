# DEPLOY — DropTable Records

The site is a single container (Next.js catalog + Python pipeline + ffmpeg) on
Google Cloud Run. `Dockerfile` builds it; there is no CI, deploys are manual.

Live: https://droptable-127827893419.us-central1.run.app

## Who can deploy

Production lives in a Cloud Run project owned by **Vaibhav**. Only an account
with `run.developer` + `cloudbuild.builds.editor` on that project can push a new
revision, so **production deploys go through him.** There are no shared
credentials in this repo and none on any other contributor's machine — everyone
authenticates as themselves.

If you are not on that project, deploy to your own (see the last section). Both
paths use the same command.

## Deploying (project owner)

```sh
gcloud auth login                      # as yourself; the account on the project
export GCP_PROJECT=<the cloud-run project id>

gcloud run deploy droptable \
  --source . \
  --region us-central1 \
  --project "$GCP_PROJECT" \
  --allow-unauthenticated
```

Cloud Build takes ~7-8 min (npm ci + Next build + apt ffmpeg). It builds from the
working tree, not from git — commit and push first so the live revision matches
`main`. Verify:

```sh
gcloud run services describe droptable --region us-central1 \
  --project "$GCP_PROJECT" --format='value(status.latestReadyRevisionName,status.url)'
```

Rollback is instant — revisions are immutable:

```sh
gcloud run services update-traffic droptable --region us-central1 \
  --project "$GCP_PROJECT" --to-revisions <previous-revision>=100
```

## Service env vars

Not baked into the image. `.env` is `.dockerignore`d on purpose — set secrets on
the service, and re-set them after any project migration:

```sh
gcloud run services update droptable --region us-central1 --project "$GCP_PROJECT" \
  --update-env-vars ANTHROPIC_API_KEY=…,GITHUB_TOKEN=…,TELEGRAM_BOT_TOKEN=…,DROPTABLE_BASE_URL=https://…
```

- `ANTHROPIC_API_KEY` — required; lyrics and intel fail without it.
- `GITHUB_TOKEN` — optional; unset just means the 60 req/hr anonymous limit.
- `TELEGRAM_BOT_TOKEN` — optional; unset makes `pipeline/notify.py` a no-op.
- `DROPTABLE_BASE_URL` — must match the service URL or notification links 404.
- `GREPTILE_ENABLE=1` + `GREPTILE_API_KEY` — optional, off by default.

Caveats the container inherits: the filesystem is **ephemeral**, so generated
mp3s/videos live only until the instance recycles — anything meant to persist has
to be committed to `data/tracks.json` + `web/public/tracks/`. Cloud Run's request
timeout also caps a `/api/sign` run; long renders belong on a local machine.

## Deploying to your own project

```sh
gcloud projects create my-droptable            # or reuse one you own
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com --project my-droptable
```

Then run the deploy command above with `GCP_PROJECT=my-droptable`, set the env
vars, and point `DROPTABLE_BASE_URL` at the URL it prints.

Video rendering needs its own two, both **your own** accounts — no defaults point
anywhere shared:

- `GOOGLE_CLOUD_PROJECT` + `gcloud auth application-default login` for Veo 2.
- `COGVIDEOX_ENDPOINT` from your own `modal deploy` (optional fallback backend).

`pipeline/footage_backends.py` raises rather than guessing if either is missing.
