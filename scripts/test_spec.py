import struct
import os
import uuid

def test_vhd():
    footer = bytearray(512)
    footer[0:8] = b'conectix'
    struct.pack_into('>I', footer, 8, 2)
    struct.pack_into('>I', footer, 12, 0x00010000)
    struct.pack_into('>Q', footer, 16, 0xFFFFFFFFFFFFFFFF)
    struct.pack_into('>I', footer, 24, 0x2DEB0000)
    footer[28:32] = b'vbox'
    struct.pack_into('>I', footer, 32, 0x00070000)
    footer[36:40] = b'Wi2k'
    total_bytes = 10 * 1024 * 1024
    struct.pack_into('>Q', footer, 40, total_bytes)
    struct.pack_into('>Q', footer, 48, total_bytes)
    struct.pack_into('>H', footer, 56, 20)
    footer[58] = 16
    footer[59] = 63
    struct.pack_into('>I', footer, 60, 2)
    footer[68:84] = uuid.uuid4().bytes
    chk = sum(footer[:64]) + sum(footer[68:])
    checksum = (~chk) & 0xFFFFFFFF
    struct.pack_into('>I', footer, 64, checksum)
    
    # Verify checksum
    # In VHD spec, sum of all bytes in footer including checksum field (as big endian int or byte sum)
    # Actually VHD spec: "The checksum is calculated by summing all bytes in the footer except for the checksum field, then taking the one's complement of that sum."
    print("VHD footer generated, size =", len(footer))

test_vhd()
