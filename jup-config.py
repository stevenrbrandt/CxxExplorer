import os
from tornado import web

if "OAUTH" in os.environ and os.environ["OAUTH"] == "yes":
    from oauthenticator.github import GitHubOAuthenticator

    class MyGitHubOAuthenticator(GitHubOAuthenticator):
        async def authenticate(self, handler, data=None):
          userdict = await super().authenticate(handler, data)
          allowed_users = "/home/allowed_users.txt"
          users = set()
          if os.path.exists(allowed_users):
              with open(allowed_users, "r") as fd:
                  for user in fd.readlines():
                      users.add(user.strip())
          if userdict["name"] in users:
              return userdict
          else:
              raise web.HTTPError(403, "User '%s' has not been given access. Please request it from your instructor." % userdict['name'])

    c.JupyterHub.authenticator_class = MyGitHubOAuthenticator
else:
    c.JupyterHub.authenticator_class = 'jupyterhub.auth.LocalAuthenticator'
c.JupyterHub.log_level = 'DEBUG'
c.Spawner.debug = True
c.LocalProcessSpawner.debug = True
#c.JupyterHub.authenticator_class = 'jupyterhub.auth.LocalAuthenticator'
#c.JupyterHub.ssl_cert = '/etc/pki/tls/cert.pem'
#c.JupyterHub.ssl_key  = '/etc/pki/tls/private/jupyter.cct.lsu.edu.key'

# openssl genrsa -out rootCA.key 2048
# openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 1024 -out rootCA.pem

#c.JupyterHub.ssl_cert = '/root/rootCA.pem'
#c.JupyterHub.ssl_key = '/root/rootCA.key'
if os.environ["PORT"] == "443":
    c.JupyterHub.ssl_cert = '/etc/pki/tls/certs/tutorial.cct.lsu.edu.cer'
    c.JupyterHub.ssl_key =  '/etc/pki/tls/private/tutorial.cct.lsu.edu.key'
#c.JupyterHub.ssl_cert = '/etc/pki/tls/certs/melete05.cct.lsu.edu_bundle.cer'
#c.JupyterHub.ssl_key =  '/etc/pki/tls/private/melete05.cct.lsu.edu.key'
c.JupyterHub.base_url = '/hpx/'
#c.Spawner.args = ['--NotebookApp.allow_origin=*']
#c.JupyterHub.ssl_cert = '/etc/pki/tls/certs/tutorial.cct.lsu.edu.cer'
#c.JupyterHub.ssl_key =  '/etc/pki/tls/private/tutorial.cct.lsu.edu.key'

#from oauthenticator.google import GoogleOAuthenticator
#c.JupyterHub.authenticator_class = GoogleOAuthenticator
c.NotebookApp.terminado_settings = { 'shell_command': 'bash' }

def pre_spawn_hook(spawner):
    import mkuser
    print("Running pre-spawn hook")
    print("User:",spawner.user.name)
    mkuser.mkuser(spawner.user.name)

# Configure to use Github Auth
if "OAUTH" in os.environ and os.environ["OAUTH"] == "yes":
    #c.Authenticator.create_system_users = True
    #c.Authenticator.add_user_cmd = ['/usr/local/bin/mkuser','USERNAME']
    c.Authenticator.blacklist = set()
    c.Authenticator.admin_users = set(['stevenrbrandt'])
    c.Spawner.pre_spawn_hook = pre_spawn_hook
