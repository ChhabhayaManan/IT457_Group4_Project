# Infrastructure (Terraform)

Everything runs in **ap-south-1 (Mumbai)**. Every resource is tagged
`Project = group4-hotstar` (provider `default_tags`), which is how the budget
and `scripts/cost_report.py` find our spend.

```
                       Internet
                          |
        CloudFront (E4, optional) --- /score cached 5 s
                          |
 public subnets  [ ALB :80 ]        [ NAT gateway ]
                     |                     ^
 private subnets [ ASG: c7i-flex.large app servers :8000 ] [ k6 box ] [ video box ]
                     |
     CloudWatch dashboard + alarms, SSM parameter (panic flag), Budget $50
```

## Modules

| Module | What it creates | Switched by |
|--------|-----------------|-------------|
| `network` | VPC 10.40.0.0/16, 2 public + 2 private subnets in 2 AZs, internet gateway, one NAT gateway | always |
| `alb` | load balancer, target group on port 8000 (health check `/health`), listener on 80 | always |
| `compute` | launch template (user data from `app/`), Auto Scaling group, IAM role, CPU step scaling (`scaling.tf`), pre-warm schedule (`schedule.tf`) | `scaling_mode` |
| `observability` | CloudWatch dashboard and the 5xx / p95 alarms | always |
| `cdn` | CloudFront in front of the ALB with the 5 s `/score` cache policy | `enable_cdn` |
| `loadgen` | k6 EC2 box (c7i-flex.large), results bucket, test scripts uploaded from `loadtest/` | `enable_loadgen` |
| `video` | FFmpeg ingest box, private video bucket, CloudFront for HLS (optional demo) | `enable_video` |

Root files: `budget.tf` ($50 monthly budget, alerts at $20, $50 and $50
forecast; credits are not counted, so the alerts still fire), `flags.tf`
(SSM parameter `/group4-hotstar/panic-mode`), `providers.tf`, `versions.tf`
(S3 backend with native locking, no DynamoDB).

## One-time setup

Needs Terraform 1.10 or newer, the AWS CLI with credentials for the project
account, and the Session Manager plugin (for the k6 and video boxes).

```bash
# 1. State bucket (its own local state, kept in infra/bootstrap/, gitignored)
terraform -chdir=infra/bootstrap init
terraform -chdir=infra/bootstrap apply          # prints state_bucket

# 2. Backend and variables (both gitignored)
cp infra/backend.hcl.example infra/backend.hcl          # put state_bucket in it
cp infra/terraform.tfvars.example infra/terraform.tfvars  # set budget_email
terraform -chdir=infra init -backend-config=backend.hcl

# 3. vCPU quota for E2/E3 (needs 8) and the c7i-flex type in our two zones
bash infra/scripts/check_quota.sh
```

Then in the Billing console, once: **Cost allocation tags -> activate
`Project`** (needed by the cost report; it only counts from activation on).

## Variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `budget_email` | none (set in `terraform.tfvars`) | gets the budget alerts |
| `instance_type` | `c7i-flex.large` | app server type (2 vCPU, allowed on the AWS Free plan); keep it the same for every run |
| `loadgen_instance_type` | `c7i-flex.large` | k6 box (2 vCPU; its CPU stayed under 80% in our runs) |
| `scaling_mode` | `fixed` | `fixed` (E1), `step` (E2), `scheduled` (E3) |
| `fixed_size` | 1 | servers in `fixed` mode (1 to 10) |
| `asg_max` | 3 | ceiling in `step`/`scheduled`; 3 x 2 vCPU + the k6 box = our 8 vCPU quota |
| `prewarm_start`, `prewarm_end`, `prewarm_size` | `""`, `""`, 2 | E3 schedule (UTC, RFC 3339) |
| `enable_cdn` | false | CloudFront (E4) |
| `enable_loadgen` | false | k6 box (all experiments) |
| `enable_video` | false | video demo |
| `play_iterations` | 20000 | CPU cost of one `/play` call |

## Experiments

Each file in `experiments/` is one setup. Apply it, run the k6 script from
your laptop with `loadtest/start_run.py`, then apply the next one.

| File | Setup | k6 script |
|------|-------|-----------|
| `base.tfvars` | 1 server, no k6 box: the live URL | none |
| `e1-fixed-{1,2,3}.tfvars` | fixed 1, 2, 3 servers (`-4` and `-8` only with a bigger quota) | `constant_rate.js` |
| `e2-step.tfvars` | CPU step scaling, 1 to 3 | `spike.js` |
| `e3-prewarm.tfvars` | step scaling + pre-warm to 2 before the spike (**edit the times**) | `spike.js` |
| `e4-cdn.tfvars` | CloudFront on, 1 server | `constant_rate.js` with `MIX=score`, both `--target` values |
| `e5-panic.tfvars` | fixed 2 servers, flip the SSM flag between runs | `overload.js` |

```bash
terraform -chdir=infra plan  -var-file=experiments/e1-fixed-3.tfvars   # read it first
terraform -chdir=infra apply -var-file=experiments/e1-fixed-3.tfvars
python infra/scripts/smoke_test.py "$(terraform -chdir=infra output -raw alb_url)"
```

Switching between E1 sizes only changes the Auto Scaling group, so it is
quick; new servers need about 2 minutes to pass health checks. Wait for the
smoke test to show every expected instance ID before starting k6.

## Outputs

| Output | Use |
|--------|-----|
| `alb_url` | the live URL (course deliverable) |
| `cdn_url` | CloudFront URL when `enable_cdn` |
| `dashboard_url` | CloudWatch dashboard |
| `asg_name` | Auto Scaling group, for the console and `measure_boot.py` |
| `loadgen_instance_id`, `results_bucket` | used by `loadtest/start_run.py` |
| `video_*` | video demo (see `video/README.md`) |

## What it costs while it is up

Rough on-demand prices in ap-south-1 (check the AWS pricing pages before
quoting them):

| Item | About |
|------|-------|
| NAT gateway | $0.056 per hour + data |
| Load balancer | $0.024 per hour + capacity units |
| Public IPv4 addresses (ALB, NAT) | $0.005 per hour each |
| c7i-flex.large (app servers and the k6 box) | about $0.085 per hour each (5% under c7i.large) |
| t3.small video box | $0.022 per hour (+ CPU credits while encoding) |

The base stack alone (1 server, no k6 box) is roughly **$4.40 a day**, so
**destroy it at the end of every experiment day**. A full test day (k6 box
plus 1 to 3 servers for 4 to 6 hours) is about $3 to $4; every test day,
the rehearsal and the viva together come to about $13 to $16, under the $20
alert. The real numbers come from `python infra/scripts/cost_report.py`.

## Destroy checklist (end of every experiment day)

1. Results are safe: `analysis/data/<run>/` exists for every run of the day
   (the results bucket is deleted with the stack).
2. Screenshots for the day are taken (`docs/screenshots/README.md`).
3. Destroy with the same var-file that was last applied:
   ```bash
   terraform -chdir=infra destroy -var-file=experiments/<last>.tfvars
   ```
   CloudFront takes about 15 minutes to disable; let it finish.
4. Check nothing is left (Mumbai region), all should be empty:
   ```bash
   aws ec2 describe-instances --filters Name=tag:Project,Values=group4-hotstar \
     Name=instance-state-name,Values=pending,running,stopping,stopped --query 'Reservations[].Instances[].InstanceId'
   aws ec2 describe-nat-gateways --filter Name=tag:Project,Values=group4-hotstar \
     Name=state,Values=pending,available --query 'NatGateways[].NatGatewayId'
   aws ec2 describe-addresses --filters Name=tag:Project,Values=group4-hotstar --query 'Addresses[].PublicIp'
   aws elbv2 describe-load-balancers --query 'LoadBalancers[].LoadBalancerName'
   aws cloudfront list-distributions --query 'DistributionList.Items[].Comment'
   ```
5. Next morning: Billing -> Cost Explorer shows no new hourly charges.

The state bucket from `bootstrap/` stays until the course is over (it costs
cents). At the very end: empty it (all versions) in the S3 console, then
`terraform -chdir=infra/bootstrap destroy`.
