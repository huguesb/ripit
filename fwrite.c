#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>
#include <errno.h>


ssize_t write_or_exit(int fd, const char *buf, size_t len) {
    ssize_t w = write(fd, buf, len);
    if (w == -1) {
        perror("fwrite: write()");
        exit(EXIT_FAILURE);
    }
    return w;
}


int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage:\n%s <path> ...\nWrite arguments to path, in non-blocking mode, ignoring errors", argv[0]);
        return EXIT_FAILURE;
    }
    
    signal(SIGPIPE, SIG_IGN);

    int fd = open(argv[1], O_WRONLY | O_NONBLOCK);
    if (fd == -1) {
        perror("fwrite: open()");
        exit(EXIT_FAILURE);
    }

    for (int i = 2; i < argc; ++i) {
        int w = 0;
        int n = strlen(argv[i]);
        while (w < n) {
            w += write_or_exit(fd, argv[i] + w, n - w);
        }
        write_or_exit(fd, i+1 == argc ? "\n" : " ", 1);
    }
    close(fd);
    return EXIT_SUCCESS;
}

