#!/bin/bash
# Make a live HLS stream with two qualities (720p and 360p), like a sports
# broadcast with adaptive bitrate. The input is FFmpeg's own test pattern and
# a tone, so there is no copyrighted footage.
#
#   ffmpeg_hls.sh [seconds] [out dir]      default 600 s into /var/video/out
#
# Output: master.m3u8 -> v0/index.m3u8 (720p), v1/index.m3u8 (360p), 4 s segments.
# The playlists keep the last 10 segments, so players join "live".
set -euo pipefail

SECONDS_TO_RUN="${1:-600}"
OUT="${2:-/var/video/out}"
mkdir -p "${OUT}/v0" "${OUT}/v1"

ffmpeg -hide_banner -loglevel warning -re \
  -f lavfi -i "testsrc2=size=1280x720:rate=25" \
  -f lavfi -i "sine=frequency=440:sample_rate=48000" \
  -t "${SECONDS_TO_RUN}" \
  -filter_complex "[0:v]split=2[hi][lo];[lo]scale=640:360[lo360]" \
  -map "[hi]" -map 1:a -map "[lo360]" -map 1:a \
  -c:v libx264 -preset veryfast -tune zerolatency -g 100 -keyint_min 100 -sc_threshold 0 \
  -b:v:0 2500k -maxrate:v:0 2700k -bufsize:v:0 5000k \
  -b:v:1 700k -maxrate:v:1 750k -bufsize:v:1 1400k \
  -c:a aac -b:a 96k -ac 2 \
  -f hls -hls_time 4 -hls_list_size 10 -hls_flags delete_segments+independent_segments \
  -master_pl_name master.m3u8 \
  -hls_segment_filename "${OUT}/v%v/seg_%05d.ts" \
  -var_stream_map "v:0,a:0 v:1,a:1" \
  "${OUT}/v%v/index.m3u8"
