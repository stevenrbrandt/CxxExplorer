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

# Establish the code needed to create a user
if [ "$CODE" != "" ]
then
    echo $CODE > /usr/enable_mkuser
fi

# Re-create all existing users with the correct id
for h in /home/*
do
  if [ -r $h/.bashrc ]
  then
     mkuser $(basename $h)
  fi
done

if [ "$OAUTH_CLIENT_ID" = "" ]
then
  echo Using invent your own password auth...
  cp /root/cyolauthenticator/docker/*.html /usr/local/share/jupyterhub/templates
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
jupyterhub --ip 0.0.0.0 --port $PORT -f jup-config.py
