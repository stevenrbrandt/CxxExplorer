import pipes3

from traceback import print_exc
from IPython.core.magic import register_cell_magic
from IPython.display import display, HTML, Image
import html
import inspect
import re
from pipes1 import delim
#from is_expr import is_expr
from cin import hpxify
import os
from subprocess import Popen, PIPE

def show_images():
    for fn in os.listdir("."):
        if fn.endswith(".pbm"):
            img = fn[:-4]+".png"
            if (not os.path.exists(img)) or os.stat(fn).st_mtime > os.stat(img).st_mtime:
                p = Popen(["convert", fn, img], stdout=PIPE, stderr=PIPE, universal_newlines=True)
                o, e = p.communicate()
                if os.path.exists(img):
                    display(HTML("<h2>Image file generated: "+img+"</h2>"))
                    display(Image(img))


@register_cell_magic
def bash(line, cell):
    get_ipython().system(cell)
    show_images()

results = {}

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
    pinterp.kill()
    pinterp.wait()
    pinterp = pipes3.init_cling()
    for cmd in history[0:n]:
        history += [cmd]
        color_text("#eeeeee","replaying: "+cmd)
        pinterp.stdin.write(cmd+delim+'\n')
        pinterp.stdin.flush()
        out = pipes3.read_output(pinterp, pinterp.stdout)
        err = pipes3.read_output(pinterp, pinterp.stderr)
        color_text("#f8f8ff",out[0])
        color_text("#ffcccc",err[0])
        if "Segfault or Fatal error" in out[0]:
            pinterp.wait()
            pinterp = pipes3.init_cling()

@register_cell_magic
def cling(line, code):
    global pinterp, history, prev_history, results
    if line is None:
        line2 = None
    else:
        line2 = re.sub(r'--init\b','',line)
    if pinterp is None:
        pinterp = pipes3.init_cling()
    elif line != line2:
        pinterp = pipes3.init_cling()
    try:
        istack = inspect.stack()
        # Figure out where in the stack the symbol is supposed to go
        #for i in range(len(istack)):
        #    print("stack:",i,istack[i][0].f_globals.get("foo","UNDEF"))
        if len(istack) > 2:
            caller = istack[2][0].f_globals
        else:
            caller = {}
        #code = replvar(code, results)
        code = replvar(code, caller)
        if code.startswith(".expr "):
            pass
        #elif is_expr(code):
        #    code = ".expr "+code
        code, use_hpx, has_main, msg = hpxify(code)
        if "$debug=true" in code:
            print("HPXIFY:",code)
            print("USE HPX:",use_hpx)
            print("MSG:",msg)
        history += [code]
        pinterp.stdin.write(code+delim+"\n")
        pinterp.stdin.flush()
        out = pipes3.read_output(pinterp, pinterp.stdout)
        err = pipes3.read_output(pinterp, pinterp.stderr)
        #if "Segfault or Fatal error" in out[0] or "signal 11" in err[0]:
        #    pinterp.kill()
        #    pinterp.wait()
        #    pinterp = pipes3.init_cling()
        #    prev_history = history
        #    history = []
        res = {"out":out[0], "err":err[0], "type":None}
        color_text("#f8f8ff",out[0])
        if len(out) > 1:
            color_text("#eeffee",out[1])
            res["type"] = out[1]
        color_text("#ffcccc",err[0])
        if line2 is not None:
            results[line2.strip()] = res
    except Exception as e:
        print_exc()
    finally:
        show_images()

if __name__ == "__main__":
    cling("","""

#include <run_hpx.cpp>
#include <functional>

// The Fibonacci function written using hpx async
int fib(int n) {
    if(n < 2) return n;

    // launch a thread
    hpx::future<int> f1 = hpx::async(hpx::launch::async, fib,n-1);

    // do work while the thread is running
    int f2 = fib(n-2);

    // wait for the thread to complete
    return f1.get() + f2;
}""")
    cling("","""
{
    int n=10;
    std::cout << "fib(" << n << ")=" << fib(n) << "x" << std::endl;
}
""")
