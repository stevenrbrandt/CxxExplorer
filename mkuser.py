#!/usr/bin/python3

from os import stat
import os
from subprocess import call
import sys
import pwd

class UserExists(Exception):
    pass

def mkuser(user):
    if not os.path.exists("/usr/enable_mkuser"):
      raise Exception("mkuser disabled")

    home = "/home/%s" % user
    cmd = ["useradd",user,"-s","/bin/bash"]
    if os.path.exists(home):
      uid = stat(home).st_uid
      try:
        return pwd.getpwuid(uid)
        # The user already exists, nothing to do
        raise UserExists("User exists: %s %d" % (user,uid))
      except KeyError:
        pass
      cmd += ["-u",str(uid)]
    else:
      cmd += ["-m"]
      uids = set()
      for path in os.listdir("/home"):
        u = stat("/home/%s" % path).st_uid
        uids.add(u)
      for u in range(1000,100000):
        if u in uids:
          continue
        try:
          pwd.getpwuid(u)
        except KeyError:
          uid = u
          cmd += ["-u",str(uid)]
          break

    print(cmd)
    call(cmd)

def getpwnam(user):
    try:
        return pwd.getpwnam(user)
    except:
        try:
            mkuser(user)
        except UserExists as ue:
            pass
        return pwd.getpwnam(user)

if __name__ == "__main__":
    mkuser(sys.argv[1])
