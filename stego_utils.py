"""
Steganography Utilities - Phase E: Cryptographic Deal Tracking
AES-128 Encryption + LSB (Least Significant Bit) Encoding
"""
import base64
import os
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Load encryption keys from environment or use defaults (16 bytes each)
SECRET_KEY = os.getenv("ENCRYPTION_KEY", "16ByteSecretKey!").encode()[:16]
IV = os.getenv("ENCRYPTION_IV", "16ByteInitVector").encode()[:16]


def encrypt_payload(data: str) -> str:
    """
    Encrypts the string using AES-128 (CBC mode) and returns base64.
    
    Args:
        data: Plaintext string to encrypt
        
    Returns:
        Base64 encoded encrypted ciphertext
    """
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
    return base64.b64encode(ct_bytes).decode('utf-8')


def decrypt_payload(b64_data: str) -> str:
    """
    Decrypts the base64 string back to plaintext.
    
    Args:
        b64_data: Base64 encoded encrypted data
        
    Returns:
        Decrypted plaintext or error message
    """
    try:
        ct_bytes = base64.b64decode(b64_data)
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
        pt = unpad(cipher.decrypt(ct_bytes), AES.block_size)
        return pt.decode('utf-8')
    except Exception as e:
        return f"Decryption Failed or No Payload Found: {str(e)}"


def hide_data(image_path: str, payload_text: str):
    """
    Encrypts text and hides it in the Least Significant Bits of an image.
    
    Args:
        image_path: Path to the image file (PNG recommended)
        payload_text: Text to encrypt and hide
    """
    # Encrypt the payload
    encrypted_b64 = encrypt_payload(payload_text)
    
    # Convert to binary and add unique 16-bit delimiter
    binary_data = ''.join(format(ord(i), '08b') for i in encrypted_b64) + '1111111111111110'
    
    # Open image and convert to RGB
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    
    data_index = 0
    data_len = len(binary_data)
    
    # Embed data in LSB of Red channel
    for y in range(img.height):
        for x in range(img.width):
            if data_index < data_len:
                r, g, b = pixels[x, y]
                # Modify the Least Significant Bit of the Red channel
                r = (r & ~1) | int(binary_data[data_index])
                pixels[x, y] = (r, g, b)
                data_index += 1
            else:
                break
        if data_index >= data_len:
            break
    
    # Save as PNG (lossless format required for steganography)
    img.save(image_path, format="PNG")


def extract_data(image_path: str) -> str:
    """
    Extracts binary from the LSBs, stops at the delimiter, and decrypts it.
    
    Args:
        image_path: Path to the image with hidden data
        
    Returns:
        Decrypted payload text or error message
    """
    try:
        # Open image
        img = Image.open(image_path).convert('RGB')
        pixels = img.load()
        
        binary_data = ""
        
        # Extract LSB from Red channel
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]
                binary_data += str(r & 1)
        
        # Split by 16-bit delimiter
        delimiter = '1111111111111110'
        extracted_bin = binary_data.split(delimiter)[0]
        
        # Convert binary chunks back to characters
        chars = []
        for i in range(0, len(extracted_bin), 8):
            byte = extracted_bin[i:i+8]
            if len(byte) == 8:
                chars.append(chr(int(byte, 2)))
        
        extracted_b64 = ''.join(chars)
        
        # Decrypt and return
        return decrypt_payload(extracted_b64)
    
    except Exception as e:
        return f"Extraction Failed: {str(e)}"
