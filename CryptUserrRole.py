import hashlib
import base64
from cryptography.fernet import Fernet

class CryptUserRole:
    def __init__(self, role: str):
        self.role = role
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)

    def encrypt_role(self) -> str:
        # Encrypt the role using Fernet symmetric encryption
        encrypted_role = self.cipher_suite.encrypt(self.role.encode())
        return encrypted_role.decode()

    def decrypt_role(self, encrypted_role: str) -> str:
        try:
            # Decrypt the role using Fernet symmetric encryption
            decrypted_role = self.cipher_suite.decrypt(encrypted_role.encode())
            return decrypted_role.decode()
        except Exception as e:
            return f"Decryption failed: {str(e)}"

if __name__ == "__main__":
    role = "admin"
    crypt_user_role = CryptUserRole(role)
    encrypted_role = crypt_user_role.encrypt_role()
    print(f"Original Role: {role}")
    print(f"Encrypted Role: {encrypted_role}")
    print(f"Decrypted Role: {crypt_user_role.decrypt_role(encrypted_role)}")