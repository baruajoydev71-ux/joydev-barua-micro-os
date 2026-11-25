import struct

with open(r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\micro-os.iso", "rb") as f:
    data = f.read()

print("Total size:", len(data))
# Check Sector 18 (Boot Catalog)
cat = data[18*2048 : 19*2048]
print("Cat Header:", hex(cat[0]), hex(cat[1]))
print("Cat Key:", hex(cat[30]), hex(cat[31]))
print("Bootable:", hex(cat[32]))
print("Media type:", hex(cat[33]))
load_seg = struct.unpack("<H", cat[34:36])[0]
print("Load seg:", hex(load_seg))
print("Sector count:", struct.unpack("<H", cat[38:40])[0])
print("Load RBA:", struct.unpack("<I", cat[40:44])[0])

# Check Sector 20 (Boot Image)
boot_img = data[20*2048 : 22*2048]
print("Boot img len:", len(boot_img))
print("MBR signature:", hex(boot_img[510]), hex(boot_img[511]))
print("At 512 (0x7E00):", hex(boot_img[512]), hex(boot_img[513]), hex(boot_img[514]))
