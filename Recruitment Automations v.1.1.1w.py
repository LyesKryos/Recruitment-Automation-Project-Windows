# All Rights Reserved
#
# Copyright (c) 2020 Lies Kryos
#
# Created by Techcable
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import requests
from bs4 import BeautifulSoup
from time import sleep
from time import strftime
import re
from webbrowser import open_new_tab
# winsound omitted on all non-Windows platforms
from winsound import Beep
import logging

# sets up the logging
logging.basicConfig(filename="recruitment_automation_logging.log", level=logging.WARNING,
                    format='%(asctime)s %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

# contains all universal data
class Data:
    sending_to = []
    dont_send_to = []
    add_if_1 = 0
    frequency = 450
    duration = 950


# sanitizes userinput for nation names, replacing spaces with underscores
def sanitize(userinput: str) -> str:
    # replaces user input with proper, url-friendly code
    to_regex = userinput.replace(" ", "_")
    return re.sub(r"[^a-zA-Z0-9_-]", '', to_regex)


# sanitizes userinput for template IDs, replacing "%" with the proper URL code "%25"
def sanitize_links(userinput: str) -> str:
    # replaces user input with proper, url-friendly code
    to_regex = userinput.replace("%", "%25")
    return re.sub(r"(%)", '%', to_regex)


# simple puppet filter, removing all nations with any Arabic number from the sending to list
def numbers_bye(nationinput):
    numbers_found = re.findall(r"\d")
    print(numbers_found)


# the base code function
def code():
    error_count = 0
    while True:
        # gathers user information
        nation_name = input("Input your nation name: ")
        verification = input("Log into your nation, visit https://www.nationstates.net/page=verify_login, and copy-paste "
                             "your verfication code here: ")
        s_nation_name = sanitize(nation_name)
        check = requests.get(
            f"https://www.nationstates.net/cgi-bin/api.cgi?a=verify&nation={s_nation_name}&checksum={verification}")
        check2 = sanitize(check.text)
        sleep(0.6)
        if check2 == "1":
            break
            # breaks out of loop if verification is successful
        else:
            print("Nation verification code failed. Please ensure both nation name and code are correct. Ensure you "
                  "are logged into the correct nation. You may need to regenerate your verification code.")
            logging.warning(f"User verification of nation {nation_name} failed")
            continue
            # continues loop if verification fails or if any other error occurs
    # gathers template ID and cleans it
    template_unclean = input("Input your recruitment template ID here: ")
    template = sanitize_links(template_unclean)
    # creates UA using the nation name and gathers nation's region name
    headers = {"User-Agent": f"{nation_name} (Verified by API)"}
    region_response = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation_name}&q=region",
                                   headers=headers)
    sleep(0.6)
    soup = BeautifulSoup(region_response.text, "lxml")
    region = soup.region.string
    while True:
        response_recruit = requests.get("https://www.nationstates.net/cgi-bin/api.cgi?q=newnations", headers=headers)
        sleep(0.6)
        # grabs the new nations
        soup = BeautifulSoup(response_recruit.text, "lxml")
        if response_recruit.status_code == 429:
            error_count += 1
            if error_count == 2:
                logging.critical("Too many API requests. Program exited safely.")
                exit("Too many requests. Exiting now.")
            print("429 Error: Too many requests. Waiting 15 minutes.")
            sleep(900)
            continue
        try:
            newnations = soup.newnations.string
        except AttributeError:
            print("No new nations. Waiting 60 seconds")
            sleep(60)
            continue
        list_newnations = newnations.split(",")
        # creates list of new nations up to 8 long
        first_eight = (list_newnations[0:8])
        for x in first_eight:
            pattern = r"\d+"
            find_recruit = requests.get(
                f"https://www.nationstates.net/cgi-bin/api.cgi?nation={x}&q=tgcanrecruit;from={region}",
                headers=headers)
            sleep(0.6)
            soup = BeautifulSoup(find_recruit.text, "lxml")
            # checks for recruitment possibility
            try:
                canrecruit = soup.tgcanrecruit.string
            except AttributeError:
                continue
            if canrecruit == "1":
                Data.sending_to.append(x)
                # adds to list if the canrecruit is TRUE
            elif canrecruit == "0":
                # does not add to list if the canrecruit is FALSE
                pass
            if x in Data.dont_send_to:
                # removes any ineligible nations using the already recruited list
                try:
                    Data.sending_to.remove(x)
                except ValueError:
                    pass
            if len(Data.sending_to) == 0:
                break
            # puppet filter
            for nations in Data.sending_to:
                number_present = re.search(pattern, nations)
                if number_present is None:
                    pass
                else:
                    Data.sending_to.remove(nations)
            Data.dont_send_to.append(x)
            # adds nation name to the dont send to list
            seperator = ","
            sending_to_string = seperator.join(Data.sending_to)
            # generates the full list of nations being targeted
        times = strftime("%Y-%m-%d %H:%M:%S")
        if len(Data.sending_to) == 0:
            # adds 30 seconds to the wait time if there are no nations in the queue, giving time for more nations to
            # be generated without burning API calls
            sleep(30)
            continue
        url = f"https://www.nationstates.net/page=compose_telegram?tgto={sending_to_string};message={template}"
        print(f"{times} {len(Data.sending_to)} nations: {url}")
        # generates a beep on Windows platforms. This line is omitted in the Mac OS and Linux editions
        Beep(Data.frequency, Data.duration)
        openlink = input("To open link, hit enter: ")
        if openlink == "":
            # opens the link in a new tab of the default web browser
            open_new_tab(url)
        if len(Data.sending_to) == 1:
            # adds 30 seconds to the wait time if there is only a single nation in the list
            Data.add_if_1 += 30
        sleep(len(Data.sending_to) * 10 + Data.add_if_1)
        # pads the API call time
        Data.sending_to.clear()
        Data.add_if_1 = 0
        if len(Data.dont_send_to) == 100:
            # clears the list if it is 100 items long
            del Data.dont_send_to[50:100]


try:
    code()
except Exception as exception_error:
    logging.critical(f"Program experienced unexpected error. Program terminated with {exception_error}.")




