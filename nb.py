# This script is designed to test notebooks.
# It is a work in progres...
import os
import json
import sys
import pipes3
from termcolor import colored

pinterp = None #pipes3.init_cling()
print("Starting up...")

result = {}
result_num = 0

def process(jdata,key=None):
    global result_num
    if type(jdata) == list:
        for jd in jdata:
            process(jd)
    elif type(jdata) == dict and jdata.get("cell_type","") == "code":
        assert "source" in jdata
        assert type(jdata["source"]) == list
        src = "\n".join(jdata["source"])
        result_num += 1
        pinterp.stdin.write(src+'$delim$\n')
        pinterp.stdin.flush()
        out = pipes3.read_output(pinterp, pinterp.stdout)
        err = pipes3.read_output(pinterp, pinterp.stderr)
        if src in result:
            r = result[src]
            assert r["num"] == result_num, "%d <=> %d" % (r["num"], result_num)
            #assert r["out"] == out, "%s <=> %s" % (r["out"], out)
            assert r["err"] == err, "%s <=> %s" % (r["err"], err)
            print(colored("CHECKED PASSED","green"))
        else:
            print("src:",colored(src,"cyan"))
            print("out:",colored(out,"yellow"))
            print("err:",colored(err,"red"))
            result[src] = {"num":result_num, "out":out, "err":err}
            print(colored("NOT CHECKED","magenta"))
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
        pinterp = pipes3.init_cling()
        chk = a+".json"
        if os.path.exists(chk):
            with open(chk, "r") as fd2:
                result = json.loads(fd2.read().strip())
        else:
            result = {}
        result_num = 0
        jdata = json.loads(fd.read().strip())
        process(jdata)
        if not os.path.exists(chk):
            with open(chk,"w") as fd:
                fd.write(json.dumps(result))
