#/usr/sbin/sshd 
#export REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/tutorial.cct.lsu.edu_intermediate.cer
export PORT=80
export OAUTH=yes
if [ "$OAUTH" = "yes" ]
then
    source /oauth/oauth.sh
fi
touch /usr/enable_mkuser
echo jupyterhub --ip 0.0.0.0 --port $PORT -f jup-config.py
jupyterhub --ip 0.0.0.0 --port $PORT -f jup-config.py
