#ifndef RUN_HPX_CPP
#define RUN_HPX_CPP
//  Copyright (c) 2016-2022 Hartmut Kaiser
//  Copyright (c) 2019-2026 Steven R. Brandt
//
//  Distributed under the Boost Software License, Version 1.0.
//
// Embed HPX in Cling. The runtime is started for one run_hpx() call and
// torn down afterwards so the fork-based Jupyter kernel can snapshot a
// process that is not full of HPX worker threads.

#include <hpx/hpx.hpp>
#include <hpx/hpx_start.hpp>
#include <hpx/condition_variable.hpp>
#include <hpx/functional.hpp>
#include <hpx/mutex.hpp>
#include <hpx/runtime.hpp>
#include <hpx/thread.hpp>

#include <functional>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <type_traits>
#include <utility>
#include <vector>

namespace hpx_global {

#if defined(linux) || defined(__linux) || defined(__linux__)

int __argc = 1;
char __arg0__[] {"jupytercling"};
char* __argv__[] {static_cast<char*>(__arg0__), nullptr};
char** __argv = static_cast<char**>(__argv__);

#elif defined(__APPLE__)

#include <crt_externs.h>

inline int get_arraylen(char** argv)
{
    int count = 0;
    if (nullptr != argv)
    {
        while (nullptr != argv[count])
            ++count;
    }
    return count;
}

int __argc = get_arraylen(*_NSGetArgv());
char** __argv = *_NSGetArgv();

#endif

struct manage_global_runtime
{
    explicit manage_global_runtime(int nth)
      : running_(false)
      , rts_(nullptr)
    {
        std::ostringstream thread_spec;
        thread_spec << "--hpx:threads=" << nth;
        std::vector<std::string> const cfg = {
            "hpx.run_hpx_main!=1",
            thread_spec.str(),
            "hpx.commandline.allow_unknown!=1",
            "hpx.commandline.aliasing!=0",
            "hpx.stacks.small_size=0x160000"};

        hpx::function<int(int, char**)> start_function =
            [this](int argc, char** argv) { return this->hpx_main(argc, argv); };

        hpx::init_params init_args;
        init_args.cfg = cfg;
        init_args.mode = hpx::runtime_mode::default_;

        if (!hpx::start(start_function, __argc, __argv, init_args))
        {
            std::abort();
        }

        std::unique_lock<std::mutex> lk(startup_mtx_);
        while (!running_)
            startup_cond_.wait(lk);
    }

    ~manage_global_runtime()
    {
        {
            std::lock_guard<hpx::spinlock> lk(mtx_);
            rts_ = nullptr;
        }
        cond_.notify_one();
        hpx::stop();
    }

    void register_thread(char const* name)
    {
        hpx::register_thread(rts_, name);
    }
    void unregister_thread()
    {
        hpx::unregister_thread(rts_);
    }

protected:
    int hpx_main(int, char**)
    {
        rts_ = hpx::get_runtime_ptr();
        {
            std::lock_guard<std::mutex> lk(startup_mtx_);
            running_ = true;
        }
        startup_cond_.notify_one();

        {
            std::unique_lock<hpx::spinlock> lk(mtx_);
            if (rts_ != nullptr)
                cond_.wait(lk);
        }
        return hpx::finalize();
    }

private:
    hpx::spinlock mtx_;
    hpx::condition_variable_any cond_;

    std::mutex startup_mtx_;
    std::condition_variable startup_cond_;
    bool running_;
    hpx::runtime* rts_;
};

manage_global_runtime* init = nullptr;

int next_id_seq = 1;
std::string next_id()
{
    std::ostringstream buf;
    buf << "id=" << next_id_seq++;
    return buf.str();
}

struct thread_registration_wrapper
{
    explicit thread_registration_wrapper(char const* name)
    {
        init->register_thread(name);
    }
    ~thread_registration_wrapper()
    {
        init->unregister_thread();
    }
};

void submit_work(int nth, std::function<void()> work_item)
{
    if (init == nullptr)
        init = new manage_global_runtime(nth);
    std::string id = next_id();
    std::function<void()> hpx_work_item = [&]() {
        thread_registration_wrapper register_thread(id.c_str());
        hpx::run_as_hpx_thread(work_item);
    };
    std::thread t(hpx_work_item);
    t.join();
    delete init;
    init = nullptr;
}

}    // namespace hpx_global

const int run_hpx_threads = 4;

template <typename F>
typename std::invoke_result_t<F> run_hpx(F f)
{
    using R = std::invoke_result_t<F>;
    if constexpr (std::is_same_v<R, void>)
    {
        hpx_global::submit_work(run_hpx_threads, f);
    }
    else
    {
        R r{};
        hpx_global::submit_work(run_hpx_threads, [&r, &f]() { r = f(); });
        return r;
    }
}
#endif
