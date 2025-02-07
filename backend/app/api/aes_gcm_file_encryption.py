import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import logging
import hmac
from hashlib import sha256

logger = logging.getLogger("uvicorn")

def generate_aes_gcm_key() -> bytes:
    """
    Generates a new 128 bits AES-GCM key.
    """
    return AESGCM.generate_key(bit_length=128)

def encrypt_file_aes_gcm(input_file_path: str, output_file_path: str, encryption_key: str) -> None:
    """
    Encrypts a file using AES-GCM.
    """
    try:
        if not os.path.exists(input_file_path):
            raise FileNotFoundError(f"Input file {input_file_path} does not exist")
        
        if os.path.exists(output_file_path):
            raise FileExistsError(f"Output file {output_file_path} already exists")
        
        # Initialize AES-GCM
        aesgcm = AESGCM(encryption_key)
        
        # Open the input file for reading in binary mode and output file for writing in binary mode
        with open(input_file_path, 'rb') as infile, open(output_file_path, 'wb') as outfile:
            # Read the file in chunks to avoid loading the entire file into memory
            while True:
                # Generate a unique nonce for each chunk
                nonce = os.urandom(12)

                chunk = infile.read(8192)  # Read 8KB at a time, adjust as needed for performance vs memory use
                if not chunk:
                    break
                # Encrypt each chunk and write it to the output file
                ciphertext = aesgcm.encrypt(nonce, chunk, None)
                # Write the nonce to the beginning of the chunk
                outfile.write(nonce)
                # A chunk of size 8208 is written to the output file: 8192 data + 16 GCM tag
                outfile.write(ciphertext)

        # Try to decrypt the file to test if the encryption is valid # TODO Make more efficient
        decrypt_file_aes_gcm(output_file_path, output_file_path + ".test-decryption", encryption_key)
        # If the decryption is successful, delete the test decrypted file
        os.remove(output_file_path + ".test-decryption")

    except Exception as e:
        logger.error(f"Error encrypting file: {e}")
        raise e

def decrypt_file_aes_gcm(input_file_path: str, output_file_path: str, encryption_key: str) -> None:
    """
    Decrypts a file using AES-GCM.
    """
    try:
        # Open the encrypted file
        with open(input_file_path, 'rb') as infile, open(output_file_path, 'wb') as outfile:

                
            # Initialize AES-GCM
            aesgcm = AESGCM(encryption_key)
            
            # Read the file in chunks
            while True:
                # Read the nonce from the beginning of the chunk
                nonce = infile.read(12)

                chunk = infile.read(8192 + 16)  # 8192 data + 16 GCM tag
                if len(chunk) == 0:
                    break
                # Decrypt each chunk and write it to the output file
                plaintext = aesgcm.decrypt(nonce, chunk, None)
                outfile.write(plaintext)
            # Set the decrypted file to be readable and writable by the user
            os.chmod(output_file_path, 0o600)

    except Exception as e:
        if "HMAC tag verification failed" in str(e):
            logger.error(f"Error decrypting file, the key is invalid: {e}")
            raise Exception("Invalid key")
        else:
            logger.error(f"Unexpected error decrypting file: {e}")
            raise e

# Example usage:
#if __name__ == "__main__":
#    key = AESGCM.generate_key(bit_length=256)  # Use 256-bit key for AES-GCM

#    # Encrypt
#    encrypt_file('largefile.txt', 'largefile_encrypted.bin', key)
    
#    # Decrypt
#    decrypt_success = decrypt_file('largefile_encrypted.bin', 'largefile_decrypted.txt', key)
#    if decrypt_success:
#        print("Decryption successful!")
#    else:
#        print("Decryption failed!")