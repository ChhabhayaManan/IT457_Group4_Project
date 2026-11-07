# Panic-mode flag (E5). The app re-reads it every few seconds; "on" turns /home
# into a static response so CPU goes to /play. Flip it without a redeploy:
#   aws ssm put-parameter --name /group4-hotstar/panic-mode --value on --overwrite

resource "aws_ssm_parameter" "panic_mode" {
  name        = "/${var.project_name}/panic-mode"
  description = "on = switch off non-critical features (graceful degradation)"
  type        = "String"
  value       = "off"

  # Flipped by hand during E5; Terraform must not reset it on the next apply.
  lifecycle {
    ignore_changes = [value]
  }
}
