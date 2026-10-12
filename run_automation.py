"""
==============================================================================
FILE HISTORY CARD
------------------------------------------------------------------------------
File:           run_automation.py
Author:         Asif Zaman
Created:        2026-10-12
Responsibility: Plug-and-play automation orchestrator and CLI entry point.
                Loads credentials directly from environment variables (.env)
                with ZERO popup dialogs or manual clicks. Provides plug-and-play
                functions for immediate, scheduled, and recurring automated logins.
==============================================================================
"""

import os
import sys
import argparse
from typing import Optional, Union, Any
from datetime import datetime, time as dtime
from dotenv import load_dotenv

from framework import GenericLoginFramework
from scheduler import (
    scheduled_login,
    scheduled_recurring_login,
    scheduled_interval_login,
    parse_target_time
)
from logger import log_activity


def automated_login(
    url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    auto_captcha: Optional[bool] = None,
    headless: Optional[bool] = None,
    timeout: int = 12
) -> Any:
    """
    Plug-and-play function for 100% automated login with NO popup and NO manual clicks.
    Retrieves values from .env automatically if parameters are omitted.

    Parameters:
      url: Target website URL (default: .env TARGET_URL or default portal).
      username: User / Merchant ID (default: .env MERCHANT_ID or LOGIN_USERNAME).
      password: Password (default: .env MERCHANT_PASSWORD or LOGIN_PASSWORD).
      auto_captcha: Solve image CAPTCHA offline via TrOCR (default: .env AUTO_CAPTCHA or True).
      headless: Run Chrome headless without opening a visible window (default: .env HEADLESS or False).
      timeout: Element wait timeout in seconds (default: 12).

    Returns:
      webdriver.Chrome: The active Selenium WebDriver instance.
    """
    # 1. Load environment variables
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(base_dir, ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        load_dotenv()

    # 2. Resolve credentials & config from arguments or .env
    raw_url = url or os.getenv("LOGIN_URL") or os.getenv("TARGET_URL") or os.getenv("MERCHANT_URL")
    resolved_url = raw_url.strip() if raw_url else ""

    raw_user = username or os.getenv("MERCHANT_ID") or os.getenv("LOGIN_USERNAME") or os.getenv("USERNAME")
    resolved_username = raw_user.strip() if raw_user else ""

    raw_pass = password or os.getenv("MERCHANT_PASSWORD") or os.getenv("LOGIN_PASSWORD") or os.getenv("PASSWORD")
    resolved_password = raw_pass.strip() if raw_pass else ""

    if headless is None:
        resolved_headless = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
    else:
        resolved_headless = headless

    if auto_captcha is None:
        resolved_auto_captcha = os.getenv("AUTO_CAPTCHA", "true").lower() in ("true", "1", "yes")
    else:
        resolved_auto_captcha = auto_captcha

    # 3. Validate
    if not resolved_url:
        raise ValueError(
            "Missing target URL! Please define LOGIN_URL in your .env file "
            "or pass it via argument (url=... or --url <URL>)."
        )

    if not resolved_username or not resolved_password:
        raise ValueError(
            "Missing credentials! Please define MERCHANT_ID and MERCHANT_PASSWORD in .env "
            "or pass them directly as arguments (username=..., password=...)."
        )

    masked_user = f"{resolved_username[:3]}***" if len(resolved_username) > 3 else "***"
    log_activity("==================================================")
    log_activity("        GENERIC WEB AUTO-LOGIN FRAMEWORK          ")
    log_activity("==================================================")
    log_activity(f"[Run] Target URL   : {resolved_url}")
    log_activity(f"[Run] Username     : {masked_user}")
    log_activity(f"[Run] Headless     : {resolved_headless}")
    log_activity(f"[Run] Auto CAPTCHA : {resolved_auto_captcha}")
    log_activity("==================================================")

    # 4. Execute login flow
    framework = GenericLoginFramework(headless=resolved_headless, timeout=timeout)
    return framework.login(
        url=resolved_url,
        username=resolved_username,
        password=resolved_password,
        auto_captcha=resolved_auto_captcha
    )


def main():
    parser = argparse.ArgumentParser(
        description="Zero-click Web Auto-Login Framework (loads credentials from .env)."
    )
    parser.add_argument("--url", type=str, default=None, help="Target URL (overrides .env LOGIN_URL)")
    parser.add_argument("-u", "--username", type=str, default=None, help="Username/ID (overrides .env MERCHANT_ID)")
    parser.add_argument("-p", "--password", type=str, default=None, help="Password (overrides .env MERCHANT_PASSWORD)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--no-captcha", action="store_true", help="Disable automatic CAPTCHA solving")
    parser.add_argument(
        "--schedule",
        type=str,
        default=None,
        help="Schedule login at a specific time (e.g. '16:30', '04:30 PM', '+45m', '2026-10-12 18:00')"
    )
    parser.add_argument(
        "--daily",
        type=str,
        default=None,
        help="Run recurring daily login at specified time (e.g. '09:00', '09:00 AM')"
    )
    parser.add_argument(
        "--every",
        type=int,
        default=None,
        help="Run recurring login at regular interval in minutes (e.g. 60 for every hour)"
    )

    args = parser.parse_args()

    auto_captcha = False if args.no_captcha else None
    headless = True if args.headless else None

    # Handle recurring interval
    if args.every:
        log_activity(f"[Main] Setting up interval login every {args.every} minutes...")
        scheduled_interval_login(
            interval_minutes=args.every,
            url=args.url,
            username=args.username,
            password=args.password,
            auto_captcha=auto_captcha,
            headless=headless,
            background=False
        )
        return

    # Handle daily recurring schedule
    if args.daily:
        log_activity(f"[Main] Setting up recurring daily login at {args.daily}...")
        scheduled_recurring_login(
            time_of_day=args.daily,
            url=args.url,
            username=args.username,
            password=args.password,
            auto_captcha=auto_captcha,
            headless=headless,
            background=False
        )
        return

    # Handle one-time scheduled login
    if args.schedule:
        log_activity(f"[Main] Scheduling login for {args.schedule}...")
        scheduled_login(
            target_time=args.schedule,
            url=args.url,
            username=args.username,
            password=args.password,
            auto_captcha=auto_captcha,
            headless=headless,
            background=False
        )
        return

    # Default: Run immediately with data from .env (ZERO CLICKS, NO POPUP)
    try:
        automated_login(
            url=args.url,
            username=args.username,
            password=args.password,
            auto_captcha=auto_captcha,
            headless=headless
        )
    except Exception as e:
        log_activity(f"[Error] {e}", level="ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()

__all__ = [
    "automated_login",
    "scheduled_login",
    "scheduled_recurring_login",
    "scheduled_interval_login",
    "parse_target_time",
    "log_activity"
]

