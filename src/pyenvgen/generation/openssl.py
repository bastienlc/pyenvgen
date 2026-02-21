"""OpenSSL generation rule – generates cryptographic material via the ``cryptography`` package.

Supported commands
------------------
``rsa``
    RSA private key in PEM format.
    Args: ``key_size`` (int, default 2048), ``encoding`` (``pem`` | ``der_b64``, default ``pem``).
``ec``
    Elliptic-curve private key.
    Args: ``curve`` (``secp256r1`` | ``secp384r1`` | ``secp521r1`` | ``secp256k1``, default ``secp256r1``),
    ``encoding`` (``pem`` | ``der_b64``, default ``pem``).
``ed25519``
    Ed25519 private key.
    Args: ``encoding`` (``pem`` | ``raw_b64``, default ``pem``).
``x25519``
    X25519 private key (useful for WireGuard-style key exchange).
    Args: ``encoding`` (``pem`` | ``raw_b64``, default ``raw_b64``).
``fernet``
    A URL-safe base64-encoded 32-byte Fernet key.
``random``
    Random bytes.
    Args: ``length`` (int, default 32), ``encoding`` (``hex`` | ``base64`` | ``base64url``, default ``hex``).
"""

from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa, x25519

from pyenvgen.schema import OpenSSLGeneration

_EC_CURVES: dict[str, ec.EllipticCurve] = {
    "secp256r1": ec.SECP256R1(),
    "secp384r1": ec.SECP384R1(),
    "secp521r1": ec.SECP521R1(),
    "secp256k1": ec.SECP256K1(),
}


def _pem_or_der_b64(
    key_bytes_pem: bytes, key_bytes_der: bytes, encoding_name: str
) -> str:
    if encoding_name == "pem":
        return key_bytes_pem.decode()
    return base64.b64encode(key_bytes_der).decode()


def _rsa(args: dict) -> str:
    key_size: int = int(args.get("key_size", 2048))
    encoding_name: str = args.get("encoding", "pem")
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    return _pem_or_der_b64(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        encoding_name,
    )


def _ec(args: dict) -> str:
    curve_name: str = args.get("curve", "secp256r1")
    encoding_name: str = args.get("encoding", "pem")
    if curve_name not in _EC_CURVES:
        raise ValueError(
            f"Unsupported EC curve: {curve_name!r}. Choose from {list(_EC_CURVES)}"
        )
    key = ec.generate_private_key(_EC_CURVES[curve_name])
    return _pem_or_der_b64(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        encoding_name,
    )


def _ed25519(args: dict) -> str:
    encoding_name: str = args.get("encoding", "pem")
    key = ed25519.Ed25519PrivateKey.generate()
    if encoding_name == "pem":
        return key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
    return base64.b64encode(
        key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
    ).decode()


def _x25519(args: dict) -> str:
    encoding_name: str = args.get("encoding", "raw_b64")
    key = x25519.X25519PrivateKey.generate()
    if encoding_name == "pem":
        return key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
    return base64.b64encode(
        key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
    ).decode()


def _fernet(_args: dict) -> str:
    return Fernet.generate_key().decode()


def _random(args: dict) -> str:
    length: int = int(args.get("length", 32))
    encoding_name: str = args.get("encoding", "hex")
    raw = os.urandom(length)
    if encoding_name == "hex":
        return raw.hex()
    if encoding_name == "base64":
        return base64.b64encode(raw).decode()
    if encoding_name == "base64url":
        return base64.urlsafe_b64encode(raw).decode()
    raise ValueError(f"Unsupported encoding for random: {encoding_name!r}")


_COMMANDS = {
    "rsa": _rsa,
    "ec": _ec,
    "ed25519": _ed25519,
    "x25519": _x25519,
    "fernet": _fernet,
    "random": _random,
}


def generate_openssl(rule: OpenSSLGeneration) -> str:
    """Dispatch to the appropriate cryptographic generator for *rule.command*."""
    if rule.command not in _COMMANDS:
        raise ValueError(
            f"Unsupported openssl command: {rule.command!r}. "
            f"Supported: {', '.join(_COMMANDS)}"
        )
    return _COMMANDS[rule.command](rule.args)
