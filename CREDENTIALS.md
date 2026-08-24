# CREDENTIALS — shared-access teardown, 2026-08-24

During the hackathon this project was built across two contributors' cloud
accounts. That is now undone: **everyone authenticates as themselves, and no
account's credentials sit on anyone else's machine.**

## Why

Two credentials belonging to one contributor were present on the other's laptop,
and that contributor's infrastructure was hardcoded into the pipeline. Convenient
for a two-day build, wrong to keep: a long-lived key on someone else's disk can't
be audited, scoped, or rotated on its owner's terms, and it leaks into shell
history and tool logs.

## Removed (2026-08-24)

| What | Where it lived | Action |
|---|---|---|
| Bedrock IAM access key + secret | agent config, plaintext | Deleted, along with the region and model-id vars that used it |
| Same key echoed into tool logs | local agent session logs | Overwritten in place |
| Borrowed `gcloud` login | local gcloud credential store | `gcloud auth revoke` — token revoked server-side, local copy gone |
| Application Default Credentials | quota-projected to the other account's project | `gcloud auth application-default revoke` |
| CLI logs naming that account | local gcloud logs | Deleted |

The machine's `gcloud auth list` now shows a single account: its owner's.

## Removed from this repo

- `pipeline/footage_backends.py` no longer defaults to anyone's GCP project for
  Veo 2, and no longer hardcodes a personal Modal endpoint for the CogVideoX
  backend. Both are now `GOOGLE_CLOUD_PROJECT` / `COGVIDEOX_ENDPOINT`, and the
  backends **raise rather than silently reaching for infrastructure the caller
  doesn't own.**
- `.env.example` documents both as "your own".
- No credential was ever committed — `.env` is gitignored and `.dockerignore`d.
  `data/telegram_subscribers.json` is gitignored too; it held a real chat ID.

## Action required — Vaibhav (key owner)

1. **Rotate the Bedrock IAM key.** It sat in plaintext on another machine and was
   read into tool logs, so treat it as disclosed regardless of the cleanup above:
   IAM → Users → Security credentials → deactivate, then delete, that access key.
   Nothing here needs it; Claude access in this project is `ANTHROPIC_API_KEY`.
2. **Confirm the revoke** at Google Account → Security → Third-party access, and
   re-auth wherever you actually work.
3. **Production deploys route through whoever holds the Cloud Run project** — see
   [DEPLOY.md](DEPLOY.md). To hand production off, grant a contributor
   `run.developer` + `cloudbuild.builds.editor`, or let them redeploy into their
   own project and repoint `DROPTABLE_BASE_URL`. The container is
   project-agnostic; only the env vars are per-deployment.

## Going forward

Nobody shares a key to reach a shared service. Grant an IAM role on the project
instead — revocable, per-person, and it lands in the audit log. Anything that
genuinely needs a static credential in production goes on the Cloud Run service,
never in a dotfile that syncs to a laptop.
