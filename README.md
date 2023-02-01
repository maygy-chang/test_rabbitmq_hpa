# test rabbitmq hpa
### create rabbitmq, producer, and consumers
- sh run.sh -z
### delete rabbitmq, producer, and consumers
- sh run.sh -r
### generate traffic with initial replicas=50, max replicas=100 for 300 minutes by using overprovision algorithms
- sh run.sh -i 50 -m 100 -n 300
### generate traffic with initial replicas=50, max replicas=100, and CPU threshold=50% for 300 minutes by using K8sHPA algorithms
- sh run.sh -i 50 -m 100 -k 300 -c 50
### modify configuration
- modify define.py
