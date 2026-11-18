/* USB device reset for the ipTIME A3000mini on the Gen5W head unit. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <linux/usbdevice_fs.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <unistd.h>

static int number(const char *path, int base)
{
    FILE *file = fopen(path, "r");
    if (!file)
        return -1;
    char text[32];
    int ok = fgets(text, sizeof(text), file) != NULL;
    fclose(file);
    if (!ok)
        return -1;
    char *end;
    long value = strtol(text, &end, base);
    if (end == text || value < 0 || value > INT_MAX ||
        end[strspn(end, " \t\n\r")])
        return -1;
    return (int)value;
}

static int eligible(const char *interface)
{
    char path[96];
    const char *attributes[] = {
        "bInterfaceClass", "bInterfaceSubClass", "bInterfaceProtocol",
    };
    if (number("idVendor", 16) != 0x0bda || number("idProduct", 16) != 0xb812 ||
        number("authorized", 10) != 1 || number("bConfigurationValue", 10) != 1 ||
        number("bNumInterfaces", 10) != 1)
        return 0;
    for (size_t i = 0; i < sizeof(attributes) / sizeof(attributes[0]); ++i) {
        snprintf(path, sizeof(path), "%s/%s", interface, attributes[i]);
        if (number(path, 16) != 0xff)
            return 0;
    }
    snprintf(path, sizeof(path), "%s/driver", interface);
    struct stat entry;
    return lstat(path, &entry) == -1 && errno == ENOENT;
}

int main(int argc, char **argv)
{
    const char prefix[] = "/sys/bus/usb/devices/";
    if (argc != 2 || strncmp(argv[1], prefix, sizeof(prefix) - 1))
        return 2;
    const char *port = argv[1] + sizeof(prefix) - 1;
    size_t len = strlen(port);
    if (!len || len > 48 || strspn(port, "0123456789-.") != len ||
        port[0] < '0' || port[0] > '9')
        return 2;

    /* A cwd reference pins this specific sysfs device if the port is reused. */
    if (chdir(argv[1])) {
        perror("USB reset: open sysfs device");
        return 1;
    }
    char interface[56];
    snprintf(interface, sizeof(interface), "%s:1.0", port);
    int bus = number("busnum", 10);
    int device = number("devnum", 10);
    if (bus < 1 || bus > 255 || device < 2 || device > 127 || !eligible(interface)) {
        fputs("USB reset: expected an authorized, unbound A3000mini\n", stderr);
        return 2;
    }
    char node[40];
    snprintf(node, sizeof(node), "/dev/bus/usb/%03d/%03d", bus, device);
    int fd = open(node, O_RDWR | O_CLOEXEC);
    if (fd < 0) {
        perror("USB reset: open USB device");
        return 1;
    }
    unsigned char descriptor[18];
    ssize_t got = read(fd, descriptor, sizeof(descriptor));
    if (got != (ssize_t)sizeof(descriptor) || descriptor[0] != 18 || descriptor[1] != 1 ||
        descriptor[8] != 0xda || descriptor[9] != 0x0b ||
        descriptor[10] != 0x12 || descriptor[11] != 0xb8 ||
        number("busnum", 10) != bus || number("devnum", 10) != device || !eligible(interface)) {
        fputs("USB reset: device identity or binding changed\n", stderr);
        close(fd);
        return 2;
    }
    if (ioctl(fd, USBDEVFS_RESET, 0) < 0) {
        perror("USB reset: USBDEVFS_RESET");
        close(fd);
        return 1;
    }
    close(fd);
    printf("USB reset completed for A3000mini on %s\n", port);
    return 0;
}
