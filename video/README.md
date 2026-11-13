# Optional video demo: live HLS through CloudFront

Not part of the five experiments. It shows the other half of Hotstar's
design: video is files on a CDN, not traffic on the app servers.

```
FFmpeg (ingest EC2) --> S3 bucket (private) --> CloudFront --> hls.js player
   2 qualities, 4 s        live/ prefix,           .ts cached,      switches 720p/360p
   HLS segments            expires after 1 day     .m3u8 for 2 s    with the network
```

| File | Runs on | What it does |
|------|---------|--------------|
| `ffmpeg_hls.sh` | ingest box | test pattern + tone -> 720p and 360p HLS in `/var/video/out` |
| `upload_segments.sh` | ingest box | every 2 s: segments, then playlists, to `s3://$VIDEO_BUCKET/live/` |
| `player/index.html` | browser | hls.js player with quality, bandwidth, buffer and live delay |

Terraform copies the `*.sh` files to `/opt/video/` on the box
(`infra/modules/video`). The source is FFmpeg's test pattern, so there is no
copyrighted footage.

## Run it (about 20 minutes, under $0.10)

```bash
# 1. Create it (only with the team's go-ahead; it costs money while up)
terraform -chdir=infra apply -var-file=experiments/base.tfvars -var enable_video=true

# 2. Put the player at the bucket root
aws s3 cp video/player/index.html "s3://$(terraform -chdir=infra output -raw video_bucket)/index.html"

# 3. Start the stream: open a shell on the box ...
aws ssm start-session --target "$(terraform -chdir=infra output -raw video_instance_id)"
# ... and inside it (wait until `tail /var/log/video-boot.log` shows VIDEO_BOOT_DONE)
sudo /opt/video/ffmpeg_hls.sh 900 &
sudo /opt/video/upload_segments.sh

# 4. Watch: open the player URL (give it about 15 s for the first segments)
terraform -chdir=infra output -raw video_player_url

# 5. Remove it again
terraform -chdir=infra apply -var-file=experiments/base.tfvars -var enable_video=false
```

The player also works from disk: open `player/index.html` and paste
`video_stream_url` into the box (the CDN sends CORS headers).

## What to point out

- **Quality switching**: in Chrome dev tools, Network -> throttle to "Fast 4G"
  or slower; "Quality now" drops from 720p to 360p and comes back.
- **The CDN does the work**: `curl -sI <segment url>` twice shows
  `x-cache: Hit from cloudfront`; S3 sees one request per segment per edge,
  however many people watch.
- **Live delay**: about 3 segments (12 s) behind the encoder, set by
  `liveSyncDurationCount: 3` in the player and `hls_time 4` in FFmpeg.

## If it does not play

- Box log: `sudo tail -50 /var/log/video-boot.log` (FFmpeg download failed?
  set `ffmpeg_url` in `infra/modules/video/variables.tf` to another static build).
- `aws s3 ls s3://<video_bucket>/live/ --recursive | tail` should list fresh
  `.ts` files and three `.m3u8`.
- A 403 from CloudFront means the object is not there yet (the bucket is private).
