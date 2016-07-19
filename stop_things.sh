./env/bin/supervisorctl stop all
./opt/rabbitmq_server-3.6.3/sbin/rabbitmqctl stop
kill -9 $(cat /tmp/supervisord.pid)
