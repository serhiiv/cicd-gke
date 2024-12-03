#!/bin/bash

#=== wait 30 seconds for view retry iterations
sleep 30

#=== check retry iteration
docker logs rl-master


#=== check quorum
curl -s --json '{"wc": 3, "text": "Msg4"}' --request POST http://127.0.0.1:8000


#=== get message from master
curl -s http://127.0.0.1:8000


#=== send (Msg4, W=1) - Ok'
curl -s --json '{"wc": 1, "text": "Msg4"}' --request POST http://127.0.0.1:8000


#=== get message from master
curl -s http://127.0.0.1:8000


#=== get message from slave-1
curl -s http://127.0.0.1:8001


#=== get containers status
curl -s http://127.0.0.1:8000/health


#=== Start S2'
docker container start rl-slave-2


