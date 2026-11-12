variable "name" {
  description = "Name prefix for resources."
  type        = string
}

variable "vpc_id" {
  description = "VPC for the ingest box."
  type        = string
}

variable "subnet_id" {
  description = "Private subnet for the ingest box (internet through the NAT)."
  type        = string
}

variable "instance_type" {
  description = "Ingest box type. Encoding two qualities live needs about 2 vCPU."
  type        = string
  default     = "t3.small"
}

variable "video_dir" {
  description = "Path to the video/ folder; its *.sh scripts are copied to the box."
  type        = string
}

variable "ffmpeg_url" {
  description = "Static FFmpeg build for x86_64 Linux (tar.xz with ffmpeg at the top level)."
  type        = string
  default     = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
}
