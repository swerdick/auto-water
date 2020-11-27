# Learnings

### PI Architecture

The Rasberry PI 3 I am using using 32bit ARM architecture.  It wasn't too difficult to find a 32bit ARM base image to base my container off of.  I could even build and run it successfully on the PI itself.  However; building the image on a build node in Gitlab CI/CD proved to be very challenging.  Eventually I learned about something called BuildX which is a Moby plugin that lets you build Docker images for multiple target arcitectures regardless of the architecture of the local system.  After finding a base image on Dockerhub that had the tool installed I was at last able to build the container image in Gitlab CI/CD

### Greengrass Logging

I was getting an obscure error in CloudWatch logs indicating that there was a Greengrass worker thread (or something) encountering an error during deployment.  The error wasn't showing up in my CloudWatch logs because the error wasn't occuring in my actual application code.  After a lot of digging I found that errors thrown by the Greengrass connectors are stored on the local filesystem (I don't believe they show up in CloudWatch).  Investigating there revealed my issue was that the Docker connector couldn't find my docker-compose.yml file.  It was an easy fix once I found an error to go off of.
https://docs.aws.amazon.com/greengrass/latest/developerguide/greengrass-logs-overview.html#gg-logs-local


