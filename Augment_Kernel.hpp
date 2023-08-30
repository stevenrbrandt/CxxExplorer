///-----------------------------------
/// Inserted code
int parent = getpid();
int child = -1;
int child2 = -1;

const char *FAIL="~**FAIL**~";

const int trapio_buf_siz = 10000;

std::string fname(int fd,int pid) {
    std::ostringstream fname;
    fname << "out-" << fd << "-" << pid;
    return fname.str();
}

std::string fnread(std::string fn) {
    int fd = open(fn.c_str(), O_RDONLY);
    char buf[trapio_buf_siz+1];
    int n = read(fd, buf, trapio_buf_siz);
    return std::string(buf, n);
}

struct TrapIO {
    int dupfd, fd, rd;
    char buf[trapio_buf_siz+1];
    std::string fstr;
    TrapIO(int fd_) : fd(fd_) {
        dupfd = dup(fd);
        fstr = fname(fd, getpid());
        int fdalt = open(fstr.c_str(), O_WRONLY|O_TRUNC|O_CREAT, 0600);
        if(fdalt >= 0) {
            close(fd);
            dup(fdalt);
            close(fdalt);
        }
        rd = open(fstr.c_str(), O_RDONLY);
        //::unlink(fstr.c_str());
    }
    char *get() {
        int nbytes = read(rd, buf, trapio_buf_siz);
        buf[nbytes] = 0;
        return buf;
    }
    void cleanup() {
        close(fd);
        dup(dupfd);
        close(dupfd);
        unlink(fstr.c_str());
    }
};

Pipe chan;
Pipe code_chan;

void 
sig_exit(int sig_num)
{
    std::cerr << "Died from signal " << sig_num << std::endl;
	exit(0);
}

char* cling_eval(TheMetaProcessor *metaProc, const char *code) {
    bool good = false;
    char *result = 0;
    if(child < 0) {
        child = fork();
    }
    if(child == 0) {
        signal(SIGINT , sig_exit);
        signal(SIGABRT , sig_exit);
        signal(SIGILL , sig_exit);
        signal(SIGFPE , sig_exit);
        signal(SIGSEGV, sig_exit);
        signal(SIGTERM , sig_exit);
        while(true) {
            Pipe chan2;
            char *code_c = code_chan.read("code");
            child2 = fork();
            if(child2 == 0) {
                TrapIO fd1(1), fd2(2);
                char *result = cling_eval_inner(metaProc, code_c, good);

                // Ensure all IO is flushed
                std::cout << std::flush;
                std::cerr << std::flush;
                fflush(stdout);
                fflush(stderr);

                fd1.cleanup();
                fd2.cleanup();

                chan2.writeInt(good);
                if(good)
                    chan.writeInt(getpid());
                else
                    chan.writeInt(0);
                chan.write(fd1.get());
                chan.write(fd2.get());
                chan.write(result);
                if(!good)
                    exit(1);
            } else {
                int good = chan2.readIntTmout(1);
                for(int t=0;t<50;t++) {
                    if(good >= 0) {
                        // child responded
                        break;
                    }
                    int wstatus;
                    if(waitpid(child2, &wstatus, WNOHANG) > 0) {
                        // child has exited
                        break;
                    }
                    // try again
                    good = chan2.readIntTmout(5);
                }
                if(good > 0) {
                    exit(0);
                } else if(good < 0) {
                    chan.writeInt(0);
                    std::string fout = fname(1, child2);
                    std::string ferr = fname(2, child2);
                    std::string bout = fnread(fout);
                    std::string berr = fnread(ferr);
                    chan.write(bout.c_str());
                    chan.write(berr.c_str());
                    chan.write("Unknown failure");
                    ::unlink(fout.c_str());
                    ::unlink(ferr.c_str());
                } else {
                    int status;
                    wait(&status);
                }
            }
        }
    } else {
        code_chan.write(code);
        int pid = chan.readInt();

        result = chan.read("stdout");
        std::cout << result << std::flush;

        result = chan.read("stderr");
        std::cerr << result << std::flush;

        result = chan.read("result");

        if(pid == child || pid == 0) {
            ;
        } else {
            int status;
            wait(&status);
            child = pid;
        }
    }
    return result;
}
///-----------------------------------
