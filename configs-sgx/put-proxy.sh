#!/usr/bin/env bash

shopt -s globstar

# Ensure that the CWD is set to script's location
cd "${0%/*}"
CWD=$(pwd)

set -e

###

FROM=$1
TO=$2

if [ "$#" -ne 2 ]
then
	echo "Illegal number of parameters, need 2"
	exit 1
fi

if [ "$(id -u)" != "0" ]
then
	echo "Must be run as root"
	exit 1
fi

PROXY_TMP=proxy-tmp

rm -rf $PROXY_TMP
mkdir $PROXY_TMP

for port in $(seq $FROM $TO)
do
	echo $port

	cp proxy-seed.service $PROXY_TMP/proxy-$port.service
	sed -i -e "s/__PORT__/$port/g" $PROXY_TMP/proxy-$port.service

done

cp -p $PROXY_TMP/proxy-*.service /lib/systemd/system/

systemctl daemon-reload

echo "Done."
