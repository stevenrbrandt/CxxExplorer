import os
from subprocess import Popen, PIPE
import re
import sys
import inspect
import ast
import numpy as np
import importlib

load_func = """
#include <dlfcn.h>
#include <fstream>
#include <sstream>
#include <stdlib.h>
#include <unistd.h>
#include <assert.h>

static inline void *load_func(const char *fun) {
    std::ostringstream fname;
    fname << getenv("HOME") << "/tmp/" << fun << ".so.txt";
    std::string so_txt = fname.str();

    std::ifstream in;
    in.open(so_txt.c_str());
    assert(in.good());

    std::string ver;
    in >> ver;

    std::ostringstream fun2;
    fun2 << fun << "_v" << ver;

    std::ostringstream lib;
    lib << getenv("HOME") << "/tmp/" << fun2.str() << ".so";
    in.close();
    in.open(lib.str().c_str());
    assert(in.good());
    in.close();

    void *handle = dlopen(lib.str().c_str(), RTLD_LAZY);
    return dlsym(handle, fun);
}
"""

if "JPY_PARENT_PID" in os.environ:
    is_jupyter = True
else:
    is_jupyter = False

home = os.environ["HOME"]
def tmp_dir():
    return os.path.join(home, "tmp")

# Figure out where stuff is
info = sys.version_info
vpattern = '^python%d\.%d' % (info.major, info.minor)
for item in os.listdir("/usr/include"):
    if re.match(vpattern, item):
        python_header = os.path.join("/usr/include",item)
        test_file = os.path.join(python_header,"Python.h")
        if os.path.exists(test_file):
            break

os.makedirs(tmp_dir(), exist_ok=True)

# Locate pybind11
if os.path.exists("/usr/local/include/pybind11/pybind11.h"):
    pybind11_header = "/usr/local/include"
else:
    local = os.path.join(home,".local","include")
    if os.path.exists(local):
        for item in os.listdir(local):
            if re.match(vpattern, item):
                pybind11_header = os.path.join(local,item)
                test_file = os.path.join(pybind11_header,"pybind11","pybind11.h")
                if os.path.exists(test_file):
                    break
    else:
        pybind11_header = "[pybind11 install directory]"

flags = "-std=c++14"

def set_flags(f):
    global flags
    flags = f

def ttran_(n):
    "A helper for ttran in translating Python names to C++ names"
    if n == "np.float32":
        return "std::float32_t";
    elif n == "np.float64":
        return "std::float64_t";
    elif n == "np.int64":
        return "std::int64_t";
    elif n == "str":
        return "std::string"
    elif n == "None":
        return "void";
    elif n == "List":
        return "std::vector"
    elif n == "Dict":
        return "std::map"
    elif n == '[':
        return '<'
    elif n == ']':
        return '>'
    else:
        return n

def ttran(n):
    "Translate Python names to C++ names"
    s = ''
    for i in re.finditer(r'[\w\.]+|.',n):
        s += ttran_(i.group(0))
    return s


class basic_type:
    def __init__(self,name=None):
        if name is not None:
            self.full_name = name

class template_type:
    def __init__(self,name=None):
        if name is not None:
            self.full_name = name
    def __getitem__(self,a):
        pass
    def __getslice__(self,*a):
        pass

type_names = {}

def create_type(name,alt=None,is_template=False):
    global type_names
    assert name is not None
    if alt is not None:
        type_names[name] = alt
    else:
        type_names[name] = name
    stack = inspect.stack()
    if 1 < len(stack):
        index = 1
    else:
        index = 0
    if is_template:
        stack[index].frame.f_globals[name] = template_type(name)
    else:
        stack[index].frame.f_globals[name] = basic_type(name)

create_type("svec",alt="std::vector",is_template=True)
create_type("smap",alt="std::map",is_template=True)

def gettype(ty):
    """
    Extract a C++ type from an AST element.
    """
    global type_names
    if ty is None:
        return "None"
    t = type(ty)
    if t == ast.Name:
        if ty.id in type_names.keys():
            return type_names[ty.id]
        return ty.id
    elif t in [np.float64]:
        return str(t)
    elif t in [ast.Index, ast.NameConstant]:
        return gettype(ty.value)
    elif t in [ast.Attribute]:
        return gettype(ty.value)+"."+gettype(ty.attr)
    elif t == ast.Subscript:
        return gettype(ty.value)+'['+gettype(ty.slice)+']'
    elif t == ast.Tuple:
        # If we're processing a Dict[str,str]
        # the "str,str" part is an ast.Tuple
        s = ''
        sep = ''
        for e in ty.elts:
            s += sep + gettype(e)
            sep = ','
        return s
    elif t == ast.Call:
        if ty.func.id == "Ref":
            return "%s&" % gettype(ty.args[0])
        elif ty.func.id == "Const":
            return "%s const" % gettype(ty.args[0])
        elif ty.func.id == "Move":
            return "%s&&" % gettype(ty.args[0])
        elif ty.func.id == "Ptr":
            return "%s*" % gettype(ty.args[0])
        else:
            s = ty.func.id + "<"
            for i in len(ty.args):
                if i > 0:
                    s += ","
                arg = ty.args[i]
                s += gettype(arg)
            s += ">"
            return s
    elif type(ty) == str:
        print(ty)
        raise Exception("?")
    else:
        print(ty.func.id)
        print(ty.args,"//",dir(ty.args[0]))
        print(ty.args[0].s, ty.args[1].id)
        print("<<",ty.__class__.__name__,">>",dir(ty))
        raise Exception("?")


def get_args(tree):
    nm = tree.__class__.__name__

    if nm in ["Module"]:
        for k in tree.body:
            args = get_args(k)
            if args is not None:
                return args

    elif nm in ["FunctionDef"]:
        args = []
        cargs = []
        oargs = ""
        for a in tree.args.args:
            type = ttran(gettype(a.annotation))
            args += [type+" "+a.arg]
            oargs += ',py::arg("%s")' % a.arg
            cargs += [a.arg]
            #oargs += ','+type
        return [",".join(args), oargs, cargs, ttran(gettype(tree.returns)) ]

    raise Exception("Could not find args")

class fcall:
    def __init__(self,base,fun_name,suffix,args,rettype):
        self.base = base
        self.fun_name = fun_name
        assert not re.match(r'.*_v\d+$',fun_name), fun_name
        self.suffix = suffix
        self.args_decl = args
        self.rettype = rettype
        if tmp_dir() not in sys.path:
            sys.path += [tmp_dir()]
        fpath = os.path.join(tmp_dir(),fun_name+suffix+".so")
        self.m = importlib.import_module(fun_name+suffix,fpath)

    def __call__(self,*args):
        self.m.load()
        if is_jupyter:
            try:
                outfile = os.path.join(tmp_dir(),"out.txt")
                fd1 = open(outfile, "w")
                save_out = os.dup(1)
                os.close(1)
                os.dup(fd1.fileno())

                errfile = os.path.join(tmp_dir(),"err.txt")
                fd2 = open(errfile, "w")
                save_err = os.dup(2)
                os.close(2)
                os.dup(fd2.fileno())

                return self.m.call(*args)
            finally:
                fd1.close()
                os.close(1)
                os.dup(save_out)
                os.close(save_out)
                print(open(outfile,"r").read(),end='')

                fd2.close()
                os.close(2)
                os.dup(save_err)
                os.close(save_err)
                print(open(errfile,"r").read(),end='')
        else:
            return self.m.call(*args)

# Create the basic source code
def write_src(**kwargs):

        wrapper = kwargs['wrapper']
        raw_name = kwargs["raw_name"]
        args = kwargs["args"]
        oargs = kwargs["oargs"]
        rettype = kwargs["rettype"]

        if wrapper is not None:
            cargs = kwargs["cargs"]
            call_args = "(" + ",".join(cargs) + ")"
            kwargs['wrap'] = wrap_src(
                f=raw_name,
                args=args,
                rettype=rettype,
                oargs=oargs,
                call_args=call_args,
                wrapper=wrapper.fun_name
            )
            kwargs['wrap_name'] = raw_name + "_wrapped"
        else:
            kwargs['wrap_name'] = raw_name
            kwargs['wrap'] = ''

        return """
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
{headers}

{fun_decls}

namespace py = pybind11;

extern "C" {rettype} {raw_name}({args}){{
  {body}
}};

{wrap}

extern "C" void load_functions() {{
    {fun_calls}
}}

PYBIND11_MODULE({name}, m) {{
    m.def("load",load_functions,"function"),
    m.def("call",{wrap_name},"function"{oargs});
}}
""".format(**kwargs)

def wrap_src(**kwargs):
    if kwargs["rettype"] == "void":
        src = """
    void {f}_wrapped({args}) {{
        std::function<void()> f = [&](){{
            {f}{call_args};
        }};
        {wrapper}(f);
    }}
""".format(**kwargs)
    else:
        src = """
    {rettype} {f}_wrapped({args}) {{
        {rettype} r;
        std::function<void()> f = [&](){{
            r = {f}{call_args};
        }};
        {wrapper}(f);
        return r;
    }}
""".format(**kwargs)
    return src

class py11:

    def __init__(self,*kargs,**kwargs):

        if 'recompile' in kwargs:
            self.recompile = kwargs['recompile']
        else:
            self.recompile = False

        if 'headers' in kwargs:
            self.headers = kwargs['headers']
        else:
            self.headers = []

        fun_decls = ''
        fun_calls = ''
        funs_list = []
        if 'funs' in kwargs:
            funs_list += kwargs['funs']
        if 'wrap' in kwargs:
            wrapper = kwargs['wrap']
            assert wrapper != None
            funs_list += [wrapper]
            self.wrapper = wrapper
        else:
            self.wrapper = None

        if len(funs_list) > 0:
            fun_decls += load_func
            for f in funs_list: #kwargs['funs']:
                f1 = ''
                f2 = ''
                f1 += 'typedef {rettype}(*{f}_type_def)({args_decl});\n'
                f1 += '{f}_type_def {f} = nullptr;\n'
                f2 += '{f} = ({f}_type_def)load_func("{f}");\n'
                f1 = f1.format(
                    f=f.fun_name,
                    dir=tmp_dir(),
                    rettype=f.rettype,
                    args_decl=f.args_decl);
                f2 = f2.format(
                    f=f.fun_name,
                    dir=tmp_dir(),
                    rettype=f.rettype,
                    args_decl=f.args_decl);
                fun_decls += f1
                fun_calls += f2
        self.fun_decls = fun_decls
        self.fun_calls = fun_calls

    def __call__(self,fun):
        base = os.path.join(tmp_dir(), fun.__name__)
        src = inspect.getsource(fun)
        tree = ast.parse(src)
        args, oargs, cargs, rettype = get_args(tree)
        code = ""
        fname = base+'.cpp'
        mname = base+'.so.txt'

        if os.path.exists(mname):
            with open(mname, "r") as fd:
                version = int(fd.read().strip())
        else:
            version = 0
        suffix = "_v"+str(version)
        libname = base+suffix+'.so'

#        if self.wrapper is not None:
#            call_args = "(" + ",".join(cargs) + ")"
#            wrap = wrap_src(
#                f=fun.__name__,
#                args=args,
#                rettype=rettype,
#                oargs=oargs,
#                call_args=call_args,
#                wrapper=self.wrapper.fun_name
#            )
#            wrap_name = fun.__name__ + "_wrapped"
#        else:
#            wrap_name = fun.__name__
#            wrap = ''

        src = write_src(
            name=fun.__name__+suffix,
            raw_name=fun.__name__,
            wrapper=self.wrapper,
            body=fun.__doc__,
            headers='\n'.join(['#include '+h for h in self.headers]),
            rettype=rettype,
            args=args,
            oargs=oargs,
            cargs=cargs,
            fun_decls=self.fun_decls,
            fun_calls=self.fun_calls
        )

        suffix = ''
        if os.path.exists(fname):
            code = open(fname).read()
        suffix = "_v"+str(version)
        if code != src or self.recompile or not os.path.exists(libname):
            old_file = base + suffix + '.so'
            if os.path.exists(old_file):
                os.remove(old_file)
            version += 1
            suffix = "_v"+str(version)
            base += suffix
            src = write_src(
                name=fun.__name__+suffix,
                raw_name=fun.__name__,
                wrap_name=fun.__name__,
                wrapper=self.wrapper,
                body=fun.__doc__,
                headers='\n'.join(['#include '+h for h in self.headers]),
                rettype=rettype,
                args=args,
                oargs=oargs,
                cargs=cargs,
                fun_decls=self.fun_decls,
                fun_calls=self.fun_calls
            )

            with open(mname, "w") as fd:
                print(version,file=fd)

            with open(fname, "w") as fd:
                fd.write(src)
            cmd="g++ {flags} -I{python_header} -I{pybind11_header} -rdynamic -fPIC -shared -o {base}.so {fname}".format(base=base,python_header=python_header,pybind11_header=pybind11_header,flags=flags,fname=fname)
            r = 0
            try:
                print(cmd)
                proc = Popen(cmd.split(' '),stdout=PIPE,stderr=PIPE,universal_newlines=True) 
                outs, errs = proc.communicate()
                print(outs,end='')
                print(errs,end='')
                r = proc.poll()
            except Exception as e:
                print(e)
                r = 1
                print("Except",e)
            if r != 0:
                if os.path.exists(base+".so"):
                    os.remove(base+".so")
                return None
        return fcall(base,fun.__name__,suffix,args,rettype)
