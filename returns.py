'''
Analysing portfolio performance and returns from lenden club
'''
#%% Loading libraries and defining functions

import pandas as pd
import numpy as np
import scipy.optimize
from datetime import date
import os

# Defining a function to calculate xirr

def calc_xnpv(rate, values, dates):

    if rate <= -1.0:
        return float('inf')
    d0 = dates[0]    # or min(dates)
    return sum([ vi / (1.0 + rate)**((di - d0).days / 365.0) for vi, di in zip(values, dates)])

def calc_xirr(values, dates):

    try:
        return scipy.optimize.newton(lambda r: calc_xnpv(r, values, dates), 0.0)
    except RuntimeError:    # Failed to converge?
        return scipy.optimize.brentq(lambda r: calc_xnpv(r, values, dates), -1.0, 1e10)

#%% Loading data

dad_dir = "C:\\Apps\\Srungeer\\Documents\\Personal\\Personal Finance\\LenDen Club\\Input\\Dad"
sru_dir = "C:\\Apps\\Srungeer\\Documents\\Personal\\Personal Finance\\LenDen Club\\Input\\Srungeer"

account_list = []
invest_list = []

for dir in [sru_dir]:
    for filename in os.listdir(dir):
        if "ACCOUNT_STATEMENT" in filename:
            df = pd.read_csv(dir + "\\" + filename)
            account_list.append(df)
        elif "INVESTMENT_HISTORY" in filename:
            df = pd.read_csv(dir + "\\" + filename)
            invest_list.append(df)

account_details = pd.concat(account_list, sort = False)
invest_hist = pd.concat(invest_list, sort = False)

#%% Data cleaning

## Data formats

account_details["Date"] = pd.to_datetime(account_details["Date"].str.split(" ", expand = True)[0], format = "%d/%m/%Y")

num_cols = ["Principal Repaid", "Principal Outstanding", "Interest Repaid", "Investment"]
invest_hist[num_cols] = invest_hist[num_cols].astype(str).applymap(lambda x:  np.nan if x == "-" else float(x.strip("₹").strip().replace(",", "")))

invest_hist["Interest Rate"] = invest_hist["Interest Rate"].str.strip("%").astype(float)/100

# Transaction type in account statement
 
payment = ["REPAYMENT", "DELAY PENAL CHARGE", "BROKEN PERIOD INTEREST", "REFERRAL BONUS",
            "COMMITMENT INTEREST"]
fees = ["FACILITATION FEE"]
add_money = ["ADD MONEY"]

account_details.loc[account_details["Type"].isin(payment), "Category"] = "Payment"
account_details.loc[account_details["Type"].isin(fees), "Category"] = "Fees"
account_details.loc[account_details["Type"].isin(add_money), "Category"] = "Investment"

# Loan status category
default_status = ["delayed 2", "delayed 3", "default", "written off", "npa"]

invest_hist.loc[invest_hist["Status"].isin(default_status), "Loan Status"] = "Default"
invest_hist.loc[invest_hist["Status"] == "regular", "Loan Status"] = "Regular"
invest_hist.loc[invest_hist["Status"].isin(["confirmed", "committed", "disbursed"]), "Loan Status"] = "Invested"
invest_hist.loc[invest_hist["Status"].isin(["closed", "prepaid"]), "Loan Status"] = "Closed"
invest_hist.loc[invest_hist["Status"] == "delayed 1", "Loan Status"] = "Delayed"


#%% Calculations

# Amount received till date
amount_received = account_details.loc[account_details["Category"] == "Payment", "Credit"].sum()

# Amount invested
amount_added = account_details.loc[account_details["Category"] == "Investment", "Credit"].sum()

# Default rate
default_rate = invest_hist.loc[invest_hist["Loan Status"] == "Default", "Loan ID"].nunique()/invest_hist["Loan ID"].nunique()

# Future cashflow
open_loans = invest_hist[invest_hist["Loan Status"].isin(["Regular", "Delayed", "Investment"])]
open_loans["Pending EMIs"] = open_loans["Tenure (months)"] - open_loans["Paid EMI Count"]

future_cashflow = []
for loan in open_loans["Loan ID"]:
    loan_details = open_loans[open_loans["Loan ID"] == loan]
    cashflow = loan_details["EMI"].to_list()*loan_details["Pending EMIs"].values[0]
    future_cashflow.append(cashflow)

future_cashflow = pd.DataFrame(future_cashflow)
future_cashflow["PV"] = future_cashflow.apply(lambda x: np.npv(0.08/12, pd.concat([pd.Series(0), x[0:len(x)].dropna()])), axis = 1)
future_cashflow["MOD"] = future_cashflow.drop("PV", axis = 1).sum(axis = 1)

present_value = future_cashflow["PV"].sum()

# Portfolio value
portfolio_value = amount_received + present_value*(1-default_rate)
unrisked_portfolio_value = amount_received + present_value

## Return metrics

# ROI
roi = (portfolio_value - amount_added)/amount_added
print("Return on Investment: {0}%".format(np.round(roi*100, 1)))

# CAGR
n = (account_details["Date"].max() - account_details["Date"].min()).days/365

cagr = np.power(portfolio_value/amount_added, 1/n) - 1
cagr_unrisked = np.power(unrisked_portfolio_value/amount_added, 1/n) - 1

print("Compound annual growth rate: {0}%".format(np.round(cagr*100, 1)))

# XIRR

dates = list(account_details.loc[account_details["Category"] == "Investment", "Date"])
dates.append(account_details["Date"].max())

values = list(account_details.loc[account_details["Category"] == "Investment", "Credit"])
values.append(-portfolio_value)

xirr = calc_xirr(values, dates)

print("Extended internal rate of return: {0}%".format(np.round(xirr*100, 1)))

#%% Scratch code

# Alternative calculation
invest_hist["Principal Repaid"].sum()
invest_hist["Interest Repaid"].sum()
invest_hist["Principal Outstanding"].sum()

# Backcalcualting Lenden's XIRR
invest_hist["Principal Repaid"].sum()-invest_hist["Interest Repaid"].sum() + 39.37

# Money received in Mar 2020
account_details.loc[(account_details["Date"].dt.month == 3) & (
                     account_details["Date"].dt.year == 2020) & (
                     account_details["Category"] == "Payment"), "Credit"].sum()
