#%% Importing libraries

import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

# Defining function to parse text output from selenium
def text_parser(i, drop_str):

    data = results[i].text.split("\n")
    data.remove(drop_str)
    data = pd.DataFrame(zip(data[0::2], data[1::2]))
    data["Category"] = drop_str
    return data

#%% Loading list of loan IDs

#investment_history = pd.read_excel("LenDen_INVESTMENT_HISTORY_Dad.xlsx", header = 1, skip_rows = 0)
investment_history = pd.read_excel("LenDen_INVESTMENT_HISTORY_Srungeer.xlsx", header = 1, skip_rows = 0)

#%% Opening lenden club portfolio page using Selenium webdriver

# Initialising a Firefox webdriver
driver = webdriver.Firefox()
driver.get("https://app.lendenclub.com/app/lender/my-investments") # Connecting to loan portfolio page

# Opening lenden club page and logging in

username = driver.find_element_by_name("username")
password = driver.find_element_by_name("password")

#username.send_keys("athreyasa.boda@outlook.com")
#password.send_keys("no5mukil")

username.send_keys("srungeersimha@gmail.com")
password.send_keys("iluvcallofduty")

driver.find_element_by_class_name("login-button").click()
time.sleep(10) # allowing for time to login

#%% Scraping loan details

loan_data_combined = [] # Initiating variable to store loan data

for loanID in investment_history["Loan ID"].unique():

    # URL for loan details
    loanurl = "https://app.lendenclub.com/app/lender/invest/" + loanID

    # Reloading loan details page
    driver.get(loanurl) # Connecting to page
    #time.sleep(5)

    # Executing scrip to scroll down to bottom of page to ensure page loads
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight); \
                          var lenOfPage=document.body.scrollHeight;return lenOfPage;")

    # Pulling loan details

    results = driver.find_elements_by_class_name("loan-details")
    print(loanID, " ", len(results)) # 7 Sections

    ## Parsing section by section

    # Loan details section
    loan_details = text_parser(0, "Loan Details")

    # Personal details section
    personal_details = text_parser(1, "Personal Details")

    # Score details
    score_details = text_parser(2, "data")
    score_details.loc[0,1] = score_details.loc[0,1].lstrip("0100") # Gettign lenden score

    # Credit details
    credit_details = text_parser(3, "Credit Line Details")
    credit_details = credit_details.loc[0:2] # dropping existing loan details

    # Default details
    default_details = results[4].text.split("\n")
    default_details.remove("Delinquency Details")
    default_details.remove("Default Details")
    if len(default_details) == 7: default_details.insert(5, "NO") # Artifically adding bank defaulter status as No, since it seems to be missing int he website
    default_details = pd.DataFrame(zip(default_details[0::2], default_details[1::2]))
    default_details["Category"] = "Default Details"

    # Proffessional details
    proffessional_details = text_parser(5, "Professional Details")

    # Loan history
    loan_history = results[6].text.split("\n")[-2:]
    loan_history = pd.DataFrame(loan_history)[0].str.split(":", expand = True)
    loan_history["Category"] = "Loan History"

    # Getting loan purpose
    loan_purpose = driver.find_elements_by_class_name("invest-paper")
    loan_purpose = loan_purpose[0].text.split("\n")[4]
    loan_purpose = pd.DataFrame(zip(["Loan Purpose"], [loan_purpose]))
    loan_purpose["Category"] = "Loan Details"

    # Concatenating data together
    loan_data = pd.concat([loan_details, personal_details, score_details, credit_details, default_details, 
                        proffessional_details, loan_history, loan_purpose], sort = True)
    loan_data = loan_data.reset_index(drop = True).rename(columns = {0:"Parameter", 1:"Value"})
    loan_data["LoanID"] = loanID

    loan_data_combined.append(loan_data)

loan_data_combined = pd.concat(loan_data_combined, sort = True)

#%% Reshaping loan data

loan_data_unstack = loan_data_combined.pivot(index = "LoanID", columns = "Parameter", 
                                            values = "Value").reset_index()

#%% Shutting down webdriver and exporting data

driver.quit()

#loan_data_unstack.to_csv("loandata_dad.csv", index = False)
loan_data_unstack.to_csv("loandata_srungeer.csv", index = False)
