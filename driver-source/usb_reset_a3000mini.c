/* USB device reset for the ipTIME A3000mini on the Gen5W head unit. */
#define _GNU_SOURCE
#include <errno.h>
#include <dirent.h>
#include <fcntl.h>
#include <limits.h>
#include <linux/usbdevice_fs.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#ifndef USB_SYSFS
#define USB_SYSFS "/sys/bus/usb/devices"
#endif
#ifndef USB_NET_FLAGS
#define USB_NET_FLAGS "/sys/class/net/rtwlan0/flags"
#endif

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

static int identity(void)
{
    return number("idVendor", 16) == 0x0bda && number("idProduct", 16) == 0xb812 &&
           number("authorized", 10) == 1 && number("bConfigurationValue", 10) == 1 &&
           number("bNumInterfaces", 10) == 1;
}

static int vendor_interface(const char *interface)
{
    char path[96];
    const char *attributes[] = {
        "bInterfaceClass", "bInterfaceSubClass", "bInterfaceProtocol",
    };
    for (size_t i = 0; i < sizeof(attributes) / sizeof(attributes[0]); ++i) {
        snprintf(path, sizeof(path), "%s/%s", interface, attributes[i]);
        if (number(path, 16) != 0xff)
            return 0;
    }
    return 1;
}

static int eligible(const char *interface)
{
    char path[96];
    if (!identity() || !vendor_interface(interface))
        return 0;
    snprintf(path, sizeof(path), "%s/driver", interface);
    struct stat entry;
    return lstat(path, &entry) == -1 && errno == ENOENT;
}

static int path_join(char *out, size_t size, const char *base, const char *tail)
{
    int length = snprintf(out, size, "%s/%s", base, tail);
    return length >= 0 && (size_t)length < size;
}

static int driver_is(const char *path, const char *name)
{
    char resolved[PATH_MAX];
    if (!realpath(path, resolved))
        return 0;
    const char *base = strrchr(resolved, '/');
    return base && strcmp(base + 1, name) == 0;
}

static int root_attribute(const char *root, const char *name, int base)
{
    char path[PATH_MAX];
    if (!path_join(path, sizeof(path), root, name))
        return -1;
    return number(path, base);
}

static int root_empty(const char *root)
{
    DIR *directory = opendir(root);
    if (!directory)
        return 0;
    struct dirent *entry;
    int empty = 1;
    while ((entry = readdir(directory))) {
        if (entry->d_name[0] == '.')
            continue;
        char child[PATH_MAX];
        if (!path_join(child, sizeof(child), root, entry->d_name) ||
            root_attribute(child, "idVendor", 16) >= 0) {
            empty = 0;
            break;
        }
    }
    closedir(directory);
    return empty;
}

/* Linux 3.18 ehci-sysfs.c accepts -port to return ownership to EHCI. */
static int reclaim_high_speed(const char *port)
{
    char root[PATH_MAX], path[PATH_MAX], companion[PATH_MAX] = "";
    const char *dash = strrchr(port, '-');
    int devnum = number("devnum", 10);
    if (!dash || strcmp(dash, "-1") || strspn(port, "0123456789-") != strlen(port) ||
        !identity() || number("speed", 10) != 12 || devnum < 2 || devnum > 127 ||
        !realpath("..", root) || root_attribute(root, "maxchild", 10) != 1 ||
        root_attribute(root, "busnum", 10) != number("busnum", 10) ||
        !path_join(path, sizeof(path), root, "../driver") ||
        !driver_is(path, "ohci-platform")) {
        fputs("USB high-speed: expected a direct A3000mini on a single-port OHCI root\n", stderr);
        return 2;
    }
    int flags = number(USB_NET_FLAGS, 0);
    if (flags >= 0 && (flags & 1)) {
        fputs("USB high-speed: interface is already UP\n", stderr);
        return 2;
    }
    char interface[56];
    int length = snprintf(interface, sizeof(interface), "%s:1.0", port);
    if (length < 0 || (size_t)length >= sizeof(interface) || !vendor_interface(interface))
        return 2;
    length = snprintf(path, sizeof(path), "%s/driver", interface);
    if (length < 0 || (size_t)length >= sizeof(path))
        return 2;
    struct stat state;
    if (lstat(path, &state) == 0) {
        if (!driver_is(path, "rtl88x2bu"))
            return 2;
    } else if (errno != ENOENT) {
        return 2;
    }

    DIR *devices = opendir(USB_SYSFS);
    if (!devices)
        return 1;
    struct dirent *entry;
    int candidates = 0;
    while ((entry = readdir(devices))) {
        if (strncmp(entry->d_name, "usb", 3) || !entry->d_name[3] ||
            strspn(entry->d_name + 3, "0123456789") != strlen(entry->d_name + 3))
            continue;
        if (!path_join(root, sizeof(root), USB_SYSFS, entry->d_name) ||
            root_attribute(root, "idVendor", 16) != 0x1d6b ||
            root_attribute(root, "idProduct", 16) != 2 ||
            root_attribute(root, "maxchild", 10) != 1 ||
            !path_join(path, sizeof(path), root, "../driver") ||
            !driver_is(path, "ehci-platform"))
            continue;
        candidates++;
        if (!root_empty(root) || !path_join(companion, sizeof(companion), root, "../companion")) {
            companion[0] = '\0';
            break;
        }
    }
    closedir(devices);
    if (candidates != 1 || !companion[0] || !identity() || number("devnum", 10) != devnum ||
        number("speed", 10) != 12) {
        fputs("USB high-speed: a unique unused EHCI platform port was not identified\n", stderr);
        return 2;
    }
    int fd = open(companion, O_WRONLY | O_CLOEXEC);
    if (fd < 0) {
        perror("USB high-speed: open companion control");
        return 1;
    }
    ssize_t written = write(fd, "-1\n", 3);
    int result = written == 3 ? 0 : 1;
    if (result)
        perror("USB high-speed: return port 1 to EHCI");
    close(fd);
    if (!result)
        printf("USB high-speed: requested EHCI ownership for port 1 (A3000mini %s)\n", port);
    return result;
}

struct host_control {
    char device[PATH_MAX], driver[PATH_MAX], name[96];
    int bind_fd, unbind_fd, restore;
};

static volatile sig_atomic_t host_interrupted;
static void host_signal(int signal_number) { host_interrupted = signal_number; }

static int host_interface_idle(void)
{
    int flags = number(USB_NET_FLAGS, 0);
    if (flags >= 0) return !(flags & 1);
    struct stat state;
    return lstat(USB_NET_FLAGS, &state) < 0 && errno == ENOENT;
}

static void host_pause(unsigned milliseconds)
{
#ifndef USB_HOST_TEST_NO_DELAY
    struct timespec delay = {milliseconds / 1000, (long)(milliseconds % 1000) * 1000000};
    while (!host_interrupted && nanosleep(&delay, &delay) && errno == EINTR) {}
#else
    (void)milliseconds;
#endif
}

static int root_has_only_target(const char *root)
{
    char current[PATH_MAX], child[PATH_MAX], resolved[PATH_MAX];
    if (!getcwd(current, sizeof(current))) return 0;
    DIR *dir = opendir(root);
    if (!dir) return 0;
    struct dirent *entry;
    int count = 0, valid = 1;
    while ((entry = readdir(dir))) {
        if (entry->d_name[0] == '.') continue;
        if (!path_join(child, sizeof(child), root, entry->d_name)) { valid = 0; break; }
        if (root_attribute(child, "idVendor", 16) < 0) continue;
        if (!realpath(child, resolved) || strcmp(current, resolved)) { valid = 0; break; }
        count++;
    }
    closedir(dir);
    return valid && count == 1;
}

static int open_host_control(const char *root, const char *driver, int product,
                             struct host_control *host)
{
    char path[PATH_MAX];
    if (root_attribute(root, "idVendor", 16) != 0x1d6b ||
        root_attribute(root, "idProduct", 16) != product ||
        root_attribute(root, "devnum", 10) != 1 ||
        root_attribute(root, "maxchild", 10) != 1 ||
        !path_join(path, sizeof(path), root, "../driver") || !driver_is(path, driver) ||
        !realpath(path, host->driver) ||
        !path_join(path, sizeof(path), root, "..") || !realpath(path, host->device)) return 0;
    const char *name = strrchr(host->device, '/');
    if (!name || !name[1] || strlen(++name) >= sizeof(host->name) ||
        strspn(name, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-") != strlen(name)) return 0;
    strcpy(host->name, name);
    if (!path_join(path, sizeof(path), host->driver, "bind")) return 0;
    host->bind_fd = open(path, O_WRONLY | O_CLOEXEC);
    if (host->bind_fd < 0) perror("USB cold recovery: open external bind control");
    if (!path_join(path, sizeof(path), host->driver, "unbind")) return 0;
    host->unbind_fd = open(path, O_WRONLY | O_CLOEXEC);
    if (host->unbind_fd < 0) perror("USB cold recovery: open external unbind control");
    return host->bind_fd >= 0 && host->unbind_fd >= 0;
}

static int host_write(int fd, const char *name)
{
    char value[100];
    int length = snprintf(value, sizeof(value), "%s\n", name);
    if (length <= 0 || (size_t)length >= sizeof(value)) return 0;
    if (lseek(fd, 0, SEEK_SET) < 0 && errno != ESPIPE) return 0;
    ssize_t result;
    do { result = write(fd, value, (size_t)length); } while (result < 0 && errno == EINTR);
    return result == length;
}

static int host_restore(struct host_control *host, const char *label)
{
    if (!host->restore) return 1;
    int ok = host_write(host->bind_fd, host->name);
    /* If another kernel path already rebound it, preserve that valid binding. */
    if (!ok) {
        char path[PATH_MAX];
        ok = path_join(path, sizeof(path), host->device, "driver") && driver_is(path, label);
    }
    printf("USB cold recovery: restore %s device=%s result=%d\n", label, host->name, ok);
    if (ok) host->restore = 0;
    return ok;
}

/* Reprobe only the unique external single-port platform pair, EHCI first.
 * Internal tcc-ehci, occupied roots, hubs and UP interfaces never qualify.
 * Driver remove/probe may reset the PHY; a physical VBUS power cut is not assumed. */
static int restart_external_hosts(const char *port)
{
    char ohci_root[PATH_MAX], ehci_root[PATH_MAX] = "", path[PATH_MAX];
    struct host_control ohci = {.bind_fd = -1, .unbind_fd = -1};
    struct host_control ehci = {.bind_fd = -1, .unbind_fd = -1};
    int result = 2, candidates = 0, ohci_count = 0;
    int devnum = number("devnum", 10);
    const char *dash = strrchr(port, '-');
    char interface[64];
    struct stat entry;
    if (!dash || strcmp(dash, "-1") || strspn(port, "0123456789-") != strlen(port) ||
        !identity() || number("speed", 10) != 12 || devnum < 2 || devnum > 127 ||
        !realpath("..", ohci_root) || !root_has_only_target(ohci_root) ||
        root_attribute(ohci_root, "busnum", 10) != number("busnum", 10) ||
        !host_interface_idle()) goto done;
    int length = snprintf(interface, sizeof(interface), "%s:1.0", port);
    if (length <= 0 || (size_t)length >= sizeof(interface) || !vendor_interface(interface) ||
        !path_join(path, sizeof(path), interface, "driver")) goto done;
    if (lstat(path, &entry) == 0) { if (!driver_is(path, "rtl88x2bu")) goto done; }
    else if (errno != ENOENT) goto done;

    DIR *devices = opendir(USB_SYSFS);
    if (!devices) goto done;
    struct dirent *item;
    while ((item = readdir(devices))) {
        char root[PATH_MAX], link[PATH_MAX];
        if (strncmp(item->d_name, "usb", 3) || !item->d_name[3] ||
            strspn(item->d_name + 3, "0123456789") != strlen(item->d_name + 3) ||
            !path_join(root, sizeof(root), USB_SYSFS, item->d_name) ||
            !path_join(link, sizeof(link), root, "../driver")) continue;
        if (driver_is(link, "ohci-platform")) ohci_count++;
        if (!driver_is(link, "ehci-platform")) continue;
        candidates++;
        if (root_empty(root) && realpath(root, ehci_root)) continue;
        ehci_root[0] = 0;
        break;
    }
    closedir(devices);
    if (candidates != 1 || ohci_count != 1 || !ehci_root[0] ||
        !open_host_control(ohci_root, "ohci-platform", 1, &ohci) ||
        !open_host_control(ehci_root, "ehci-platform", 2, &ehci) ||
        !strcmp(ohci.device, ehci.device) || !identity() || number("devnum", 10) != devnum ||
        number("speed", 10) != 12 || !root_has_only_target(ohci_root) || !root_empty(ehci_root)) goto done;
    if (!host_interface_idle()) goto done;

    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_handler = host_signal;
    sigemptyset(&action.sa_mask);
    host_interrupted = 0;
    if (sigaction(SIGTERM, &action, NULL) || sigaction(SIGINT, &action, NULL) ||
        sigaction(SIGHUP, &action, NULL)) goto done;
    if (host_interrupted) goto done;
    result = 1;
    printf("USB cold recovery: validated OHCI=%s EHCI=%s port=1\n", ohci.name, ehci.name);
    fflush(stdout);
    ohci.restore = 1;
    if (!host_write(ohci.unbind_fd, ohci.name)) goto restore;
    puts("USB cold recovery: external OHCI unbound");
    if (host_interrupted) goto restore;
    ehci.restore = 1;
    if (!host_write(ehci.unbind_fd, ehci.name)) goto restore;
    puts("USB cold recovery: external EHCI unbound; pause_ms=1500");
    host_pause(1500);
    if (host_interrupted) goto restore;
    if (!host_restore(&ehci, "ehci-platform")) goto restore;
    puts("USB cold recovery: EHCI first; pause_ms=1000");
    host_pause(1000);
    if (!host_interrupted && host_restore(&ohci, "ohci-platform")) result = 0;
restore:
    /* Always attempt both restorations, even when one fails or a signal arrives. */
    { int a = host_restore(&ehci, "ehci-platform");
      int b = host_restore(&ohci, "ohci-platform");
      if (!a || !b || host_interrupted) result = 1; }
done:
    if (ohci.bind_fd >= 0) close(ohci.bind_fd);
    if (ohci.unbind_fd >= 0) close(ohci.unbind_fd);
    if (ehci.bind_fd >= 0) close(ehci.bind_fd);
    if (ehci.unbind_fd >= 0) close(ehci.unbind_fd);
    if (result == 2) puts("USB cold recovery: refused by topology, device, interface or control-endpoint checks");
    printf("USB cold recovery: request_exit=%d (actual USB speed must be verified)\n", result);
    return result;
}

int main(int argc, char **argv)
{
    const char prefix[] = USB_SYSFS "/";
    int high_speed = argc == 3 && strcmp(argv[1], "--high-speed") == 0;
    int restart_hosts = argc == 3 && strcmp(argv[1], "--restart-hosts") == 0;
    if (argc != 2 && !high_speed && !restart_hosts)
        return 2;
    const char *device_path = (high_speed || restart_hosts) ? argv[2] : argv[1];
    if (strncmp(device_path, prefix, sizeof(prefix) - 1))
        return 2;
    const char *port = device_path + sizeof(prefix) - 1;
    size_t len = strlen(port);
    if (!len || len > 48 || strspn(port, "0123456789-.") != len ||
        port[0] < '0' || port[0] > '9')
        return 2;

    /* A cwd reference pins this specific sysfs device if the port is reused. */
    if (chdir(device_path)) {
        perror("USB reset: open sysfs device");
        return 1;
    }
    if (high_speed)
        return reclaim_high_speed(port);
    if (restart_hosts)
        return restart_external_hosts(port);
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
