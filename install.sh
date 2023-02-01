#!/bin/bash
os_name=`cat /etc/os-release | grep NAME | grep -v "_" | awk -F= '{print $2}' | awk -F \" '{print $2}' `
echo "OS: $os_name"
cat /etc/centos-release|grep -i 'CentOS Linux release 7'
if [ "$?" = "0" ]; then
    version="7"
fi
if [ "$version" = "7" ]; then
    yum -y --enablerepo=extras install epel-release
    yum install -y --enablerepo="epel" python-pip
    yum install -y python-yaml # read yaml
    yum install psmisc -y  # killall command
    yum install -y python2-devel  # avoid subprocess32 exception
    yum install -y gcc  # avoid subprocess32 exception
    yum -y install httpd-tools
    yum install -y git
  	yum install net-tools nfs-utils wget -y
    yum install java-devel
    pip install --upgrade "pip < 21.0"
    pip install wheel
    pip install subprocess32  # call kafka commands
    pip install statsmodels==0.10.0
    pip install statistics
    pip install pymongo
    curl -L https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
    python run_config.py metrics create
    python run_config.py prometheus create
else
	echo "Only support CentosOS Linux release 7 now"
fi

touch requirements.done

which python > /dev/null 2>&1
if [ "$?" != "0" ]; then
    echo -e "\n$(tput setaf 1)Error! Failed to locate python command. Pls make sure \"python\" command exist.$(tput sgr 0)"
    if [ "$version" = "8" ]; then
        echo "$(tput setaf 2)You can try to create a hard link \"python\" points to your python2 command.$(tput sgr 0)"
    fi
    exit 1
fi
