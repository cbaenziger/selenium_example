# Selenium Example

This Python project is a project using [Selenium](https://www.selenium.dev/) to test an example webpage.

I wanted to test that a hand-rolled roll-over image map worked and then found I kept talking to people going through coding boot camps about testing websites. I would recommend that this is likely an out-moded process being I do not write in modern JavaScript frameworks like React, Bootstrap, HTMX, etc.

## Webpage under test
The sample webpage is a bespoke, hand-written HTML page. Some axioms of the webpage's design can be found as [a comment in it](https://github.com/cbaenziger/selenium_example/blob/main/webpages/index.html#L3-L20). See a [running version](https://clayb.net/selenium_example_site/) of the webpage to play with it; see the silly JavaScript roll-over image map there to understand what kicked this Selenium project off.

## Python test code
The project here is mainly [a Python script](./main.py) which kicks off [PyTest](https://docs.pytest.org/en/7.4.x/) and uses Selenium to run some test cases on the webpage.

### Slow Web Server

To provide a means for testing AJAX (in the end not used here), I use an artifically [Slow Web Server](./slow_webserver.py). The Slow Web Server provides the following features:
* Can be throttled to emulate a slow link while testing locally
* See the `BPS` variable for the **bytes** per-second (note BPS in the era of modems were **bits** per-second -- a factor of eight slower)
* The webserver implements a [Python Context Manager](https://docs.python.org/3/reference/datamodel.html#context-managers) so one can use it with the `wtih` statemetnt for easy clean-up.

### PyUnit Features Used
Some PyUnit features and design choices of the tests are:
* Capturing and presenting [Python logging](https://docs.python.org/3/howto/logging.html)
* Creates [PyTest fixtures](https://docs.pytest.org/en/6.2.x/fixture.html) _(I probably should have used the built-ins for temporary directories, rather than rolling my own.)_
* [Parameterizes](https://docs.pytest.org/en/7.1.x/example/parametrize.html) the test-cases
* A configurable `HUMAN_WAIT_TIME` to show tests moving through the webpage in a human-time for debugging

### Selenium Features Used
Some Selenium features and design choices are:
* While not used here, for testing AJAX, a function is included `is_element_visible_in_viewpoint` which shows how one can use JavaScript in Selenium tests. _Thanks to the author in [StackOverflow Question ](https://stackoverflow.com/a/63656230)_
* Here only Firefox is used to test the webpage. Selenium supports many [WebDrivers](https://www.selenium.dev/documentation/webdriver/) and Chrome or other browsers could be used.
* Artifically a 500 pixel by 500 pixel web browser window size is used. _Playing with the web browser image size can affect the tests and of course webpage rendering too_
* As I run in a Linux environment with `/tmp` not shared I have to create a temporary directory for Selenium to use

### Test Cases

The PyUnit test cases leveraging Selenium perform the following simple checks:

* Find the roll over image
* Navigate to the right part of the image map using the HTML alt attribute for the image
* Make sure the image map changes to present the selected coffee
* Clicks the image map to go to the coffee's section of the webpage (using an HTML anchor)
* Takes and displays a screen shot of the final page navigated to
    * Many folks I've talked to have to do this manually when doing manual webpage tests (this could automatically do that and save them to a directory)

## Running the Tests

One can run the test by following these steps (on most Linux distributions):
1. Ensure you have `python3` and `pip` installed
1. Run `pip install -r requirements.txt`
1. Run `python3 ./main.py`
1. Go to https://github.com/mozilla/geckodriver/releases and install the `geckodriver` WebDriver to allow Selenium to talk to Firefox
1. Run `python3 ./main.py` and see the tests run
