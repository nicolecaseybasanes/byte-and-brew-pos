# utils/hash_gen.py
import bcrypt

def generate_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

if __name__ == "__main__":
    pwd = input("Enter password to hash: ")
    print(f"Hashed: {generate_hash(pwd)}")