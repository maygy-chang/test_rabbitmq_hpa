import subprocess
import os


class OC:
    cmd = "oc"

    def __init__(self):
        ret = self.check_platform()
        if ret != 0:
            self.cmd = "kubectl"

    def check_platform(self):
        cmd = "oc > /dev/null 2>&1"
        ret = os.system(cmd)
        return ret

    def run_cmd(self, cmd, is_show=False):
        if is_show:
            print cmd
        output = os.popen(cmd).read()
        return output

    def run_subprocess_cmd(self, cmd, is_show=False):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        (stdout, stderr) = p.communicate()
        _ = p.wait()
        output = stdout
        if is_show:
            print output
        return output

    def run_os_cmd(self, cmd):
        ret = os.system(cmd)
        return ret

    def describe_secret(self, namespace, pod):
        cmd = "%s describe secret %s -n %s" % (self.cmd, pod, namespace)
        output = self.run_cmd(cmd)
        return output

    def get_secret_by_specific_name(self, namespace, name):
        cmd = "%s get secret -n %s | grep %s" % (self.cmd, namespace, name)
        output = self.run_cmd(cmd)
        return output

    def get_secret_yaml(self, secret_name, namespace):
        cmd = "%s get secret %s -n %s -o yaml " % (self.cmd, secret_name, namespace)
        output = self.run_cmd(cmd)
        return output

    def get_pods(self, namespace):
        cmd = "%s get pods -n %s" % (self.cmd, namespace)
        output = self.run_cmd(cmd)
        return output

    def login(self, user, password):
        cmd = "%s login -u %s -p %s 2>1 > /dev/null" % (self.cmd, user, password)
        ret = self.run_os_cmd(cmd)
        print "login Openshift by %s" % user
        return ret

    def get_deploymentconfig(self, ns):
        cmd = "%s get deploymentconfig -n %s" % (self.cmd, ns)
        output = self.run_cmd(cmd)
        return output

    def get_deployment(self, ns):
        cmd = "%s get deployment -n %s" % (self.cmd, ns)
        output = self.run_cmd(cmd)
        return output

    def delete_deployment(self, app_name, ns):
        cmd = "%s delete deployment %s -n %s" % (self.cmd, app_name, ns)
        output = self.run_cmd(cmd)
        return output

    def get_statefulset(self, ns):
        cmd = "%s get statefulset -n %s" % (self.cmd, ns)
        output = self.run_cmd(cmd)
        return output

    def delete_statefulset(self, app_name, ns):
        cmd = "%s delete statefulset %s -n %s" % (self.cmd, app_name, ns)
        output = self.run_cmd(cmd)
        return output

    def get_statefulset_yaml(self, app_name, ns):
        cmd = "%s get statefulset %s -o yaml -n %s" % (self.cmd, app_name, ns)
        output = self.run_cmd(cmd)
        return output

    def get_pvc(self, ns):
        cmd = "%s get pvc -n %s" % (self.cmd, ns)
        output = self.run_cmd(cmd)
        return output

    def delete_pvc(self, pvc, ns):
        cmd = "%s delete pvc %s -n %s" % (self.cmd, pvc, ns)
        print cmd
        output = self.run_cmd(cmd)
        return output

    def apply_file(self, file_name, namespace="", is_show=False):
        cmd = "%s apply -f %s" % (self.cmd, file_name)
        if namespace:
            cmd = "%s apply -f %s -n %s" % (self.cmd, file_name, namespace)
        output = self.run_cmd(cmd, is_show=is_show)
        return output

    def delete_file(self, file_name, namespace, is_show=False):
        cmd = "%s delete -f %s" % (self.cmd, file_name)
        if namespace:
            cmd = "%s delete -f %s -n %s" % (self.cmd, file_name, namespace)
        output = self.run_cmd(cmd, is_show=is_show)
        return output

    def set_pod_env_list(self, pod_name):
        cmd = "%s set env pod %s --list" % (self.cmd, pod_name)
        output = self.run_cmd(cmd)
        return output

    def exec_cmd(self, namespace, pod_name, command, is_show=False):
        cmd = "%s -n %s exec -i %s -- %s" % (self.cmd, namespace, pod_name, command)
        if is_show:
            print cmd
        output = self.run_subprocess_cmd(cmd)
        return output

    def exec_cat(self, namespace, pod_name, file_name):
        cmd = "%s -n %s exec -i %s -- cat %s" % (self.cmd, namespace, pod_name, file_name)
        print cmd
        output = self.run_subprocess_cmd(cmd)
        return output

    def expose_service(self, namespace, service_name):
        cmd = "%s -n %s expose %s" % (self.cmd, namespace, service_name)
        output = self.run_cmd(cmd)
        return output

    def get_service(self, namespace):
        cmd = "%s get service -n %s" % (self.cmd, namespace)
        output = self.run_cmd(cmd)
        return output

    def delete_service(self, service_name, namespace):
        cmd = "%s delete service %s -n %s" % (self.cmd, service_name, namespace)
        output = self.run_cmd(cmd)
        return output

    def scale_replica(self, namespace, resource_type, resource, num_replica):
        cmd = "%s scale %s %s --replicas=%d -n %s &" % (self.cmd, resource_type, resource, num_replica, namespace)
        print cmd
        output = self.run_cmd(cmd)
        return output

    def get_pod_json(self, pod, namespace):
        cmd = "%s get pod %s -n %s -o json" % (self.cmd, pod, namespace)
        output = self.run_cmd(cmd)
        return output

    def get_nodes(self):
        cmd = "%s get nodes" % self.cmd
        output = self.run_cmd(cmd)
        return output

    def delete_pod(self, pod_name, namespace):
        cmd = "%s delete pod %s -n %s " % (self.cmd, pod_name, namespace)
        output = self.run_cmd(cmd)
        return output

    def get_routes(self, namespace):
        cmd = "%s get routes -n %s " % (self.cmd, namespace)
        output = self.run_cmd(cmd)
        return output

    def autoscale_replica(self, namespace, resource_type, resource, num_replica, percent):
        cmd = "%s autoscale %s %s --max=%d --cpu-percent=%s -n %s" % (self.cmd, resource_type, resource, num_replica, percent, namespace)
        output = self.run_cmd(cmd)
        return output

    def delete_hpa(self, namespace, resource):
        cmd = "%s delete hpa %s -n %s" % (self.cmd, resource, namespace)
        output = self.run_cmd(cmd)
        return output

    def get_services_all_namespace(self):
        cmd = "%s get services --all-namespaces" % self.cmd
        output = self.run_cmd(cmd)
        return output

    def get_pods_all_namespace(self):
        cmd = "%s get pods --all-namespaces" % self.cmd
        output = self.run_cmd(cmd)
        return output

    def get_deployments_all_namespace(self):
        cmd = "%s get deployments --all-namespaces" % self.cmd
        output = self.run_cmd(cmd)
        return output

    def get_statefulsets_all_namespace(self):
        cmd = "%s get statefulsets --all-namespaces" % self.cmd
        output = self.run_cmd(cmd)
        return output

    def get_deploymentconfigs_all_namespace(self):
        cmd = "%s get deploymentconfigs --all-namespaces" % self.cmd
        output = self.run_cmd(cmd)
        return output

    def get_specific_deploymentconfig(self, app_namespace, resource):
        cmd = "%s get deploymentconfig %s -n %s -o yaml" % (self.cmd, resource, app_namespace)
        output = self.run_cmd(cmd)
        return output

    def get_specific_deployment(self, app_namespace, resource):
        cmd = "%s get deployment %s -n %s -o yaml" % (self.cmd, resource, app_namespace)
        print cmd
        output = self.run_cmd(cmd)
        return output

    def patch_deployment(self, namespace, deployment, output):
        cmd = '%s patch deployment %s --type merge --patch "$(cat %s)" -n %s' % (self.cmd, deployment, output, namespace)
        # print cmd
        output = self.run_cmd(cmd)
        return output

    def patch_statefulset(self, namespace, statefulset, output):
        cmd = '%s patch statefulset %s --type merge --patch "$(cat %s)" -n %s' % (self.cmd, statefulset, output, namespace)
        output = self.run_cmd(cmd)
        return output

    def patch_deploymentconfig(self, namespace, deploymentconfig, output):
        cmd = '%s patch deploymentconfig %s --patch "$(cat %s)" -n %s' % (self.cmd, deploymentconfig, output, namespace)
        output = self.run_cmd(cmd)
        return output

    def get_configmap(self, namespace, configmap):
        cmd = "%s get configmap %s -n %s -o json" % (self.cmd, configmap, namespace)
        output = self.run_cmd(cmd)
        return output

    def log_pod(self, namespace, pod):
        cmd = "%s log %s -n %s" % (self.cmd, pod, namespace)
        output = self.run_cmd(cmd)
        return output

    def get_topics(self, namespace):
        cmd = "%s get kafkatopic -n %s" % (self.cmd, namespace)
        output = self.run_cmd(cmd)
        return output

    def delete_topics(self, namespace):
        cmd = "%s delete kafkatopic -n %s" % (self.cmd, namespace)
        output = self.run_cmd(cmd)
        return output

    def label_node(self, node_name, label_name):
        cmd = "%s label node %s %s --overwrite=true" % (self.cmd, node_name, label_name)
        # print cmd
        output = self.run_cmd(cmd)
        return output

    def get_nodes(self):
        cmd = "%s get nodes --show-labels" % self.cmd
        output = self.run_cmd(cmd)
        return output

    def create_ns(self, namespace):
        cmd = "%s create ns %s" % (self.cmd, namespace)
        output = self.run_cmd(cmd)
        return output

    def get_pods_wide(self, namespace):
        cmd = "%s get pods -o wide -n %s" % (self.cmd, namespace)
        output = self.run_cmd(cmd)
        return output
