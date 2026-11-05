# IT457 Group 4 – mini-Hotstar on AWS

Cloud Computing (IT457) project, Theme 3: Scalability. Case study: how Disney+ Hotstar
scales live cricket streaming to tens of millions of concurrent viewers.

This repository is a small proof of concept of Hotstar's control path: a FastAPI service
behind an Application Load Balancer, running in an Auto Scaling Group that adds servers when
traffic spikes and removes them when it drops. k6 load tests measure how it behaves.

**Results:** [`docs/results/README.md`](docs/results/README.md) ·
**Viva demo:** [`docs/viva-demo.md`](docs/viva-demo.md)

## Team

| Name | Roll No. | Owns |
| --- | --- | --- |
| Manan Chhabhaya | 202301222 | Infrastructure (Terraform, AWS) |
| Kalp Chaniyara | 202303022 | Application and observability |
| Deep Raval | 202303058 | Load testing and analysis |

## Course deliverables

| Deliverable | Where |
| --- | --- |
| Live URL of the load balancer | `terraform -chdir=infra output alb_url` (up during the viva) |
| Auto Scaling proof | `docs/screenshots/` (ASG activity, alarms) and `docs/figures/e2_e3_timeline.png` |
| Graph: response time vs instance count | `docs/figures/e1_latency_vs_instances.png` |
| Infrastructure as code | `infra/` |

## Experiments

| ID | Question | Setup |
| --- | --- | --- |
| E1 | How does latency change with 1, 2, 4, 8 servers at the same load? | fixed group, `constant_rate.js` |
| E2 | How fast does CPU step scaling react to a spike? | 1–10 servers, `spike.js` |
| E3 | Does pre-warming before a known spike remove the gap? | E2 + scheduled floor of 6 |
| E4 | What does a CDN do for cacheable responses (`/score`)? | CloudFront 5 s cache vs direct |
| E5 | Does panic mode keep `/play` alive under overload? | SSM flag off vs on, `overload.js` |

Optional: a live HLS video demo through CloudFront (`video/`).

## Repository layout

```
infra/      Terraform modules, experiment var-files, cost and quota scripts   (Manan)
app/        FastAPI service, user-data script, boot-time script              (Kalp)
video/      optional FFmpeg HLS demo and hls.js player                       (Kalp)
loadtest/   k6 scripts, run helper for the k6 box, per-second aggregation    (Deep)
analysis/   summary tables, graphs, cost per run                             (Deep)
docs/       results, figures, screenshots, viva demo                         (all)
```

Each folder has its own README: [`infra/`](infra/README.md), [`app/`](app/README.md),
[`loadtest/`](loadtest/README.md), [`video/`](video/README.md).

## Quick start

```bash
# one-time setup: state bucket, backend, budget email, vCPU quota -> infra/README.md
terraform -chdir=infra apply -var-file=experiments/e1-fixed-4.tfvars
python infra/scripts/smoke_test.py "$(terraform -chdir=infra output -raw alb_url)"
python loadtest/start_run.py e1 n4 1 constant_rate.js -e RATE=50 -e DURATION=10m
python analysis/pull_cloudwatch.py analysis/data/e1-n4-r1
python analysis/summarize.py && python analysis/make_figures.py
terraform -chdir=infra destroy -var-file=experiments/e1-fixed-4.tfvars
```

## Before the experiments: vCPU quota

E2 and E3 can grow to 10 app servers (2 vCPU each) plus the k6 box, so the account needs at
least 22 On-Demand Standard vCPUs in `ap-south-1`. New accounts sometimes get less.

```bash
bash infra/scripts/check_quota.sh
```

If it prints `TOO LOW`, request an increase right away (approval can take a day), or lower
the ASG maximum for E2/E3 with `-var asg_max=<n>`.

## Cost

A $50 monthly budget with email alerts guards the account. The stack costs money every hour
it is up (mostly the NAT gateway and the load balancer), so it is destroyed at the end of
every experiment day; see the **destroy checklist** in [`infra/README.md`](infra/README.md).
