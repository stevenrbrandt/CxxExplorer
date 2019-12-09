import os

if "OAUTH" in os.environ and os.environ["OAUTH"] == "yes":
    c.JupyterHub.authenticator_class = 'jupyterhub.auth.GitHubOAuthenticator'
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

# Configure to use Github Auth
if "OAUTH" in os.environ and os.environ["OAUTH"] == "yes":
    c.LocalAuthenticator.create_system_users = True
    c.LocalAuthenticator.add_user_cmd = ['/usr/local/bin/mkuser','USERNAME']
    c.Authenticator.blacklist = set()
    c.Authenticator.admin_users = set(['stevenrbrandt'])
    c.MyOAuthenticator.client_id = '9c4793b7d0f3e3584939'
    c.MyOAuthenticator.client_secret = 'b3d5f7c888c6b1a31d5be4af39db2011165e764a'
    c.MyOAuthenticator.oauth_callback_url = 'https://tutorial.cct.lsu.edu/hpx/hub/oauth_callback'
    #c.MyOAuthenticator.oauth_callback_uri = 'https://tutorial.cct.lsu.edu/hpx/hub/oauth_callback'

    from oauthenticator.github import GitHubOAuthenticator
    c.JupyterHub.authenticator_class = GitHubOAuthenticator
