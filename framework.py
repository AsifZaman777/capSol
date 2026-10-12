"""
==============================================================================
FILE HISTORY CARD
------------------------------------------------------------------------------
File:           framework.py
Author:         Asif Zaman
Created:        2026-10-12
Responsibility: Core automation engine and DOM heuristics layer. Manages Selenium
                Chrome WebDriver lifecycle, site profile matching, heuristic
                discovery of login elements (username, password, captcha, submit),
                and end-to-end login flow execution while keeping browser detached.
==============================================================================
"""

import os
import time
from typing import Optional, Tuple, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from captcha_solver import CaptchaSolver
from logger import log_activity

class SiteProfile:
    """Pre-configured selectors for specific websites."""
    def __init__(
        self,
        name: str,
        url_identifier: str,
        user_selector: Optional[Tuple[By, str]] = None,
        pass_selector: Optional[Tuple[By, str]] = None,
        captcha_img_selector: Optional[Tuple[By, str]] = None,
        captcha_input_selector: Optional[Tuple[By, str]] = None,
        submit_selector: Optional[Tuple[By, str]] = None
    ):
        self.name = name
        self.url_identifier = url_identifier
        self.user_selector = user_selector
        self.pass_selector = pass_selector
        self.captcha_img_selector = captcha_img_selector
        self.captcha_input_selector = captcha_input_selector
        self.submit_selector = submit_selector

class GenericLoginFramework:
    """
    Automated Login Framework.
    Supports registered site profiles and generic links via DOM heuristics.
    """
    def __init__(self, headless: bool = False, timeout: int = 12):
        self.headless = headless
        self.timeout = timeout
        self.profiles: Dict[str, SiteProfile] = {}
        self.captcha_solver = CaptchaSolver()
        self._register_default_profiles()

    def _register_default_profiles(self):
        """Registers default profiles with verified selectors."""
        sample_profile = SiteProfile(
            name="Sample Portal",
            url_identifier="example-portal.com",
            user_selector=(By.ID, "user"),
            pass_selector=(By.ID, "passwd"),
            captcha_img_selector=(By.XPATH, "//form[@id='loginform']//img | //img[contains(@src, 'captcha')]"),
            captcha_input_selector=(By.ID, "captcha"),
            submit_selector=(By.ID, "submit")
        )
        self.register_profile(sample_profile)

    def register_profile(self, profile: SiteProfile):
        self.profiles[profile.url_identifier.lower()] = profile

    def match_profile(self, url: str) -> Optional[SiteProfile]:
        for identifier, profile in self.profiles.items():
            if identifier in url.lower():
                return profile
        return None

    def initialize_driver(self) -> webdriver.Chrome:
        """Configures Chrome WebDriver to keep session open after script finishes."""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        else:
            chrome_options.add_experimental_option("detach", True)

        return webdriver.Chrome(options=chrome_options)

    # ---------------- Element Locators ---------------- #

    def find_password_field(self, driver: webdriver.Chrome, profile: Optional[SiteProfile] = None) -> WebElement:
        if profile and profile.pass_selector:
            return WebDriverWait(driver, self.timeout).until(EC.visibility_of_element_located(profile.pass_selector))

        # Generic heuristics
        selectors = [
            "//input[@type='password' and not(@disabled)]",
            "//input[contains(translate(@name, 'PASS', 'pass'), 'pass') and not(@type='hidden')]",
            "//input[contains(translate(@id, 'PASS', 'pass'), 'pass') and not(@type='hidden')]"
        ]
        for xpath in selectors:
            for el in driver.find_elements(By.XPATH, xpath):
                if el.is_displayed():
                    return el

        raise Exception("Unable to locate a visible password field on this page.")

    def find_username_field(self, driver: webdriver.Chrome, password_element: WebElement, profile: Optional[SiteProfile] = None) -> WebElement:
        if profile and profile.user_selector:
            return WebDriverWait(driver, self.timeout).until(EC.visibility_of_element_located(profile.user_selector))

        # Heuristic 1: Preceding input before the password field
        try:
            preceding_inputs = password_element.find_elements(
                By.XPATH, 
                "./preceding::input[not(@type='hidden') and not(@type='password') and not(@type='submit') and not(@type='button') and not(@type='checkbox') and not(@type='radio')]"
            )
            for el in reversed(preceding_inputs):
                if el.is_displayed() and el.is_enabled():
                    return el
        except Exception:
            pass

        # Heuristic 2: Standard username/login identifiers
        common_xpaths = [
            "//input[@type='text' or @type='email' or not(@type)][contains(translate(@name, 'USER', 'user'), 'user') or contains(translate(@name, 'LOGIN', 'login'), 'login') or contains(translate(@name, 'EMAIL', 'email'), 'email')]",
            "//input[contains(translate(@id, 'USER', 'user'), 'user') or contains(translate(@id, 'LOGIN', 'login'), 'login') or contains(translate(@id, 'EMAIL', 'email'), 'email')]",
            "//input[@type='email']",
            "//input[@type='text' and not(@type='hidden')]"
        ]
        for xpath in common_xpaths:
            for el in driver.find_elements(By.XPATH, xpath):
                if el.is_displayed() and el.is_enabled():
                    return el

        raise Exception("Unable to locate a visible username or login field.")

    def find_captcha_elements(self, driver: webdriver.Chrome, profile: Optional[SiteProfile] = None) -> Tuple[Optional[WebElement], Optional[WebElement]]:
        """Returns (captcha_image, captcha_input) if detected; otherwise (None, None)."""
        if profile and profile.captcha_img_selector and profile.captcha_input_selector:
            try:
                img = WebDriverWait(driver, 3).until(EC.visibility_of_element_located(profile.captcha_img_selector))
                inp = WebDriverWait(driver, 3).until(EC.visibility_of_element_located(profile.captcha_input_selector))
                return img, inp
            except Exception:
                pass

        # Heuristics for CAPTCHA image
        img_xpaths = [
            "//img[contains(translate(@src, 'CAPTCHA', 'captcha'), 'captcha') or contains(translate(@src, 'CAPTURE', 'capture'), 'capture') or contains(@src, 'setCapture')]",
            "//img[contains(translate(@id, 'CAPTCHA', 'captcha'), 'captcha') or contains(translate(@class, 'CAPTCHA', 'captcha'), 'captcha') or contains(translate(@alt, 'CAPTCHA', 'captcha'), 'captcha')]",
            "//canvas[contains(translate(@id, 'CAPTCHA', 'captcha'), 'captcha')]"
        ]
        found_img = None
        for xpath in img_xpaths:
            for img in driver.find_elements(By.XPATH, xpath):
                if img.is_displayed() and img.size['width'] > 20 and img.size['height'] > 15:
                    found_img = img
                    break
            if found_img:
                break

        # Heuristics for CAPTCHA input field
        input_xpaths = [
            "//input[contains(translate(@name, 'CAPTCHA', 'captcha'), 'captcha') or contains(translate(@id, 'CAPTCHA', 'captcha'), 'captcha')]",
            "//input[contains(translate(@name, 'CAPTURE', 'capture'), 'capture') or contains(translate(@id, 'CAPTURE', 'capture'), 'capture')]",
            "//input[contains(translate(@placeholder, 'CAPTCHA', 'captcha'), 'captcha') or contains(translate(@placeholder, 'SECURITY', 'security'), 'security') or contains(translate(@placeholder, 'CODE', 'code'), 'code')]"
        ]
        found_input = None
        for xpath in input_xpaths:
            for inp in driver.find_elements(By.XPATH, xpath):
                if inp.is_displayed() and inp.is_enabled():
                    found_input = inp
                    break
            if found_input:
                break

        return found_img, found_input

    def find_submit_button(self, driver: webdriver.Chrome, profile: Optional[SiteProfile] = None) -> Optional[WebElement]:
        if profile and profile.submit_selector:
            try:
                return WebDriverWait(driver, self.timeout).until(EC.element_to_be_clickable(profile.submit_selector))
            except Exception:
                pass

        selectors = [
            "//form//button[@type='submit']",
            "//form//input[@type='submit']",
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(translate(., 'LOGIN', 'login'), 'login') or contains(translate(., 'SIGN IN', 'sign in'), 'sign in') or contains(translate(., 'SUBMIT', 'submit'), 'submit')]",
            "//input[@type='button' and (contains(translate(@value, 'LOGIN', 'login'), 'login') or contains(translate(@value, 'SIGN IN', 'sign in'), 'sign in'))]"
        ]
        for xpath in selectors:
            for btn in driver.find_elements(By.XPATH, xpath):
                if btn.is_displayed() and btn.is_enabled():
                    return btn

        return None

    # ---------------- Login Workflow ---------------- #

    def login(self, url: str, username: str, password: str, auto_captcha: bool = True) -> Optional[webdriver.Chrome]:
        """Executes the complete login workflow."""
        driver = None
        try:
            driver = self.initialize_driver()
            if auto_captcha:
                self.captcha_solver.warmup()

            profile = self.match_profile(url)
            site_label = f"profile: '{profile.name}'" if profile else "Generic DOM Heuristics"
            log_activity(f"[Framework] Running with {site_label}")

            log_activity(f"[Framework] Navigating to: {url}")
            driver.get(url)

            # 1. Locate fields
            log_activity("[Framework] Locating input fields...")
            pass_elem = self.find_password_field(driver, profile)
            user_elem = self.find_username_field(driver, pass_elem, profile)

            # 2. Enter credentials
            masked_user = f"{username[:3]}***" if len(username) > 3 else "***"
            log_activity(f"[Framework] Entering username ({masked_user})...")
            user_elem.clear()
            user_elem.send_keys(username)

            log_activity("[Framework] Entering password...")
            pass_elem.clear()
            pass_elem.send_keys(password)

            # 3. Handle CAPTCHA if detected
            captcha_img, captcha_input = self.find_captcha_elements(driver, profile)
            if captcha_img and captcha_input:
                log_activity("[Framework] CAPTCHA detected on page.")
                if auto_captcha:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    temp_captcha_path = os.path.join(base_dir, "images", "temp_captcha.png")
                    os.makedirs(os.path.dirname(temp_captcha_path), exist_ok=True)

                    log_activity("[Framework] Capturing CAPTCHA...")
                    captcha_img.screenshot(temp_captcha_path)

                    predicted_digits, raw = self.captcha_solver.solve_image(temp_captcha_path)
                    log_activity(f"[Framework] Solved CAPTCHA: '{predicted_digits}' (Raw: '{raw}')")

                    captcha_input.clear()
                    captcha_input.send_keys(predicted_digits)
            else:
                log_activity("[Framework] No CAPTCHA found on page.")

            # 4. Submit form
            log_activity("[Framework] Submitting login form...")
            submit_btn = self.find_submit_button(driver, profile)
            if submit_btn:
                submit_btn.click()
            else:
                target_field = captcha_input if (captcha_img and captcha_input) else pass_elem
                target_field.send_keys(Keys.ENTER)

            # 5. Post-submit status
            time.sleep(3)
            log_activity(f"[Framework] Current URL: {driver.current_url}")
            log_activity(f"[Framework] Page Title: {driver.title}")

            otp_found = driver.find_elements(By.XPATH, "//input[contains(translate(@id, 'OTP', 'otp'), 'otp') or contains(translate(@name, 'OTP', 'otp'), 'otp')]")
            if otp_found:
                log_activity("[Framework] OTP / 2FA screen detected. Browser remains open for manual verification.", level="WARNING")
            else:
                log_activity("[Framework] Login completed successfully.")

            return driver

        except Exception as e:
            log_activity(f"[Framework Error] {e}", level="ERROR")
            if driver:
                log_activity("[Framework] Browser is kept open for manual inspection.", level="WARNING")
            return driver


# ---------------- Plug-and-Play Convenience Aliases ---------------- #

def automated_login(*args, **kwargs):
    """Zero-click automated login taking credentials directly from .env."""
    from run_automation import automated_login as _al
    return _al(*args, **kwargs)


def scheduled_login(*args, **kwargs):
    """Schedule automated login at a specific time (e.g. '16:30', '4:30 PM', '+30m')."""
    from scheduler import scheduled_login as _sl
    return _sl(*args, **kwargs)


def scheduled_recurring_login(*args, **kwargs):
    """Schedule recurring daily login at a given time of day."""
    from scheduler import scheduled_recurring_login as _srl
    return _srl(*args, **kwargs)


__all__ = [
    "SiteProfile",
    "GenericLoginFramework",
    "automated_login",
    "scheduled_login",
    "scheduled_recurring_login",
    "log_activity"
]

