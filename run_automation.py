"""
==============================================================================
FILE HISTORY CARD
------------------------------------------------------------------------------
File:           run_automation.py
Author:         Asif Zaman
Created:        2026-10-12
Responsibility: Main orchestrator and entry point for the automation application.
                Prompts the user for target URL and credentials via the GUI popup,
                initializes the GenericLoginFramework, and executes the auto-login.
==============================================================================
"""

import sys
from popup import prompt_credentials
from framework import GenericLoginFramework

def main():
    print("==================================================")
    print("        GENERIC WEB AUTO-LOGIN FRAMEWORK          ")
    print("==================================================")
    print("Prompting user for credentials and target URL...")

    # 1. Open the popup dialog for user to enter/confirm credentials & URL
    creds = prompt_credentials()

    if not creds:
        print("Login cancelled by user.")
        sys.exit(0)

    url = creds["url"]
    username = creds["username"]
    password = creds["password"]
    auto_captcha = creds.get("auto_captcha", True)

    print(f"\nInitiating automated login for: {url}")
    print(f"User: {username}")

    # 2. Run the generic automation framework
    framework = GenericLoginFramework(headless=False)
    driver = framework.login(
        url=url,
        username=username,
        password=password,
        auto_captcha=auto_captcha
    )

if __name__ == "__main__":
    main()
