# App: mini-Hotstar control-path API

A small FastAPI service standing in for the API calls the Hotstar app makes
before video starts: is the match live, what is the score, may this viewer
play, what is on the home page. Video never goes through it (see `video/`).

Each endpoint has a deliberate cost profile, so the load tests can show how
different kinds of traffic scale:

| Endpoint | Method | Work | Cost | Why it is there |
|----------|--------|------|------|-----------------|
| `/` | GET | constant JSON | tiny | "match live" check; proves the ALB works |
| `/score` | GET | constant JSON, `Cache-Control: public, max-age=5` | tiny | identical for every viewer, so a CDN can cache it (E4) |
| `/play` | POST | HMAC token check + PBKDF2 (20 000 rounds) | heavy, ~20 ms CPU | login + DRM signing; the path that must survive (E5) |
| `/home` | GET | PBKDF2 (5 000 rounds), or static rails in panic mode | medium | personalisation, the first thing to drop under load (E5) |
| `/health` | GET | `{"status": "ok"}` | none | ALB health check |

Every response carries `X-Instance-Id` (and most bodies an `instance` field),
so you can see the load balancer spreading requests over servers.

## Requests and responses

```bash
curl -s $URL/
# {"status":"Match live, stream available","instance":"i-0abc..."}

curl -s $URL/score
# {"match":"IND vs AUS","score":"287/4","overs":"45.2","updated":1794300000,"instance":"i-0abc..."}

# /play needs token = hex HMAC-SHA256(PLAY_SECRET, user_id)
TOKEN=$(python -c "import hmac,hashlib;print(hmac.new(b'group4-demo-secret',b'u1',hashlib.sha256).hexdigest())")
curl -s -X POST $URL/play -H 'Content-Type: application/json' -d "{\"user_id\":\"u1\",\"token\":\"$TOKEN\"}"
# {"playback_url":"https://cdn.example.com/live/master.m3u8?exp=...&sig=...","expires":...,"instance":"i-0abc..."}
# wrong token -> 401 {"detail":"invalid token"}

curl -s $URL/home
# {"rails":[...4 rails...],"personalised":true,"panic":false,"instance":"i-0abc..."}
```

The secret is a demo value shared with the k6 scripts (`PLAY_SECRET`); it
protects nothing real.

## Panic mode

`panic.py` reads the SSM parameter named in `PANIC_PARAM`
(`/group4-hotstar/panic-mode`) every 5 seconds in a background thread. When
it is `on`, `/home` returns two static rails with no CPU work. If the read
fails (throttling, no network) the last value is kept; the app never crashes
because of the flag. Without `PANIC_PARAM` the `PANIC_MODE` environment
variable is used instead (handy locally).

```bash
aws ssm put-parameter --name /group4-hotstar/panic-mode --value on --overwrite
```

## Settings (environment variables)

| Variable | Default | Set by |
|----------|---------|--------|
| `PLAY_SECRET` | `group4-demo-secret` | – |
| `PLAY_ITERATIONS` | 20000 | Terraform `play_iterations` |
| `HOME_ITERATIONS` | 5000 | – |
| `PANIC_PARAM` | unset | Terraform (SSM parameter name) |
| `PANIC_POLL_SECONDS` | 5 | – |
| `PANIC_MODE` | `off` | only used without `PANIC_PARAM` |
| `AWS_REGION` | – | Terraform |
| `INSTANCE_ID` | from instance metadata (IMDSv2), else hostname | tests |

## How it gets onto EC2

No AMI baking and no container registry: `infra/modules/compute` renders
`user_data.sh.tftpl` with every `app/*.py` file and `requirements.txt`
embedded (base64), plus the settings above as `/etc/hotstar.env`. On boot
the script installs Python 3.12, creates a venv, installs the pinned
requirements and starts `uvicorn main:app --workers 2` as a systemd service
on port 8000. The boot log is `/var/log/hotstar-boot.log`
(`BOOT_START` / `BOOT_DONE` timestamps). User data must stay under 16 KB;
Terraform checks this before apply.

`scripts/measure_boot.py` times one new server from request to healthy
target, which is the floor for how fast reactive scaling can react.

## Run locally

```bash
cd app
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest                                          # unit tests
INSTANCE_ID=local uvicorn main:app --port 8000  # then curl localhost:8000/
```

The `Dockerfile` builds the same service as a container (Python 3.12 slim,
non-root, 2 workers) for anyone who prefers Docker locally; EC2 does not use it.
