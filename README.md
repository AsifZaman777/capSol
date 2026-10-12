### Web Auto-Login Framework with Offline AI CAPTCHA Solver

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.0%2B-43B02A.svg)](https://www.selenium.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C.svg)](https://pytorch.org/)
[![HuggingFace](https://img.shields.io/badge/Model-TrOCR-yellow.svg)](https://huggingface.co/anuashok/ocr-captcha-v3)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An intelligent, zero-click browser automation framework built with **Python**, **Selenium**, and **TrOCR (Vision-Encoder-Decoder)**.

Credentials and settings are loaded directly from `.env` with **zero popup dialogs and no manual clicks**. Includes plug-and-play functions for **immediate logins**, **scheduled logins at a specific time**, and **recurring daily schedules**.

---

#### ✨ Features

- **⚡ Zero-Click Plug-and-Play**: Credentials and target URLs load seamlessly from `.env` (or function arguments). No popups or manual user interaction required.
- **⏰ Flexible Scheduling Engine**: Schedule logins at specific times (e.g. `16:30`, `04:30 PM`, `+45m`, or `2026-10-12 18:00`), recurring daily schedules, or recurring intervals.
- **🌐 Generic Link Support**: Heuristic engine that automatically detects login fields (username, password, captcha image, captcha input, and submit buttons) on any generic website without hardcoded selectors.
- **🧠 100% Offline AI CAPTCHA Solver**: Utilizes [anuashok/ocr-captcha-v3](https://huggingface.co/anuashok/ocr-captcha-v3) TrOCR model stored locally on disk. Fast, zero API costs, and immune to Hugging Face Hub rate limits.
- **🎯 Site Profile Support**: Register precise selectors for specific target websites (e.g. custom corporate or merchant portals) with automatic fallback to generic heuristics.
- **🔒 Session & 2FA Persistence**: Keeps the Chrome browser open with `detach: True`, allowing seamless transition to manual OTP/SMS two-factor verification or dashboard inspection.

---

#### 📁 Project Structure

```text
├── models/
│   └── ocr-captcha-v3/        # Offline TrOCR model weights & configurations
├── model-rnd/
│   └── model_benchmark.png    # Accuracy comparison chart across evaluated models
├── images/
│   └── temp_captcha.png       # Scratch storage for captured CAPTCHAs
├── logs/                      # Date-stamped daily activity logs (auto-rotated)
├── framework.py               # Generic automation engine & DOM heuristics
├── scheduler.py               # Plug-and-play scheduling engine (one-time & recurring)
├── logger.py                  # Daily timestamped activity logger (logs/activity_YYYY-MM-DD.log)
├── captcha_solver.py          # Offline TrOCR inference module
├── download_model.py          # Utility script to pre-cache the OCR model
├── run_automation.py          # Plug-and-play orchestrator & CLI entry point
├── requirements.txt           # Project dependencies
├── .env.example               # Example environment file
└── README.md
```

---

#### 🔬 HF Model Benchmarks (R&D)

To select the most robust OCR engine for diverse real-world CAPTCHAs, an extensive empirical benchmark was conducted across multiple Vision-Encoder-Decoder models on 21 challenging CAPTCHA variants (covering warped fonts, strike lines, speckle noise, drop shadows, low contrast, and alternating cases).

The full experimental workflow, predictions, and evaluation code are documented in:  
📄 **[`Captcha_breaker_RnD.ipynb`](Captcha_breaker_RnD.ipynb)**

### 📊 Benchmark Comparison (Exact Match Accuracy)

<p align="center">
  <img src="model-rnd/model_benchmark.png" alt="Model Accuracy Comparison" width="650"/>
</p>

| Model                     | Hugging Face Repository                                                                                 | Exact Match Accuracy | Evaluation Insights                                                                                                                                                             |
| :------------------------ | :------------------------------------------------------------------------------------------------------ | :------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Base Model (Selected)** | [`anuashok/ocr-captcha-v3`](https://huggingface.co/anuashok/ocr-captcha-v3)                             |      **28.57%**      | **Highest overall accuracy.** Exhibits superior generalization across varied font weights, noise speckles, and distorted characters. Selected as the framework's default model. |
| **FT Model 1**            | [`dathuynh1108/ocr-captcha-v3-finetuned`](https://huggingface.co/dathuynh1108/ocr-captcha-v3-finetuned) |        23.81%        | Competitive on standard alphanumeric strings but suffered degradation on heavy background noise and stroke artifacts.                                                           |
| **FT Model 2**            | [`emelnov/ocr-captcha-v4-mailru`](https://huggingface.co/emelnov/ocr-captcha-v4-mailru)                 |        9.52%         | Specialized primarily for Mail.ru CAPTCHA formats; struggled with mixed casing and complex multi-word distortions.                                                              |

---

### 🚀 Quick Start

#### 1. Clone the Repository & Install Dependencies

```bash
git clone https://github.com/your-username/local_automation.git
cd local_automation

# Create & activate virtual environment
python -m venv venv
venv\Scripts\activate      # On Windows
# source venv/bin/activate # On macOS/Linux

pip install -r requirements.txt
```

#### 2. Configure Credentials in `.env`

Copy `.env.example` to `.env` and fill in your credentials:

```env
LOGIN_URL=https://example.com/login
MERCHANT_ID=demo_user_123
MERCHANT_PASSWORD=demo_secure_password
HEADLESS=false
AUTO_CAPTCHA=true
```

#### 3. Cache Model Locally (Offline Use)

```bash
python download_model.py
```

---

### 💻 Plug-and-Play Usage

#### Option A: Run from Command Line (CLI)

```bash
# 1. Run immediately (takes credentials from .env, zero clicks!)
python run_automation.py

# 2. Schedule login at a specific time today (e.g. 16:30 or 4:30 PM)
python run_automation.py --schedule "16:30"

# 3. Schedule relative delay (e.g. 45 minutes from now)
python run_automation.py --schedule "+45m"

# 4. Schedule recurring daily login (e.g. 9:00 AM every morning)
python run_automation.py --daily "09:00"

# 5. Run headless in the background
python run_automation.py --headless
```

#### Option B: Plug into Your Own Python Scripts

```python
from run_automation import (
    automated_login,
    scheduled_login,
    scheduled_recurring_login
)

# 1. Immediate automated login (reads credentials from .env)
driver = automated_login()

# 2. Immediate automated login with explicit credentials
driver = automated_login(
    url="https://example.com/login",
    username="my_username",
    password="my_password",
    headless=True
)

# 3. Scheduled login at a particular time
scheduled_login(target_time="16:30")

# 4. Scheduled login in background thread (non-blocking)
thread, stop_event = scheduled_login(target_time="04:30 PM", background=True)

# 5. Recurring daily login at 08:00 AM with custom scraper callback
def my_scraper(driver):
    print("Scraping daily reports with authenticated driver...")
    driver.get("https://example.com/reports")
    # extract data...
    driver.quit()

scheduled_recurring_login(time_of_day="08:00", callback=my_scraper)
```

---

### 📝 Daily Activity Logging & Audit Trail

The framework automatically records all activities, timestamps, scheduler events, CAPTCHA solutions, and errors in a date-stamped log file:

📁 **`logs/activity_YYYY-MM-DD.log`**

- **Auto-Rotation**: Rotates to a new file automatically each midnight (`activity_2026-10-12.log`, `activity_2026-10-13.log`, etc.).
- **Dual Output**: Streams clean logs to both console stdout and disk concurrently.
- **Sample Log Entry**:
  ```text
  [2026-10-12 08:00:00] [INFO] [Scheduler] 🔔 Target time reached: 2026-10-12 08:00:00
  [2026-10-12 08:00:01] [INFO] [Run] Target URL   : https://example.com/login
  [2026-10-12 08:00:01] [INFO] [Run] Username     : dem***
  [2026-10-12 08:00:02] [INFO] [Framework] Navigating to: https://example.com/login
  [2026-10-12 08:00:04] [INFO] [Framework] Locating input fields...
  [2026-10-12 08:00:05] [INFO] [Framework] Entering credentials (dem***)...
  [2026-10-12 08:00:06] [INFO] [Framework] CAPTCHA detected on page.
  [2026-10-12 08:00:07] [INFO] [Framework] Solved CAPTCHA: '4892' (Raw: '4892')
  [2026-10-12 08:00:09] [INFO] [Framework] Login completed successfully.
  [2026-10-12 08:00:10] [INFO] [Scheduler] Executing post-login callback/scraper...
  ```

---

### 🛠️ How Generic Link Heuristics Work

When an unfamiliar URL is passed to the framework, the heuristic engine resolves elements dynamically:

| Element           | Heuristic Strategy                                                                                                                              |
| :---------------- | :---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Password**      | Detects the primary visible `input[type='password']` element.                                                                                   |
| **Username**      | Evaluates preceding visible inputs relative to the password field, followed by common attributes (`name="user"`, `id="login"`, `type="email"`). |
| **CAPTCHA Image** | Scans for image/canvas tags matching `captcha`, `capture`, or `setCapture` keywords with valid display dimensions.                              |
| **CAPTCHA Input** | Identifies text inputs associated with captcha keywords or adjacent to the captcha image.                                                       |
| **Submit Button** | Searches for submit buttons inside the form, button text matching `Login` / `Sign In` / `Submit`, or sends the `ENTER` key.                     |

---

### ⚙️ Adding Custom Site Profiles

To register explicit selectors for a specific website, add a `SiteProfile`:

```python
from framework import GenericLoginFramework, SiteProfile, By

my_site = SiteProfile(
    name="My Custom Portal",
    url_identifier="myportal.com",
    user_selector=(By.ID, "username"),
    pass_selector=(By.ID, "password"),
    captcha_img_selector=(By.ID, "captcha-img"),
    captcha_input_selector=(By.ID, "captcha-code"),
    submit_selector=(By.CSS_SELECTOR, "button.btn-login")
)

framework = GenericLoginFramework()
framework.register_profile(my_site)
```

---

### ⚖️ Disclaimer & Ethical Use Notice

> [!WARNING]
> **Strictly for Educational, Learning, and Legitimate Personal Automation Purposes Only.**
>
> - The CAPTCHA recognition functionality is provided strictly as a technical demonstration of OCR and deep learning models (TrOCR) integrated with browser automation workflows.
> - **Do NOT use this tool for unethical, unauthorized, or malicious actions**, including but not limited to credential stuffing, unauthorized data harvesting, bypassing security safeguards on third-party services without permission, or violating any website's Terms of Service (ToS).
> - The author is not responsible for any misuse, account suspensions, or legal liabilities arising from the use or modification of this project. Always ensure you have authorization before automating interactions with any web application.

---

#### 🛡️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
