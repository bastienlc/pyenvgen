"""Tests for the openssl (cryptography) generation rule."""

from __future__ import annotations

import pytest

from pyenvgen.generation import generate_value
from pyenvgen.schema import OpenSSLGeneration


class TestGenerateValueOpenSSL:
    def test_rsa_pem(self) -> None:
        rule = OpenSSLGeneration(command="rsa", args={"key_size": 1024})
        value = generate_value(rule)
        assert "BEGIN RSA PRIVATE KEY" in value or "BEGIN PRIVATE KEY" in value

    def test_rsa_der_b64(self) -> None:
        import base64
        rule = OpenSSLGeneration(command="rsa", args={"key_size": 1024, "encoding": "der_b64"})
        value = generate_value(rule)
        # Should be valid base64
        base64.b64decode(value)

    def test_ec_pem(self) -> None:
        rule = OpenSSLGeneration(command="ec", args={"curve": "secp256r1"})
        value = generate_value(rule)
        assert "PRIVATE KEY" in value

    def test_ec_unsupported_curve(self) -> None:
        rule = OpenSSLGeneration(command="ec", args={"curve": "not_a_curve"})
        with pytest.raises(ValueError, match="Unsupported EC curve"):
            generate_value(rule)

    def test_ed25519_pem(self) -> None:
        rule = OpenSSLGeneration(command="ed25519")
        value = generate_value(rule)
        assert "PRIVATE KEY" in value

    def test_ed25519_raw_b64(self) -> None:
        import base64
        rule = OpenSSLGeneration(command="ed25519", args={"encoding": "raw_b64"})
        value = generate_value(rule)
        raw = base64.b64decode(value)
        assert len(raw) == 32  # Ed25519 private key is 32 bytes

    def test_x25519_raw_b64_default(self) -> None:
        import base64
        rule = OpenSSLGeneration(command="x25519")
        value = generate_value(rule)
        raw = base64.b64decode(value)
        assert len(raw) == 32  # X25519 private key is 32 bytes

    def test_x25519_pem(self) -> None:
        rule = OpenSSLGeneration(command="x25519", args={"encoding": "pem"})
        value = generate_value(rule)
        assert "PRIVATE KEY" in value

    def test_fernet(self) -> None:
        from cryptography.fernet import Fernet
        rule = OpenSSLGeneration(command="fernet")
        value = generate_value(rule)
        # Should be a valid Fernet key
        Fernet(value.encode())

    def test_random_hex(self) -> None:
        rule = OpenSSLGeneration(command="random", args={"length": 16, "encoding": "hex"})
        value = generate_value(rule)
        assert len(value) == 32  # 16 bytes = 32 hex chars
        int(value, 16)  # valid hex

    def test_random_base64(self) -> None:
        import base64
        rule = OpenSSLGeneration(command="random", args={"length": 16, "encoding": "base64"})
        value = generate_value(rule)
        raw = base64.b64decode(value)
        assert len(raw) == 16

    def test_random_base64url(self) -> None:
        import base64
        rule = OpenSSLGeneration(command="random", args={"length": 16, "encoding": "base64url"})
        value = generate_value(rule)
        raw = base64.urlsafe_b64decode(value)
        assert len(raw) == 16

    def test_unknown_command_raises(self) -> None:
        rule = OpenSSLGeneration(command="unknown")
        with pytest.raises(ValueError, match="Unsupported openssl command"):
            generate_value(rule)

    def test_each_call_produces_unique_value(self) -> None:
        rule = OpenSSLGeneration(command="random", args={"length": 32})
        v1 = generate_value(rule)
        v2 = generate_value(rule)
        assert v1 != v2
