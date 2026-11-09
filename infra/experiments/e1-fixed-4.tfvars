# E1: fixed group of 4 instances; same k6 rate as the other E1 sizes.
# Optional: 4 x 2 + 2 (k6) = 10 vCPU, more than our quota of 8. Use e1-fixed-3 instead.
fixed_size     = 4
enable_loadgen = true
