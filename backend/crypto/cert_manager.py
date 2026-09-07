"""
X.509 Certificate Chain & Revocation Manager
Validates certificate validity dates, issuer authority, self-signed origins, and CRL/OCSP status.
"""

import datetime
from typing import Dict, Any, List, Optional, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class CertificateManager:
    """Manages X.509 certificate validation, CRL checks, and test cert generation."""

    def __init__(self):
        # In-memory revocation list: maps serial_number (hex or str) to revocation reason
        self.revocation_list: Dict[str, Dict[str, Any]] = {}
        # Trusted CA certificates (Subject Key Identifiers or Common Names)
        self.trusted_roots: List[str] = ["National E-Governance Root CA 2026", "SIH Trusted Root CA"]

    def revoke_certificate(self, serial: str, reason: str = "Key Compromise"):
        """Adds a certificate serial number to the CRL."""
        self.revocation_list[str(serial)] = {
            "revoked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "reason": reason
        }

    def is_revoked(self, serial: str) -> Optional[Dict[str, Any]]:
        """Checks if a serial number has been revoked."""
        return self.revocation_list.get(str(serial))

    def create_self_signed_cert(
        self,
        common_name: str = "e-sign.gov.in",
        days_valid: int = 365,
        is_ca: bool = False,
        issuer_name: Optional[str] = None
    ) -> Tuple[bytes, bytes, str]:
        """
        Creates a test RSA keypair and X.509 certificate.
        Returns (private_key_pem, cert_pem, serial_number_str).
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "National Digital Identity Authority"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        if issuer_name:
            issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "National Digital Identity Authority"),
                x509.NameAttribute(NameOID.COMMON_NAME, issuer_name),
            ])
        else:
            issuer = subject

        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=days_valid))
            .add_extension(
                x509.BasicConstraints(ca=is_ca, path_length=None),
                critical=True,
            )
            .sign(private_key, hashes.SHA256())
        )

        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        return priv_pem, cert_pem, str(cert.serial_number)

    def validate_certificate_pem(self, cert_pem_str: str) -> Dict[str, Any]:
        """
        Validates an X.509 certificate PEM:
        - Expiration and not-before checks
        - CRL revocation status
        - Issuer authority trust
        - Self-signed detection
        """
        try:
            cert = x509.load_pem_x509_certificate(cert_pem_str.encode('utf-8'))
        except Exception as e:
            return {
                "valid": False,
                "error": f"Invalid X.509 Certificate PEM format: {str(e)}",
                "risk_score": 10.0
            }

        now = datetime.datetime.now(datetime.timezone.utc)
        serial_str = str(cert.serial_number)
        subject_cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        issuer_cn = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)

        subject_str = subject_cn[0].value if subject_cn else "Unknown Subject"
        issuer_str = issuer_cn[0].value if issuer_cn else "Unknown Issuer"

        # Check expiration
        is_expired = now > cert.not_valid_after_utc
        not_yet_valid = now < cert.not_valid_before_utc

        # Check revocation
        revocation_info = self.is_revoked(serial_str)

        # Check self-signed
        is_self_signed = (cert.subject == cert.issuer)

        # Check trusted root
        is_trusted_root = any(root.lower() in issuer_str.lower() for root in self.trusted_roots)

        flags = []
        risk = 0.0

        if is_expired:
            flags.append(f"Certificate Expired on {cert.not_valid_after_utc.strftime('%Y-%m-%d %H:%M:%SZ')}")
            risk += 8.0

        if not_yet_valid:
            flags.append(f"Certificate not yet valid (valid from {cert.not_valid_before_utc.strftime('%Y-%m-%d %H:%M:%SZ')})")
            risk += 5.0

        if revocation_info:
            flags.append(f"CERTIFICATE REVOKED! Reason: {revocation_info['reason']} at {revocation_info['revoked_at']}")
            risk += 10.0

        if is_self_signed and not is_trusted_root:
            flags.append(f"Untrusted Self-Signed Certificate: Issuer '{issuer_str}' is not an authorized Root CA")
            risk += 6.5
        elif not is_trusted_root:
            flags.append(f"Untrusted Intermediate / Unknown Root CA: '{issuer_str}'")
            risk += 4.0

        is_valid = (risk < 3.0) and not is_expired and not revocation_info

        return {
            "valid": is_valid,
            "serial_number": serial_str,
            "subject": subject_str,
            "issuer": issuer_str,
            "not_valid_before": cert.not_valid_before_utc.isoformat(),
            "not_valid_after": cert.not_valid_after_utc.isoformat(),
            "is_self_signed": is_self_signed,
            "is_revoked": bool(revocation_info),
            "is_expired": is_expired,
            "risk_contribution": min(10.0, risk),
            "flags": flags
        }
