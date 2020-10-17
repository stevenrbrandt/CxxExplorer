import os
from tornado import web
from time import sleep

if "OAUTH_CLIENT_ID" in os.environ:
    from oauthenticator.github import GitHubOAuthenticator

    class MyGitHubOAuthenticator(GitHubOAuthenticator):
        async def authenticate(self, handler, data=None):
          if data is None:
            userdict = await super().authenticate(handler, data)
            data = {}
            with open("/tmp/log.txt", "a") as fd:
                print("git:",userdict, file=fd)
          else:
            userdict = { "name":data["username"] }
            with open("/tmp/log.txt", "a") as fd:
                print("nogit:",data, file=fd)
          allowed_users = "/home/allowed_users.txt"
          users = set()
          if os.path.exists(allowed_users):
              with open(allowed_users, "r") as fd:
                  for user in fd.readlines():
                      users.add(user.strip())
          enable_mkuser = os.path.exists("/usr/enable_mkuser")
          if "code" in data and userdict["name"] not in users and enable_mkuser:
              with open("/usr/enable_mkuser", "r") as fd:
                  code = fd.read().strip()
              if data["code"] == code:
                  with open(allowed_users, "a") as fd:
                      print(userdict["name"], file=fd)
                      users.add(userdict["name"])
              else:
                  sleep(10)
          if userdict["name"] in users:
              return userdict
          elif enable_mkuser:
              e = web.HTTPError(403, "User '%s' does not have access. Please request with a code below." % userdict['name'])
              e.my_message = 'Login'
              e.user = userdict["name"]
              raise e
          else:
              raise web.HTTPError(403, "User '%s' has not been given access. Please request it from your instructor." % userdict['name'])

    c.JupyterHub.authenticator_class = MyGitHubOAuthenticator
else:
    c.JupyterHub.authenticator_class = 'cyolauthenticator.CYOLAuthenticator'
c.JupyterHub.log_level = 'DEBUG'
c.Spawner.debug = True
c.LocalProcessSpawner.debug = True

# If the port is set to 443, a key & cert should be mounted in the container.
if os.environ["PORT"] == "443":
    c.JupyterHub.ssl_cert = '/etc/pki/tls/certs/tutorial.cct.lsu.edu.cer'
    c.JupyterHub.ssl_key =  '/etc/pki/tls/private/tutorial.cct.lsu.edu.key'

if 'BASE_URL' in os.environ:
    c.JupyterHub.base_url = os.environ['BASE_URL'] #'/hpx/'

c.NotebookApp.terminado_settings = { 'shell_command': 'bash' }

def pre_spawn_hook(spawner):
    import mkuser
    print("Running pre-spawn hook")
    print("User:",spawner.user.name)
    mkuser.mkuser(spawner.user.name)

# Configure to use Github Auth
if "OAUTH_CLIENT_ID" in os.environ:
    c.Spawner.pre_spawn_hook = pre_spawn_hook
