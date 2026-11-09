# Base deployment: one server, kept live for the "live URL" deliverable.
# terraform -chdir=infra apply -var-file=experiments/base.tfvars
fixed_size     = 1
enable_loadgen = false
