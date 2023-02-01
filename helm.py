import os
import json
from oc import OC


class Helm:
    cmd = "helm"

    def __init__(self):
        pass

    def run_cmd(self, cmd):
        print cmd
        output = os.popen(cmd).read()
        return output

    def add_repo(self, repo_name, repo_url):
        cmd = "%s repo add %s %s" % (self.cmd, repo_name, repo_url)
        output = self.run_cmd(cmd)
        return output

    def search_repo(self, repo_name):
        cmd = "%s search repo %s" % (self.cmd, repo_name)
        output = self.run_cmd(cmd)
        return output

    def install_app(self, app_name, repo_addr, namespace, value_file="", config_path=""):
        cmd = "%s install %s %s --namespace %s " % (self.cmd, app_name, repo_addr, namespace)
        if value_file:
            cmd = "%s install %s -f %s %s --namespace %s " % (self.cmd, app_name, value_file, repo_addr, namespace)
        if config_path:
            cmd += config_path
        output = self.run_cmd(cmd)
        return output

    def delete_app(self, app_name, namespace):
        cmd = "%s delete %s --namespace %s " % (self.cmd, app_name, namespace)
        output = self.run_cmd(cmd)
        return output

    def list_app(self, namespace):
        cmd = "%s list --namespace %s " % (self.cmd, namespace)
        output = self.run_cmd(cmd)
        # print output
        return output

    def update_repo(self):
        cmd = "helm repo update"
        output = self.run_cmd(cmd)
        return output

    def update_app_by_commands(self, app_name, namespace, repo_addr, commands):
        cmd = "%s upgrade %s --namespace %s %s %s" % (self.cmd, app_name, namespace, repo_addr, commands)
        output = self.run_cmd(cmd)
        return output
