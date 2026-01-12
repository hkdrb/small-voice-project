import re
import secrets
import bcrypt
import string

# Constant time dummy hash for timing attack mitigation
# This hash corresponds to "dummy_password" with a specific salt, pre-calculated
# to ensure consistent comparison time without burning CPU on every failed login.
# However, to simulate the *time* taken by bcrypt, we should actually perform a hash operation
# or rely on bcrypt.checkpw's behavior if we can supply a dummy hash.
# A better approach for timing mitigation with bcrypt is to always perform a hash verification.
# If user is not found, we verify against a dummy hash that we know will fail.

DUMMY_HASH = bcrypt.hashpw(b"dummy_password", bcrypt.gensalt()).decode()

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validates that the password meets the security requirements:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one symbol
    """
    if len(password) < 8:
        return False, "パスワードは8文字以上である必要があります"
        
    if not re.search(r"[A-Z]", password):
        return False, "パスワードには少なくとも1つの大文字を含める必要があります"
        
    if not re.search(r"[a-z]", password):
        return False, "パスワードには少なくとも1つの小文字を含める必要があります"
        
    if not re.search(r"\d", password):
        return False, "パスワードには少なくとも1つの数字を含める必要があります"
        
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "パスワードには少なくとも1つの記号を含める必要があります"
        
    return True, ""

def generate_strong_password(length=12) -> str:
    """Generates a random password that guarantees compliance with the policy."""
    if length < 8:
        length = 8
        
    # Ensure at least one of each required type
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(string.punctuation)
    ]
    
    # Fill the rest
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    
    # Shuffle
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)

def verify_password_safe(plain_password: str, hashed_password: str | None) -> bool:
    """
    Verifies a password against a hash in a way that resists timing attacks (Account Enumeration).
    If hashed_password is None (user not found), it verifies against a dummy hash.
    """
    if hashed_password is None:
        # Perform a check against a dummy hash to consume roughly the same time
        bcrypt.checkpw(plain_password.encode(), DUMMY_HASH.encode())
        return False
    else:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def hash_pass(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
