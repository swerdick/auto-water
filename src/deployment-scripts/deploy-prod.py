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

#response=greengrass_client.create_deployment(GroupId=GREENGRASS_GROUP_ID, 
#    DeploymentType='NewDeployment', 
#    GroupVersionId=latestVersion
#)

response=greengrass_client.get_group_version(GroupId=GREENGRASS_GROUP_ID, GroupVersionId=latestVersion)

#print(response)

response=greengrass_client.create_group_version(
    GroupId=GREENGRASS_GROUP_ID,
    ConnectorDefinitionVersionArn=response['Definition']['ConnectorDefinitionVersionArn'],
    CoreDefinitionVersionArn=response['Definition']['CoreDefinitionVersionArn'],
    FunctionDefinitionVersionArn=response['Definition']['FunctionDefinitionVersionArn'],
    LoggerDefinitionVersionArn=response['Definition']['LoggerDefinitionVersionArn'])

#print(response)


response=greengrass_client.create_deployment(
    DeploymentType='NewDeployment',
    GroupId=GREENGRASS_GROUP_ID,
    GroupVersionId=response['Version'])
    
#print(response)

response=greengrass_client.get_deployment_status(
    GroupId=GREENGRASS_GROUP_ID,
    DeploymentId=response['DeploymentId'])

print(response)


