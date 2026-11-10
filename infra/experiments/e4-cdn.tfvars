# E4: CloudFront in front of the ALB. Same servers; run /score through
# both URLs (start_run.py --target cdn / --target alb) and compare.
fixed_size     = 1
enable_cdn     = true
enable_loadgen = true
