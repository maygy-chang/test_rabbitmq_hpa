import sys
import os
import time
import argparse
from oc import OC
from define import traffic_interval, data_interval, number_k8shpa
from define import warm_up, number_nonhpa, config_path, transaction_timeout, prometheus_operator_name, app_replica_number
from define import app_namespace, app_name_prefix, main_app_name
from run_hpa import get_dir_name, clean_data, delete_k8s_hpa, find_pod_name, restart_pod, create_directory
from generate_traffic import initialize_traffic


def start_algo(algo, app_name):
    print "- Start algorithm (%s) for %s" % (algo, app_name)
    cmd = "python ./run_hpa.py %s start & " % (algo)
    ret = os.system(cmd)
    return ret


def stop_algo(algo, app_name):
    print "- Stop algorithm (%s) for %s" % (algo, app_name)
    cmd = "python ./run_hpa.py %s stop & " % (algo)
    ret = os.system(cmd)
    return ret


def write_logs(algo):
    ret = 0
    if prometheus_operator_name:
        # cmd = "python ./write_prometheus_log.py %s %s &" % (algo, data_interval)
        # ret = os.system(cmd)
        pass
    if algo.find("k8shpa") != -1:
        cmd = "python ./write_hpa_log.py %s &" % (data_interval)
        ret = os.system(cmd)
    return ret


def generate_traffic(algo, app_name):
    print "- Generate traffic for %s" % app_name
    cmd = "python ./generate_traffic.py %s %d &" % (algo, traffic_interval)
    ret = os.system(cmd)
    return ret


def wait_time(count):
    print "- Wait %d seconds to run main" % count
    time.sleep(count)


def run_scenario(test_case, app_name, i):
    algo = test_case
    print "=== Start to Run HPA Test(%s): %d ===" % (algo, i)
    start_algo(algo, app_name)
    initialize_traffic()
    generate_traffic(algo, app_name)  # warm up + traffic
    # warm up:
    # - generate a fixed workload to initialize apps
    # - do not collect warmup data dute do initial spikes of apps
    # traffic:
    # - start to generate a customed workload
    wait_time(warm_up*60)  # warm up and do not collect data

    algo_interval = traffic_interval
    algo_name = get_dir_name(algo)
    write_logs(algo_name)  # start to collect data

    wait_time((data_interval)*60)
    wait_time(180)  # wait to complete tracing

    print "- Stop to Run HPA Test(%s)" % (algo)
    stop_algo(algo, app_name)
    wait_time(300)  # wait to rename traces


def get_test_case_list():
    test_case_list = []
    for i in range(number_k8shpa):
        test_case_list.append("k8shpa")
    for i in range(number_nonhpa):
        test_case_list.insert(i, "nonhpa")
    print "- The order of algorithms is: ", ",".join(test_case_list)
    return test_case_list


def main(app_name):
    print "=== HPA Test ==="
    print "--- Start to Run K8sHPA Test x %d ---" % (number_k8shpa)
    start_time = time.time()
    i = 0
    test_case_list = get_test_case_list()
    for test_case in test_case_list:
        run_scenario(test_case, app_name, i)
    end_time = time.time()
    duration = (end_time - start_time)/60
    print "- It takes %d minutes" % duration


def kill_process():
    # kill data
    cmd = "killall -9 python"
    print cmd
    os.system(cmd)
    cmd = "sh cleanup.sh"
    print cmd
    os.system(cmd)


def initial_environment():
    print "=== Initial Configuration ==="
    create_directory()
    clean_data()


def check_environment():
    print "- Checking RabbitMQ..."
    try:
        pass
    except Exception as e:
        print str(e)
        sys.exit(-1)


def do_main(args):
    app_name = args.app_name[0]
    ret = OC().check_platform()
    if ret == 0:
        user = args.user[0]
        passwd = args.password[0]
        OC().login(user, passwd)

    try:
        initial_environment()
        check_environment()
        main(app_name)
    except KeyboardInterrupt:
        print "pgogram exit with keyboard interrupt"
        kill_process()
    except Exception as e:
        print "- Failed to test HPA: %s" % str(e)
        kill_process()
    return 0


def main_proc(argv):
    ret = OC().check_platform()
    if ret == 0:
        commands = [(do_main, "hpa", "Run HPA Test", [("app_name", "application name (deployment/deploymentconfig name)"), ("user", "login user name"), ("password", "password for login user")])]
    else:
        commands = [(do_main, "hpa", "Run HPA Test", [("app_name", "application name (deployment/deploymentconfig name)")])]

    try:
        parser = argparse.ArgumentParser(prog="", usage=None, description="Federator.ai management tool", version=None, add_help=True)
        parser.print_usage = parser.print_help
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)

        # subparsers for commands
        subparsers = parser.add_subparsers(help="commands")

        for function, title, desc, args_list in commands:
            # format: (function_name, parser_name, parser_desc, [(args1, args1_desc), (args2, args2_desc), ...])
            # Add command parser
            p = subparsers.add_parser(title, help=desc)
            p.set_defaults(function=function)
            for arg, arg_desc in args_list:
                p.add_argument(arg, nargs=1, help=arg_desc)

        # Run the function
        args = parser.parse_args()
        retcode = args.function(args)  # args.function is the function that was set for the particular subparser
    except ValueError as e:
        print("- Error in argument parsing. [%s]" % e)
        sys.exit(-1)

    sys.exit(retcode)


if __name__ == "__main__":
    main_proc(sys.argv)
