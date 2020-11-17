resource "aws_s3_bucket" "auto-water-bucket" {
  bucket = "constellation-auto-water"
  acl    = "private"
}