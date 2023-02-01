# test rabbitmq hpa
### create rabbitmq, producer, and consumers
- sh run.sh -z
### delete rabbitmq, producer, and consumers
- sh run.sh -r
### generate traffic without HPA
- sh run.sh -i 50 -m 100 -n 300
-- initial replica number is 50
-- maximum replcia number is 100
-- duration is 300 minutes
### modify configuration
-- modify define.py
