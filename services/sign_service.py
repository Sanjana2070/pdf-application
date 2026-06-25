import os
import datetime
from typing import Callable


class SignService:

    @staticmethod
    def sign_pdf(
        input_path: str,
        output_path: str,
        pfx_path: str,
        pfx_password: str,
        reason: str = "",
        location: str = "",
        contact: str = "",
        progress_cb: Callable[[int], None] = None,
    ) -> None:
        """
        Apply a CMS/PKCS#7 digital signature to a PDF using a .pfx certificate.

        The signature is an invisible approval signature embedded as an
        incremental update — it does not alter the original content.

        Args:
            pfx_path:     Path to the .pfx / .p12 certificate file.
            pfx_password: Password string for the .pfx file (may be empty).
            reason:       Reason text embedded in the signature.
            location:     Location text embedded in the signature.
            contact:      Contact / email embedded in the signature.
        """
        if not os.path.isfile(input_path):
            raise RuntimeError(f"File not found: {input_path}")
        if not os.path.isfile(pfx_path):
            raise RuntimeError(f"Certificate not found: {pfx_path}")

        from endesive.pdf import cms

        date = datetime.datetime.utcnow().strftime("D:%Y%m%d%H%M%S+00'00'")
        dct = {
            "aligned":      0,
            "sigflags":     3,
            "sigflagsft":   132,
            "sigpage":      0,
            "sigbutton":    True,
            "contact":      contact,
            "location":     location,
            "signingdate":  date,
            "reason":       reason,
            "signature":    "Signature1",
            "signaturebox": (0, 0, 0, 0),
        }

        if progress_cb:
            progress_cb(15)

        with open(pfx_path, "rb") as f:
            p12_data = f.read()

        with open(input_path, "rb") as f:
            pdf_data = f.read()

        if progress_cb:
            progress_cb(30)

        pw = pfx_password.encode("utf-8") if pfx_password else b""
        signed_chunk = cms.sign(pdf_data, dct, p12_data, pw, [], "sha256")

        if progress_cb:
            progress_cb(80)

        with open(output_path, "wb") as f:
            f.write(pdf_data)
            f.write(signed_chunk)

        if progress_cb:
            progress_cb(100)

    @staticmethod
    def list_signatures(pdf_path: str) -> list[dict]:
        """
        Return metadata about signature fields found in the PDF.
        This does NOT perform cryptographic verification —
        it only reports which signature fields exist.

        Returns list of dicts with keys: page (1-based), name, signed (bool).
        """
        import fitz
        if not os.path.isfile(pdf_path):
            raise RuntimeError(f"File not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        results = []
        for page in doc:
            for widget in page.widgets():
                if widget.field_type == 7:  # PDF_WIDGET_TYPE_SIGNATURE
                    val = widget.field_value
                    results.append({
                        "page":   page.number + 1,
                        "name":   widget.field_name or "(unnamed)",
                        "signed": bool(val),
                    })
        doc.close()
        return results

    @staticmethod
    def generate_test_certificate(
        output_path: str,
        common_name: str = "PDF Tools Test Signer",
        password: str = "",
        progress_cb: Callable[[int], None] = None,
    ) -> None:
        """
        Generate a self-signed RSA certificate and export it as a .pfx file.
        Intended for testing the signing workflow — not for production use.
        """
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization import pkcs12

        if progress_cb:
            progress_cb(10)

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        if progress_cb:
            progress_cb(40)

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PDF Tools"),
        ])
        now = datetime.datetime.utcnow()
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=3650))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=True,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(key, hashes.SHA256())
        )

        if progress_cb:
            progress_cb(70)

        pw_bytes = password.encode("utf-8") if password else None
        encryption = (
            serialization.BestAvailableEncryption(pw_bytes)
            if pw_bytes
            else serialization.NoEncryption()
        )
        p12_data = pkcs12.serialize_key_and_certificates(
            name=common_name.encode("utf-8"),
            key=key,
            cert=cert,
            cas=None,
            encryption_algorithm=encryption,
        )

        with open(output_path, "wb") as f:
            f.write(p12_data)

        if progress_cb:
            progress_cb(100)
