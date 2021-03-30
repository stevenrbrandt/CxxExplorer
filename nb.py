# This script is designed to test notebooks.
# It is a work in progres...
import os
import json
import sys
import pipes3
from termcolor import colored

pinterp = None #pipes3.init_cling()
print("Starting up...")

def join(lines):
    if lines is None:
        return ""
    elif type(lines) == str:
        return lines
    else:
        return " ".join(lines)

def process(jdata,key=None):
    if type(jdata) == list:
        for jd in jdata:
            process(jd)
    elif type(jdata) == dict and jdata.get("cell_type","") == "code":
        assert "source" in jdata
        assert type(jdata["source"]) == list
        src = "\n".join(jdata["source"])
        pinterp.stdin.write(src+'$delim$\n')
        pinterp.stdin.flush()
        out = join(pipes3.read_output(pinterp, pinterp.stdout))
        err = join(pipes3.read_output(pinterp, pinterp.stderr))
        print("src:",colored(src,"cyan"))
        if "ASSERTION FAILURE" in err:
            print("out:",colored(out,"yellow"))
            print("err:",colored(err,"red"))
            print(colored("FAILED","red"))
            exit(1)
        else:
            print(colored("PASSED","green"))
    elif type(jdata) == dict:
        for k in jdata:
            jd = jdata[k]
            process(jd, key=k)
    elif type(jdata) in [str, int]:
        pass
    else:
        print("info:",type(jdata), jdata, key)
        raise Exception()

for a in sys.argv[1:]:
    with open(a, "r") as fd:
        print(colored("Testing file:"+a,"magenta"))
        pinterp = pipes3.init_cling()
        jdata = json.loads(fd.read().strip())
        process(jdata)
print(colored("ALL TESTS PASSSED","green"))
