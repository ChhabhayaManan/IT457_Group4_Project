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
