# E5: panic mode under overload. Fixed size so only the flag changes.
# Flip it between runs (servers pick it up within 5 s):
#   aws ssm put-parameter --name /group4-hotstar/panic-mode --value on  --overwrite
#   aws ssm put-parameter --name /group4-hotstar/panic-mode --value off --overwrite
fixed_size     = 2
enable_loadgen = true
