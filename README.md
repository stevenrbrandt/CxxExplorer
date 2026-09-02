# CxxExplorer
This repo builds a JupyterHub/Jupyter notebook server which offers an interactive C++ experience. The primary interface for this is through cling notebooks (cling is the C++ interpreter). We extend the cling notebook with certain magics, (namely %%writefile and %%bash). However, additionally, we provide a %%cling magic cell for python notebooks, and a @py11 decorator--a way to create on-the-fly C++ functions using Pybind11.

The image is Ubuntu 24.04 with **Cling 1.3** (LLVM 20) and **HPX 1.11**.

To build, run `bash ./b.sh` (that script takes the CPU count from `lscpu`, not `nproc` — `OMP_NUM_THREADS=1` makes `nproc` report a single core). A full build compiles LLVM/Clang/Cling and HPX and needs tens of GB of RAM and disk.

You can run the CxxExplorer as a notebook using this docker-compose.yml file:
```
version: '2'

 volumes:
  cxxex_home:

services:

  cxxex-workspace:
    # Uncomment the next lines if you want to build.
    # You probably want to have a pretty powerful
    # machine if you want to do this.
    # build:
    #    args:
    #      CPUS: 12
    #     BUILD_TYPE: Release
    #   context: .
    #   dockerfile: Dockerfile
    # CPU count: pass --build-arg CPUS=$(lscpu | awk '/^CPU\(s\):/{print $2}')
    # Do not use nproc when OMP_NUM_THREADS=1.
    image: stevenrbrandt/cxxex-src
    container_name: cxxex
    user: jovyan
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
    image: stevenrbrandt/cxxex-src
    container_name: cxxex
    user: root
    entrypoint: bash /root/startup.sh
    environment:
      - "PORT=443"
      
      # Option 1: Use GitHubOAuth. To run the
      # server this way, fill in these variables
      # - "OAUTH_CLIENT_ID=..."
      # - "OAUTH_CLIENT_SECRET=..."
      # - "OAUTH_CALLBACK_URL=..."
      
      # Option 2: Use the Create Your Own Login (CYOL)
      # Authenticator. This will happen if the above
      # variables are not set.
      
      # With Ooption 1, only github users whose names
      # appear in /home/allowed_users.txt are
      # permitted to login.
      # If you set a CODE, then any user with
      # that code can add themselves to the allowed
      # users list.
      
      # With Option 2:, the CODE enables users to
      # select and create their own login name and
      # password.
      - "CODE=frog"

    ports:
      - "8004:443"
    volumes:
      - cxxex_home:/home
      # expecting these if the port is 443
      # - cert_file:/etc/pki/tls/certs/tutorial.cct.lsu.edu.cer
      # - key_file:/etc/pki/tls/private/tutorial.cct.lsu.edu.key
```

## References

* P. Diehl and S. R. Brandt, Interactive C++ code development using C++Explorer and GitHub Classroom for educational purposes, In Proceedings of Gateways 2020, Science Gateways Community Institute (SGCI), [Link](https://osf.io/qbtj3/)
