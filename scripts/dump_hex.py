with open(r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\micro-os.iso", "rb") as f:
    data = f.read()

mbr = data[20*2048 : 20*2048 + 512]
kernel = data[20*2048 + 512 : 20*2048 + 1024]

print("MBR bytes 0..64:")
print(" ".join(f"{b:02X}" for b in mbr[:64]))

print("Kernel bytes 0..64:")
print(" ".join(f"{b:02X}" for b in kernel[:64]))
