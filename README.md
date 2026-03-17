# CxxExplorer
This repo builds a JupyterHub/Jupyter notebook server which offers an interactive C++ experience. The primary interface for this is through cling notebooks (cling is the C++ interpreter). We extend the cling notebook with certain magics, (namely %%writefile and %%bash). 

To build, just uncomment the build lines in the clinet docker file below and run "docker-compose build".

You can run the CxxExplorer as a notebook using this docker-compose.yml file:
```
version: '2'

 volumes:
  cxxex_home:

services:

  cxxex-workspace:
    image: stevenrbrandt/cxxex-src:2026
    container_name: cxxex
    user: jovyan
    environment:
      - "PORT=8080"
        # Please edit this line if you want a password
      - "SECRET_TOKEN=love"
    ports:
      - "8080:8080"
    volumes:
      - cxxex_home:/home
```

## References

* P. Diehl and S. R. Brandt, Interactive C++ code development using C++Explorer and GitHub Classroom for educational purposes, In Proceedings of Gateways 2020, Science Gateways Community Institute (SGCI), [Link](https://osf.io/qbtj3/)
