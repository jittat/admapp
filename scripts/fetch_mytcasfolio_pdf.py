from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import UploadedDocument

#!/usr/bin/env python3
"""
Standalone script to fetch PDF URLs from TCAS FOLIO.
Handles authentication and PDF metadata retrieval.

Usage:
    python fetch_pdf.py <url>
    python fetch_pdf.py https://folio.mytcas.com/_/68e3880c2ef4c36c489ad051_19a3d2b7c42

Requirements:
    - .env file with TCAS_EMAIL and TCAS_PASSWORD
"""

import json
import sys
import os
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Configuration
API_BASE_URL = "https://tcas65.as.r.appspot.com"
LOGIN_ENDPOINT = "/folio-admins/login"
VERIFY_ENDPOINT = "/folio-admins/me"
PDF_BASE_URL = "https://tcas-pdf-dot-tcas65.as.r.appspot.com"
TOKEN_FILE = "mytcas-token.json"
TOKEN_EXPIRY_DAYS = 2

# Request headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Content-Type': 'application/json',
    'Origin': 'https://student.mytcas.com',
    'Referer': 'https://student.mytcas.com/',
    'Connection': 'keep-alive'
}


class TCASFetcher:
    """Handle TCAS FOLIO authentication and PDF fetching."""

    def __init__(self, email=None, password=None):
        """Initialize fetcher with credentials."""
        load_dotenv(".mytcas-env")

        self.email = email or os.getenv("TCAS_EMAIL")
        self.password = password or os.getenv("TCAS_PASSWORD")

        if not self.email or not self.password:
            raise ValueError(
                "Missing credentials. Please set TCAS_EMAIL and TCAS_PASSWORD "
                "in .env file or pass them to constructor"
            )

        self.session = requests.Session()
        self.access_token = None
        self.token_expiry = None

    def login(self):
        """
        Login to TCAS FOLIO and obtain access token.

        Returns:
            bool: True if login successful, False otherwise
        """
        login_url = f"{API_BASE_URL}{LOGIN_ENDPOINT}"

        payload = {
            "email": self.email,
            "password": self.password
        }

        try:
            response = self.session.post(
                login_url,
                headers=HEADERS,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('accessToken')

                if self.access_token:
                    self.token_expiry = datetime.now() + timedelta(days=TOKEN_EXPIRY_DAYS)
                    self._save_token()
                    print(f"✓ Login successful for {self.email}")
                    return True
                else:
                    print("✗ Login failed: No access token received")
                    return False
            else:
                print(f"✗ Login failed: HTTP {response.status_code}")
                print(f"  Response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"✗ Login error: {e}")
            return False

    def verify_token(self):
        """
        Verify if the current access token is valid.

        Returns:
            bool: True if token is valid, False otherwise
        """
        if not self.access_token:
            return False

        verify_url = f"{API_BASE_URL}{VERIFY_ENDPOINT}"

        try:
            response = self.session.get(
                verify_url,
                headers={
                    **HEADERS,
                    'accessToken': self.access_token
                }
            )

            return response.status_code == 200

        except requests.exceptions.RequestException as e:
            print(f"✗ Token verification error: {e}")
            return False

    def ensure_authenticated(self):
        """
        Ensure user is authenticated. Try to load saved token first,
        then verify it. If invalid, perform a new login.

        Returns:
            bool: True if authenticated, False otherwise
        """
        # Try to load saved token
        if self._load_token():
            # Check if token is expired
            if self.token_expiry and datetime.now() < self.token_expiry:
                # Verify token with API
                if self.verify_token():
                    #print("✓ Using saved token")
                    return True
                else:
                    print("Saved token is invalid, logging in again...")
            else:
                print("Token has expired, logging in again...")

        # If no valid token, perform login
        return self.login()

    def fetch_pdf_url(self, folio_id):
        """
        Fetch PDF URL for a given folio ID.

        Args:
            folio_id: The folio identifier (e.g., '68e3880b2ef4c36c489acfc1_199e7dca88e')

        Returns:
            dict: JSON response containing PDF URL, or None if failed
        """
        if not self.access_token:
            print("✗ Not authenticated. Call ensure_authenticated() first.")
            return None

        pdf_url = f"{PDF_BASE_URL}/folios/{folio_id}/get-pdf"

        headers = {
            **HEADERS,
            'accessToken': self.access_token,
            'Content-Length': '0'
        }

        try:
            response = self.session.post(pdf_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                #print(f"✓ PDF URL fetched successfully")
                return data
            else:
                print(f"✗ Failed to fetch PDF URL: HTTP {response.status_code}")
                print(f"  Response: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"✗ Fetch error: {e}")
            return None

    def _save_token(self):
        """Save access token to file for persistence."""
        token_data = {
            'access_token': self.access_token,
            'expiry': self.token_expiry.isoformat() if self.token_expiry else None
        }

        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)

    def _load_token(self):
        """
        Load access token from file.

        Returns:
            bool: True if token loaded successfully, False otherwise
        """
        token_file = Path(TOKEN_FILE)

        if not token_file.exists():
            return False

        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)

            self.access_token = token_data.get('access_token')
            expiry_str = token_data.get('expiry')

            if expiry_str:
                self.token_expiry = datetime.fromisoformat(expiry_str)

            return True

        except (json.JSONDecodeError, KeyError) as e:
            print(f"✗ Error loading token: {e}")
            return False

    def download_pdf(self, pdf_url, folio_id, 
                     base_path, prefix=''):
        """
        Download PDF from S3 URL and save it.

        Args:
            pdf_url: The S3 pre-signed URL for the PDF
            folio_id: The folio ID to use as filename

        Returns:
            str: Path to downloaded file, or None if failed
        """
        filename = f"{base_path}/{prefix}-{folio_id}.pdf"

        try:
            #print(f"Downloading PDF to {filename}...")
            response = self.session.get(pdf_url, stream=True)

            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))

                with open(filename, 'wb') as f:
                    if total_size == 0:
                        f.write(response.content)
                    else:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                percent = (downloaded / total_size) * 100
                                #print(f"  Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='\r')

                #print(f"\n✓ PDF downloaded successfully: {filename}")
                return filename
            else:
                #print(f"✗ Failed to download PDF: HTTP {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            #print(f"✗ Download error: {e}")
            return None


def extract_folio_id(url):
    """
    Extract folio ID from URL.

    Args:
        url: Full URL or just folio ID

    Returns:
        str: Extracted folio ID

    Examples:
        'https://folio.mytcas.com/_/68e3880c2ef4c36c489ad051_19a3d2b7c42'
        -> '68e3880c2ef4c36c489ad051_19a3d2b7c42'

        'https://tcas-pdf-dot-tcas65.as.r.appspot.com/folios/68e3880b2ef4c36c489acfc1_199e7dca88e/get-pdf'
        -> '68e3880b2ef4c36c489acfc1_199e7dca88e'
    """
    # Try to extract from folio.mytcas.com URL pattern (/_/ID)
    match = re.search(r'/_/([^/]+)', url)
    if match:
        return match.group(1)

    # Try to extract from tcas-pdf URL pattern (/folios/ID/get-pdf)
    match = re.search(r'/folios/([^/]+)(?:/get-pdf)?', url)
    if match:
        return match.group(1)

    # If no match, assume it's already a folio ID
    return url


def fetch_pdf_main(url, base_path='.', prefix=''):
    url_or_id = url
    folio_id = extract_folio_id(url_or_id)

    #print(f"Folio ID: {folio_id}")

    try:
        # Initialize fetcher
        fetcher = TCASFetcher()

        # Ensure authenticated
        if not fetcher.ensure_authenticated():
            print("✗ Authentication failed")
            sys.exit(1)

        # Fetch PDF URL
        result = fetcher.fetch_pdf_url(folio_id)

        if result:
            #print("\nResult:")
            #print(json.dumps(result, indent=2))

            # Extract and display the PDF URL
            if 'pdf' in result:
                pdf_url = result['pdf']
                #print(f"\nPDF URL: {pdf_url}")

                # Download the PDF
                downloaded_file = fetcher.download_pdf(pdf_url, folio_id, 
                                                       base_path=base_path, 
                                                       prefix=prefix)

                if not downloaded_file:
                    print("✗ Failed to download PDF")
                    return None
                
                return downloaded_file
        else:
            print("✗ Failed to fetch PDF URL")
            return None

    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None


def random_prefix(length=10):
    import random
    import string
    letters = string.digits
    return ''.join(random.choice(letters) for i in range(length))


def main():
    base_path = sys.argv[1]
    base_url = sys.argv[2]
    if base_url.endswith('/'):
        base_url = base_url[:-1]

    documents = UploadedDocument.objects.filter(document_url__contains='mytcas.com').all()

    for d in documents:
        if d.local_document_url != '':
            continue

        document_url = d.document_url
        if not document_url.startswith('https://folio.mytcas.com/'):
            print('ERROR: wrong url:', d.applicant, document_url)

        print(d.applicant, d.document_url)
        prefix = random_prefix()
        filename = fetch_pdf_main(document_url, base_path=base_path, prefix=prefix)

        if not filename:
            print('ERROR: cannot fetch pdf for', d.applicant, document_url)
            continue

        base_filename = os.path.basename(filename)
        d.local_document_url = f'{base_url}/{base_filename}'
        print(f'URL: {d.local_document_url}')
        d.save()

        #break

if __name__ == '__main__':
    main()
    
