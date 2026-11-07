#!/usr/bin/env bash
# Check the EC2 vCPU quota and instance types before the experiments
# (run in Git Bash or any shell with the AWS CLI).
#   bash infra/scripts/check_quota.sh
#
# Need: 3 app servers x 2 vCPU (c7i-flex.large) + 1 k6 box x 2 vCPU (c7i-flex.large) = 8 vCPU.
# c7i-flex.large is one of the few types the AWS Free plan allows. For E1 with 4 servers
# (e1-fixed-4.tfvars) or asg_max 4, ask for 10:
#   aws service-quotas request-service-quota-increase \
#     --service-code ec2 --quota-code L-1216C47A --desired-value 10 --region ap-south-1
set -euo pipefail

REGION="${AWS_REGION:-ap-south-1}"
APP_VCPU=2
K6_VCPU=2
MAX_APP=3
NEEDED=$(( MAX_APP * APP_VCPU + K6_VCPU ))
TYPES="c7i-flex.large"

# L-1216C47A = Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances, in vCPUs.
QUOTA=$(aws service-quotas get-service-quota \
  --service-code ec2 --quota-code L-1216C47A --region "$REGION" \
  --query 'Quota.Value' --output text)

QUOTA=${QUOTA%.*}
echo "On-Demand Standard vCPU quota in $REGION: $QUOTA (needed: $NEEDED)"

# The network module uses the first two zones; the type must exist there.
ZONES=$(aws ec2 describe-availability-zones --region "$REGION" \
  --filters Name=state,Values=available --query 'AvailabilityZones[].ZoneName' --output text \
  | tr '\t' '\n' | sort | head -2)
MISSING=0
for type in $TYPES; do
  offered=$(aws ec2 describe-instance-type-offerings --region "$REGION" \
    --location-type availability-zone --filters "Name=instance-type,Values=$type" \
    --query 'InstanceTypeOfferings[].Location' --output text)
  for zone in $ZONES; do
    if ! grep -qw "$zone" <<<"$offered"; then
      echo "MISSING: $type is not offered in $zone"
      MISSING=1
    fi
  done
done

if [ "$MISSING" -ne 0 ]; then
  echo "Pick another Free plan type, e.g. -var instance_type=m7i-flex.large -var loadgen_instance_type=m7i-flex.large."
  exit 1
fi
echo "OK: $TYPES is offered in $(echo $ZONES)."

FIT=$(( (QUOTA - K6_VCPU) / APP_VCPU ))
if [ "$QUOTA" -ge "$NEEDED" ]; then
  echo "OK: $MAX_APP app servers plus the k6 box fit (room for $FIT app servers)."
elif [ "$FIT" -ge 1 ]; then
  echo "TOO LOW: only $FIT app servers fit next to the k6 box. Request an increase"
  echo "(command at the top of this script), or run E2/E3 with -var asg_max=$FIT."
  exit 1
else
  echo "TOO LOW: not even 1 app server fits next to the k6 box. Request an increase"
  echo "(command at the top of this script) before any experiment."
  exit 1
fi
