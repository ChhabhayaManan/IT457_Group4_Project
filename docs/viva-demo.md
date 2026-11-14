# Viva demo script (about 10 minutes)

Viva window: 16–20 Nov. Rehearse once on 15 Nov with the stack up, then
destroy it. On viva day, apply `base.tfvars` **at least 15 minutes before**
the slot and run the smoke test.

```bash
terraform -chdir=infra apply -var-file=experiments/base.tfvars -var fixed_size=2
python infra/scripts/smoke_test.py "$(terraform -chdir=infra output -raw alb_url)"
```

Open beforehand, one browser tab each: the ALB URL, the CloudWatch dashboard
(`dashboard_url`), EC2 → Auto Scaling groups → `group4-hotstar-app`,
`docs/figures/`, `docs/results/README.md`.

## Run sheet

| Min | Who | Show | Say |
|----:|-----|------|-----|
| 0–1 | Manan | README team table, architecture in `infra/README.md` | Hotstar's problem: tens of millions of viewers arrive within minutes at toss time. We built the control path (API, not video) and measured how it scales. |
| 1–3 | Manan | ALB URL in the browser, refresh a few times | Live URL (deliverable 1). Two instance IDs alternate: the ALB spreads requests. Terraform built all of it; one var-file per experiment. |
| 3–4 | Kalp | `app/README.md` endpoint table, `curl /play` | Each endpoint has a cost profile. `/play` is CPU-heavy on purpose (DRM signing stand-in), `/score` is cacheable. |
| 4–5 | Kalp | CloudWatch dashboard | Instances, CPU with the 50% / 20% lines, ALB p95, 5xx. The alarms drive scaling. |
| 5–7 | Deep | `e1_latency_vs_instances.png`, E1 table | Response time vs instance count (deliverable 3). Median of 5 runs, bars are the range. Where it flattens and why. |
| 7–8 | Deep | `e2_e3_timeline.png` | Reactive scaling lags by boot time + alarm period: about 4 min with p95 at 4–5 s (no errors, requests queue). Pre-warm, like Hotstar does before a match, removes the gap: p95 stays at 52 ms. |
| 8–9 | Kalp | `e5_panic_mode.png`; flip the flag live and `curl /home` | Panic mode drops personalisation so `/play` survives. The servers see the flag within 5 s. |
| 9–10 | Manan | cost table, destroy checklist | What it cost, cost per million requests, and that everything is destroyed after each day. |

Panic flag live (Kalp, minute 8):

```bash
aws ssm put-parameter --name /group4-hotstar/panic-mode --value on --overwrite
sleep 6; curl -s "$(terraform -chdir=infra output -raw alb_url)/home"     # "panic": true
aws ssm put-parameter --name /group4-hotstar/panic-mode --value off --overwrite
```

## If the live part fails

Do not debug in front of the examiner. Say so in one line and switch to the
screenshots in `docs/screenshots/` (taken during the real runs) and the
figures. Every claim in the talk has a screenshot or a graph behind it.

| Problem | Fallback |
|---------|----------|
| ALB URL times out | servers still booting: show `base-alb-response.png`, `base-two-instances.png` |
| AWS credentials expired | screenshots only |
| Dashboard empty | normal for a fresh stack; show `e2-dashboard.png` |

## Likely questions (and who answers)

| Question | Who | Short answer |
|----------|-----|--------------|
| Why step scaling and not target tracking? | Manan | The brief says "CPU > 50% → add an instance"; step scaling is exactly that and easy to explain. Target tracking would be the production choice. |
| Why c7i-flex.large and not t3.micro? | Manan | Our AWS account is on the Free plan, which only allows a few types. t3 is burstable: under load it runs out of CPU credits and slows down, so results would change between runs. c7i-flex has no credits, so runs repeat, for about $0.085/h. |
| Why only 3 servers? | Manan | The account's vCPU limit is 8: 3 app servers x 2 vCPU plus the 2 vCPU k6 box. The scaling behaviour is the same at 3 as at 300; only the numbers are smaller. |
| Why is boot time important? | Kalp | It is the floor for reactive scaling. We measured it (`measure_boot.py`) and cut it by dropping the full OS update from user data. |
| Why not Docker / ECS? | Kalp | The course is about EC2 scaling; plain user data keeps the boot path visible and measurable. The Dockerfile is there for local use. |
| How do you know the k6 box was not the bottleneck? | Deep | Same region, its own c7i-flex.large, CPU checked during runs; error codes come from the ALB, not k6 timeouts. |
| Why 5 runs (E1) and the median? | Deep | Cloud noise between runs; the median ignores one bad run and the range shows the spread. |
| Why does /score get faster through CloudFront? | Deep | Edge hit for 5 s per path; the servers see about one request per 5 s per edge instead of every viewer. |
| How would real Hotstar differ? | all | Multi-region, video on several CDNs, pre-warmed fleets sized from match forecasts, many more services with their own panic levers. |
| What did it cost? | Manan | $3.46 on the AWS Budgets page by 8 Nov 02:25 (second account, before credits); the app servers for all 33 runs come to about $1.23 (`cost.csv`). |

## After the viva

```bash
terraform -chdir=infra destroy -var-file=experiments/base.tfvars
```

Then step 4 of the destroy checklist in `infra/README.md`.
