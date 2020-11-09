resource "aws_s3_bucket" "b" {
  bucket = "constellation-my-tf-test-bucket"
  acl    = "private"
}
