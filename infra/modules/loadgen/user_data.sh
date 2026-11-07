#!/bin/bash
# k6 load generator setup (Amazon Linux 2023). Rendered by Terraform.
set -euxo pipefail
exec > >(tee -a /var/log/loadgen-boot.log) 2>&1

# Lots of concurrent connections: raise file and port limits.
cat > /etc/security/limits.d/k6.conf <<'LIMITS'
*    soft nofile 250000
*    hard nofile 250000
LIMITS
sysctl -w net.ipv4.ip_local_port_range="1024 65535"
sysctl -w net.ipv4.tcp_tw_reuse=1

# k6, pinned to the version the team uses locally. Retries for about 5 minutes:
# on a fresh apply the NAT gateway can still be starting when this box boots.
curl -fsSL --retry 30 --retry-delay 10 --retry-all-errors --connect-timeout 10 -o /tmp/k6.tar.gz \
  "https://github.com/grafana/k6/releases/download/v${k6_version}/k6-v${k6_version}-linux-amd64.tar.gz"
tar -xzf /tmp/k6.tar.gz -C /tmp
install -m 0755 "/tmp/k6-v${k6_version}-linux-amd64/k6" /usr/local/bin/k6

# Where run.sh finds the bucket.
echo "RESULTS_BUCKET=${results_bucket}" > /etc/loadgen.env
mkdir -p /opt/loadtest
echo "LOADGEN_READY $(date +%s)"
