# Screenshots

Evidence for the report and the viva. Take each one **during or right after
the run it belongs to**, while the resources still exist (they are destroyed
after each experiment day). Save as PNG in this folder with the file name
shown, and crop out the account ID.

Region in the console: **Asia Pacific (Mumbai) ap-south-1**.

## Always

| File | Where in the console | What must be visible |
|------|----------------------|----------------------|
| `base-alb-response.png` | Browser on `alb_url` | `Match live, stream available` and the `instance` field |
| `base-two-instances.png` | Browser, refresh `alb_url` a few times (needs 2+ servers) | two different instance IDs, proof the ALB spreads load |
| `budget.png` | Billing → Budgets → `group4-hotstar-monthly` | $50 limit, current spend, the three alerts |
| `cost-by-tag.png` | Billing → Cost Explorer, group by tag `Project` | spend for `group4-hotstar` over the project dates (first activate `Project` in Billing → Cost allocation tags, or it shows $0) |

## E1, fixed sizes (9 Nov)

| File | Where | What |
|------|-------|------|
| `e1-target-group-3.png` | EC2 → Target groups → `group4-hotstar-app` → Targets | 3 targets, all `healthy` |
| `e1-dashboard.png` | CloudWatch → Dashboards → `group4-hotstar` | CPU and p95 for the whole E1 morning |

## E2, step scaling (10 Nov)

| File | Where | What |
|------|-------|------|
| `e2-asg-activity.png` | EC2 → Auto Scaling groups → `group4-hotstar-app` → Activity | the "Launching a new EC2 instance" lines, one per minute, with times |
| `e2-alarm-high.png` | CloudWatch → Alarms → `group4-hotstar-cpu-high` | graph crossing 50% and the state going to `In alarm` |
| `e2-alarm-low.png` | CloudWatch → Alarms → `group4-hotstar-cpu-low` | the scale-in after the spike |
| `e2-dashboard.png` | CloudWatch dashboard | instance count stepping up under the CPU line |
| `e2-alarm-high-all-runs.png` | CloudWatch → Alarms → `group4-hotstar-cpu-high`, 3h view | the alarm firing once per run, all 3 runs |
| `e2-alarm-p95.png` | CloudWatch → Alarms → `group4-hotstar-p95-latency`, 3h view | p95 over 1 s during each run's scale-out gap |
| `e2-asg-activity-setup.png` | Auto Scaling group → Activity, before run 1 | the group brought down to 1 server before the spike |
| `boot-time.png` | Terminal running `app/scripts/measure_boot.py` | the four timings |

## E3, pre-warm (10 Nov)

| File | Where | What |
|------|-------|------|
| `e3-scheduled-actions.png` | Auto Scaling group → Automatic scaling → Scheduled actions | `group4-hotstar-prewarm` and `-release` with their times |
| `e3-asg-activity.png` | Auto Scaling group → Activity | servers launched before the spike starts |
| `e3-scaling-policies.png` | Auto Scaling group → Automatic scaling | the step policies still on, plus the two scheduled actions |
| `e3-dashboard.png` | CloudWatch dashboard | 2 servers already in service when the spike hits |

## E4, CDN (11 Nov)

| File | Where | What |
|------|-------|------|
| `e4-cache-policy.png` | CloudFront → Policies → `group4-hotstar-score-5s` | min 0, default 5, max 5 seconds |
| `e4-cache-hits.png` | CloudFront → Reports & analytics → Cache statistics | hits vs misses for the run day (the Monitoring hit-rate graph needs paid extra metrics, so we skip it) |
| `e4-headers.png` | Terminal: `curl -s -D - -o /dev/null <cdn_url>/score` a few times (`-I` sends HEAD, which the app answers 405) | `x-cache: Hit from cloudfront` and `age` |

## E5, panic mode (11 Nov)

| File | Where | What |
|------|-------|------|
| `e5-parameter.png` | Systems Manager → Parameter Store → `/group4-hotstar/panic-mode` | value `on` and its history |
| `e5-home-panic.png` | Browser or curl on `alb_url/home` | `"panic": true`, `"personalised": false` |
