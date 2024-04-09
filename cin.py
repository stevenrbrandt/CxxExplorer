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
stmt=({for}|{if}|{while}|{ns}|{del}|{decl}|{lambda_assign}|{curl_assign}|{assign}|{curl}|{macro}|{call}|{curl}|{expr})
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
        print(cinput)
        s = StringIO()
        m.showError(s)
        s.seek(0)
        return None, s.read()

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
        self.wrapping_vars = list()
        self.code_num = 0

    def add(self, pn, g):
       if pn in ["lambda_assign", "curl_assign", "assign"]:
           code_num = self.code_num
           vtype = g.children[0].substring()
           vname = g.children[1].substring()
           if len(self.wrapping_vars) == 0:
               subclass = ""
           else:
               subclass = f": public wrapping_{code_num}__"
           self.code_num += 1
           code_num = self.code_num
           self.wrapping_vars += [(vtype, vname)]
           return f"struct wrapping_{code_num}__ {subclass} {{ {g.substring()} }};\n"
       elif pn == "decl":
           code_num = self.code_num
           vtype = g.children[0].substring()
           vname = g.children[1].substring()
           vargs = g.children[2].substring()
           if len(self.wrapping_vars) == 0:
               subclass = ""
           else:
               subclass = f": public wrapping_{code_num}__"
           self.code_num += 1
           code_num = self.code_num
           self.wrapping_vars += [(vtype, vname)]
           wr = f"wrapping_{code_num}__"
           return f"struct {wr} {subclass} {{ {vtype} {vname}; {wr}() : {vname}({vargs}){{}}  }};\n"
       elif pn in ["expr", "call", "for", "if", "curl", "del"]:
           code_num = self.code_num
           if len(self.wrapping_vars) == 0:
               subclass = ""
           else:
               subclass = f": public wrapping_{code_num}__"
           self.code_num += 1
           code_num = self.code_num
           self.wrapping_vars += [None]
           return f"struct wrapping_{code_num}__ {subclass} {{ wrapping_{code_num}__() {{ {g.substring()} }} }};\n"
       else:
           return g.substring()+"\n" + self.flush()

    def flush(self):
       code = ""
       if len(self.wrapping_vars) > 0:
          code_num = self.code_num
          code += f"wrapping_{code_num}__ *inner_{code_num}__ = "
          if use_hpx:
              code +=  "run_hpx([](){ "
              code += f" return new wrapping_{code_num}__(); "
              code +=  "});\n"
          else:
              code += f" new wrapping_{code_num}__(); "
          for vv in self.wrapping_vars:
              if vv is None:
                  continue
              else:
                  code += f"{vv[0]} {vv[1]} = std::move(inner_{code_num}__->{vv[1]});\n"
          #code += f"delete inner_{code_num}__;\n"
          self.wrapping_vars = list()
       return code

cgen = CodeGen()

def hpxify(cinput):
    global use_hpx, code_num
    m, outs = parse_cxx(cinput)
    #print("Parse Tree:",m.dump())
    if m is None:
        return cinput, use_hpx, False, outs
    code = ""
    has_main = False
    for g in m.children:
        pn = g.getPatternName()
        if pn == "func":
            if g.children[1].substring() == "main":
                has_main = True
    for g in m.children:
        pn = g.getPatternName()
        txt = g.substring()
        if pn == "stmt": # and use_hpx:
            for g2 in g.children:
               pn2 = g2.getPatternName()
               if pn2 in ["lambda_assign", "curl_assign", "assign", "decl"]:
                   if "auto" in g2.children[0].substring():
                       code += cgen.flush()
                       if pn2 == "assign":
                           code += g2.children[0].substring()+" "
                           code += g2.children[1].substring()+" = "
                           if use_hpx:
                               code += "run_hpx([](){ return " + g2.children[2].substring() + ";});\n"
                           else:
                               code += g2.children[2].substring() + ";\n"
                       else:
                           code += g2.substring()+"\n"
                   else:
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
// Usage of the new expression to generate an array of integers
int *dvalues = new int[5];

// Usage of the placement new for struct and classes
struct point {
  double x,y,z;

  point (double x0=0, double y0=0, double z0=0) {
     x = x0; y = y0; z = z0;
  }
};

point *vec = new point();

// Releasing the allocate double array
delete[] dvalues;

// Releasing the allocated struct
delete vec;
            """)
            print(src)
            print("outs<<",outs,">>")
        else:
            m.showError()
