"""
==============================================================================
FILE HISTORY CARD
------------------------------------------------------------------------------
File:           scheduler.py
Author:         Asif Zaman
Created:        2026-10-12
Responsibility: Plug-and-play scheduling engine for automated browser logins.
                Supports one-time scheduling at a specific time (HH:MM or datetime),
                recurring daily schedules, post-login scraper callbacks, and
                daily timestamped activity logging.
==============================================================================
"""

import os
import re
import time
import threading
from datetime import datetime, date, timedelta, time as dtime
from typing import Union, Optional, Callable, Any, Tuple
from logger import log_activity


def parse_target_time(
    target: Union[str, dtime, datetime, int, float],
    reference_dt: Optional[datetime] = None
) -> datetime:
    """
    Parses various time formats into a concrete future datetime.

    Supported formats:
      - 24-hour time strings: "16:30", "16:30:00", "08:00"
      - 12-hour AM/PM strings: "8:00 AM", "08:00 AM", "4:30 PM"
      - Full datetime strings: "2026-10-12 16:30", "2026-10-12 16:30:00"
      - Relative strings: "+15m" (15 minutes), "+2h" (2 hours), "+45s" (45 seconds)
      - Numeric seconds: 300 (runs 300 seconds from now)
      - datetime.time objects: e.g. time(8, 0)
      - datetime.datetime objects: used directly

    If only a time-of-day is supplied and that time has already passed today,
    it automatically schedules for the next day.
    """
    now = reference_dt or datetime.now()

    # 1. Already a datetime
    if isinstance(target, datetime):
        return target

    # 2. A datetime.time object
    if isinstance(target, dtime):
        candidate = datetime.combine(now.date(), target)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    # 3. Numeric seconds offset
    if isinstance(target, (int, float)):
        return now + timedelta(seconds=float(target))

    if not isinstance(target, str):
        raise TypeError(f"Unsupported target_time type: {type(target)}. Expected str, time, datetime, or int/float.")

    cleaned = target.strip()

    # 4. Relative offset format: "+10m", "+2h", "+30s"
    rel_match = re.match(r"^\+(\d+)\s*([smhd])$", cleaned, re.IGNORECASE)
    if rel_match:
        val = int(rel_match.group(1))
        unit = rel_match.group(2).lower()
        if unit == 's':
            return now + timedelta(seconds=val)
        elif unit == 'm':
            return now + timedelta(minutes=val)
        elif unit == 'h':
            return now + timedelta(hours=val)
        elif unit == 'd':
            return now + timedelta(days=val)

    # 5. Full datetime string formats
    full_dt_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
    ]
    for fmt in full_dt_formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            pass

    # 6. Time-only formats (24-hr and 12-hr AM/PM)
    time_formats = [
        "%H:%M:%S",
        "%H:%M",
        "%I:%M:%S %p",
        "%I:%M %p",
        "%I %p",
    ]
    normalized_time = re.sub(r'(?i)(\d+)(am|pm)', r'\1 \2', cleaned).upper()

    for fmt in time_formats:
        try:
            parsed_t = datetime.strptime(normalized_time, fmt).time()
            candidate = datetime.combine(now.date(), parsed_t)
            if candidate <= now:
                candidate += timedelta(days=1)
            return candidate
        except ValueError:
            pass

    raise ValueError(
        f"Could not parse scheduled time: '{target}'. "
        f"Supported examples: '08:00', '08:00 AM', '2026-10-12 08:00:00', '+30m'."
    )


def format_duration(seconds: float) -> str:
    """Formats seconds into human-readable duration."""
    total_seconds = int(max(0, seconds))
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def wait_until(
    target_dt: datetime,
    stop_event: Optional[threading.Event] = None,
    log_milestones: bool = True
) -> bool:
    """
    Waits until target_dt is reached. Returns True when reached, or False if cancelled.
    Responsive to Ctrl+C and stop_event.
    """
    now = datetime.now()
    if target_dt <= now:
        return True

    total_wait = (target_dt - now).total_seconds()
    target_str = target_dt.strftime("%Y-%m-%d %H:%M:%S")
    log_activity(f"[Scheduler] ⏰ Waiting until {target_str} (in {format_duration(total_wait)})...")

    last_logged = now
    try:
        while True:
            if stop_event and stop_event.is_set():
                log_activity("[Scheduler] Wait cancelled by stop event.", level="WARNING")
                return False

            now = datetime.now()
            remaining = (target_dt - now).total_seconds()
            if remaining <= 0:
                log_activity(f"[Scheduler] 🔔 Target time reached: {target_str}")
                return True

            # Periodic log update every 5 minutes if waiting a long time
            if log_milestones and (now - last_logged).total_seconds() >= 300 and remaining > 60:
                log_activity(f"[Scheduler] Still waiting... {format_duration(remaining)} remaining until {target_str}")
                last_logged = now

            sleep_chunk = min(1.0, remaining)
            time.sleep(sleep_chunk)

    except KeyboardInterrupt:
        log_activity("[Scheduler] Schedule interrupted by user (Ctrl+C).", level="WARNING")
        return False


def scheduled_login(
    target_time: Union[str, dtime, datetime, int, float],
    login_func: Optional[Callable[..., Any]] = None,
    callback: Optional[Callable[[Any], Any]] = None,
    background: bool = False,
    **login_kwargs
) -> Any:
    """
    Plug-and-play function to schedule a login at a specified time.

    Parameters:
      target_time: When to execute (e.g. '08:00', '08:00 AM', '+45m', '2026-10-12 08:00').
      login_func: The login function to execute (defaults to automated_login).
      callback: Optional post-login scraper callback receiving the active driver: callback(driver).
      background: If True, executes in a background daemon thread and returns (thread, stop_event).
      login_kwargs: Arguments passed to login_func.
    """
    if login_func is None:
        from run_automation import automated_login
        login_func = automated_login

    target_dt = parse_target_time(target_time)

    def _job(stop_ev: Optional[threading.Event] = None):
        if wait_until(target_dt, stop_event=stop_ev):
            log_activity(f"[Scheduler] Triggering automated login for target {target_dt.strftime('%Y-%m-%d %H:%M:%S')}...")
            driver = login_func(**login_kwargs)
            if callback and callable(callback):
                log_activity("[Scheduler] Executing post-login callback/scraper...")
                return callback(driver)
            return driver
        return None

    if background:
        stop_event = threading.Event()
        thread = threading.Thread(
            target=_job,
            args=(stop_event,),
            name=f"ScheduledLogin-{target_dt.strftime('%H%M%S')}",
            daemon=True
        )
        thread.start()
        log_activity(f"[Scheduler] Background login scheduled for {target_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        return thread, stop_event
    else:
        return _job()


def scheduled_recurring_login(
    time_of_day: Union[str, dtime],
    interval_days: int = 1,
    login_func: Optional[Callable[..., Any]] = None,
    callback: Optional[Callable[[Any], Any]] = None,
    background: bool = False,
    max_runs: Optional[int] = None,
    **login_kwargs
) -> Any:
    """
    Plug-and-play function to run automated login repeatedly every day at a specific time (e.g. '08:00').

    Parameters:
      time_of_day: Daily target time, e.g. "08:00", "08:00 AM", or time(8, 0).
      interval_days: Days between runs (default: 1 day).
      login_func: Login function to execute (defaults to automated_login).
      callback: Optional scraper callback executed after each login: callback(driver).
      background: If True, runs in a background thread and returns (thread, stop_event).
      max_runs: Maximum number of executions (None for infinite).
    """
    if login_func is None:
        from run_automation import automated_login
        login_func = automated_login

    def _loop(stop_ev: Optional[threading.Event] = None):
        run_count = 0
        while True:
            if stop_ev and stop_ev.is_set():
                break
            if max_runs is not None and run_count >= max_runs:
                log_activity(f"[Scheduler] Reached maximum runs ({max_runs}). Exiting recurring schedule.")
                break

            target_dt = parse_target_time(time_of_day)
            reached = wait_until(target_dt, stop_event=stop_ev)
            if not reached:
                break

            log_activity(f"[Scheduler] Executing scheduled login run #{run_count + 1}...")
            try:
                driver = login_func(**login_kwargs)
                if callback and callable(callback):
                    log_activity("[Scheduler] Executing post-login callback/scraper...")
                    callback(driver)
            except Exception as e:
                log_activity(f"[Scheduler Error] Recurring run #{run_count + 1} failed: {e}", level="ERROR")

            run_count += 1
            time.sleep(2)

    if background:
        stop_event = threading.Event()
        thread = threading.Thread(
            target=_loop,
            args=(stop_event,),
            name=f"RecurringLogin-{str(time_of_day)}",
            daemon=True
        )
        thread.start()
        log_activity(f"[Scheduler] Recurring login active every {interval_days} day(s) at {time_of_day}")
        return thread, stop_event
    else:
        return _loop()


def scheduled_interval_login(
    interval_minutes: int,
    run_immediately: bool = True,
    login_func: Optional[Callable[..., Any]] = None,
    callback: Optional[Callable[[Any], Any]] = None,
    background: bool = False,
    max_runs: Optional[int] = None,
    **login_kwargs
) -> Any:
    """
    Plug-and-play function to run automated login every N minutes.
    """
    if login_func is None:
        from run_automation import automated_login
        login_func = automated_login

    interval_sec = interval_minutes * 60

    def _loop(stop_ev: Optional[threading.Event] = None):
        run_count = 0
        if run_immediately:
            log_activity(f"[Scheduler] Running initial automated login...")
            try:
                driver = login_func(**login_kwargs)
                if callback and callable(callback):
                    log_activity("[Scheduler] Executing post-login callback/scraper...")
                    callback(driver)
            except Exception as e:
                log_activity(f"[Scheduler Error] Initial login failed: {e}", level="ERROR")
            run_count += 1

        while True:
            if stop_ev and stop_ev.is_set():
                break
            if max_runs is not None and run_count >= max_runs:
                break

            target_dt = datetime.now() + timedelta(seconds=interval_sec)
            reached = wait_until(target_dt, stop_event=stop_ev)
            if not reached:
                break

            log_activity(f"[Scheduler] Executing interval login #{run_count + 1}...")
            try:
                driver = login_func(**login_kwargs)
                if callback and callable(callback):
                    log_activity("[Scheduler] Executing post-login callback/scraper...")
                    callback(driver)
            except Exception as e:
                log_activity(f"[Scheduler Error] Interval login #{run_count + 1} failed: {e}", level="ERROR")
            run_count += 1

    if background:
        stop_event = threading.Event()
        thread = threading.Thread(
            target=_loop,
            args=(stop_event,),
            name=f"IntervalLogin-{interval_minutes}m",
            daemon=True
        )
        thread.start()
        log_activity(f"[Scheduler] Interval login active every {interval_minutes} minutes")
        return thread, stop_event
    else:
        return _loop()
