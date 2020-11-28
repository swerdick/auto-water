
resource "aws_kinesis_firehose_delivery_stream" "auto_water_ingestion" {
    name        = "auto-water-ingestion"
    destination = "extended_s3"
    
    extended_s3_configuration {
        role_arn   = aws_iam_role.kinesis_role.arn
        bucket_arn = aws_s3_bucket.auto-water-bucket.arn
        prefix     = "pi-sensor-data/"
    }
}

resource "aws_iam_role" "kinesis_role" {
  name = "auto-water-kinesis-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "firehose.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}


resource "aws_iam_policy" "kinesis_bucket_access_policy" {
  name = "kinesis_bucket_access_policy"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:GetObject",
        "s3:GetBucket",
        "s3:List",
        "s3:PutObject*"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:s3:::constellation-auto-water/*",
        "arn:aws:s3:::constellation-auto-water/"
      ]
    }
  ]
}
EOF
}


resource "aws_iam_policy_attachment" "kinesis_role_attachment" {
  name       = "kinesis_role_attachment"
  roles      = [aws_iam_role.kinesis_role.name]
  policy_arn = aws_iam_policy.kinesis_bucket_access_policy.arn
}
