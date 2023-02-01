#!/bin/bash
rm -rf metrics
rm -rf picture
rm -rf traffic
rm -rf k8shpa*
rm -rf nonhpa*
killall run.sh
killall curl
killall kubectl
kubectl scale statefulset my-release-rabbitmq --replicas=0 -n bitnami
kubectl scale statefulset my-release-rabbitmq --replicas=1 -n bitnami
kubectl scale deployment rabbitmq-consumer --replicas=0 -n bitnami
kubectl scale deployment rabbitmq-consumer --replicas=1 -n bitnami
kubectl scale deployment rabbitmq-publisher --replicas=0 -n bitnami
kubectl scale deployment rabbitmq-publisher --replicas=1 -n bitnami
killall python
killall java
