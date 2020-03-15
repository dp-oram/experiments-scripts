#!/usr/bin/env bash

set -e
# set -x

# Ensure that the CWD is set to script's location
cd "${0%/*}"
CWD=$(pwd)

SEED=1305
RANGE=1000
ENGINE=kalepso

{
	for size in 1 10 50 100 200 500 1000
	do
		cd $CWD/../../core/
		echo "ENV_MAXBLOCKS=${size}005" >> ./kalepsoDocker/kalepso.env

		./start-docker-compose.sh "-d"

		set +e
		echo "Waiting for Kalepso to start"
		while true
		do
			docker logs core_mysql_1 2>&1 | grep -q "port: 3306  mariadb.org binary distribution"
			if [ $? -eq 0 ]
			then
				break
			fi
			sleep 10
		done
		set -e
		echo "Kalepso started"

		cd $CWD

		./uniform-range-queries.py --engine $ENGINE --size ${size}000 --range $RANGE -v --seed $SEED

	done

	echo "Done!"
} | tee ../output/script-$(date +%s).log
