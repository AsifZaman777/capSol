from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from transformers import VisionEncoderDecoderModel, TrOCRProcessor
from dotenv import load_dotenv
from PIL import Image
import time
import os

def main():
    # read credentials local .env file
    load_dotenv('.env')
    username = os.getenv("MERCHANT_ID")
    password = os.getenv("MERCHANT_PASSWORD")
    
    if not username or not password:
        print("Error: MERCHANT_ID or MERCHANT_PASSWORD not found in .env file.")
        return

    print(f"Loaded Merchant ID: {username}")

    # TrOCR model preload
    print("Loading OCR model for captcha recognition...")
    processor = TrOCRProcessor.from_pretrained("anuashok/ocr-captcha-v3")
    model = VisionEncoderDecoderModel.from_pretrained("anuashok/ocr-captcha-v3")

    # local selenium web driver configs
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome opens for debugging
    chrome_options.add_experimental_option("detach", True)
    
    print("Initializing Chrome browser...")
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        #sslcommerz merchant login page url
        target_url = "https://merchant.sslcommerz.com/?request=dTFyQWlsb2dpbjp2aWV3dTFyQWk%3D&id=dTFyQWkxdTFyQWk%3D"
        print(f"Navigating to {target_url}...")
        driver.get(target_url)

        #creds input
        print("Locating credential fields...")
        user_input = wait.until(EC.visibility_of_element_located((By.ID, "user")))
        passwd_input = wait.until(EC.visibility_of_element_located((By.ID, "passwd")))

        print("Entering Login ID...")
        user_input.clear()
        user_input.send_keys(username)

        print("Entering Password...")
        passwd_input.clear()
        passwd_input.send_keys(password)

        #read captcha
        print("Locating captcha image...")
        captcha_img = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//form[@id='loginform']//img | //img[contains(@src, 'setCapture')]")
        ))
        
        # save ss to images directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        captcha_path_name = os.path.join(base_dir, "images", "temp_captcha.png")
        captcha_img.screenshot(captcha_path_name)
        print("Captured captcha image.")
        
        image = Image.open(captcha_path_name).convert("RGBA")
        background = Image.new("RGBA", image.size, (255, 255, 255))
        combined = Image.alpha_composite(background, image).convert("RGB")

        pixel_values = processor(combined, return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        predicted_raw = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        predicted_digits = ''.join(c for c in predicted_raw if c.isdigit())[:4]
        print(f"Predicted Captcha: {predicted_digits} (raw: {predicted_raw})")

        # write captcha
        capture_input = wait.until(EC.visibility_of_element_located((By.ID, "capture")))
        capture_input.clear()
        capture_input.send_keys(predicted_digits)

        # auto hit login
        submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "wp-submit")))
        print("Submitting login form...")
        submit_btn.click()

        # drive to the next page
        print("Waiting for page redirection...")
        time.sleep(5)
        
        print(f"Current URL: {driver.current_url}")
        print(f"Page Title: {driver.title}")

        # check the next page 
        otp_inputs = driver.find_elements(By.ID, "otp")
        if otp_inputs:
            print("Notice: OTP verification is required. Chrome remains open for you to enter the OTP.")
        else:
            print("Successfully driven to post-login page! Chrome is kept open.")

    except Exception as e:
        print("An error occurred during automation: ", e)
        print("Chrome is kept open so you can view the state or continue manually.")

    # Note: driver.quit() is intentionally omitted so Chrome stays open!

if __name__ == '__main__':
    main()
