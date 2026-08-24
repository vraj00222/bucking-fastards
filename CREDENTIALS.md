# CREDENTIALS — shared-access teardown, 2026-08-24

During the hackathon this repo was built on a mix of two people's cloud accounts.
That is now undone: **each contributor authenticates as themselves, and no
account's credentials sit on anyone else's machine.** This file records what was
removed and what the affected owner still needs to do.

## Why

Two of Vaibhav's credentials were on Vraj's laptop, and his infrastructure was
hardcoded into the pipeline. Convenient for a two-day build, wrong to keep: a
long-lived key on someone else's disk can't be audited, rotated, or scoped, and
it ends up in shell history and tool logs.

## Removed from Vraj's machine (2026-08-24)

| What | Where it was | Action taken |
|---|---|---|
| Bedrock IAM key (`AKIA…BRHN`) + secret | `~/.claude/settings.json`, plaintext | Deleted, with the `AWS_REGION` / `CLAUDE_CODE_USE_BEDROCK` / `ANTHROPIC_DEFAULT_*_MODEL` vars that used it |
| Same key echoed into tool logs | two Claude session transcripts | Overwritten in place |
| `vaibhav@kleo.network` gcloud login | `~/.config/gcloud` credential store | `gcloud auth revoke` — token revoked server-side, local creds gone |
| Application Default Credentials | quota-projected to his Cloud Run project | `gcloud auth application-default revoke` |
| gcloud CLI logs naming the account | `~/.config/gcloud/logs` | Deleted |

`gcloud auth list` on that machine now shows one account, `vrajpatel00222@gmail.com`.

## Removed from this repo

- `pipeline/footage_backends.py` no longer defaults to his GCP project for Veo 2,
  and no longer hardcodes his Modal endpoint for the CogVideoX backend. Both are
  now `GOOGLE_CLOUD_PROJECT` / `COGVIDEOX_ENDPOINT`, and the backends **raise
  instead of silently falling back to infrastructure the caller doesn't own.**
- `.env.example` documents both as "your own".
- No credentials were ever committed — `.env` is gitignored and
  `.dockerignore`d. `data/telegram_subscribers.json` is now gitignored too; it
  held a real Telegram chat ID.

## Action required — Vaibhav

1. **Rotate the Bedrock IAM key.** It sat in plaintext on another machine and was
   read into tool logs, so treat it as disclosed regardless of the cleanup above:
   IAM → Users → Security credentials → deactivate, then delete, that access key.
   Nothing in this repo needs it — Claude access here is `ANTHROPIC_API_KEY`.
2. **Confirm the gcloud revoke** on your side (Google Account → Security →
   Third-party access) and re-auth wherever *you* actually work.
3. **Production deploys now route through you** — you hold the only account with
   `run.developer` on the Cloud Run project. See [DEPLOY.md](DEPLOY.md).
4. If you'd rather hand production off entirely, either grant a contributor
   `run.developer` + `cloudbuild.builds.editor`, or let them redeploy into their
   own project and repoint `DROPTABLE_BASE_URL` — the container is
   project-agnostic, only the env vars are per-deployment.

## Going forward

Nobody shares a key to reach a shared service. Grant an IAM role on the project
instead — revocable, per-person, and it shows up in the audit log. For anything
that genuinely needs a static credential in production, put it on the Cloud Run
service, not in a dotfile that syncs to a laptop.
