import os
import json


class Kubectl:

    cmd = "kubectl"

    def __init__(self):
        pass

    def get_pod_by_namespace(self, namespace):
        cmd = "%s get pods --show-labels -o wide -n %s" % (self.cmd, namespace)
        output = os.popen(cmd).read()
        return output

    def get_pod(self):
        cmd = "%s get pods --show-labels -o wide --all-namespaces" % self.cmd
        output = os.popen(cmd).read()
        return output

    def top_pod(self, pod_name, namespace):
        cmd = "%s top pod %s -n %s" % (self.cmd, pod_name, namespace)
        output = os.popen(cmd).read()
        return output

    def top_pods(self, namespace):
        cmd = "%s top pods -n %s" % (self.cmd, namespace)
        output = os.popen(cmd).read()
        print output
        return output

    def get_svc(self):
        cmd = "%s get svc --show-labels -o wide --all-namespaces" % self.cmd
        output = os.popen(cmd).read()
        return output

    def get_deployment(self):
        cmd = "%s get deployment --show-labels -o wide --all-namespaces" % self.cmd
        output = os.popen(cmd).read()
        return output

    def get_statefulset(self):
        cmd = "%s get statefulset --show-labels -o wide --all-namespaces" % self.cmd
        output = os.popen(cmd).read()
        return output

    def get_daemonset(self):
        cmd = "%s get daemonset --show-labels -o wide --all-namespaces" % self.cmd
        output = os.popen(cmd).read()
        return output

    def get_replicaset(self):
        cmd = "%s get replicaset --show-labels -o wide --all-namespaces" % self.cmd
        output = os.popen(cmd).read()
        return output

    def get_ns(self):
        cmd = "%s get ns" % self.cmd
        output = os.popen(cmd).read()
        return output

    def scale_replica(self, namespace, resource_type, resource, num_replica):
        ret = 0
        cmd = "%s scale --replicas=%d %s/%s -n %s" % (self.cmd, num_replica, resource_type, resource, namespace)
        print cmd
        ret = os.system(cmd)
        return ret

    def get_deployment_by_jason(self, namespace, deployment):
        cmd = "%s get deployment %s -n %s -o json" % (self.cmd, deployment, namespace)
        output = json.loads(os.popen(cmd).read())
        return output

    def top_node(self, node_name):
        cmd = "%s top node %s" % (self.cmd, node_name)
        output = os.popen(cmd).read()
        return output

    def top_nodes(self):
        cmd = "%s top nodes" % (self.cmd)
        output = os.popen(cmd).read()
        print output
        return output

    def patch_deployment(self, namespace, deployment, output):
        cmd = '%s patch deployment %s --patch "$(cat %s)" -n %s' % (self.cmd, deployment, output, namespace)
        output = os.popen(cmd).read()
        return output

    def get_raw_custom_metrics(self, add_cmd=""):
        cmd = 'kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/"'
        if add_cmd:
            cmd = 'kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/%s"' % add_cmd
        print cmd
        output = os.popen(cmd).read()
        return output

    def autoscale_replica(self, resource, app_name, namespace, min_replica, max_replica, cpu_percent):
        cmd = '%s autoscale %s/%s -n %s --min=%s --max=%s --cpu-percent=%s' % (self.cmd, resource, app_name, namespace, min_replica, max_replica, cpu_percent)
        print cmd
        output = os.popen(cmd).read()
        return output

    def delete_hpa(self, app_name, namespace):
        cmd = '%s delete hpa %s -n %s' % (self.cmd, app_name, namespace)
        print cmd
        output = os.popen(cmd).read()
        return output

    def get_hpa(self, namespace):
        cmd = '%s get hpa -n %s' % (self.cmd, namespace)
        print cmd
        output = os.popen(cmd).read()
        return output

    def get_all(self, namespace):
        cmd = '%s get all -n %s' % (self.cmd, namespace)
        print cmd
        output = os.popen(cmd).read()
        return output

    def get_app_service_yaml_file(self, app, namespace, file_name):
        cmd = '%s get service %s -n %s -o yaml > %s ' % (self.cmd, app, namespace, file_name)
        output = os.popen(cmd).read()
        return output
