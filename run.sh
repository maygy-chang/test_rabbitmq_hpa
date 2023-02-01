#!/bin/bash

show_usage()
{
    cat << __EOF__

    Usage:
    Requirement:
        [-w Initial Replica number] # e.g. -w 1
        [-m Maximum Replica number] # e.g. -m 10
    Optional options:
        [-c Native HPA cpu percent] # For Native HPA (CPU) test, run with -k option. e.g. -k 40 -c 20
        [-z] # Install RabbitMQ
        [-r] # Remove RabbitMQ
    Optional Tests:
        #(Multiple choices supported)
        [-n Non HPA test duration(min)] # e.g. -n 60
        [-k K8s Native HPA test duration(min)] # e.g. -k 40
    Support only options:
        [-p] # Replace traffic pattern by workloads in ./pattern
        
__EOF__
  exit 1
}


if [ "$#" -eq "0" ]; then
    show_usage
    exit
fi


while getopts 'e:c:w:zprhf:n:k:x:m:' o; do
    case "${o}" in
        e)
            check_specified="y"
            app_name=${OPTARG}
            ;;
        w)
            web_number_specified="y"
            web_number=${OPTARG}
            ;;
        z)
            prepare_env_specified="y"
            ;;
        r)
            delete_env_specified="y"
            ;;
        p)
            change_pattern_specified="y"
            ;;
        n)
            nonhpa_test="y"
            nonhpa_test_duration=${OPTARG}
            ;;
        k)
            native_test="y"
            native_test_duration=${OPTARG}
            ;;
        c)
            native_cpu_test="y"
            cpu_percent=${OPTARG}
            ;;
        m)
            max_number_specified="y"
            max_number=${OPTARG}
            ;;
        x)
            comparison_specified="y"
            comparison_folders=${OPTARG}
            ;;

        h)
            show_usage
            exit
            ;;
        *)
            echo "Warning! wrong paramter."
            show_usage
            ;;
    esac
done


install_app()
{
    sh cleanup.sh
    python ./run_config.py all create
}


delete_app()
{
    sh cleanup.sh
    python ./run_config.py all delete
}


convertsecs() 
{
    ((h=${1}/3600))
    ((m=(${1}%3600)/60))
    ((s=${1}%60))
    printf "%02d:%02d:%02d\n" $h $m $s
}


find_test_result_folder_name()
{
    if [ "$test_type" = "k8shpa_cpu" ]; then
        metrics_folder_name=`find . -maxdepth 1 -type d -name 'k8shpa_20*metrics'|head -n 1|awk -F '/' '{print $NF}'`
        traffic_folder_name=`find . -maxdepth 1 -type d -name 'k8shpa_20*traffic'|tail -n 1|awk -F '/' '{print $NF}'`
    elif [ "$test_type" = "nonhpa" ]; then
        metrics_folder_name=`find . -maxdepth 1 -type d -name 'nonhpa_20*metrics'|head -n 1|awk -F '/' '{print $NF}'`
        traffic_folder_name=`find . -maxdepth 1 -type d -name 'nonhpa_20*traffic'|head -n 1|awk -F '/' '{print $NF}'`
    fi

    if [ "$metrics_folder_name" = "" ] || [ "$metrics_folder_name" = "" ]; then
        echo -e "\n$(tput setaf 1)Error! Can't find HPA test result folder.$(tput sgr 0)"
        leave_prog
        exit 4
    fi
}


leave_prog()
{
    if [ ! -z "$(ls -A $file_folder)" ]; then      
        echo -e "\n$(tput setaf 6)Test result files are located under $file_folder $(tput sgr 0)"
    fi
 
    cd $current_location > /dev/null
}

[ "$max_wait_pods_ready_time" = "" ] && max_wait_pods_ready_time=1500  # maximum wait time for pods become ready


pods_ready()
{
  [[ "$#" == 0 ]] && return 0

  namespace="$1"

  kubectl get pod -n $namespace \
    -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\t"}{.status.phase}{"\t"}{.status.reason}{"\n"}{end}' \
      | while read name status phase reason _junk; do
          if [ "$status" != "True" ]; then
            msg="Waiting pod $name in namespace $namespace to be ready."
            [ "$phase" != "" ] && msg="$msg phase: [$phase]"
            [ "$reason" != "" ] && msg="$msg reason: [$reason]"
            echo "$msg"
            return 1
          fi
        done || return 1

  return 0
}


wait_until_pods_ready()
{
  period="$1"
  interval="$2"
  namespace="$3"
  target_pod_number="$4"

  wait_pod_creating=1
  for ((i=0; i<$period; i+=$interval)); do

    if [[ "$wait_pod_creating" = "1" ]]; then
        # check if pods created
        if [[ "`kubectl get po -n $namespace 2>/dev/null|wc -l`" -ge "$target_pod_number" ]]; then
            wait_pod_creating=0
            echo -e "\nChecking pods..."
        else
            echo "Waiting for pods in namespace $namespace to be created..."
        fi
    else
        # check if pods running
        if pods_ready $namespace; then
            echo -e "\nAll $namespace pods are ready."
            return 0
        fi
        echo "Waiting for pods in namespace $namespace to be ready..."
    fi

    sleep "$interval"

  done

  echo -e "\n$(tput setaf 1)Warning!! Waited for $period seconds, but all pods are not ready yet. Please check $namespace namespace$(tput sgr 0)"
  leave_prog
  exit 4
}


[ "$avoid_metrics_interferece_sleep" = "" ] && avoid_metrics_interferece_sleep=600  # maximum wait time for pods become ready


sleep_interval_func()
{
    echo -e "Sleep\n"
}


collect_results()
{
    target_folder="$1"
    target_folder_short_name="$2"
    target_start="$3"
    target_end="$4"
    target_duration=$((target_end-target_start))

    find_test_result_folder_name
    mv $metrics_folder_name "${target_folder_short_name}_metrics"
    mv $traffic_folder_name "${target_folder_short_name}_traffic"
    mv picture $file_folder/$target_folder
    mv ${target_folder_short_name}_metrics $file_folder/$target_folder
    mv ${target_folder_short_name}_traffic $file_folder/$target_folder
    cp define.py $file_folder/$target_folder

}


modify_define_parameter()
{
    run_duration="$1"
    k8s_version="`kubectl version | head -n 1 | awk '{print $5}' | cut -c 12-20`"

    sed -i "s/k8s_version.*/k8s_version = $k8s_version/g" define.py
    sed -i "s/traffic_interval =.*/traffic_interval = $run_duration  # generate traffic per 1 minute during 72 minutes/g" define.py

    if [ "$web_number_specified" = "y" ]; then
        sed -i "s/app_replica_number.*/app_replica_number = $web_number  # number of replica nodes per replicaset/g" define.py
    fi

    sed -i "s/k8shpa_max_node.*/k8shpa_max_node = $max_number  # number of max replicas/g" define.py
	if [ "$test_type" = "k8shpa_cpu" ]; then
        sed -i "s/number_k8shpa.*/number_k8shpa = 1/g" define.py
        sed -i "s/number_nonhpa.*/number_nonhpa = 0/g" define.py
    elif [ "$test_type" = "nonhpa" ]; then
        sed -i "s/number_k8shpa.*/number_k8shpa = 0/g" define.py
        sed -i "s/number_nonhpa.*/number_nonhpa = 1/g" define.py
    fi

    if [ "$native_cpu_test" = "y" ]; then
        sed -i "s/k8shpa_type.*/k8shpa_type =  \"cpu\" # cpu, index, index_time, or mix/g" define.py
        sed -i "s/k8shpa_percent.*/k8shpa_percent = $cpu_percent /g" define.py
    fi
}


run_nonhpa_hpa_test()
{
    test_type="nonhpa"
    modify_define_parameter $nonhpa_test_duration
    if [ "$web_number_specified" = "y" ]; then
        test_folder_name="nonhpa_${run_duration}min_${web_number}web_${max_number}max_`date +%s`"
        test_folder_short_name="nonhpa${run_duration}m${web_number}w${max_number}m"
    fi

    mkdir -p $file_folder/$test_folder_name

    start=`date +%s`
    python -u run_main.py hpa robotshop
    end=`date +%s`

    nonhpa_avg_lag=$lag_result
    nonhpa_avg_replicas=$replica_result

    collect_results "$test_folder_name" "$test_folder_short_name" "$start" "$end"
    echo -e "\n$(tput setaf 6)NonHPA test is finished.$(tput sgr 0)"
    echo -e "$(tput setaf 6)Result files are under $file_folder/$test_folder_name $(tput sgr 0)"

}


run_native_k8s_hpa_cpu_test()
{
    test_type="k8shpa_cpu"
    modify_define_parameter $native_test_duration
    if [ "$web_number_specified" = "y" ]; then
        test_folder_name="k8shpa_cpu${cpu_percent}_${run_duration}min_${web_number}web${max_number}max_`date +%s`"
        test_folder_short_name="k8shpacpu${cpu_percent}_${run_duration}m${web_number}w${max_number}m"
    fi
    mkdir -p $file_folder/$test_folder_name

    start=`date +%s`    
    python -u run_main.py hpa robotshop
    end=`date +%s`

    native_hpa_cpu_test_avg_lag=$lag_result
    native_hpa_cpu_test_avg_replicas=$replica_result

    collect_results "$test_folder_name" "$test_folder_short_name" "$start" "$end"
    echo -e "\n$(tput setaf 6)Native HPA (CPU) test is finished.$(tput sgr 0)"
    echo -e "$(tput setaf 6)Result files are under $file_folder/$test_folder_name $(tput sgr 0)"

}



if [ "$prepare_env_specified" != "y" ] && [ "$delete_env_specified" != "y" ] && [ "$comparison_specified" != "y" ] && [ "$check_specified" != "y" ] && [ "$change_pattern_specified" != "y" ] ; then
    if [ "$web_number_specified" != "y" ]; then
        echo -e "\n$(tput setaf 1)Error! Need to use \"-s\" to specify initial web replica number.$(tput sgr 0)" && show_usage
    fi

    if [ "$nonhpa_test" != "y" ] && [ "$native_test" != "y" ]; then
        echo -e "\n$(tput setaf 1)Error! Need to use \"-n, -k or -f \" to specify algorithms.$(tput sgr 0)" && show_usage
    fi

    if [ "$max_number_specified" != "y" ]; then
        echo -e "\n$(tput setaf 1)Error! Need to use \"-m\" to specify max replica number.$(tput sgr 0)" && show_usage
    fi
    case $max_number in
      ''|*[!0-9]*) echo -e "\n$(tput setaf 1)Error! Max replica number must be a number.$(tput sgr 0)" && show_usage;;
    esac


    if  [ "$nonhpa_test" == "y" ]; then
        if [ "$native_cpu_test" != "y" ] && [ "$native_test" == "y" ]; then
            echo -e "\n$(tput setaf 1)Error! NonHPA does not use \"-c\" to specify HPA target.$(tput sgr 0)" && show_usage
        fi

    fi


    if [ "$native_test" == "y" ]; then
        if [ "$native_cpu_test" != "y" ]; then
            echo -e "\n$(tput setaf 1)Error! Need to use \"-c\" to specify native HPA type.$(tput sgr 0)" && show_usage
        fi

        if [ "$native_cpu_test" == "y" ]; then
            case $cpu_percent in
                ''|*[!0-9]*) echo -e "\n$(tput setaf 1)Error! CPU percent must be a number.$(tput sgr 0)" && show_usage;;
            esac
        fi

    fi
fi 

if [ "$prepare_env_specified" = "y" ]; then
    install_app
fi


if [ "$delete_env_specified" = "y" ]; then
    delete_app
fi


nonhpa_test_func()
{
    if [ "$nonhpa_test" = "y" ]; then
        sleep_interval_func
        previous_test="y"
        start=`date +%s`
        run_nonhpa_hpa_test
        end=`date +%s`
        duration=$((end-start))
        echo -e "\n$(tput setaf 6)It takes $(convertsecs $duration) to finish NonHPA test.$(tput sgr 0)"
    fi
}


native_hpa_cpu_test_func()
{
    if [ "$native_cpu_test" = "y" ]; then
        sleep_interval_func
        previous_test="y"
        start=`date +%s`
        run_native_k8s_hpa_cpu_test
        end=`date +%s`
        duration=$((end-start))
        echo -e "\n$(tput setaf 6)It takes $(convertsecs $duration) to finish native HPA (CPU) test.$(tput sgr 0)"
    fi

}


if [ "$comparison_specified" = "y" ]; then
    if [ "$comparison_folders" = "" ]; then
        echo -e "\n$(tput setaf 1)Error! Specify correct folders for option -x. e.g. -x test_result $(tput sgr 0)" && show_usage
    fi
    echo -e "Find $comparison_folders"
    python generate_report.py "$comparison_folders" 
    if [ "$?" != "0" ]; then
        echo -e "\n$(tput setaf 1)Error! Specify correct folders for option -x. e.g. -x test_result $(tput sgr 0)" && show_usage
        exit
    fi
fi


if [ "$check_specified" = "y" ]; then
    if [ "$app_name" = "" ]; then
        echo -e "\n$(tput setaf 1)Error! Specify correct app names for option -e. e.g. -e connect $(tput sgr 0)" && show_usage
    fi
    echo -e "Find App($app_name)"
    python run_config.py "$app_name" show
    if [ "$?" != "0" ]; then
        echo -e "\n$(tput setaf 1)Error! Specify correct folders for option -x. e.g. -e connect $(tput sgr 0)" && show_usage
    exit
    fi
fi


if [ "$change_pattern_specified" = "y" ]; then
    python run_pattern.py
fi


file_folder="./test_result"
previous_test="n"
nonhpa_test_func
native_hpa_cpu_test_func

