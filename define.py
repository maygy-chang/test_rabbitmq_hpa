# application info
cluster_name = 'my-release'
app_namespace = "bitnami"  # initial namespace
app_name_prefix = "rabbitmq-consumer"  # shard prefix name
consumer_name_list = ["rabbitmq-consumer"]
app_replica_number = 1  # number of replica nodes per replicaset
main_app_name = "rabbitmq-publisher"
clean_data_first = False

# # test case
number_k8shpa = 0
number_nonhpa = 1
k8shpa_type = "cpu"  # cpu, index, index_time, or mix
k8shpa_percent = 1
k8shpa_min_node = 1  # number of min replicas
k8shpa_max_node = 50  # number of max replicas

# configuration
traffic_path = "./traffic"
metrics_path = "./metrics"
picture_path = "./picture"
config_path = "./config"
pattern_path = "./pattern"

# # traffic - sysbench info
traffic_ratio = 10  # to create continue workloads
traffic_path = "./traffic"
traffic_interval = 50  # generate traffic per 1 minute during 72 minutes
traffic_freq = 2  # generate traffic 3 times per 1 minute
parallel_conn = 100  # number of clients
data_interval = traffic_interval + 5  # generate traffic per 1 minute during 72 minutes
warm_up = 10  # default 10 min
workload_type = "vary"  # fix: fix workload; vary: vary workload
transaction_value = 100  # avg. workload = 74.8
transaction_timeout = 1000  # max execution time (seconds)
granularity = 60
traffic_pattern = "transaction.txt.sinewave1h"

# log
log_interval = 30  # collect data per 30 seconds
query_interval = 1
query_timeout = log_interval

# prometheus
prometheus_operator_name = "my-prometheus-operator-kub-prometheus"
