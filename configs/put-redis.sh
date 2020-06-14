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

REDIS_TMP=redis-tmp

rm -rf $REDIS_TMP
mkdir $REDIS_TMP
cp redis.conf $REDIS_TMP

for port in $(seq $FROM $TO)
do
	echo $port

	cp redis-seed.conf $REDIS_TMP/redis-$port.conf
	sed -i -e "s/__PORT__/$port/g" $REDIS_TMP/redis-$port.conf

	cp redis-server-seed.service $REDIS_TMP/redis-server-$port.service
	sed -i -e "s/__PORT__/$port/g" $REDIS_TMP/redis-server-$port.service

	mkdir -p /var/lib/redis/$port
	chown redis:redis /var/lib/redis/$port
done

chown redis:redis $REDIS_TMP/*

cp -p $REDIS_TMP/redis*.conf /etc/redis/
cp -p $REDIS_TMP/redis-server-*.service /lib/systemd/system/

mkdir -p /var/run/redis
chown redis:redis /var/run/redis

rm -f /lib/systemd/system/redis-server.service
rm -f /lib/systemd/system/redis-server@.service
rm -f /etc/systemd/system/redis.service
rm -f /etc/init.d/redis-server

systemctl daemon-reload

echo "Done."
