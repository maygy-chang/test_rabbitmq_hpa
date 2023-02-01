import sys
import time
import os
import yaml
import shutil
import json
from oc import OC
from datetime import datetime
from define import warm_up, metrics_path,  picture_path, traffic_path
from define import k8shpa_percent, traffic_interval, k8shpa_type, consumer_name_list
from define import k8shpa_min_node, k8shpa_max_node, config_path
from define import app_name_prefix, app_replica_number, cluster_name, app_namespace, clean_data_first
from kubectl import Kubectl
from run_config import Config


def clean_data():
    for app_name in consumer_name_list:
        print "Clean %d Apps' data(%s) in namespaces: %s" % (app_replica_number, app_name, app_namespace)
        if clean_data_first:
            OC().scale_replica(app_namespace, "deployment", app_name, 0)

        OC().scale_replica(app_namespace, "deployment", app_name, app_replica_number)

    total_active_replicas = 0
    for app_name in consumer_name_list:
        c = Config()
        active_replicas = c.query_app_status(app_name, app_replica_number, app_namespace)
        total_active_replicas += active_replicas
    if app_replica_number == total_active_replicas:
        print "%s RabbitMQ Replicas in namespaces(%s) are ready and running\n" % (app_replica_number, app_namespace)
    else:
        raise Exception("- %s RabbitMQ Replicas in the namespace(%s) are not ready and running\n" % (active_replicas, app_namespace))

    wait_time(300)


def get_app_namespace_list():
    o = OC()
    app_namespace_list = []
    output = o.get_namespaces()
    for line in output.split("\n"):
        if line.find(app_namespace_prefix) != -1:
            app_namespace = line.split()[0]
            app_namespace_list.append(app_namespace)
    return app_namespace_list


def create_directory():
    if not os.path.exists(traffic_path):
        os.mkdir(traffic_path)
        print "%s is created" % traffic_path
    elif os.path.exists(traffic_path):
        print "%s is existed" % traffic_path

    if not os.path.exists(metrics_path):
        os.mkdir(metrics_path)
        print "%s is created" % metrics_path
    elif os.path.exists(metrics_path):
        print "%s is existed" % metrics_path

    print "\n"


def remove_directory():
    shutil.rmtree(traffic_path)
    shutil.rmtree(metrics_path)
    # shutil.rmtree(picture_path)
    print "\n"


def change_directory_name(dir_name):
    if os.path.exists(traffic_path):
        new_dir_name = "%s_traffic" % dir_name
        os.rename(traffic_path, new_dir_name)
        print "change %s to %s" % (traffic_path, new_dir_name)
    if os.path.exists(metrics_path):
        new_dir_name = "%s_metrics" % dir_name
        os.rename(metrics_path, new_dir_name)
        print "change %s to %s" % (metrics_path, new_dir_name)
    else:
        print "dir: %s is not existed" % traffic_path
    print "\n"


def find_pod_name(app_name, app_namespace):
    pod_name_list = []
    status = ""
    output = OC().get_pods(app_namespace)
    for line in output.split("\n"):
        if line.find(app_name) != -1:
            pod_name = line.split()[0]
            if pod_name.find("build") != -1:
                continue
            status = line.split()[2]
            if status not in ["Running"]:
                raise Exception("%s is %s" % (pod_name, status))
            pod_name_list.append(pod_name)
    if not pod_name_list:
        raise Exception("%s is not existed in %s" % (app_name, app_namespace))
    return pod_name_list


def restart_pod(app_name, app_namespace):
    print "- Restart App(%s)'s pods in namespace(%s)" % (app_name, app_namespace)
    output = ""
    pod_name_list = find_pod_name(app_name, app_namespace)
    for pod_name in pod_name_list:
        output = OC().delete_pod(pod_name, app_namespace)
        print output
    return output


def wait_time(waittime=warm_up*60):
    print "- Wait %s seconds to run algo" % waittime
    time.sleep(waittime)


def get_dir_name(term):
    timestamp = int(time.time())
    dt_object = str(datetime.fromtimestamp(timestamp)).split()[0]
    dir_list = os.listdir(".")
    count = 0
    for dir in dir_list:
        if dir.find(term) != -1 and not os.path.isfile(dir):
            count += 1
    dir_name = "%s_%s_%d" % (term, dt_object, count)
    return dir_name


def run_k8s_hpa_cpu(app_name, app_namespace):
    k = Kubectl()
    output = k.autoscale_replica("deployment", app_name, app_namespace, k8shpa_min_node, k8shpa_max_node, k8shpa_percent)
    print output
    k.get_hpa(app_namespace)
    return output


def replace_parameters_by_sed(term, entry, file_name):
    cmd = "sed -i 's/%s:.*/%s: %s /g' %s" % (term, term, entry, file_name)
    ret = os.system(cmd)
    if ret != 0:
        print "- Failed to update %s(%s) in %s" % (term, entry, file_name)
    return ret


def delete_k8s_hpa(app_name, app_namespace):
    k = Kubectl()
    output = k.delete_hpa(app_name, app_namespace)
    print output
    k.get_hpa(app_namespace)
    return output


def main(algo, action):
    # create_directory()
    app_name = "rabbitmq-consumer"
    app_namespace = "bitnami"
    if algo == "k8shpa":
        if action == "start":
            wait_time()
            run_k8s_hpa_cpu(app_name, app_namespace)
            print "k8shpa is deployed"
        else:
            delete_k8s_hpa(app_name, app_namespace)
            dir_name = get_dir_name("k8shpa")
            change_directory_name(dir_name)
    else:
        if action == "start":
            wait_time()
            pass
        else:
            dir_name = get_dir_name("nonhpa")
            change_directory_name(dir_name)


if __name__ == "__main__":
    try:
        algo = sys.argv[1]
        action = sys.argv[2]
        main(algo, action)
    except Exception as e:
        print "Exception:"
        print "- %s" % str(e)
        print "python run_hpa.py <algo_name> <action>"
        print "- algo_name:  nonhpa, or k8shpa"
        print "- action:  start or stop"
