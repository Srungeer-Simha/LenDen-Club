# Loading libraries

import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

#%% Initialising webdriver and logging in

# Initialising a Firefox webdriver
driver = webdriver.Firefox()
driver.get("https://app.lendenclub.com/app/lender/invest") # Connecting to loan portfolio page

# Opening lenden club page and logging in

username = driver.find_element_by_name("username")
password = driver.find_element_by_name("password")

username.send_keys("athreyasa.boda@outlook.com")
password.send_keys("no5mukil")

#username.send_keys("srungeersimha@gmail.com")
#password.send_keys("iluvcallofduty")

driver.find_element_by_class_name("login-button").click()
time.sleep(10) # allowing for time to login

#%% Getting list of loanIDs with remaining amounts

next_page_button = driver.find_element_by_xpath("/html/body/div[1]/div/div[3]/div[2]/div/div/div[1]/div[4]/button[10]")

def loans_crawler(loanIDs):

    loans = driver.find_elements_by_class_name("invest-row")
    amount = np.array([x.text.split("\n")[3] for x in loans])

    if any(amount == "-"):

        last_loan_loc = np.where(amount != "-")[0].max() if len(np.where(amount != "-")[0]) > 0 else 0
        loanIDs = loanIDs + [x.text.split("\n")[5] for x in loans[0:last_loan_loc+1]]
        return loanIDs
    
    else:

        loanIDs = loanIDs + [x.text.split("\n")[5] for x in loans]
        next_page_button.click() # Going to next page
        loans_crawler(loanIDs)

loanIDs = loans_crawler([])

#%% Getting parameters for loans

instamoney_loans = []

for loanID in loanIDs:

    # Opening loan detaila page
    loanurl = "https://app.lendenclub.com/app/lender/invest/" + loanID
    driver.get(loanurl) # Connecting to page

    # Executing scrip to scroll down to bottom of page to ensure page loads
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight); \
                          var lenOfPage=document.body.scrollHeight;return lenOfPage;")

    # Getting loan type:
    results = driver.find_elements_by_class_name("loan-details")
    loan_details = results[0].text.split("\n")
    loan_type = loan_details[2]

    if loan_type == "Instamoney":

        # Comment loans
        if "LenDen Comment" in loan_details:
            if "loans before this and has repaid successfully" in loan_details[8]:
                comment_loans = [int(x) for x in loan_details[8].split() if x.isdigit()][0]

        else: 
            comment_loans = 0

        # Loans Paid
        loan_history = [int(x.split(":")[-1].strip()) for x in results[6].text.split("\n")[-2:]]
        loans_paid = loan_history[0] - loan_history[1]

        # Credit score
        score_details = results[2].text.split("\n")
        credit_score = score_details[-1]

        # Loan Purpose, interest rate, tenure etc.
        details = driver.find_elements_by_class_name("invest-paper")[0].text.split("\n")
        loan_purpose = details[4]
        remaining_amount = details[3]
        Interest_rate = details[0]
        tenure = details[1]
        name = details[6]

        # Storing data
        column_name = ["LoanID", "Name", "Loan Type", "Interest Rate", "Remaining Amount", 
                      "Tenure", "Loan Purpose", "Loans Paid", "Comment Loans", "Credit Score"]
        values = [loanID, name, loan_type, Interest_rate, remaining_amount, tenure, loan_purpose, 
                 loans_paid, comment_loans, credit_score]
        details = pd.DataFrame(zip(column_name, values)).set_index(0).T

        instamoney_loans.append(details)

instamoney_loans = pd.concat(instamoney_loans, sort = False)

#%% Evaluating Loans

## Instamoney Loans

instamoney_loans["Loans Paid Criteria"] = instamoney_loans["Loans Paid"].apply(lambda x: True if x >= 15 else False)
instamoney_loans["Comment Loans Criteria"] = instamoney_loans["Comment Loans"].apply(lambda x: True if x > 1 else False)
instamoney_loans["Credit Score Criteria"] = instamoney_loans["Credit Score"].apply(lambda x: True if x == "Above 750" else False)

instamoney_loans["Score"] = instamoney_loans[[x for x in instamoney_loans.columns if "Criteria" in x]].sum(axis = 1)
instamoney_loans = instamoney_loans.drop([x for x in instamoney_loans.columns if "Criteria" in x], axis = 1
                        ).sort_values(by = ["Score", "Loans Paid", "Comment Loans", "Credit Score"], ascending = False)
