// SPDX-License-Identifier: AGPL-3.0-only
// Name-table test adapted from CN7PE-260902-A3000MINI-All-in-One-1.0.0.
package hmgapi.mods.cn7npecarrier;

import hmgapi.engine.MemRecipe;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;

public final class CarrierTest {
    private static final int TABLE = 0x8a2b8;
    private static final int SLOT = 0x8a2c8;

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static byte[] slot(String name) {
        return Arrays.copyOf(name.getBytes(StandardCharsets.US_ASCII), 8);
    }

    private static final class Memory implements MemRecipe.Memory {
        private final byte[] bytes = new byte[TABLE + 32];
        private int writes;

        Memory(String wifiName) {
            String[] names = {"rndis0", "ncm0", wifiName, "tether"};
            for (int index = 0; index < names.length; index++) {
                System.arraycopy(slot(names[index]), 0, bytes, TABLE + 8 * index, 8);
            }
        }

        @Override public byte[] peek(long addr, int len) {
            return Arrays.copyOfRange(bytes, (int) addr, (int) addr + len);
        }

        @Override public boolean poke(long addr, byte[] data) {
            check(addr == SLOT && data.length == 8, "Write outside the Wi-Fi slot");
            System.arraycopy(data, 0, bytes, (int) addr, data.length);
            writes++;
            return true;
        }

        @Override public long mapCode(long hint, int length) {
            throw new AssertionError("The name-table patch must not allocate executable code");
        }
    }

    public static void main(String[] args) throws Exception {
        check(UsbWifiCarrier.target("CN7NPE.KOR.0000.V039.001.260902", "tcc803x"), "Target rejected");
        check(UsbWifiCarrier.target("CN7NPE.KOR.S5W_M.V039.001.260902", "tcc803x"), "Display build rejected");
        check(!UsbWifiCarrier.target("CN7PE.KOR.0000.V039.001.260902", "tcc803x"), "CN7 PE accepted");
        check(!UsbWifiCarrier.target("CN7NPE.KOR.0000.V039.001.250902", "tcc803x"), "Older build accepted");
        check(!UsbWifiCarrier.target("CN7NPE.KOR.0000.V039.001.260902", "other"), "Wrong platform accepted");
        check(UsbWifiCarrier.supportsFingerprint("cf3cc23dad25b181a9fc12d606468715"), "Known stock hash rejected");
        check(!UsbWifiCarrier.supportsFingerprint("900150983cd24fb0d6963f7d28e17f72"), "Unknown hash accepted");
        Path root = Paths.get(args[1]);
        Path device = Files.createDirectory(root.resolve("device"));
        Path product = device.resolve("idProduct");
        Files.write(device.resolve("idVendor"), "0bda\n".getBytes(StandardCharsets.US_ASCII));
        Files.write(product, "abcd\n".getBytes(StandardCharsets.US_ASCII));
        check(!UsbWifiCarrier.hasA3000Mini(root.toFile()), "Foreign USB device accepted");
        Files.write(product, "b812\n".getBytes(StandardCharsets.US_ASCII));
        check(UsbWifiCarrier.hasA3000Mini(root.toFile()), "Target USB not detected");

        Path file = root.resolve("fixture");
        Files.write(file, "abc".getBytes(StandardCharsets.US_ASCII));
        check(UsbWifiCarrier.md5(file.toFile()).equals("900150983cd24fb0d6963f7d28e17f72"), "Wrong file MD5");
        MemRecipe recipe = MemRecipe.parse(new String(Files.readAllBytes(Paths.get(args[0])), StandardCharsets.UTF_8));
        Memory stock = new Memory("wlan0");
        check(recipe.apply(stock, 0, stock.bytes.length, null).ok(), "Stock slot rejected");
        check(Arrays.equals(stock.peek(TABLE, 32), new Memory("rtwlan0").peek(TABLE, 32)), "Unexpected table changes");
        check(recipe.apply(stock, 0, stock.bytes.length, null).ok() && stock.writes == 1, "Reapply wrote twice");
        Memory wrong = new Memory("eth0");
        check(!recipe.apply(wrong, 0, wrong.bytes.length, null).ok() && wrong.writes == 0,
                "Mismatched slot was written");
        Memory shortMapping = new Memory("wlan0");
        check(!recipe.apply(shortMapping, 0, SLOT, null).ok() && shortMapping.writes == 0,
                "Unmapped bytes were written");
        System.out.println("CN7NPE product, USB, MD5 and memory recipe checks passed");
    }
}
