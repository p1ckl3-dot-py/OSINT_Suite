# OSINT_Suite
Python-based GUI OSINT suite for identity tracking (Google Dorks), multi-platform username scanning, image forensics (EXIF/GPS), IP/port auditing, and automated intelligence report generation.


Key Features

The application is structured into five integrated modules:

1. Identity Tracking (Google Dorks)

  Automates advanced Google search queries (Dorks) based on a full name.

  Filters public records across social media platforms, official government gazettes, business registries, public directories, and indexed documents (PDF, XLS, DOC).

2. Social Media Username Scanner

  Concurrently checks username availability and profile existence across more than 25 platforms (including social networks, IT/developer hubs, multimedia sites, and gaming communities).

  Allows instant access to discovered profiles by double-clicking any result row.

3. Image Forensics & Reverse Search

  EXIF Metadata Extraction: Reveals hidden file details such as camera model, capture timestamps, and device settings.

  GPS Geolocation: Automatically extracts embedded latitude/longitude coordinates and enables a one-click button to view the exact location on Google Maps.

  Reverse Image Search: Traces image origins across Google Lens, Yandex, and TinEye, offering both a Manual Mode (zero-upload for strict OPSEC/privacy) and an Automated Mode.

4. Network & Infrastructure Auditing

  Resolves domains to IP addresses and retrieves geolocation data alongside Internet Service Provider (ISP) details.

  Scans critical network ports (FTP, SSH, HTTP, HTTPS, MySQL, RDP, etc.) to identify open services and perform basic banner grabbing.

5. Automated Intelligence Reporting

  Intelligently filters out negative results and noise, retaining only verified positive findings.

  Exports a clean, timestamped, and categorized .txt report ready for documentation or audit delivery.

Getting Started

  - Option A: Download Standalone Executable (Recommended)

  No Python installation or environment setup is required:

  Navigate to the Releases section on the right-hand side of this repository.

  Download the build for your operating system:

  - Windows: Download the .exe file and double-click to launch.

  - Linux: Download the binary, grant execution permissions (chmod +x suite_osint), and run it.

  - Option B: Run from Source Code

    If you prefer to run the application directly using Python:

      Clone the repository:

        git clone https://github.com/p1ckl3-dot-py/OSINT_Suite.git
        cd osint_suite.py


      Install the required dependencies:

        pip install requests urllib3 pillow


        *(Note: On Linux distributions, ensure Tkinter is installed via sudo apt install python3-tk)*

      Launch the application:

        python suite_osint.py


Legal Disclaimer

  This tool has been developed strictly for educational, academic, and authorized cybersecurity auditing purposes. Users are responsible for complying with all applicable local and international laws regarding data privacy and network scanning. The author assumes no liability for any misuse of this software.

Author

  p1ckl3-dot-py — 2026 Project
