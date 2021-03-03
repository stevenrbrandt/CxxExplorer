import pipes3

from traceback import print_exc
from IPython.core.magic import register_cell_magic
from IPython.display import display, HTML
import html
import inspect
import re

def color_text(color, text):
    if text != "":
        display(HTML(("<div style='background: %s;'><pre>" % color)+html.escape(text)+'</pre></div>'))

def replvar(var,globs):
    newvar = ''
    last = 0
    for g in re.finditer(r'{(\w+)}',var):
        if g.group(1) in globs:
            newvar += var[last:g.span(0)[0]]
            newvar += str(globs[g.group(1)])
            last = g.span(0)[1]
    newvar += var[last:]
    return newvar

pinterp = None
prev_history = []
history = []

def replay(n=-1):
    global prev_history, history, pinterp
    for cmd in prev_history[0:n]:
        history += [cmd]
        color_text("#eeeeee","replaying: "+cmd)
        pinterp.stdin.write(cmd+'$delim$\n')
        pinterp.stdin.flush()
        out = pipes3.read_output(pinterp, pinterp.stdout)
        err = pipes3.read_output(pinterp, pinterp.stderr)
        color_text("#f8f8ff",out[0])
        color_text("#ffcccc",err[0])
        if "Segfault or Fatal error" in out[0]:
            pinterp.wait()
            pinterp = pipes3.init_cling()

class ClingServer:
    def __init__(self):
        self.pinterp = None
        self.history = None
        self.prev_history = None
        self.count = 0
    def exec_code(self, code):
        try:
            self.count += 1
            code = re.sub(r'«','<<',code)
            if self.pinterp is None:
                self.pinterp = pipes3.init_cling()
            pinterp = self.pinterp
            caller = inspect.stack()[-1][0].f_globals
            code = replvar(code, caller)
            #history += [code]
            pinterp.stdin.write(code+"$delim$\n")
            pinterp.stdin.flush()
            out = pipes3.read_output(pinterp, pinterp.stdout)
            err = pipes3.read_output(pinterp, pinterp.stderr)
            if "Segfault or Fatal error" in out[0]:
                pinterp.wait()
                self.pinterp = pipes3.init_cling()
                self.count = 1
                pinter = self.pinterp
                out += ["Server Restart"]
                #prev_history = history
                #history = []
            res = out + err
            #res = {"out":out[0], "err":err[0], "type":None}
            #color_text("#f8f8ff",out[0])
            #if len(out) > 1:
            #    color_text("#eeffee",out[1])
            #    res["type"] = out[1]
        except Exception as e:
            print_exc()
            res = [str(e)]
        #color_text("#ffcccc",err[0])
        #if line2 is not None:
        #    caller[line2.strip()] = res
        return res
