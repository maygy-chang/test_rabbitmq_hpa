import os
import time
import sys
from define import warm_up, traffic_freq

query_timeout = 60


def wait_time(start_time, query_limit):
    count = 0
    while True:
        end_time = time.time()
        diff_time = end_time - start_time
        if diff_time >= query_limit:
            # print "- Wait %s seconds..." % diff_time
            break
        count += 1
        # print "wait 1 seconds", count
        time.sleep(1)


def initialize_traffic():
    print "--- Warm Up: %d Minutes ---" % warm_up
    for i in range(warm_up):
        print "Warm up: generate %d/%d workloads" % (i, warm_up)
        start_time = time.time()
        for j in range(traffic_freq):
            start_time1 = time.time()
            cmd = "python ./run_rabbitmq_benchmark.py %d %d &" % (0, j)
            ret = os.system(cmd)
            query_limit = int(query_timeout/traffic_freq)
            wait_time(start_time1, query_limit)
        wait_time(start_time, query_timeout)


def generate_traffic(time_count):
    print "--- Generate Traffic For %d Munites ---" % time_count
    for i in range(time_count):
        print "generate %d th workloads" % i
        start_time = time.time()
        for j in range(traffic_freq):
            start_time1 = time.time()
            cmd = "python ./run_rabbitmq_benchmark.py %d %d &" % (i, j)
            ret = os.system(cmd)
            query_limit = int(query_timeout/traffic_freq)
            wait_time(start_time1, query_limit)
        wait_time(start_time, query_timeout)


def main(time_count, action):
    total_start_time = time.time()
    print "=== Generate Traffic for %d Minutes ===" % time_count

    if action == "warmup":
        initialize_traffic()

    else:
        generate_traffic(time_count)

    total_end_time = time.time()
    print "- Completed!!!", (total_end_time - total_start_time)/60, "minutes"


if __name__ == "__main__":
    try:
        action = sys.argv[1]
        time_count = int(sys.argv[2])
        main(time_count, action)
    except Exception as e:
        print "- Failed to generate traffic: %s" % str(e)
        print "python generate_traffic.py <action> <exe_times>"
        print "action: warmup or traffic"
        print "exe_times: execution times"
