from __future__ import annotations

import ipaddress
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path


def generate_host_key(path):
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError as error:
        raise RuntimeError("cryptography no esta disponible para generar host keys") from error
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    private = ed25519.Ed25519PrivateKey.generate()
    target.write_bytes(
        private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.OpenSSH,
            serialization.NoEncryption(),
        )
    )
    if os.name != "nt":
        target.chmod(0o600)
    return str(target.resolve())


def generate_certificate(certificate, key, common_name, days=365):
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.x509.oid import NameOID
    except ImportError as error:
        raise RuntimeError("cryptography no esta disponible para generar certificados") from error
    private = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    current = datetime.now(timezone.utc)
    try:
        san = x509.IPAddress(ipaddress.ip_address(common_name))
    except ValueError:
        san = x509.DNSName(common_name.encode("idna").decode("ascii"))
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(current - timedelta(minutes=1))
        .not_valid_after(current + timedelta(days=days))
        .add_extension(x509.SubjectAlternativeName([san]), critical=False)
        .sign(private, hashes.SHA256())
    )
    cert_path, key_path = Path(certificate), Path(key)
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    if os.name != "nt":
        cert_path.chmod(0o644)
        key_path.chmod(0o600)
    return str(cert_path.resolve()), str(key_path.resolve())
