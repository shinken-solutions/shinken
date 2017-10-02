#!/usr/bin/env bash

echo "************** ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪   Installation   ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪  *************************"
python setup.py install

if [ $? != 0 ]; then
   echo "ERROR: installation failed!"
   exit 2
fi


echo "************** ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪   Starting       ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪  *************************"
# Try to start daemon, but we don't want systemd hook there
SYSTEMCTL_SKIP_REDIRECT=1 /etc/init.d/shinken start
if [ $? != 0 ]; then
   echo "ERROR: daemon start failed!"
   exit 2
fi

/etc/init.d/shinken status

if [ $? != 0 ];then
   echo "Shinken did fail to start"
   exit 2
fi

echo "Seems to be ok"
exit 0


# TODO: look what can be use on the code below

#sleep 60


echo "************** ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪   Info           ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪  *************************"

LIMIT=60
for ii in `seq 1 $LIMIT`; do
    echo "Checking agent info, loop $ii"
    opsbro agent info
    if [ $? != 0 ]; then
       if [ $ii == $LIMIT ]; then
           echo "ERROR: information get failed!"
           cat /var/log/opsbro/daemon.log
           exit 2
       fi
       echo "Let more time to the agent to start, restart this test"
       continue
    fi
    # Test OK, we can break
    echo "DBG: FINISH loop $ii"
    break
done


echo "************** ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪   Address?       ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪  *************************"

# Is there an address used by the daemon?
LIMIT=60
for ii in `seq 1 $LIMIT`; do
    echo "Checking agent addr, loop $ii"
    ADDR=$(opsbro agent info | grep Addr | awk '{print $2}')
    if [ "$ADDR" == "None" ]; then
       if [ $ii == $LIMIT ]; then
           echo "The opsbro daemon do not have a valid address."
           echo `opsbro agent info`
           exit 2
       fi
       echo "Let more time to the agent to start, restart this test"
       continue
    fi
    # Test OK, we can break
    echo "    dbg: finish loop $ii"
    break
done

echo "************** ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪   Linux GROUP      ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪  *************************"
# Check if linux group is set
echo "Checking agent addr, loop $ii"

test/assert_group.sh "linux"
if [ $? != 0 ]; then
    echo "ERROR: the group linux is missing!"
    exit 2
fi


echo "************** ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪   Docker-container GROUP      ♪┏(°.°)┛┗(°.°)┓┗(°.°)┛┏(°.°)┓ ♪  *************************"
# Check if docker-container group is set
echo "Checking agent docker group, loop $ii"

test/assert_group.sh "docker-container"
if [ $? != 0 ]; then
   echo "ERROR: the group docker-container is missing!"
   exit 2
fi
