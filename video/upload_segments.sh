#!/bin/bash
# Push the live HLS output to S3 every 2 seconds until FFmpeg stops.
# Run next to ffmpeg_hls.sh on the ingest box:
#
#   upload_segments.sh [out dir]      default /var/video/out
#
# Segments first, then playlists, so a playlist never names a segment that
# is not in S3 yet. VIDEO_BUCKET comes from /etc/video.env (set by Terraform).
set -euo pipefail
source /etc/video.env

OUT="${1:-/var/video/out}"
DEST="s3://${VIDEO_BUCKET}/live"

while true; do
  running=0
  pgrep -x ffmpeg > /dev/null && running=1

  aws s3 sync "${OUT}" "${DEST}" --only-show-errors --exclude "*" --include "*.ts" \
    --content-type video/mp2t --cache-control "max-age=86400"
  aws s3 cp "${OUT}" "${DEST}" --recursive --only-show-errors --exclude "*" --include "*.m3u8" \
    --content-type application/vnd.apple.mpegurl --cache-control "max-age=2"

  if [ "${running}" -eq 0 ]; then
    echo "ffmpeg is not running; final upload done"
    break
  fi
  sleep 2
done
