# CxxExplorer
This repo builds a JupyterHub/Jupyter notebook server which offers an interactive C++ experience. The primary interface for this is through cling notebooks (cling is the C++ interpreter). We extend the cling notebook with certain magics, (namely %%writefile and %%bash). However, additionally, we provide a %%cling magic cell for python notebooks, and a @py11 decorator--a way to create on-the-fly C++ functions using Pybind11.

To build, just run "docker-compose build".

You can run the CxxExplorer as a notebook using this docker-compose.yml file:
```
version: '2'

 volumes:
  cxxex_home:

services:

  cxxex-workspace:
    image: stevenrbrandt/cxxex
    container_name: cxxex
    user: jovyan
    #user: root
    #entrypoint: bash /root/startup.sh
    environment:
      - "PORT=80"
        # Please edit this line
      - "SECRET_TOKEN=love"
    ports:
      - "8004:80"
    volumes:
      - cxxex_home:/home
```
Or you can run it as a server
```
version: '2'

volumes:
  cxxex_home:

services:

  cxxex-workspace:
    image: stevenrbrandt/cxxex
    container_name: cxxex
    user: root
    entrypoint: bash /root/startup.sh
    environment:
      - "PORT=443"
      
      # Normally, only github users whose names
      # appear in /home/allowed_users.txt are
      # permitted to login.
      # If you set a CODE, then any user with
      # that code can add themselves to the allowed
      # users list.
      - "CODE=frog"
      
      # To use GitHubOAuth, fill in these variables
      # - "OAUTH_CLIENT_ID=..."
      # - "OAUTH_CLIENT_SECRET=..."
      # - "OAUTH_CALLBACK_URL=..."

    ports:
      - "8004:443"
    volumes:
      - cxxex_home:/home
      # expecting these if the port is 443
      # - cert_file:/etc/pki/tls/certs/tutorial.cct.lsu.edu.cer
      # - key_file:/etc/pki/tls/private/tutorial.cct.lsu.edu.key
```
