"""Exercise the EHCI port handoff against isolated Linux sysfs fixtures."""
from pathlib import Path
import shutil
import subprocess
import tempfile


def write(directory, **values):
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in values.items():
        (directory / name).write_text(f"{value}\n")


with tempfile.TemporaryDirectory() as temporary:
    work = Path(temporary)
    devices = work / "devices"
    devices.mkdir()
    drivers = work / "drivers"
    for name in ("ohci-platform", "ehci-platform", "tcc-ehci", "rtl88x2bu", "other"):
        (drivers / name).mkdir(parents=True)
    for controller, bus, product in (("ohci-platform", 3, "0001"),
                                      ("ehci-platform", 4, "0002"),
                                      ("tcc-ehci", 1, "0002")):
        parent = work / controller
        root = parent / f"usb{bus}"
        write(root, idVendor="1d6b", idProduct=product, maxchild=1, busnum=bus)
        (parent / "driver").symlink_to(drivers / controller)
        (parent / "companion").write_text("untouched")
        (devices / root.name).symlink_to(root)
    dongle = work / "ohci-platform/usb3/3-1"
    write(dongle, idVendor="0bda", idProduct="b812", authorized=1,
          bConfigurationValue=1, bNumInterfaces=1, devnum=2, busnum=3, speed=12)
    interface = dongle / "3-1:1.0"
    write(interface, bInterfaceClass="ff", bInterfaceSubClass="ff", bInterfaceProtocol="ff")
    (interface / "driver").symlink_to(drivers / "rtl88x2bu")
    (devices / "3-1").symlink_to(dongle)
    flags = work / "flags"
    flags.write_text("0x0\n")
    binary = work / "usb-reset"
    subprocess.run([
        "cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-Os",
        f'-DUSB_SYSFS="{devices}"', f'-DUSB_NET_FLAGS="{flags}"',
        "driver-source/usb_reset_a3000mini.c", "-o", str(binary),
    ], check=True)
    control = work / "ehci-platform/companion"

    def invoke(success=False, port="3-1"):
        control.write_text("untouched")
        result = subprocess.run([str(binary), "--high-speed", str(devices / port)],
                                capture_output=True, text=True)
        assert (result.returncode == 0) == success, result
        assert control.read_text().startswith("-1\n") == success
        assert (work / "tcc-ehci/companion").read_text() == "untouched"
        return result

    invoke(success=True)
    (interface / "driver").unlink()
    invoke(success=True)  # Recovery can precede initial module binding.
    (interface / "driver").symlink_to(drivers / "other")
    invoke()
    (interface / "driver").unlink()
    (interface / "driver").symlink_to(drivers / "rtl88x2bu")
    for attribute, value, original in (("idProduct", "1234", "b812"),
                                        ("authorized", "0", "1"),
                                        ("speed", "480", "12"),
                                        ("bNumInterfaces", "2", "1")):
        (dongle / attribute).write_text(value + "\n")
        invoke()
        (dongle / attribute).write_text(original + "\n")
    flags.write_text("0x1\n")
    invoke()
    flags.write_text("0x0\n")
    (interface / "bInterfaceClass").write_text("08\n")
    invoke()
    (interface / "bInterfaceClass").write_text("ff\n")
    busy = work / "ehci-platform/usb4/4-1"
    write(busy, idVendor="0781", idProduct="5567")
    invoke()
    shutil.rmtree(busy)
    extra = work / "other-ehci/usb5"
    write(extra, idVendor="1d6b", idProduct="0002", maxchild=1, busnum=5)
    (extra.parent / "driver").symlink_to(drivers / "ehci-platform")
    (extra.parent / "companion").write_text("untouched")
    (devices / "usb5").symlink_to(extra)
    invoke()
    (devices / "usb5").unlink()
    (devices / "3-1.2").symlink_to(dongle)
    invoke(port="3-1.2")
    (work / "ehci-platform/driver").unlink()
    invoke()
    for arguments in ([], ["--high-speed"], ["--unknown", str(devices / "3-1")],
                      ["--high-speed", "/unrelated/3-1"]):
        result = subprocess.run([str(binary), *arguments], capture_output=True)
        assert result.returncode != 0

print("Verified EHCI handoff, device identity, direct-port topology, driver ownership, "
      "interface state, unrelated devices/controllers, and ambiguous roots.")
