#!/usr/bin/env python3

import warnings

from math import exp
from time import sleep
from getpass import getpass
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.webdriver.support.ui import Select

warnings.filterwarnings("ignore", category=DeprecationWarning) 

CANVAS_COURSE_URL = "https://umich.instructure.com/courses/498706/grades"
FLIPIT_HOME = "https://flipitphysics.com"
FLIPIT_GRADES = "https://www.flipitphysics.com/Course/Gradebook?enrollmentID={}"

E = 1690 # Total Extra Credit Points
C = 35
t = E/2

def canvas_login(driver, user, pwd):
    driver.get(CANVAS_COURSE_URL)
    driver.find_elements_by_class_name("um")[0].click()

    driver.find_element_by_id("login").send_keys(user)
    driver.find_element_by_id("password").send_keys(pwd)

    driver.find_element_by_id("loginSubmit").click()

def flipit_login(driver, user, pwd):
    driver.get(FLIPIT_HOME)
    
    driver.find_element_by_id("Email").send_keys(user)
    driver.find_element_by_id("Password").send_keys(pwd)

    driver.find_element_by_id("BTN").click()
    driver.find_elements_by_css_selector("td.wg-course-name div a")[0].click()
    grades_url = FLIPIT_GRADES.format(parse_qs(urlparse(driver.current_url).query)['enrollmentID'][0])
    driver.get(grades_url)

def clean_clicker_points(scores):
    if(len(scores) % 2):
        scores.append('0')
    return sum(min(10, max(int(n) if (n := scores[i]).isdigit() else 0, int(n) if (n := scores[i+1]).isdigit() else 0)) for i in range(0, len(scores), 2))

def scrape_canvas(driver):
    clicker_points = [n[1] for x in driver.find_elements_by_class_name("grade") if len(n := x.text.split("\n")) == 2]

    quiz_grades = clicker_points[-6:]
    final_clicker_points = clean_clicker_points(clicker_points[:-7])

    quiz_totals = [int(n) for x in driver.find_elements_by_css_selector("td.possible.points_possible")[-9:] if (n := x.text)]

    final_quiz_scores = [int(x)/y for x, y in zip(quiz_grades, quiz_totals)]
    final_quiz_scores.remove(min(final_quiz_scores))

    return (sum(final_quiz_scores)/5)*100, final_clicker_points

def scrape_flipit(driver):
    return sum((float(i.text[:-1])/100)*y for x,y in [("pl", 10), ("cp", 10), ("hw", 30)] for i in driver.find_elements_by_css_selector(f"span.gradebook-numberOnly.{x}")) 

def main():
    username = input("Uniqname: ")
    canvas_password = getpass("Canvas Password: ")
    flipit_password = getpass("FlipIt Password: ")

    driver = webdriver.Firefox()
    canvas_login(driver, username, canvas_password)

    while(driver.current_url != CANVAS_COURSE_URL):
        sleep(1)

    Q, s = scrape_canvas(driver)
    flipit_login(driver, f"{username}@umich.edu", flipit_password)
    s += scrape_flipit(driver)
    driver.quit()

    Y = C * (1 - exp(-s/t))
    y = 1 - 0.01*Y

    thresholds = [(82, "A-"), (86, "A"), (96, "A+")]
    F = [4*(((z-Y)/y) - .75*Q) for z in [82, 86, 96]]


    print(f"Quiz Average {Q}")

    print(f"Extra Credit Earned {s}/{E}")
    print(f"Y: {Y} {y}")
    print("Final Grade Requirements: ")
    for letter, grd in zip(thresholds, F):
        print(f"\t{letter[1]}: {grd}") 


if __name__ == "__main__":
    main()
