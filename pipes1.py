import ctypes, os, sys, re
from signal import *

delim = '$delim$'
end = '$end$'
delimend = delim+end

class my_void_p(ctypes.c_void_p):
  pass

def clearout(sig,frame):
    sys.stdout.write(delimend)
    sys.stdout.flush()
    sys.stderr.write(delimend)
    sys.stderr.flush()
    exit(2)

#signal(SIGABRT.value, clearout)

class cling:
    def __init__(self):
        bver = 0
        for fn in os.listdir("/usr/lib64"):
            g = re.match(r'libboost_system.so.1.(\d+).*',fn)
            if g:
                bver = int(g.group(1))
        ctypes.CDLL("/usr/lib64/libboost_system.so.1.%d.0" % bver,ctypes.RTLD_GLOBAL)
        ctypes.CDLL("/usr/lib64/libboost_filesystem.so.1.%d.0" % bver,ctypes.RTLD_GLOBAL)
        ctypes.CDLL("/usr/lib64/libboost_program_options.so.1.%d.0" % bver,ctypes.RTLD_GLOBAL)
        ctypes.CDLL("/usr/lib64/libboost_thread.so.1.%d.0" % bver,ctypes.RTLD_GLOBAL)
        if os.path.exists("/usr/local/lib64/libhpx.so"):
            ctypes.CDLL("/usr/local/lib64/libhpx.so",ctypes.RTLD_GLOBAL)
            flags = [b"-lhpx"]
        else:
            ctypes.CDLL("/usr/local/lib64/libhpxd.so",ctypes.RTLD_GLOBAL)
            flags = [b"-DHPX_DEBUG", b"-lhpxd"]
        self.clingJupyter = ctypes.CDLL("/usr/lib/libclingJupyter.so", mode = ctypes.RTLD_GLOBAL)
        clingInstDir=b"/usr/lib/clang/5.0.0"
        stdopt=b"-std=c++17"
        argv = [
                        b"cling",
                        b"-I" + clingInstDir + b"/include/",
                        b"-std=c++17",
                        b"-I.",
                        b"-L/usr/local/lib64",
                        #b"-lboost_filesystem",
                        #b"-lboost_program_options",
                        #b"-lboost_system"
                        #b"-I/usr/local/include",
                        #b"-I/usr/include"
            ] + flags
        argc = len(argv)
        CharPtrArrayType = ctypes.c_char_p * argc
        llvmResourceDirCP = ctypes.c_char_p("/usr".encode('utf8'))
        sideband_pipe, pipe_in = os.pipe()
        self.clingJupyter.cling_create.restype = my_void_p
        self.clingJupyter.cling_eval.restype = my_void_p
        self.interp = self.clingJupyter.cling_create(
            ctypes.c_int(argc), CharPtrArrayType(*argv), llvmResourceDirCP, pipe_in)

    def run_cmd(self,code):
        stringResult = self.clingJupyter.cling_eval(self.interp, ctypes.c_char_p(code.encode('utf8')))
        if stringResult:
            s = ctypes.cast(stringResult, ctypes.c_char_p).value.decode('utf8', 'replace').strip()
            if s != '':
                print(delim)
                print(s)
        print(delimend)
        sys.stdout.flush()
        sys.stderr.flush()
        print(delimend,file=sys.stderr)
        sys.stderr.flush()

cl = cling()

root_pid = os.getpid()

def readinp(inp):
    inbuf = ''
    while True:
        inbuf += inp.readline()
        if delim in inbuf:
            parts = inbuf.split(delim)
            inbuf = parts[0].strip()+'\n'
            return inbuf

if __name__ == "__main__":
    if len(sys.argv) > 2:
        cl.run_cmd("#include <foo.cpp>")
        #cl.run_cmd(".L x.cpp")
        #cl.run_cmd("a")
        #cl.run_cmd("int fut = run_hpx([]()->int{ return 4; });")
        cl.run_cmd('auto b = fun([](){ return 42; });')
    else:
        while True:
            inbuf = readinp(sys.stdin) 
            cl.run_cmd(inbuf)
