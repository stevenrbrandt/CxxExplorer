#ifndef RUN_HPX_CPP
#define RUN_HPX_CPP
//  Copyright (c) 2016 Hartmut Kaiser
//
//  Distributed under the Boost Software License, Version 1.0. (See accompanying
//  file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

// This example demonstrates several things:
//
// - How to initialize (and terminate) the HPX runtime from a global object
//   (see the type `manage_global_runtime' below)
// - How to register and unregister any (kernel) thread with the HPX runtime
// - How to launch an HPX thread from any (registered) kernel thread and
//   how to wait for the HPX thread to run to completion before continuing.
//   Any value returned from the HPX thread will be marshaled back to the
//   calling (kernel) thread.
//
// This scheme is generally useful if HPX should be initialized from a shared
// library and the main executable might not even be aware of this.

#include <hpx/hpx.hpp>
#include <hpx/include/run_as.hpp>
#include <hpx/hpx_start.hpp>

#include <mutex>
#include <string>
#include <vector>
#include <sstream>

namespace hpx_global {

///////////////////////////////////////////////////////////////////////////////
// Store the command line arguments in global variables to make them available
// to the startup code.

#if defined(linux) || defined(__linux) || defined(__linux__)

int __argc = 1;
char __arg0__[] { "jupytercling" };
char* __argv__[] {(char*)__arg0__,0};
char** __argv = (char**)__argv__;

void set_argv_argv(int argc, char* argv[], char* env[])
{
    //__argc = argc;
    //__argv = argv;
}

__attribute__((section(".init_array")))
    void (*set_global_argc_argv)(int, char*[], char*[]) = &set_argv_argv;

#elif defined(__APPLE__)

#include <crt_externs.h>

inline int get_arraylen(char** argv)
{
    int count = 0;
    if (nullptr != argv)
    {
        while(nullptr != argv[count])
            ++count;
    }
    return count;
}

#error "Bad"
int __argc = get_arraylen(*_NSGetArgv());
char** __argv = *_NSGetArgv();

#endif

///////////////////////////////////////////////////////////////////////////////
// This class demonstrates how to initialize a console instance of HPX
// (locality 0). In order to create an HPX instance which connects to a running
// HPX application two changes have to be made:
//
//  - replace hpx::runtime_mode_console with hpx::runtime_mode_connect
//  - replace hpx::finalize() with hpx::disconnect()
//
struct manage_global_runtime
{
    manage_global_runtime(int nth)
      : running_(false), rts_(nullptr)
    {
#if defined(HPX_WINDOWS)
        hpx::detail::init_winsocket();
#endif

        std::ostringstream thread_spec;
        thread_spec << "--hpx:threads=" << nth;
        std::vector<std::string> const cfg = {
            // make sure hpx_main is always executed
            "hpx.run_hpx_main!=1",
            thread_spec.str().c_str(),
            // allow for unknown command line options
            "hpx.commandline.allow_unknown!=1",
            // disable HPX' short options
            "hpx.commandline.aliasing!=0",
            "hpx.stacks.small_size=0x160000"
        };

        using hpx::util::placeholders::_1;
        using hpx::util::placeholders::_2;
        hpx::util::function_nonser<int(int, char**)> start_function =
            hpx::util::bind(&manage_global_runtime::hpx_main, this, _1, _2);

        if (!hpx::start(start_function, __argc, __argv, cfg, hpx::runtime_mode_console))
        {
            // Something went wrong while initializing the runtime.
            // This early we can't generate any output, just bail out.
            std::abort();
        }

        // Wait for the main HPX thread (hpx_main below) to have started running
        std::unique_lock<std::mutex> lk(startup_mtx_);
        while (!running_)
            startup_cond_.wait(lk);
    }

    ~manage_global_runtime()
    {
        // notify hpx_main above to tear down the runtime
        {
            std::lock_guard<hpx::lcos::local::spinlock> lk(mtx_);
            rts_ = nullptr;               // reset pointer
        }

        cond_.notify_one();     // signal exit

        // wait for the runtime to exit
        hpx::stop();
    }

    // registration of external (to HPX) threads
    void register_thread(const char *name)
    {
        hpx::register_thread(rts_, name);
    }
    void unregister_thread()
    {
        hpx::unregister_thread(rts_);
    }

protected:
    // Main HPX thread, does nothing but wait for the application to exit
    int hpx_main(int argc, char* argv[])
    {
        // Store a pointer to the runtime here.
        rts_ = hpx::get_runtime_ptr();

        // Signal to constructor that thread has started running.
        {
            std::lock_guard<std::mutex> lk(startup_mtx_);
            running_ = true;
        }

        startup_cond_.notify_one();

        // Here other HPX specific functionality could be invoked...

        // Now, wait for destructor to be called.
        {
            std::unique_lock<hpx::lcos::local::spinlock> lk(mtx_);
            if (rts_ != nullptr)
                cond_.wait(lk);
        }

        // tell the runtime it's ok to exit
        return hpx::finalize();
    }

private:
    hpx::lcos::local::spinlock mtx_;
    hpx::lcos::local::condition_variable_any cond_;

    std::mutex startup_mtx_;
    std::condition_variable startup_cond_;
    bool running_;

    hpx::runtime* rts_;
};

// This global object will initialize HPX in its constructor and make sure HPX
// stops running in its destructor.
manage_global_runtime *init = nullptr;//new manage_global_runtime;//nullptr;

int next_id_seq = 1;
//char next_id_buf[5];
std::string next_id() {
  //sprintf(next_id_buf,"id=%d",next_id_seq++);
  std::ostringstream buf;
  buf << "id=" << next_id_seq++;
  return std::move(buf.str());
}

///////////////////////////////////////////////////////////////////////////////
struct thread_registration_wrapper
{
    thread_registration_wrapper(const char *name)
    {
        // Register this thread with HPX, this should be done once for
        // each external OS-thread intended to invoke HPX functionality.
        // Calling this function more than once will silently fail (will
        // return false).
        init->register_thread(name);
    }
    ~thread_registration_wrapper()
    {
        // Unregister the thread from HPX, this should be done once in the
        // end before the external thread exists.
        init->unregister_thread();
    }
};

///////////////////////////////////////////////////////////////////////////////

void submit_work(int nth,std::function<void()> work_item) {
    if(init == nullptr)
        init = new manage_global_runtime(nth);
    std::string id = next_id();
    std::function<void()> hpx_work_item = [&](){
        thread_registration_wrapper register_thread(id.c_str());
        hpx::threads::run_as_hpx_thread(work_item);
    };
    std::thread t(hpx_work_item);
    t.join();
    delete init;
    init = nullptr;
}

};

const int run_hpx_threads = 4;

template<typename F>
typename std::result_of<F()>::type run_hpx(F f) {
    if constexpr(std::is_same<typename std::result_of<F()>::type,void>::value) {
        hpx_global::submit_work(run_hpx_threads, f);
    } else {
        typename std::result_of<F()>::type r;
        hpx_global::submit_work(run_hpx_threads, [&r,&f](){ 
            r = f();
        });
        return std::move(r);
    }
}
#endif
