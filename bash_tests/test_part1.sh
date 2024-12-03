#!/bin/bash

#=== Start M + S1 + S1
docker container prune --force && docker compose up -d


#=== wait for at least one heartbeat
sleep 12
#=== get containers status
curl -s http://127.0.0.1:8000/health


#=== send (Msg1, W=1) - Ok
curl -s --json '{"wc": 1, "text": "Msg1"}' --request POST http://127.0.0.1:8000


#=== get message from master
curl -s http://127.0.0.1:8000


#=== get message from slave-1
curl -s http://127.0.0.1:8001


#=== get message from slave-2
curl -s http://127.0.0.1:8002


#=== Stop S2
docker container stop rl-slave-2 && sleep 2


#=== send (Msg2, W=2) - Ok
curl -s --json '{"wc": 2, "text": "Msg2"}' --request POST http://127.0.0.1:8000


#=== get message from master
curl -s http://127.0.0.1:8000


#=== get message from slave-1
curl -s http://127.0.0.1:8001


# 
# after the next command, you need to start 'bash_tests/test_part2.sh'
# 
#=== send (Msg3, W=3) - Wait
time curl -s --json '{"wc": 3, "text": "Msg3"}' --request POST http://127.0.0.1:8000


# 
# continue after executing the 'bash_tests/test_part2.sh'
# 
#=== get message from slave-2
curl -s http://127.0.0.1:8002


#=== wait for at least one heartbeat
sleep 11

#=== get containers status
curl -s http://127.0.0.1:8000/health


#=== get message from master
curl -s http://127.0.0.1:8000


#=== get message from slave-1
curl -s http://127.0.0.1:8001


#=== get message from slave-2
curl -s http://127.0.0.1:8002


#=== check master logs
docker logs rl-master


#=== Stop M + S1 + S1'
docker compose down


