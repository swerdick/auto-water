
resource "aws_iam_role" "pi_role" {
  name = "pi_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "greengrass.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_policy" "pi_bucket_access_policy" {
  name = "pi_bucket_access_policy"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:GetObject",
        "s3:GetBucket",
        "s3:List"
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

resource "aws_iam_policy" "pi_cloudwatch_policy" {
  name = "pi_cloudwatch_policy"
  
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            "Resource": [
                "arn:aws:logs:*:*:*"
            ]
        }
    ]
}
EOF
}

resource "aws_iam_policy_attachment" "pi_role_attachment" {
  name       = "pi_role_attachment"
  roles      = [aws_iam_role.pi_role.name]
  policy_arn = aws_iam_policy.pi_bucket_access_policy.arn
}

resource "aws_iam_policy_attachment" "pi_cloudwatch_role_attachment" {
  name       = "pi_role_attachment"
  roles      = [aws_iam_role.pi_role.name]
  policy_arn = aws_iam_policy.pi_cloudwatch_policy.arn
}
