# E3: step scaling plus a scheduled pre-warm before the known spike.
# Set both times (UTC, IST minus 5:30) just before applying:
#   prewarm_start = about 5 minutes before spike.js starts its spike
#   prewarm_end   = after the spike's hold ends
scaling_mode   = "scheduled"
prewarm_size   = 2
prewarm_start  = "2026-11-10T04:25:00Z"
prewarm_end    = "2026-11-10T04:50:00Z"
enable_loadgen = true
