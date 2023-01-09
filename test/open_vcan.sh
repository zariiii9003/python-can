#!/bin/bash

apt-get -y install linux-modules-extra-$(uname -r)
modprobe vcan

ip link add dev vcan0 type vcan
ip link set up vcan0 mtu 72
ip link add dev vxcan0 type vcan
ip link set up vxcan0 mtu 72
ip link add dev slcan0 type vcan
ip link set up slcan0 mtu 72
