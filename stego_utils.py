import base64
import os
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

SECRET_KEY = os.getenv("ENCRYPTION_KEY", "16ByteSecretKey!").encode()[:16]
IV = os.getenv("ENCRYPTION_IV", "16ByteInitVector").encode()[:16]


# AES-128-CBC encryption with PKCS7 padding
def encrypt_payload(data: str) -> str:
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
    return base64.b64encode(ct_bytes).decode('utf-8')


def decrypt_payload(b64_data: str) -> str:
    try:
        ct_bytes = base64.b64decode(b64_data)
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
        pt = unpad(cipher.decrypt(ct_bytes), AES.block_size)
        return pt.decode('utf-8')
    except Exception as e:
        return f"Decryption Failed or No Payload Found: {str(e)}"


# Embed encrypted payload in LSB (Least Significant Bit) of Red channel
def hide_data(image_path: str, payload_text: str):
    encrypted_b64 = encrypt_payload(payload_text)
    
    # Convert to binary + 16-bit delimiter for extraction boundary
    binary_data = ''.join(format(ord(i), '08b') for i in encrypted_b64) + '1111111111111110'
    
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    
    data_index = 0
    data_len = len(binary_data)
    
    for y in range(img.height):
        for x in range(img.width):
            if data_index < data_len:
                r, g, b = pixels[x, y]
                r = (r & ~1) | int(binary_data[data_index])
                pixels[x, y] = (r, g, b)
                data_index += 1
            else:
                break
        if data_index >= data_len:
            break
    
    img.save(image_path, format="PNG")


# Extract hidden data from LSB of Red channel, decrypt via AES-128
def extract_data(image_path: str) -> str:
    try:
        img = Image.open(image_path).convert('RGB')
        pixels = img.load()
        
        binary_data = ""
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]
                binary_data += str(r & 1)
        
        delimiter = '1111111111111110'
        extracted_bin = binary_data.split(delimiter)[0]
        
        chars = []
        for i in range(0, len(extracted_bin), 8):
            byte = extracted_bin[i:i+8]
            if len(byte) == 8:
                chars.append(chr(int(byte, 2)))
        
        extracted_b64 = ''.join(chars)
        
        return decrypt_payload(extracted_b64)
    
    except Exception as e:
        return f"Extraction Failed: {str(e)}"
