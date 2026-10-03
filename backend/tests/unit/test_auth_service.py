from app.core.security import hash_password, verify_password

def test_password_stored_as_argon2id():
    """T03: Password stored as Argon2id; not in responses."""
    password = "SuperSecretPassword123"
    hashed = hash_password(password)
    
    # Check that it starts with the Argon2id prefix
    assert hashed.startswith("$argon2id$")
    
    # Check that verification succeeds
    assert verify_password(password, hashed) is True
    
    # Check that verification fails for wrong password
    assert verify_password("WrongPassword", hashed) is False
