/* SPDX-License-Identifier: AGPL-3.0-or-later */
/* Read-only hostapd control client. Never prints station addresses or keys. */
#define _GNU_SOURCE
#include <ctype.h>
#include <errno.h>
#include <stddef.h>
#include <poll.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

#ifndef CONTROL_PATH
#define CONTROL_PATH "/data/misc/wifi/hostapd-kp-usb/rtwlan0"
#endif

static long long now_ms(void)
{
    struct timespec time;
    if (clock_gettime(CLOCK_MONOTONIC, &time))
        return -1;
    return (long long)time.tv_sec * 1000 + time.tv_nsec / 1000000;
}

static int request(int fd, const char *command, char *reply, size_t size, long long deadline)
{
    if (send(fd, command, strlen(command), 0) != (ssize_t)strlen(command))
        return -1;
    for (;;) {
        long long now = now_ms();
        if (now < 0 || now >= deadline)
            return -1;
        struct pollfd wait = { .fd = fd, .events = POLLIN };
        int result = poll(&wait, 1, (int)(deadline - now));
        if (result < 0 && errno == EINTR)
            continue;
        if (result <= 0 || !(wait.revents & POLLIN))
            return -1;
        ssize_t got = recv(fd, reply, size, MSG_TRUNC);
        if (got <= 0 || (size_t)got >= size)
            return -1;
        reply[got] = '\0';
        return 0;
    }
}

static int station_count(int fd, long long deadline)
{
    char command[64] = "STA-FIRST", reply[16384], seen[32][18];
    int total = 0, count = 0;
    for (;;) {
        if (request(fd, command, reply, sizeof(reply), deadline))
            return -1;
        if (!strcmp(reply, "FAIL\n"))
            return count;
        if (total == 32 || strlen(reply) < 18 || reply[17] != '\n')
            return -1;
        for (int i = 0; i < 17; ++i) {
            if ((i + 1) % 3 == 0 ? reply[i] != ':' : !isxdigit((unsigned char)reply[i]))
                return -1;
            reply[i] = (char)tolower((unsigned char)reply[i]);
        }
        for (int i = 0; i < total; ++i)
            if (!strncmp(seen[i], reply, 17))
                return -1;
        memcpy(seen[total], reply, 17);
        seen[total++][17] = '\0';
        int authorized = -1;
        char *save, *line = strtok_r(reply + 18, "\n", &save);
        for (; line; line = strtok_r(NULL, "\n", &save)) {
            if (!strncmp(line, "flags=", 6)) {
                authorized = strstr(line + 6, "[AUTHORIZED]") && strstr(line + 6, "[ASSOC]") ? 1 : 0;
                break;
            }
            /* Android 4.4 hostapd's numeric IEEE 802.1X PortStatus MIB. */
            if (!strcmp(line, "dot1xAuthAuthControlledPortStatus=1"))
                authorized = 1;
            if (!strcmp(line, "dot1xAuthAuthControlledPortStatus=2"))
                authorized = 0;
        }
        if (authorized < 0)
            return -1; /* Let the caller use the Realtek associated-station table. */
        count += authorized;
        snprintf(command, sizeof(command), "STA-NEXT %s", seen[total - 1]);
    }
}

int main(void)
{
    int fd = socket(AF_UNIX, SOCK_DGRAM, 0);
    if (fd < 0)
        return 1;
    struct sockaddr_un local = { .sun_family = AF_UNIX };
    int length = snprintf(local.sun_path + 1, sizeof(local.sun_path) - 1,
                          "kp-rtwlan0-stations-%ld", (long)getpid());
    struct sockaddr_un remote = { .sun_family = AF_UNIX };
    memcpy(remote.sun_path, CONTROL_PATH, sizeof(CONTROL_PATH));
    int count = -1;
    long long start = now_ms();
    if (start >= 0 && length > 0 && (size_t)length < sizeof(local.sun_path) - 1 &&
        bind(fd, (struct sockaddr *)&local, (socklen_t)(offsetof(struct sockaddr_un, sun_path) + 1 + length)) == 0 &&
        connect(fd, (struct sockaddr *)&remote, sizeof(remote)) == 0)
        count = station_count(fd, start + 1000);
    close(fd);
    if (count < 0)
        return 1;
    printf("%d\n", count);
    return 0;
}
