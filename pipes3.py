from subprocess import *
import sys, os
from pipes1 import delim, end, delimend


def init_cling():
    import pipes1
    return Popen([
            "python3",
            pipes1.__file__
        ],
        #bufsize=0,
        stdout=PIPE,
        stderr=PIPE,
        stdin=PIPE,
        universal_newlines=True)

def readinp(inp):
    inbuf = ''
    while True:
        inbuf += inp.readline()
        if delim in inbuf:
            return inbuf

def read_output(p,stream):
    outbuf = ''
    types = None
    while p.poll() is None:
        line = stream.readline()
        if line is None:
            break
        outbuf += line
        if delimend in outbuf:
            parts = outbuf.split(delim)
            assert parts[-1] == end+"\n"
            return parts[0:-1]
    os.set_blocking(stream.fileno(), False)
    outbuf += os.read(stream.fileno(),10000).decode()
    return [outbuf+"\nSegfault or Fatal error"]
            
def run_cmd(p):
    cmd = readinp(sys.stdin)
    p.stdin.write(cmd)
    p.stdin.flush()
    result = read_output(p,p.stdout)
    print("result:",result)
    error = read_output(p,p.stderr)
    print("error:",error)

#p = init_cling()
#while p.poll()  is None:
#    run_cmd(p)
