from pathlib import Path
from PIL import Image
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from slow_webserver import SlowWebServer
import logging
import os
import pytest
import tempfile
import time
import urllib.parse

# delay some actions so a human can follow-along for visual debugging
HUMAN_WAIT_TIME = 0.5
# global to configure saving screenshots
SAVE_SCREENSHOTS = True

TEST_COFFEES = ["el valle", "tater heap", "epauli", "liso"]


def is_element_visible_in_viewpoint(driver, element):
    """
    Determine if an element is in view of the web browser using JavaScript
    This function from https://stackoverflow.com/a/63656230
    NOTE: This function is licensed under CC SA 4.0 terms per Stack Overflow's
          licensing page https://stackoverflow.com/help/licensing
    """
    return driver.execute_script("""var elem = arguments[0],
                                    box = elem.getBoundingClientRect(),
                                    cx = box.left + box.width / 2,
                                    cy = box.top + box.height / 2,
                                    e = document.elementFromPoint(cx, cy);
                                    for (; e; e = e.parentElement) {
                                      if (e === elem)
                                        return true;
                                    }
                                    return false;
                                 """, element)


def bring_element_into_view(element):
    """
    Try to bring an element into the viewport by sending the element the home-key
    From https://stackoverflow.com/a/48731548
    ;param element - a Selenium object
    ;returns: None
    """
    # Use home key on default_image element to center it on the screen; side effect of hitting the home key is it
    # centers on the screen -- however Selenium errors as images don't accept typing
    try:
        element.send_keys(Keys.HOME)
    except ElementNotInteractableException:
        pass


@pytest.mark.parametrize("default_image_src_parameter, coffee_name_parameter", zip(("bag%20dance/default.png",)*len(TEST_COFFEES), TEST_COFFEES))
def test_image_rollover_present(driver_fixture, base_url_fixture, default_image_src_parameter, coffee_name_parameter):
    """
    Test HTML for the rollover image, image map and that we are moused on the image area
    :param driver_fixture: The Selenium webdriver object (provided by a Pytest Fixture)
    :param base_url_fixture: The webpage URL that was loaded (provided by a Pytest Fixture)
    :param default_image_src_parameter: The image map default IMG SRC value from Pytest parameterization
    :param coffee_name_parameter: The coffee name to be testing from Pytest parameterization
    :return:
    """
    time.sleep(HUMAN_WAIT_TIME)
    # We are looking for the default image of a roll-over image map (note pre-caching may mean the roll-over images are nowhere in the DOM on initial load)
    default_image = driver_fixture.find_element(By.XPATH, f'//img[@src="{default_image_src_parameter}"]')
    try:
        # Verify image we are rolling over to is not visible -- may be pre-cached though (css hidden attribute and/or 0 size)
        coffee_image = driver_fixture.find_element(By.XPATH, f'//img[@src="bag%20dance/{urllib.parse.quote(coffee_name_parameter)}.png"]')
        logging.getLogger("auspicious.test_image_rollover_present").info(f'Coffee image: {coffee_image.get_attribute("src")}')
        logging.getLogger("auspicious.test_image_rollover_present").info(
            f"On URL: {driver_fixture.current_url}; default image is displayed: {default_image.is_displayed()} , mouse_over_image is displayed: {coffee_image.is_displayed()}")
    except NoSuchElementException:
        logging.getLogger("auspicious.test_image_rollover_present").info(
            f"On URL: {driver_fixture.current_url}; default image is displayed: {default_image.is_displayed()} , mouse_over_image is displayed: Not found in DOM -- not doing pre-caching")

    bring_element_into_view(default_image)

    # Code to query for the element to be loaded -- unnecessary for our use-case it turns out; would be good if using AJAX to inject the image
    # while not is_element_visible_in_viewpoint(driver, default_image):
    #     print("Waiting for JavaScript to see element is loaded")
    #     time.sleep(HUMAN_WAIT_TIME)
    # element = WebDriverWait(driver, 5).until(
    #    EC.visibility_of_element_located((By.XPATH, '//img[@src="bag%20dance/tater%20heap.png"]'))
    # )


@pytest.mark.parametrize("coffee_name_parameter", TEST_COFFEES)
def test_coffee(driver_fixture, base_url_fixture, coffee_name_parameter):
    """
    Test HTML for mouse-over code to determine we can move from a default image to a specific coffee
    :param driver_fixture: The Selenium webdriver object (provided by a Pytest Fixture)
    :param base_url_fixture: The webpage URL that was loaded (provided by a Pytest Fixture)
    :param coffee_name_parameter: The coffee name lower case and with spaces (i.e. "tater heap")
    :return: success or raises on failure
    """
    default_image_src = "bag%20dance/default.png"
    default_image = driver_fixture.find_element(By.XPATH, f'//img[@src="{default_image_src}"]')
    bring_element_into_view(default_image)

    # Format for all our image's alt attribute
    alt_tag_text = f"A picture highlighting {coffee_name_parameter.title()} coffee"
    # coffee names may have spaces; URL escape the name, as our test webpage does
    escaped_coffee_name = urllib.parse.quote(coffee_name_parameter)

    # mouse-over the image; note the arbitrary coordinates are taken from the image-map's HTML (take the average to ensure we're in bounds)
    # HTML element is:
    # <area alt="tater heap" title="" shape="rect" coords="476,175,585,400" onmouseover="updateimage('Tater Heap')" onmouseleave="defaultimage()" href="#tater_heap"/>
    area = driver_fixture.find_element(By.XPATH, f'//area[@alt="{alt_tag_text}"]')
    coords = area.get_attribute("coords").split(",")
    avg_coords = (((int(coords[0])+int(coords[2]))/2), (int(coords[1])+int(coords[3]))/2)
    logging.getLogger("auspicious.test_coffee").info(f"Found area: {area.get_property('alt')}; coords: {area.get_property('coords')}; avg: {avg_coords} onmouseover: {area.get_property('href')}")
    # Note: the average coordinates each have one added to them (list comprehension) and the resultant two-item list passed in for two parameters
    ActionChains(driver_fixture).move_to_element_with_offset(default_image, *[i for i in avg_coords]).click().perform()

    time.sleep(HUMAN_WAIT_TIME)

    # assert that we are at the URL with an HTML anchor tag of the (URL escaped) coffee's name
    assert driver_fixture.current_url == os.path.join(base_url_fixture, "#" + escaped_coffee_name)

    if SAVE_SCREENSHOTS:
        # here we parse the URL which is an anchor to the specific coffee
        file_name = os.path.join(os.environ["TMPDIR"], os.path.basename(driver_fixture.current_url.partition("#")[2])) + ".png"
        driver_fixture.save_screenshot(file_name)
        logging.getLogger("auspicious.test_coffee").info(f"Screenshot writing: '{file_name}'")
        show_screenshot(coffee_name_parameter)
    time.sleep(HUMAN_WAIT_TIME)


@pytest.fixture(scope="session", autouse=True)
def driver_fixture():
    """
    Fixture to instantiate the Selenium driver
    :return: Selenium Webdriver
    """
    with tempfile.TemporaryDirectory(dir=str(Path.home())) as tmpdir:
        # Selenium will load its own Firefox temporary profile from the OS'es temporary directory
        # work around running in a FlatPack/AppImage/Snap install where /tmp is inaccessible by creating an explicit tmpdir
        logging.getLogger("auspicious.driver_fixture").info(f"Using tmp dir: {tmpdir}")
        os.environ["TMPDIR"] = tmpdir

        options = FirefoxOptions()
        # Set the browser page to a standardized size (helps ensure
        options.add_argument("--width=500")
        options.add_argument("--height=500")
        _driver = webdriver.Firefox(options=options,
                                    executable_path=os.path.join(os.path.dirname(__file__), 'geckodriver'))
        _driver.maximize_window()

        yield _driver

        # close the web browser driver
        _driver.close()


def show_screenshot(coffee):
    file_path = os.path.join(os.environ["TMPDIR"], os.path.basename(urllib.parse.quote(coffee)) + ".png")
    logging.getLogger("auspicious.show_screenshot").info(f"Reading: '{file_path}'")
    screenshot = Image.open(file_path)
    screenshot.show()


@pytest.fixture(scope="class", autouse=True)
def base_url_fixture(driver_fixture: webdriver, web_server_fixture: SlowWebServer):
    """
    Simple fixture to load a webpage and print the title
    :param driver_fixture: Selenium web driver (provided by a Pytest Fixture)
    :param url: The URL to load
    :return: None - will raise if page load fails
    """
    testURL = f"http://{web_server_fixture.ADDRESS}:{web_server_fixture.PORT}/webpages"
    driver_fixture.get(testURL)

    # Print webpage title
    logging.getLogger("auspicious.base_url").info(f"Page Title: {driver_fixture.title}")
    return (testURL)


@pytest.fixture(scope="session", autouse=True)
def web_server_fixture():
    """
    Pytest fixture to yield our artificially slow webserver
    Uses Python Context Manager (https://docs.python.org/3/reference/datamodel.html#context-managers) to exit and close
    the webserver when it goes out-of-scope
    :return:
    """
    with SlowWebServer() as web_server:
        yield web_server


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for module in "SlowSocketWriter" "SlowWebServer" "auspicious":
        logging.getLogger(module).setLevel(logging.DEBUG)
    # give a help message if geckodriver is unavailable
    if not os.path.exists("geckodriver"):
        raise FileNotFoundError("Need file `geckodriver` in $PATH to talk to Firefox. Find Geckodriver at https://github.com/mozilla/geckodriver/releases")
    # enable logging output in running tests
    retcode = pytest.main(["-o", "log_cli=True", "-o", "log_cli_level=INFO", "--show-capture=log", __file__])
