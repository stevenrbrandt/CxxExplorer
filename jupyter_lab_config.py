# C++Explorer does not install JupyterLab extensions from PyPI.
# JupyterLab 4.2.5's default "pypi" manager also crashes on httpx>=0.28
# (AsyncClient no longer accepts proxies=).
c.LabApp.extension_manager = "readonly"
