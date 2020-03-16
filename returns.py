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

account_details = []
invest_hist = []

for dir in [sru_dir]:
    for filename in os.listdir(dir):
        if "ACCOUNT_STATEMENT" in filename:
            df = pd.read_csv(dir + "\\" + filename)
            account_details.append(df)
        elif "INVESTMENT_HISTORY" in filename:
            df = pd.read_csv(dir + "\\" + filename)
            invest_hist.append(df)

account_details = pd.concat(account_details, sort = False)
invest_hist = pd.concat(invest_hist, sort = False)

#%% Data cleaning

account_details["Date"] = pd.to_datetime(account_details["Date"].str.split(" ", expand = True)[0])
