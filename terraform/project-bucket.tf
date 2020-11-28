resource "aws_s3_bucket" "auto-water-bucket" {
  bucket = "constellation-auto-water"
  acl    = "private"
}

resource "aws_s3_bucket_public_access_block" "auto-water-bucket" {
  bucket = aws_s3_bucket.auto-water-bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
