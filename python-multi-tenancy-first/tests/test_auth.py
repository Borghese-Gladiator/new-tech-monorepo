import time

import pytest
import jwt

from multi_tenancy.auth import (
    hash_password,
    verify_password,
    make_token,
    decode_token,
    JWT_SECRET,
    JWT_ALG,
)


class TestPasswordHashing:
    @pytest.mark.parametrize("pw", ["password", "s3cr3t!", "", "a" * 72])
    def test_hash_then_verify(self, pw):
        hashed = hash_password(pw)
        assert verify_password(pw, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_hashes_are_unique(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt salts differ


class TestJWT:
    def test_roundtrip(self):
        token = make_token(user_id=42, tenant_id=7)
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["tenant_id"] == 7

    def test_expired_token_rejected(self):
        payload = {
            "sub": "1",
            "tenant_id": 1,
            "iat": int(time.time()) - 7200,
            "exp": int(time.time()) - 3600,
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(token)

    def test_bad_secret_rejected(self):
        token = jwt.encode({"sub": "1", "tenant_id": 1, "exp": time.time() + 3600}, "wrong-secret", algorithm=JWT_ALG)
        with pytest.raises(jwt.InvalidSignatureError):
            decode_token(token)
