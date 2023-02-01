import time
import os
import sys
import json
from random import choice, randint
from oc import OC
from define import traffic_ratio, traffic_interval, config_path, traffic_freq, workload_type
from define import main_app_name, app_namespace, transaction_value
from define import app_name_prefix, parallel_conn, cluster_name


class RabbitmqBenchmark:
    oc = OC()
    host = ""
    port = 5672
    username = "user"
    password = "password"
    namespace = app_namespace

    def __init__(self):
        self.host, self.port = self.find_service_by_namespace(cluster_name)

    def run_cmd(self, cmd):
        pod_name_list = self.find_pod_by_namespace(self.namespace, main_app_name)
        pod_name = pod_name_list[0]
        output = self.oc.exec_cmd(self.namespace, pod_name, cmd, is_show=True)
        return output

    def find_pod_by_namespace(self, namespace, app_name):
        pod_name_list = []
        output = self.oc.get_pods(namespace)
        for line in output.split("\n"):
            if line.find(app_name) != -1:
                pod_name = line.split()[0]
                pod_name_list.append(pod_name)
        return pod_name_list

    def find_service_by_namespace(self, app_name):
        service_name = ""
        port = self.port
        output = self.oc.get_service(self.namespace)
        for line in output.split("\n"):
            print line, app_name
            if line.find(app_name) != -1 and line.find("headless") == -1:
                service_name = line.split()[0]
        print "- Find RabbitMQ Host(%s)" % service_name
        return service_name, port

    def run_rabbitmq_traffic(self, req_count, freq_count):
        print "- Run RabbitMQ-Benchmark Traffic to RabbitMQ"
        cmd = ""
        transaction_list = self.get_transaction_list()
        trans_num = (transaction_value * traffic_ratio / traffic_freq)
        if workload_type != "fix":
            new_req_count = req_count % len(transaction_list)
            transaction_num = transaction_list[new_req_count] * traffic_ratio
            trans_num = int(transaction_num/traffic_freq)
        print "- %d-%dth start to generate %d clients and %d transactions to host(%s)" % (req_count, freq_count, parallel_conn, trans_num, self.host)
        output = self.run_traffic(trans_num)
        self.write_workload(output, req_count, freq_count)
        return cmd

    def get_transaction_list(self):
        transaction_list = []
        fn = "./transaction.txt"
        with open(fn, "r") as f:
            output = f.read()
            for line in output.split("\n"):
                if line:
                    transaction = int(float(line.split()[0]))
                    transaction_list.append(transaction)
        return transaction_list

    def write_workload(self, output, workload_id, freq_id):
        fn = "./traffic/rabbitmq-benchmark-%d-%d" % (workload_id, freq_id)
        with open(fn, "w") as f:
            for line in output.split("\n"):
                f.write("%s\n" % line)
        print "- Workload: %s/%d is completed" % (fn, traffic_interval)

    def run_traffic(self, trans_num):
        cmd = "send amqp://%s:%s@%s %s " % (self.username, self.password, self.host, trans_num)
        output = self.run_cmd(cmd)
        return output


def main(count, freq):
    r = RabbitmqBenchmark()
    r.run_rabbitmq_traffic(count, freq)


if __name__ == "__main__":
    try:
        request_count = int(sys.argv[1])
        freq_count = int(sys.argv[2])
        main(request_count, freq_count)
    except Exception as e:
        print "- Failed to run rabbitmq benchmark: %s" % str(e)
        print "python run_rabbitmq_benchmark <num_of_operations> <exe_order>"
        print "num_of_operations: number of operations"
        print "exe_order: execution order"
