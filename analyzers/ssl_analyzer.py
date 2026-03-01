import ssl
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse
from config import SSL_WARNING_DAYS, REQUEST_TIMEOUT
class SSLAnalyzer:
    def __init__(self, url: str):
        self.url = url
        parsed = urlparse(url)
        self.hostname = parsed.netloc
        self.port = parsed.port or 443
    def _error_response(self, message: str, error: str = None) -> dict:
        return {
            'exists': False,
            'status': 'error',
            'message': message,
            'error': error or message,
            'summary': {'status': 'error', 'message': message, 'days_remaining': None}
        }
    def analyze(self) -> dict:
        try:
            cert_info = self._get_certificate_info()
            result = self._analyze_certificate(cert_info)
            result['summary'] = {
                'status': result['status'],
                'message': result['message'],
                'days_remaining': result.get('days_remaining')
            }
            return result
        except ssl.SSLError as e:
            return self._error_response(f'SSL connection error: {str(e)}', str(e))
        except socket.timeout:
            return self._error_response('SSL connection timed out', 'Timeout')
        except socket.gaierror as e:
            return self._error_response(f'DNS resolution error: {str(e)}', str(e))
        except Exception as e:
            return self._error_response(f'SSL analysis failed: {str(e)}', str(e))
    def _get_certificate_info(self) -> dict:
        context = ssl.create_default_context()
        with socket.create_connection((self.hostname, self.port), timeout=REQUEST_TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                cert = ssock.getpeercert()
                return cert
    def _analyze_certificate(self, cert: dict) -> dict:
        not_after_str = cert.get('notAfter', '')
        not_before_str = cert.get('notBefore', '')
        try:
            not_after = datetime.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
            not_before = datetime.strptime(not_before_str, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                not_after = datetime.strptime(not_after_str, '%b  %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
                not_before = datetime.strptime(not_before_str, '%b  %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
            except Exception:
                not_after = None
                not_before = None
        now = datetime.now(timezone.utc)
        days_remaining = (not_after - now).days if not_after else None
        issuer = cert.get('issuer', ())
        issuer_dict = {}
        for item in issuer:
            for key, value in item:
                issuer_dict[key] = value
        subject = cert.get('subject', ())
        subject_dict = {}
        for item in subject:
            for key, value in item:
                subject_dict[key] = value
        if days_remaining is None:
            status = 'warning'
            message = 'SSL certificate expiration date could not be read'
        elif days_remaining < 0:
            status = 'error'
            message = f'SSL certificate expired {abs(days_remaining)} days ago!'
        elif days_remaining <= SSL_WARNING_DAYS:
            status = 'warning'
            message = f'SSL certificate will expire in {days_remaining} days'
        else:
            status = 'success'
            message = f'SSL certificate is valid ({days_remaining} days remaining)'
        return {
            'exists': True,
            'status': status,
            'message': message,
            'days_remaining': days_remaining,
            'valid_from': not_before.strftime('%Y-%m-%d %H:%M:%S') if not_before else None,
            'valid_until': not_after.strftime('%Y-%m-%d %H:%M:%S') if not_after else None,
            'issuer': {
                'organization': issuer_dict.get('organizationName', 'Unknown'),
                'common_name': issuer_dict.get('commonName', 'Unknown')
            },
            'subject': {
                'common_name': subject_dict.get('commonName', 'Unknown'),
                'organization': subject_dict.get('organizationName', '')
            },
            'san': cert.get('subjectAltName', []),
            'serial_number': cert.get('serialNumber', ''),
            'version': cert.get('version', '')
        }