#ifndef PIPE_HPP
#define PIPE_HPP

#include <assert.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <iostream>
#include <fcntl.h>
#include <sys/select.h>
#include <poll.h>

const char *RD_TMOUT = "/* Read Timeout */";

class Pipe {
    int pipe_fd[2];
public:
    Pipe() {
        pipe(pipe_fd);
    }
    ~Pipe() {
        close(pipe_fd[0]);
        close(pipe_fd[1]);
    }
    void writeInt(int n) {
        ::write(pipe_fd[1], &n, sizeof(n));
    }
    void write(const char *s) {
        if(s == 0)
            s = "";
        int n = strlen(s);
        writeInt(n);
        ::write(pipe_fd[1], s, n);
    }
    int readIntTmout(int tmout) {
        if(tmout > 0) {
            pollfd pd;
            pd.fd = pipe_fd[0];
            pd.events = POLLIN;//
            pd.revents = 0;
            sigset_t sigmask;
            timespec tmo;
            tmo.tv_sec = tmout;
            tmo.tv_nsec = 0;
            int ready = ppoll(&pd, 1, &tmo, &sigmask);
            if(ready <= 0) {
                return -1;
            }
        }
        int n = readInt();
        return n;
    }

    int readInt(const char *msg="") {
        int n = 0;
        ::read(pipe_fd[0], &n, sizeof(n));
        return n;
    }
    char *read(const char *msg="") {
        int n = readInt(msg);
        if(n < 0) {
            n = strlen(RD_TMOUT);
            char *s = (char *)malloc(sizeof(char)*(n+1));
            strcpy(s, RD_TMOUT);
            return s;
        }
        assert(n < 10000);
        char *s = (char *)malloc(sizeof(char)*(n+1));
        ::read(pipe_fd[0], s, n);
        s[n] = 0;
        return s;
    }
};
#endif
