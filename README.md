# Auto-Water

This repository contains source code and terraform scripts for getting a rasberrypi to talk to AWS

Found this lovely docker image to enable building armv7 images in gitlab CI.  Required for running containers on the rasberry pi

https://hub.docker.com/r/jonoh/docker-buildx-qemu

### Greengrass
AWS Greengrass seems like it will let me automate deployments of containerized applications to my rasberry pi device.  I'll try setting it up that way to automate code deployments

Greengrass getting started guide (very helpful): https://docs.aws.amazon.com/greengrass/latest/developerguide/gg-gs.html

I ended up running the `quickstart script` referenced in the getting started guide to initialize my rasberry-pi.  This created a group, lambda, and core in AWS pretty painlessly and helped me quickly understand how these tools work togather.

### Greengrass and Terraform

Terraform does not currently support AWS IOT Greengrass.  There are open issues and PRs out there on github to add support, but they are not yet merged.  Until Terraform adds support for this service I will need to use CloudFormation to keep my infrastructure as code.

Here are links to some of those open issues:
* https://github.com/terraform-providers/terraform-provider-aws/issues/10865
* https://github.com/terraform-providers/terraform-provider-aws/issues/10866
* https://github.com/terraform-providers/terraform-provider-aws/issues/10867
* https://github.com/terraform-providers/terraform-provider-aws/issues/10870
* https://github.com/terraform-providers/terraform-provider-aws/issues/10873
* https://github.com/terraform-providers/terraform-provider-aws/issues/10869
* https://github.com/terraform-providers/terraform-provider-aws/issues/10872
* https://github.com/terraform-providers/terraform-provider-aws/issues/10871


