#/usr/sbin/sshd 
#export REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/tutorial.cct.lsu.edu_intermediate.cer
export PORT=80
export OAUTH=yes
if [ "$OAUTH" = "yes" ]
then
    export OAUTH_CLIENT_ID=9c4793b7d0f3e3584939
    export OAUTH_CLIENT_SECRET=b3d5f7c888c6b1a31d5be4af39db2011165e764a
    export OAUTH_CALLBACK_URL=https://tutorial.cct.lsu.edu/hpx/hub/oauth_callback
fi
touch /usr/enable_mkuser
jupyterhub --ip 0.0.0.0 --port $PORT -f jup-config.py
