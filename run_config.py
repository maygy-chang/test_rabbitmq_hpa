import os
import sys
import json
import time
import yaml
import shutil
import base64
from oc import OC
from kubectl import Kubectl
from define import config_path, app_namespace, prometheus_operator_name, k8shpa_max_node
from define import log_interval, query_interval, main_app_name, app_replica_number, app_name_prefix, cluster_name
from helm import Helm
from curl import Curl
query_timeout = 50


class Config:
    o = OC()
    h = Helm()
    k = Kubectl()
    iterations = 100
    config_path = config_path
    query_interval = 30
    namespace = app_namespace

    def __init__(self):
        pass

    def check_app_status(self, app_name, status, namespace=""):
        # print "- Check App(%s) status" % app_name
        count = 0
        output = ""
        if not namespace:
            output = self.o.get_pods(self.namespace)
        if namespace:
            output = self.o.get_pods(namespace)
        is_exporter = False
        for line in output.split("\n"):
            if line.find(app_name) != -1:
                pod_ready = line.split()[1]
                real_ready = pod_ready.split("/")[0]
                pred_ready = pod_ready.split("/")[1]
                pod_status = line.split()[2]
                if line.find("exporter") != -1:
                    is_exporter = True
                if status == "running":
                    if pod_status == "Running" and real_ready == pred_ready:
                        count += 1
                    else:
                        # print line
                        print "\n"
                        pass
                if status == "terminated":
                    if pod_status == "Terminating":
                        count += 1
        if is_exporter and app_name.find("exporter") == -1 and status == "running":
            num_pods = count - 1
        else:
            num_pods = count
        return num_pods

    def wait_time(self, start_time, query_interval=30):
        for i in range(log_interval):
            end_time = int(time.time())
            diff_time = end_time - start_time
            if diff_time >= query_timeout:
                break
            time.sleep(query_interval)

    def query_app_status(self, app_name, pod_threshold, namespace):
        print "\n"
        print "Waiting for App(%s) in namespace(%s) to be ready..." % (app_name, namespace)
        active_pods = self.check_app_status(app_name, "running", namespace=namespace)
        for i in range(self.iterations):
            active_pods = self.check_app_status(app_name, "running", namespace=namespace)
            if pod_threshold > active_pods:
                # scale up
                if active_pods == pod_threshold:
                    if active_pods == 1:
                        print "- %s pod of App(%s) are ready and running..." % (active_pods, app_name)
                    else:
                        print "- %s pods of App(%s) are ready and running..." % (active_pods, app_name)
                    break
                else:
                    inactive_pods = abs(pod_threshold - active_pods)
                    if inactive_pods == 1:
                        print "- %s pod of App(%s) are not scaled up..." % (inactive_pods, app_name)
                    else:
                        print "- %s pods of App(%s) are not scaled up..." % (inactive_pods, app_name)
                    start_time = int(time.time())
                    if app_name in ["ratings", "shipping"]:
                        self.wait_time(start_time, query_interval=60)
                    else:
                        self.wait_time(start_time)
            else:
                # scale down
                num_pods = self.check_app_status(app_name, "terminated", namespace=namespace)
                remain_pods = abs(num_pods - pod_threshold)
                if (num_pods == 0 and pod_threshold == active_pods and app_name != "my-cluster-kafka") or (num_pods == 0 and pod_threshold <= active_pods and app_name == "my-cluster-kafka"):
                    if remain_pods == 1:
                        print "- %s pod of App(%s) are ready and running" % (remain_pods, app_name)
                    else:
                        print "- %s pods of App(%s) are ready and running" % (remain_pods, app_name)
                    break
                else:
                    remain_pods = abs(num_pods - pod_threshold)
                    if remain_pods == 1:
                        print "- %s pods of App(%s) are not scaled down..." % (remain_pods, app_name)
                    else:
                        print "- %s pods of App(%s) are not scaled down..." % (remain_pods, app_name)
                    start_time = int(time.time())
                    self.wait_time(start_time)
        print "\n"
        if active_pods != pod_threshold and app_name.find("my-cluster-kafka") == -1:
            raise Exception("- App(%s) failed to run(%s/%s)" % (app_name, active_pods, pod_threshold))
        return active_pods

    def get_service_ip(self, app_name, namespace="", type=""):
        ip = ""
        port = ""
        output = ""
        if namespace:
            output = self.o.get_service(namespace)
        else:
            output = self.o.get_service(self.namespace)

        for line in output.split("\n"):
            if line.find(app_name) != -1:
                ip = line.split()[2]
                port = line.split()[4].split(",")[0].split("/")[0].split(":")[0]
                if app_name.find("connect") != -1 and type == "exporter":
                    port = line.split()[4].split(",")[1].split("/")[0]
                if app_name.find("mysql") != -1 and type == "exporter":
                    port = line.split()[4].split(",")[1].split("/")[0]
                print "- Find ip(%s) and port(%s) of app(%s)" % (ip, port, app_name)
                break
        if not ip or not port:
            print "app(%s)'s service is not existed..." % (app_name)
        return ip, port

    def curl_metrics(self, app_name, ip, port):
        ret = 0
        try:
            c = Curl(ip, port)
            json_output = c.get_metrics(app_name)
            print "- App(%s) is not working: %s" % (app_name, json_output.get("message"))
            ret = -1
        except Exception as e:
            print "- App(%s) is working" % app_name
            ret = 0
        return ret

    def curl_service_monitors(self, app_name, ip, port):
        ret = -1
        count = 0
        try:
            c = Curl(ip, port)
            json_output = c.get_service_monitors(app_name)
            for item in json_output.get("data").get("activeTargets"):
                job_name = item.get("labels").get("job")
                health = item.get("health")
                if job_name == app_name and health == "up":
                    # print "- Service monitor of App(%s) is %s" % (app_name, health)
                    count += 1
                    ret = 0
            print "- App(%s) has %d active service monitors" % (app_name, count)
        except Exception as e:
            pass
        print "\n"
        return ret

    def query_service_monitors(self, app_name):
        print "\n"
        print "Waiting for Prometheus Target binding with App(%s)..." % (app_name)
        ret = -1
        ip, port = self.get_service_ip(prometheus_operator_name, namespace="monitoring")
        for i in range(self.iterations):
            ret = self.curl_service_monitors(app_name, ip, port)
            if ret == 0:
                break
            start_time = int(time.time())
            self.wait_time(start_time)
        if ret == -1:
            print "- Service monitors of App(%s) do not work" % app_name
        return ret

    def add_helm_repo(self, repo_name, app_name):
        ret = -1
        repo_addr = ""
        if repo_name == "stable":
            # repo_addr = "https://kubernetes-charts.storage.googleapis.com"
            repo_addr = "https://charts.helm.sh/stable"
        elif repo_name == "incubator":
            repo_addr = "https://charts.helm.sh/incubator"
        elif repo_name.find("prometheus") != -1:
            repo_addr = "https://prometheus-community.github.io/helm-charts"
        elif repo_name.find("bitnami") != -1:
            repo_addr = "https://charts.bitnami.com/bitnami"
        output = self.h.add_repo(repo_name, repo_addr)
        output = self.h.search_repo(app_name)
        for line in output.split("\n"):
            if line.find(app_name) != -1:
                print "- Search App(%s) in Helm repositories(%s)" % (app_name, repo_addr)
                ret = 0
                break
        output = self.h.update_repo()
        print output
        return ret

    def install_helm_app(self, repo_name, app_name):
        ret = -1
        if app_name.find("prometheus") != -1 and repo_name.find("exporter") == -1:
            output = self.h.install_app("my-prometheus-operator", "%s/kube-prometheus-stack" % repo_name, "monitoring", config_path="")

        if app_name.find("redis") != -1 and repo_name.find("prometheus") != -1:
            output = self.h.install_app(app_name, "%s/prometheus-redis-exporter" % repo_name, app_namespace, "%s/prometheus/prom-values.yaml" % (config_path))

        if repo_name.find("bitnami") != -1:
            output = self.h.install_app(app_name, "%s/rabbitmq" % repo_name, app_namespace, "%s/bitnami/rabbitmq-values.yaml" % (config_path))
        if repo_name.find("rabbitmq") != -1:
            # stable/prometheus-rabbitmq-exporter
            output = self.h.install_app(app_name, "prometheus-community/prometheus-rabbitmq-exporter", app_namespace, "%s/rabbitmq-exporter.yaml" % config_path)

        # check
        namespace = self.namespace
        if app_name.find("prometheus") != -1:
            namespace = "monitoring"
        output = self.h.list_app(namespace)
        for line in output.split("\n"):
            if line.find(app_name) != -1:
                print "- Helm package(%s) is installed" % app_name
                ret = 0
                break
        return ret

    def delete_helm_app(self, app_name):
        ret = 0
        # check
        namespace = self.namespace
        if app_name.find("prometheus") != -1:
            namespace = "monitoring"
        output = self.h.list_app(namespace)
        for line in output.split("\n"):
            if line.find(app_name) != -1:
                print "- Helm package(%s) is not uninstalled" % app_name
                ret = -1
        print ret
        if ret == 0:
            print "- Helm package(%s) is uninstalled" % app_name
        return output

    def check_storage(self, app_name):
        volume_list = []
        output = self.o.get_pvc(self.namespace)
        for line in output.split("\n"):
            if line.find(app_name) != -1:
                volume = line.split()[0]
                volume_list.append(volume)
        print "- Find persistent volumme: ", volume_list
        return volume_list

    def delete_storage(self, app_name):
        ret = -1
        volume_list = self.check_storage(app_name)
        for volume in volume_list:
            output = self.o.delete_pvc(volume, self.namespace)
            print output

        num_volume = self.query_storage(app_name, 0)
        if num_volume == 0:
            ret = 0
            print "- Delete App(%s)'s persistent volume"
        return ret

    def query_storage(self, app_name, storage_threshold):
        num_volume = 0
        for i in range(self.iterations):
            volume_list = self.check_storage(app_name)
            num_volume = len(volume_list)
            if num_volume == storage_threshold and storage_threshold != 0:
                print "- %d storages are created for App(%s)" % (num_volume, app_name)
                break
            elif num_volume == storage_threshold and storage_threshold == 0:
                print "- %d storages are deleted for App(%s)" % (num_volume, app_name)
                break
            else:
                start_time = int(time.time())
                self.wait_time(start_time)
        return num_volume

    def find_app_pod(self, app_name):
        pod_list = []
        try:
            output = self.o.get_pods(self.namespace)
            for line in output.split("\n"):
                if line.find(app_name) != -1 and line.find("Running") != -1:
                    pod = line.split()[0]
                    pod_list.append(pod)
        except Exception as e:
            print "- Failed to find App(%s) pod: %s" % (app_name, str(e))
            return pod_list
        print "- Find App(%s)'s %d pods(%s) in ns (%s)" % (app_name, len(pod_list), pod_list, self.namespace)
        return pod_list

    def find_service_by_namespace(self, app_name, namespace, is_node_type=False):
        ip = ""
        port = ""
        output = self.o.get_service(namespace)
        for line in output.split("\n"):
            if line.find(app_name) != -1:
                ip = line.split()[2]
                port = line.split()[4].split(":")[0].split("/")[0]
                if is_node_type:
                    port = line.split()[4].split(":")[1].split("/")[0]
                break
        host = "%s:%s" % (ip, port)
        print "- Find service(%s)'s host(%s) is in namespace(%s)\n" % (app_name, host, namespace)
        return host

    def find_pod_host_by_namespace(self, app_name, namespace):
        ip = ""
        port = "6379"
        print app_name, namespace
        output = self.o.get_pod_wide(app_name, namespace)
        for line in output.split("\n"):
            if line.find(app_name) != -1:
                ip = line.split()[-4]
                break
        host = "%s:%s" % (ip, port)
        print "- Find pod(%s)s' host(%s) is in namespace(%s)\n" % (app_name, host, namespace)
        return host

    def replace_parameters_by_sed(self, term, entry, file_name):
        cmd = "sed -i 's/%s:.*/%s: %s /g' %s" % (term, term, entry, file_name)
        ret = os.system(cmd)
        if ret != 0:
            print "- Failed to update %s(%s) in %s" % (term, entry, file_name)
        return ret

    def update_service_type(self, app_name, namespace):
        file_name = "%s/prometheus/%s" % (config_path, "%s.yaml" % app_name)
        self.k.get_app_service_yaml_file(app_name, namespace, file_name)
        self.replace_parameters_by_sed("type", "NodePort", file_name)
        output = self.o.apply_file(file_name, namespace)
        print "- Update service(%s)'s type in namespace(%s) to NodePort" % (app_name, namespace)
        self.find_service_by_namespace(app_name, namespace, is_node_type=True)

    def find_pod_by_namespace(self, namespace, app_name):
        pod_name = ""
        output = self.o.get_pods(namespace)
        for line in output.split("\n"):
            if line.find(app_name) != -1:
                pod_name = line.split()[0]
                break
        print "- Find App(%s)'s Pod(%s) in namespace(%s)" % (app_name, pod_name, namespace)
        return pod_name



def create_metrics():
    print "=" * 80
    print "Install Metric-server"
    c = Config()
    c.add_helm_repo("stable", "metric-server")
    h = Helm()
    file_name = "%s/metrics-server.yaml" % config_path
    h.install_app("metrics-server", "stable/metrics-server", "kube-system", value_file=file_name)
    h.list_app("kube-system")
    print "- Metric-server is installed"
    print "\n"


def delete_metrics():
    print "=" * 80
    print "Uninstall Metrics server"
    h = Helm()
    h.delete_app("metrics-server", "kube-system")
    h.list_app("kube-system")
    print "- Metrics server is uninstalled"
    print "\n"


def show_metrics():
    k = Kubectl()
    k.top_pods(app_namespace)
    k.top_nodes()


def create_prometheus():
    print "=" * 80
    print "Install Prometheus "
    c = Config()
    o = OC()
    o.create_ns("monitoring")
    c.add_helm_repo("prometheus-community", "prometheus")
    c.install_helm_app("prometheus-community", "my-prometheus-operator")
    c.query_app_status("alertmanager-my-prometheus-operator-kub-alertmanager", 1, namespace="monitoring")
    c.query_app_status("my-prometheus-operator-grafana", 1, namespace="monitoring")
    c.query_app_status("my-prometheus-operator-kub-operator", 1, namespace="monitoring")
    c.query_app_status("my-prometheus-operator-kube-state-metrics", 1, namespace="monitoring")
    c.query_app_status("prometheus-my-prometheus-operator-kub-prometheus", 1, namespace="monitoring")

    c.update_service_type("my-prometheus-operator-grafana", "monitoring")
    c.update_service_type("my-prometheus-operator-kub-prometheus", "monitoring")
    print "- Grafana's username/password is admin/prom-operator"
    print "- Import grafana GUI in ./grafana: \n"
    print "- Prometheus is installed"
    print "\n"


def delete_prometheus():
    print "=" * 80
    print "Delete Prometheus "
    c = Config()
    o = OC()
    h = Helm()
    h.delete_app("my-prometheus-operator", app_namespace)
    c.query_app_status("alertmanager-my-prometheus-operator-kub-alertmanager", 0, namespace="monitoring")
    c.query_app_status("my-prometheus-operator-grafana", 0, namespace="monitoring")
    c.query_app_status("my-prometheus-operator-kub-operator", 0, namespace="monitoring")
    c.query_app_status("my-prometheus-operator-kube-state-metrics", 0, namespace="monitoring")
    c.query_app_status("prometheus-my-prometheus-operator-kub-prometheus", 0, namespace="monitoring")


def create_bitnami():
    print "=" * 80
    print "Create Bitnami"
    c = Config()
    o = OC()
    o.create_ns(app_namespace)
    c.add_helm_repo("bitnami", "bitnami")
    c.install_helm_app("bitnami", cluster_name)
    c.query_app_status("%s-rabbitmq" % cluster_name, 1, app_namespace)

    file_name = "%s/deploy-publisher.yaml" % config_path
    output = o.apply_file(file_name, app_namespace)
    file_name = "%s/deploy-consumer.yaml" % config_path
    output = o.apply_file(file_name, app_namespace)

    c.query_app_status("rabbitmq-publisher", 1, app_namespace)
    c.query_app_status("rabbitmq-consumer", app_replica_number, app_namespace)
    # helm install my-test -f rabbitmq-exporter.yaml -n bitnami stable/prometheus-rabbitmq-exporter
    c.install_helm_app("rabbitmq-exporter", "my-test")
    c.query_app_status("my-test-prometheus-rabbitmq-exporter", 1, app_namespace)


def delete_bitnami():
    print "=" * 80
    print "Delete Bitnami"
    h = Helm()
    c = Config()
    o = OC()
    file_name = "%s/deploy-publisher.yaml" % config_path
    output = o.delete_file(file_name, app_namespace)
    file_name = "%s/deploy-consumer.yaml" % config_path
    output = o.delete_file(file_name, app_namespace)

    h.delete_app(app_name_prefix, app_namespace)
    c.query_app_status("rabbitmq-publisher", 0, app_namespace)
    c.query_app_status("rabbitmq-consumer", 0, app_namespace)

    h.delete_app("my-release", app_namespace)
    c.query_app_status("%s-rabbitmq" % cluster_name, 0, app_namespace)

    h.delete_app("my-test", app_namespace)
    c.query_app_status("my-test", 0, app_namespace)


def create_all():
    print "="*80
    print "Install All Applications"
    o = OC()
    create_bitnami()
    print "- All applications are installed"
    print "\n"


def delete_all():
    print "="*80
    print "Uninstall All Applications"
    delete_bitnami()
    print "\n"
    print "- All applications are uninstalled"
    print "\n"


def main(app_name, action, is_force=False, is_fed=False):
    if app_name == "metrics":
        if action == "create":
            create_metrics()
        elif action == "delete":
            delete_metrics()
        else:
            show_metrics()

    elif app_name == "prometheus":
        if action == "create":
            create_prometheus()

    elif app_name == "all":
        if action == "create":
            create_all()
        else:
            delete_all()

    elif app_name == "bitnami":
        if action == "create":
            create_bitnami()
        elif action == "delete":
            delete_bitnami()


if __name__ == "__main__":
    try:
        app_name = sys.argv[1]
        action = sys.argv[2]
        main(app_name, action)
    except Exception as e:
        print "Exception:"
        print "- %s" % str(e)
        print "python run_config.py <app_name> <action>"
        print "- app_name:  bitnami, node, exporter, adapter, metrics or prometheus"
        print "- action:  create, delete or show"
