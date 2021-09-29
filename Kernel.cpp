//------------------------------------------------------------------------------
// CLING - the C++ LLVM-based InterpreterG :)
// author:  Axel Naumann <axel@cern.ch>
//
// This file is dual-licensed: you can choose to license it under the University
// of Illinois Open Source License or the GNU Lesser General Public License. See
// LICENSE.TXT for details.
//------------------------------------------------------------------------------

// FIXME: This file shall contain the decl of cling::Jupyter in a future
// revision!
//#include "cling/Interpreter/Jupyter/Kernel.h"

#include "cling/Interpreter/Interpreter.h"
#include "cling/Interpreter/Value.h"
#include "cling/MetaProcessor/MetaProcessor.h"
#include "cling/Utils/Output.h"

#include "cling/Interpreter/Exception.h"
#include "llvm/Support/raw_ostream.h"

#include <map>
#include <string>
#include <cstring>
#include <iostream>
#include <sstream>
#include <fstream>

#include <Pipe.hpp>
#include <sys/wait.h>

#ifndef _WIN32
# include <unistd.h>
#else
# include <io.h>
# define write _write
#endif

// FIXME: should be moved into a Jupyter interp struct that then gets returned
// from create.
int pipeToJupyterFD = -1;

namespace cling {
  namespace Jupyter {
    struct MIMEDataRef {
      const char* m_Data;
      const long m_Size;

      MIMEDataRef(const std::string& str):
      m_Data(str.c_str()), m_Size((long)str.length() + 1) {}
      MIMEDataRef(const char* str):
      MIMEDataRef(std::string(str)) {}
      MIMEDataRef(const char* data, long size):
      m_Data(data), m_Size(size) {}
    };

    /// Push MIME stuff to Jupyter. To be called from user code.
    ///\param contentDict - dictionary of MIME type versus content. E.g.
    /// {{"text/html", {"<div></div>", }}
    ///\returns `false` if the output could not be sent.
    bool pushOutput(const std::map<std::string, MIMEDataRef> contentDict) {

      // Pipe sees (all numbers are longs, except for the first:
      // - num bytes in a long (sent as a single unsigned char!)
      // - num elements of the MIME dictionary; Jupyter selects one to display.
      // For each MIME dictionary element:
      //   - size of MIME type string  (including the terminating 0)
      //   - MIME type as 0-terminated string
      //   - size of MIME data buffer (including the terminating 0 for
      //     0-terminated strings)
      //   - MIME data buffer

      // Write number of dictionary elements (and the size of that number in a
      // char)
      unsigned char sizeLong = sizeof(long);
      if (write(pipeToJupyterFD, &sizeLong, 1) != 1)
        return false;
      long dictSize = contentDict.size();
      if (write(pipeToJupyterFD, &dictSize, sizeof(long)) != sizeof(long))
        return false;

      for (auto iContent: contentDict) {
        const std::string& mimeType = iContent.first;
        long mimeTypeSize = (long)mimeType.size();
        if (write(pipeToJupyterFD, &mimeTypeSize, sizeof(long)) != sizeof(long))
          return false;
        if (write(pipeToJupyterFD, mimeType.c_str(), mimeType.size() + 1)
            != (long)(mimeType.size() + 1))
          return false;
        const MIMEDataRef& mimeData = iContent.second;
        if (write(pipeToJupyterFD, &mimeData.m_Size, sizeof(long))
            != sizeof(long))
          return false;
        if (write(pipeToJupyterFD, mimeData.m_Data, mimeData.m_Size)
            != mimeData.m_Size)
          return false;
      }
      return true;
    }
  } // namespace Jupyter
} // namespace cling

extern "C" {
///\{
///\name Cling4CTypes
/// The Python compatible view of cling

/// The MetaProcessor cast to void*
using TheMetaProcessor = void;

/// Create an interpreter object.
TheMetaProcessor*
cling_create(int argc, const char *argv[], const char* llvmdir, int pipefd) {
  pipeToJupyterFD = pipefd;
  auto I = new cling::Interpreter(argc, argv, llvmdir);
  return new cling::MetaProcessor(*I, cling::errs());
}


/// Destroy the interpreter.
void cling_destroy(TheMetaProcessor *metaProc) {
  cling::MetaProcessor *M = (cling::MetaProcessor*)metaProc;
  cling::Interpreter *I = const_cast<cling::Interpreter*>(&M->getInterpreter());
  delete M;
  delete I;
}

/// Stringify a cling::Value
static std::string ValueToString(const cling::Value& V) {
  std::string valueString;
  {
    llvm::raw_string_ostream os(valueString);
    V.print(os);
  }
  return valueString;
}

const char *expr = ".expr";
const int nexpr = strlen(expr);
int sequence = 0;

/// Evaluate a string of code. Returns nullptr on failure.
/// Returns a string representation of the expression (can be "") on success.
char* cling_eval_inner(TheMetaProcessor *metaProc, const char *code,bool& good) {
  cling::MetaProcessor *M = (cling::MetaProcessor*)metaProc;
  cling::Value V;
  cling::Interpreter::CompilationResult Res;
  bool isExcept = false;
  try {
    good = 0;
    std::ostringstream cmd;
    std::ostringstream fname;
  	fname << getenv("HOME") << "/.code" << (sequence++) << ".cc";
  	std::ofstream cfile(fname.str());
    if(strncmp(code,expr,nexpr) == 0) {
        cfile << "struct __tmp__" << sequence << " {" << std::endl;

        // constructor
        cfile << "__tmp__" << sequence << " (){" << std::endl;
        cfile << "#ifdef WRAP_EXPR" << std::endl;
        cfile << "WRAP_EXPR(init();)" << std::endl;
        cfile << "#else" << std::endl;
        cfile << "init();" << std::endl;
        cfile << "#endif" << std::endl;
        cfile << "}" << std::endl;

        cfile << "static void init() {" << std::endl;
	    cfile << (code+nexpr) << std::endl;
        cfile << "}" << std::endl;

        cfile << "} __tmp__instance__" << sequence << ";" << std::endl;
    } else {
   	    cfile << code << std::endl;
    }
   	cfile.close();
 	cmd << ".L " << fname.str();
    std::string cmdstr = cmd.str();
    if (M->process(cmdstr.c_str(), Res, &V, /*disableValuePrinting*/ true)) {
      //cling::Jupyter::pushOutput({{"text/html", "Incomplete input! Ignored."}});
      std::cout << "Incomplete input! Ignored." << std::endl;
      M->cancelContinuation();
      return nullptr;
    }
    std::string fstr = fname.str();
    //unlink(fstr.c_str());
    good = (Res == 0);
  }
  catch(cling::InterpreterException& e) {
    //std::string output (strcat("Caught an interpreter exception:", e.what().c_str())) ;
    std::string output ("Caught an interpreter exception:");
    output += e.what();
    cling::Jupyter::pushOutput({{"text/html", output}});
    isExcept = true;
  }
  catch(std::exception& e) {
    //std::string output(strcat("Caught a standard exception:" , e.what().c_str())) ;
    std::string output("Caught a standard exception:") ;
    output += e.what();
    cling::Jupyter::pushOutput({{"text/html", output}});
    isExcept = true;
  }
  catch(...) {
    std::string output = "Exception occurred. Recovering...\n";
    cling::Jupyter::pushOutput({{"text/html", output}});
    isExcept = true;
  }

  if (isExcept) {
    return nullptr;
  }

  if (Res != cling::Interpreter::kSuccess)
    return nullptr;

  if (!V.isValid())
    return strdup("");
  return strdup(ValueToString(V).c_str());
}

#include <Augment_Kernel.hpp>

void cling_eval_free(char* str) {
  free(str);
}

/// Code completion interfaces.

/// Start completion of code. Returns a handle to be passed to
/// cling_complete_next() to iterate over the completion options. Returns nulptr
/// if no completions are known.
void* cling_complete_start(const char* code) {
  return new int(42);
}

/// Grab the next completion of some code. Returns nullptr if none is left.
const char* cling_complete_next(void* completionHandle) {
  int* counter = (int*) completionHandle;
  if (++(*counter) > 43) {
    delete counter;
    return nullptr;
  }
  return "COMPLETE!";
}

///\}

} // extern "C"
