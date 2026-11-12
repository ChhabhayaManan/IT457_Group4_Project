#!/bin/bash
# Video ingest box (optional demo): installs a static FFmpeg build and the
# scripts from video/ into /opt/video. Nothing starts by itself; run the
# scripts through Session Manager (see video/README.md).
set -euxo pipefail
exec > >(tee -a /var/log/video-boot.log) 2>&1

dnf -y install --setopt=install_weak_deps=False tar xz

curl -fsSL -o /tmp/ffmpeg.tar.xz "${ffmpeg_url}"
mkdir -p /tmp/ffmpeg
tar -xJf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1
install -m 0755 /tmp/ffmpeg/ffmpeg /usr/local/bin/ffmpeg
rm -rf /tmp/ffmpeg /tmp/ffmpeg.tar.xz
/usr/local/bin/ffmpeg -version | head -1

mkdir -p /opt/video /var/video/out
%{ for name, content in scripts ~}
echo '${content}' | base64 -d > /opt/video/${name}
chmod 0755 /opt/video/${name}
%{ endfor ~}

cat > /etc/video.env <<'ENV'
%{ for key, value in env ~}
${key}=${value}
%{ endfor ~}
ENV
echo "VIDEO_BOOT_DONE $(date +%s)"
