# How much money has all of this cost?

I started off with the Rasberry PI 3 itself and a small collection of wires/breadboard so I wont count that for now

* ~ 9$ on a 5 pack of moisture sensors.  Currently unavailable on amazon
    * kuman 5PCS Soil Moisture Sensor Kit Compatible with Raspberry pi Arduino Mega 2560 with 10PIN Female to Female Jump Cables 20PIN Male to Female Dupont Jump Cable Automatic Watering System KY70
    
* Gitlab has been free so far.  I haven't hit my limits on repository size or CI/CD minutes so the free tier has been more than enough

* Currently the AWS bill is 0.03$ per month.  1 cent for the active Greengrass core and the other 2 cents are related to S3 costs.  Currently I'm only using S3 to host my `docker-compose.yml` file, but I anticipate my data storage needs will continue to grow

* So far I've been able to easily stay within the free tier for the following AWS services
    * CloudWatch
    * Lambda
    * SNS
