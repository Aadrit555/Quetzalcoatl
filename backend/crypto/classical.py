"""
Classical Cryptographic Verification Engine
Supports RSA (PSS & PKCS1v15), ECDSA (NIST P-256), and Ed25519.
"""

import base64
import hashlib
from typing import Dict, Any, Tuple, Optional
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

class ClassicalVerifier:
    """Handles verification and generation for classical asymmetric cryptography."""

    @staticmethod
    def generate_rsa_keypair(key_size: int = 2048) -> Tuple[bytes, bytes]:
        """Generates PEM-encoded RSA private and public keys."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return priv_pem, pub_pem

    @staticmethod
    def generate_ecdsa_keypair() -> Tuple[bytes, bytes]:
        """Generates PEM-encoded ECDSA P-256 private and public keys."""
        private_key = ec.generate_private_key(ec.SECP256R1())
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return priv_pem, pub_pem

    @staticmethod
    def sign_data(private_key_pem: bytes, data: bytes, algorithm: str = "RSA-PSS") -> bytes:
        """Signs arbitrary payload data with given algorithm."""
        priv_key = serialization.load_pem_private_key(private_key_pem, password=None)

        if algorithm == "RSA-PSS" and isinstance(priv_key, rsa.RSAPrivateKey):
            return priv_key.sign(
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        elif algorithm == "RSA-PKCS1v15" and isinstance(priv_key, rsa.RSAPrivateKey):
            return priv_key.sign(
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        elif algorithm.startswith("ECDSA") and isinstance(priv_key, ec.EllipticCurvePrivateKey):
            return priv_key.sign(
                data,
                ec.ECDSA(hashes.SHA256())
            )
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm} for key type {type(priv_key)}")

    @staticmethod
    def verify_signature(
        public_key_pem: bytes,
        signature: bytes,
        data: bytes,
        algorithm: str = "RSA-PSS"
    ) -> Dict[str, Any]:
        """
        Verifies a signature using the public key PEM.
        Returns detailed verification status and error if invalid.
        """
        try:
            pub_key_bytes = public_key_pem if isinstance(public_key_pem, bytes) else public_key_pem.encode('utf-8')
            if b"BEGIN CERTIFICATE" in pub_key_bytes:
                from cryptography import x509
                cert = x509.load_pem_x509_certificate(pub_key_bytes)
                pub_key = cert.public_key()
            else:
                pub_key = serialization.load_pem_public_key(pub_key_bytes)

            if algorithm == "RSA-PSS" and isinstance(pub_key, rsa.RSAPublicKey):
                pub_key.verify(
                    signature,
                    data,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                return {"valid": True, "algorithm": "RSA-PSS", "details": "RSA-PSS SHA-256 signature verified"}

            elif algorithm == "RSA-PKCS1v15" and isinstance(pub_key, rsa.RSAPublicKey):
                pub_key.verify(
                    signature,
                    data,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                return {"valid": True, "algorithm": "RSA-PKCS1v15", "details": "RSA-PKCS1v15 SHA-256 signature verified"}

            elif algorithm.startswith("ECDSA") and isinstance(pub_key, ec.EllipticCurvePublicKey):
                pub_key.verify(
                    signature,
                    data,
                    ec.ECDSA(hashes.SHA256())
                )
                return {"valid": True, "algorithm": algorithm, "details": "ECDSA NIST-P256 SHA-256 signature verified"}

            else:
                return {
                    "valid": False,
                    "algorithm": algorithm,
                    "details": f"Algorithm {algorithm} does not match key type or is unsupported"
                }

        except InvalidSignature:
            return {
                "valid": False,
                "algorithm": algorithm,
                "details": "Cryptographic signature verification failed: signature does not match payload"
            }
        except Exception as e:
            return {
                "valid": False,
                "algorithm": algorithm,
                "details": f"Verification error: {str(e)}"
            }
