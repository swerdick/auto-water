import boto3

s3_client = boto3.client('s3')
greengrass_client = boto3.client('greengrass')

S3_BUCKET_NAME = 'constellation-auto-water'
S3_DOCKER_COMPOSE_KEY = 'pi-artifacts/docker-compose.yml'
GREENGRASS_GROUP_ID = '5d1ebd1d-5727-4dbf-9970-e5a7441018f9'

##############################################################

print('starting s3 upload...')
s3_client.upload_file('../poc/docker-compose.yml', S3_BUCKET_NAME, S3_DOCKER_COMPOSE_KEY)

print('starting greengrass deployment...')
response=greengrass_client.get_group(GroupId=GREENGRASS_GROUP_ID)
latestVersion=response['LatestVersion']

response=greengrass_client.create_deployment(GroupId=GREENGRASS_GROUP_ID, 
    DeploymentType='Redeployment', 
    GroupVersionId=latestVersion
)

print(response)
