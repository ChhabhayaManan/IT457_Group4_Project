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
  app_dir               = "${path.root}/../app"

  app_env = {
    AWS_REGION      = var.aws_region
    PLAY_ITERATIONS = tostring(var.play_iterations)
  }
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
