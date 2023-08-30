cd /root

# If oauth is to be used, 
# the following variables should be
# set.
#
# export OAUTH_CLIENT_ID=...
# export OAUTH_CLIENT_SECRET=...
# export OAUTH_CALLBACK_URL=...

# Load environment file if present
if [ -d /env/env.sh ]
then
    source /env/env.sh
fi

# Create the codefile needed to allow
# user self-authorization.
if [ "$CODE" != "" ]
then
    echo $CODE > /usr/enable_mkuser
fi

if [ -r /home/passwd ]
then
    cp /home/passwd /etc/passwd
fi

if [ -r /home/shadow ]
then
    cp /home/shadow /etc/shadow
fi

# Re-create all existing users with the correct id
# Needed if one mounts a persistent /home because
# /etc/passwd cannot easily be mounted. So all user
# data is normally lost on reboot.
for h in /home/*
do
  if [ -r $h/.bashrc ]
  then
     mkuser $(basename $h)
  fi
done

# If this JupyterHub is not setup for GitHubOAuth, then
# it will instead use the Create Your Own Login Authenticator.
if [ "$OAUTH_CLIENT_ID" = "" ]
then
  echo Using invent your own password auth...
  cp /root/cyolauthenticator/docker/*.html /usr/local/share/jupyterhub/templates
  cp /root/login2.html /usr/local/share/jupyterhub/templates/login.html
else
  if [ "$CODE" != "" ]
  then
     echo "Code is set."
     if [ "$BASE_URL" = "" ]
     then
        BASE_URL="/"
     fi
     perl -p -i -e "s{/BASE_URL/}{${BASE_URL}}g" /root/error.html
     cp /root/error.html /usr/local/share/jupyterhub/templates
  fi
  cp /root/login.html /usr/local/share/jupyterhub/templates
  echo Using GitHub OAuth...
fi

# Start the server.
jupyterhub --ip 0.0.0.0 --port $PORT -f jup-config.py
