terraform {
  backend "http" {}
}

provider "aws" {
  region     = var.region
  access_key = var.accessKey
  secret_key = var.accessSecret
  version = "~> 3.0"
}
