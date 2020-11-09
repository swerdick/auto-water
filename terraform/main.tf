terraform {
  backend "http" {}
}

provider "aws" {
  region     = var.region
  version = "~> 2.0"
}
