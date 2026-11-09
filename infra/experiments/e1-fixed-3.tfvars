# E1: fixed group of 3 instances; same k6 rate as the other E1 sizes.
# 3 x 2 vCPU + the k6 box (2) = 8 vCPU, exactly our quota.
fixed_size     = 3
enable_loadgen = true
