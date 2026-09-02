# A simple calculator based on Piraha

import sys
from piraha import Grammar, compileSrc, Matcher
from io import StringIO

src_code = r"""
skipper=([ \t\r\n]|//.*)*
directive= \#.*
name=[a-zA-Z_][a-zA-Z_0-9]*
type=(const |){name}(::{name})*(< {astuff}+ >|)( [*&])*
quote="(\\.|[^"])*"
char='(\\.|[^'])'

angle=< {astuff} >
paren=\({sstuff}*\)
brak=\[{stuff}*\]
curl=\{{sstuff}*\}
sstuff=([^{}()\[\]"]+|{paren}|{brak}|{quote}|{curl}|{char})
stuff=([^{}()\[\]";]+|{paren}|{brak}|{quote}|{curl}|{char})
astuff=([^{}()\[\]";<>]+|{paren}|{brak}|{quote}|{curl}|{char}|< {astuff}+ >)

tfunc=template {angle} {func}
tclass=template {angle} {class}
func=(static|) (inline|) {type} {name} {paren} {curl} 
class=(struct|class) {name} (: {type}( , {type})* |){curl} ;
declargs=({paren}|{curl}|)

rhs = {stuff}+
array_decl={type} {name} \[ {stuff} \]( = {curl}|) ;
decl={type} {name} {declargs} ;
ns = namespace {name}( :: {name})*( = {name}( :: {name})* ;| {curl})
lambda_rhs={brak} {paren} (-> {type} |){curl}
lambda_assign={type} {name} = {lambda_rhs} ;
curl_assign={type} {name} = {curl} ;
assign={type} {name} = {rhs} ;
for=for {paren} {stmt}
if=if {paren} {stmt}( {else_if}|)*( {else})
else=else {stmt}
else_if=else if {paren} {stmt}
while=while \({stuff}\) {stmt}
expr={stuff}+ ;
call={name}( :: {name})* {paren} ;
del=delete {stuff} ;
stmt=({for}|{if}|{while}|{ns}|{del}|{array_decl}|{decl}|{lambda_assign}|{curl_assign}|{assign}|{curl}|{macro}|{call}|{curl}|{expr})
macro=[A-Z][_A-Z]+ {paren}( ;|)
using=using {rhs} ;
typedef=typedef {rhs} ;
namespace=namespace {curl}

src=^( ({quote}|{namespace}|{using}|{typedef}|{directive}|{ns}|{tfunc}|{tclass}|{class}|{func}|{stmt}))* $
"""

g = Grammar()

# Compile a grammar from a file
compileSrc(g, src_code)

# Create a matcher
def parse_cxx(cinput):
    m = Matcher(g,g.default_rule, cinput)
    if m.matches():
        pass
        #print("Success! Dump parse tree...")
        #with open("cin-debug.txt", "w") as fd:
        #    print(m.gr.dump(),file=fd)
        outs = ""
        for k in m.gr.children:
            pnm = k.getPatternName()
            if pnm == "stmt":
                for k2 in k.children:
                    pnm2 = k2.getPatternName()
                    outs += pnm2 + "\n"
            else:
                outs += pnm + "\n"
        return m.gr, outs
    else:
        # Show a helpful error message
        #print(cinput)
        s = StringIO()
        m.showError(s)
        s.seek(0)
        erm = s.read()
        return None, erm

code_wrap = """
struct foo__%d_ {
   foo__%d_() {
      run_hpx([](){ 
        %s
      });
   }
} foo_inst_%d_;
"""

use_hpx = False
#code_num = 0

class CodeGen:
    def __init__(self):
        self.pending_stmts = []
        self.code_num = 0

    def _hpxish(self, text):
       # Include typedef-hidden HPX types (e.g. executor_type) so construction
       # does not run as a global initializer before the runtime is started.
       keys = ("future", ".get()", ".then(", "hpx", "execution::",
               "executor", "block_executor", "compute::", "host_targets")
       return any(k in text for k in keys)

    def add(self, pn, g):
       if pn in ["lambda_assign", "curl_assign", "assign"]:
           vtype = g.children[0].substring()
           vname = g.children[1].substring()
           rhs = g.children[2].substring()
           # Keep HPX assignments as globals so later cells can see them.
           # Initialize inside cxxex_cell (process() after .L) instead of a
           # global initializer — that path hits Cling ORC static-init failures
           # on parallel algorithms.
           if use_hpx and (self._hpxish(vtype) or self._hpxish(rhs)):
               if "auto" in vtype:
                   decl = f"decltype({rhs}) {vname};\n"
               else:
                   decl = f"{vtype} {vname};\n"
               self.pending_stmts.append(f"{vname} = {rhs};")
               return decl
           out = self.flush()
           if self._hpxish(vtype) or self._hpxish(rhs):
               return out + f"{vtype} {vname} = run_hpx([](){{ return {rhs}; }});\n"
           return out + g.substring()+"\n"
       elif pn == "decl":
           # Emit the global now but do not flush pending statements: a later
           # `hpx::fill` in the same cell must share the run_hpx() that
           # constructs executor_type, because run_hpx starts and stops HPX
           # per call.
           return g.substring() + "\n"
       elif pn in ["expr", "call", "for", "if", "curl", "del"]:
           self.pending_stmts.append(g.substring())
           return ""
       else:
           return self.flush() + g.substring()

    def flush(self):
       if not self.pending_stmts:
           return "\n"
       self.code_num += 1
       n = self.code_num
       body = "\n".join(self.pending_stmts)
       self.pending_stmts = []
       # Define a function and ask Kernel.cpp to process() the call after .L.
       # Global constructors that invoke HPX parallel algorithms fail in Cling's
       # ORC runStaticInitializersOnce; a later process() call does not.
       if use_hpx:
           return (f"void cxxex_cell_{n}() {{ run_hpx([]() {{ {body} }}); }}\n"
                   f"// CXXEX_RUN cxxex_cell_{n}\n")
       return (f"void cxxex_cell_{n}() {{ {body} }}\n"
               f"// CXXEX_RUN cxxex_cell_{n}\n")

cgen = CodeGen()

prior_defs = dict()

def redef(symbol):
    val = prior_defs.get(symbol, None)
    if val is None:
        prior_defs[symbol] = 1
        return ""
    elif val == 1:
        prior_defs[symbol] += 1
        return f"#define {symbol} {symbol}_redef__{val}\n"
    else:
        prior_defs[symbol] += 1
        return f"#undef {symbol}\n#define {symbol} {symbol}_redef__{val}\n"

def hpxify(cinput):
    global use_hpx, code_num

    # Backwards compatible with older versions of the C++Explorer
    if cinput.startswith(".expr"):
        cinput = "{" + cinput[5:] + "}"

    m, outs = parse_cxx(cinput)
    #print("Parse Tree:",m.dump())
    if m is None:
        return cinput, use_hpx, False, outs
    code = ""
    inc_run_hpx = False
    has_main = False
    for g in m.children:
        pn = g.getPatternName()
        if pn in ["func", "tfunc"]:
            func_name = g.children[1].substring()
            code += redef(func_name)
            if pn == "func" and func_name == "main":
                has_main = True
        elif pn in ["class", "tclass"]:
            class_name = g.children[0].substring()
            code += redef(class_name)
        elif pn == "stmt": # and use_hpx:
            for g2 in g.children:
               pn2 = g2.getPatternName()
               if pn2 in ["lambda_assign", "curl_assign", "assign", "decl", "array_decl"]:
                   var_name = g2.children[1].substring()
                   code += redef(var_name)

    for g in m.children:
        pn = g.getPatternName()
        txt = g.substring()
        if pn in ["directive"]:
            code += g.substring()+"\n"
            if (not use_hpx) and "hpx" in g.substring():
                use_hpx = True
            if (not inc_run_hpx) and "hpx" in g.substring():
                inc_run_hpx = True
                code += "#include <run_hpx.cpp>\n"
        elif pn == "stmt": # and use_hpx:
            for g2 in g.children:
               pn2 = g2.getPatternName()
               if pn2 in ["lambda_assign", "curl_assign", "assign", "decl"]:
                   code += cgen.add(pn2, g2)
                   #vtype = g2.children[0].substring()
                   #vname = g2.children[1].substring()
                   #if len(wrapping_vars) == 0:
                   #    subclass = ""
                   #else:
                   #    subclass = f": public wrapping_{code_num}__"
                   #code_num += 1
                   #wrapping_vars += [(vtype, vname)]
                   #code += f"struct wrapping_{code_num}__ {subclass} {{ {g2.substring()}; }};\n"
                   #wrapping_vars g
               elif pn2 in ["expr", "call", "for", "if", "curl", "del"]:
                   code += cgen.add(pn2, g2)
                   #if len(wrapping_vars) == 0:
                   #    subclass = ""
                   #else:
                   #    subclass = f": public wrapping_{code_num}__"
                   #code_num += 1
                   #wrapping_vars += [None]
                   #code += f"struct wrapping_{code_num}__ {subclass} {{ wrapping_{code_num}__() {{ {g2.substring()}; }} }};\n"
                   #code += code_wrap % (code_num, code_num, txt, code_num)
               else:
                   #if len(wrapping_vars) > 0:
                   #   code +=  "run([](){\n"
                   #   code += f"  wrapping_{code_num}__ *inner_{code_num}__ = new wrapping_{code_num}__();\n"
                   #   code +=  "});\n"
                   #   for vv in wrapping_vars:
                   #       if vv is None:
                   #           continue
                   #       else:
                   #           code += f"{vv[0]} {vv[1]} = std::move(inner_{code_num}__->vv[1]);\n"
                   #   code += f"delete inner_{code_num}__;\n"
                   #   wrapping_vars = list()
                   code += cgen.flush()
                   code += g2.substring()+"\n"
        elif pn == "directive":
            code += cgen.flush()
            code += txt + "\n"
            if "hpx/" in txt and not use_hpx and not has_main:
                use_hpx = True
                code += "#include <run_hpx.cpp>\n"
        else:
            code += cgen.flush()
            code += txt + "\n"
    code += cgen.flush()
    #print(">>>",code)
    if use_hpx:
        pass #code += "hpx_global::shutdown();\n";
    return code, use_hpx, has_main, outs

if __name__ == "__main__":
    if len(sys.argv) > 2:
        with open(sys.argv[1], "r") as fd:
            cinput = fd.read()
        crule = sys.argv[2]
        print(crule, cinput)
        m = Matcher(g, crule, cinput)
        if m.matches():
            print("Success! Dump parse tree...")
            print(m.gr.dump())
        else:
            m.showError()
    else:
        cinput = r"""
#include <iostream>
#include <hpx/hpx.hpp>

using namespace std;

hpx::future<int> f = hpx::async([](){ return 42; });

cout << f.get() << endl;

executor_type exec(host_targets);
std::vector<float> vd;
for(int i=0;i<10;i++) vd.push_back(1.f);
hpx::fill(execution::par.on(exec),vd.begin(),vd.end(),1.0f*getpid());
for(int i=0;i<10;i++) cout << vd[i] << " "; cout << std::endl;
"""
        crule = "src"
        m = Matcher(g, crule, cinput)
        if m.matches():
            print("Success!")
            src, a, b, outs = hpxify(cinput)
            print(src)
            print("outs<<",outs,">>")
            src, a, b, outs = hpxify("""
struct A { int a; };
            """)
            print(src)
            print("outs<<",outs,">>")
            src, a, b, outs = hpxify("""
struct A { int b; };
            """)
            print(src)
            print("outs<<",outs,">>")
        else:
            m.showError()
