all: build test stop

# this is to forward X apps to host:
# See: http://stackoverflow.com/a/25280523/1336939
XSOCK=/tmp/.X11-unix
XAUTH=/tmp/.docker.xauth

# paths
TBB_PATH=/home/docker/tor-browser_en-US/
CRAWL_PATH=/home/docker/tbcrawl
GUEST_SSH=/home/docker/.ssh
HOST_SSH=${HOME}/.ssh

ENV_VARS = \
	--env="DISPLAY=${DISPLAY}" 					\
	--env="XAUTHORITY=${XAUTH}"					\
	--env="VIRTUAL_DISPLAY=$(VIRTUAL_DISPLAY)"  \
	--env="TBB_PATH=${TBB_PATH}"
VOLUMES = \
	--volume=${XSOCK}:${XSOCK}					\
	--volume=${XAUTH}:${XAUTH}					\
	--volume=${HOST_SSH}:${GUEST_SSH}			\
	--volume=`pwd`:${CRAWL_PATH}				\

PARAMS=-c wang_and_goldberg -t WebFP -u ./etc/localized-urls-100-top.csv -s
#PARAMS=-c default -t WebFP -u ./etc/localized-urls-100-top.csv -s -x 1200x800

build:
	@docker build -t tbcrawl --rm .

run:
	@docker run -it --rm ${ENV_VARS} ${VOLUMES} --privileged tbcrawl ${CRAWL_PATH}/Entrypoint.sh "$(PARAMS)"
	#@docker run -it --rm ${ENV_VARS} ${VOLUMES} --privileged tbcrawl bash

stop:
	@docker stop `docker ps -a -q -f ancestor=tbcrawl`
	@docker rm `docker ps -a -q -f ancestor=tbcrawl`

destroy:
	@docker rmi -f tbcrawl

reset: stop destroy
