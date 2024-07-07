import logging
import re
from datetime import datetime
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException


def upload_file(
        driver: WebDriver,
        video_path: str,
        title: str,
        description: str,
        game: str,
        kids: bool,
        upload_time: datetime,
        thumbnail_path: str = None,
):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ytcp-button#create-icon"))).click()
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//tp-yt-paper-item[@test-id="upload-beta"]'))
    ).click()
    video_input = driver.find_element(By.XPATH,'//input[@type="file"]')
    video_input.send_keys(video_path)

    _set_basic_settings(driver, title, description, thumbnail_path)
    _set_advanced_settings(driver, game, kids)
    # Go to visibility settings
    for i in range(3):
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "next-button"))).click()

    _set_time(driver, upload_time)
    _wait_for_processing(driver)
    # Go back to endcard settings
    driver.find_element_by_css_selector("#step-badge-1").click()
    _set_endcard(driver)

    for _ in range(2):
        # Sometimes, the button is clickable but clicking it raises an error, so we add a "safety-sleep" here
        sleep(5)
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "next-button"))).click()

    sleep(5)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "done-button"))).click()

    # Wait for the dialog to disappear
    sleep(5)
    logging.info("Upload is complete")


def _wait_for_processing(driver):
    # Wait for processing to complete
    progress_label: WebElement = driver.find_element_by_css_selector("span.progress-label")
    pattern = re.compile(r"(finished processing)|(processing hd.*)|(check.*)")
    current_progress = progress_label.get_attribute("textContent")
    last_progress = None
    while not pattern.match(current_progress.lower()):
        if last_progress != current_progress:
            logging.info(f'Current progress: {current_progress}')
        last_progress = current_progress
        sleep(5)
        current_progress = progress_label.get_attribute("textContent")


def _set_basic_settings(driver: WebDriver, title: str, description: str, thumbnail_path: str = None):
    title_input: WebElement = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                '//ytcp-mention-textbox[@label="Title"]//div[@id="textbox"]',

            )
        )
    )

    # Input meta data (title, description, etc ... )
    description_input: WebElement = driver.find_element_by_xpath(
        '//ytcp-mention-textbox[@label="Description"]//div[@id="textbox"]'
    )
    thumbnail_input: WebElement = driver.find_element_by_css_selector(
        "input#file-loader"
    )

    title_input.clear()
    title_input.send_keys(title)
    description_input.send_keys(description)
    if thumbnail_path:
        thumbnail_input.send_keys(thumbnail_path)


