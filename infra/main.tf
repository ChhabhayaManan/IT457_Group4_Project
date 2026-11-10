module "network" {
  source = "./modules/network"

  name     = var.project_name
  vpc_cidr = var.vpc_cidr
}

module "alb" {
  source = "./modules/alb"

  name              = var.project_name
  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids
}

module "compute" {
  source = "./modules/compute"

  name                  = var.project_name
  vpc_id                = module.network.vpc_id
  private_subnet_ids    = module.network.private_subnet_ids
  alb_security_group_id = module.alb.alb_security_group_id
  target_group_arn      = module.alb.target_group_arn
  instance_type         = var.instance_type
  fixed_size            = var.fixed_size
  scaling_mode          = var.scaling_mode
  asg_max               = var.asg_max
  prewarm_start         = var.prewarm_start
  prewarm_end           = var.prewarm_end
  prewarm_size          = var.prewarm_size
  app_dir               = "${path.root}/../app"
  panic_param_arn       = aws_ssm_parameter.panic_mode.arn

  app_env = {
    AWS_REGION      = var.aws_region
    PLAY_ITERATIONS = tostring(var.play_iterations)
    PANIC_PARAM     = aws_ssm_parameter.panic_mode.name
  }
}

module "observability" {
  source = "./modules/observability"

  name                    = var.project_name
  aws_region              = var.aws_region
  asg_name                = module.compute.asg_name
  alb_arn_suffix          = module.alb.alb_arn_suffix
  target_group_arn_suffix = module.alb.target_group_arn_suffix
}

module "cdn" {
  source = "./modules/cdn"
  count  = var.enable_cdn ? 1 : 0

  name         = var.project_name
  alb_dns_name = module.alb.alb_dns_name
}

module "loadgen" {
  source = "./modules/loadgen"
  count  = var.enable_loadgen ? 1 : 0

  name          = var.project_name
  vpc_id        = module.network.vpc_id
  subnet_id     = module.network.private_subnet_ids[0]
  instance_type = var.loadgen_instance_type
  loadtest_dir  = "${path.root}/../loadtest"
}
