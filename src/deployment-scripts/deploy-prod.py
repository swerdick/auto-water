import boto3

s3_client = boto3.client('s3')
#greengrass_client = boto3.client('greengrass')

S3_BUCKET_NAME = 'constellation-auto-water'
S3_DOCKER_COMPOSE_KEY = 'docker-dependencies'

print('starting s3 upload...')
s3_client.upload_file('../poc/docker-compose.yml', S3_BUCKET_NAME, S3_DOCKER_COMPOSE_KEY)

