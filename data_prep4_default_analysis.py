#%% Importing libraries

import pandas as pd
import numpy as np

#%% Loading files

# Dad's profile
investment_his_dad = pd.read_excel("LenDen_INVESTMENT_HISTORY_Dad.xlsx", header = 1, skip_rows = 0)
loan_details_dad = pd.read_csv("loandata_dad.csv")

# Srunegeer's profiles
investment_his_ss = pd.read_excel("LenDen_INVESTMENT_HISTORY_Srungeer.xlsx", header = 1, skip_rows = 0)
loan_details_ss = pd.read_csv("loandata_srungeer.csv")

#%% Data processing function

def exp_parser(x):
    if (pd.notna(x) and "year/s" in x.lower()):
        x = float(x.lower().strip("year/s").strip())
    elif (pd.notna(x) and "month/s" in x.lower()):
        x = float(x.lower().strip("month/s").strip())/12
    else:
        x
    
    return x

def data_prep(history, details):

    # Merging data
    history.rename(columns = {"Loan ID": "LoanID"}, inplace = True) # Aligning column names
    output = pd.merge(history, details, on = "LoanID", how = "inner")
    
    ## Data Cleaning

    # Dropping redundant column
    output.drop(["Sr. No.", 'My Investment'], axis = 1, inplace = True)

    # Converting number columns into float
    num_cols = ['Current EMI', "EMI Amount", "Monthly Income", "Total Credit Limit", 
                "Total Family Members", 'Principal Outstanding', "Interest Repaid", 
                "Earning Family Members"]
    output[num_cols] = output[num_cols].astype(str).applymap(
       lambda x: np.nan if x == "-" else float(x.strip("₹").strip().replace(",", "")))

    # Fixing case
    output[["Borrower", "Designation", "City", "Employer Name"]] = output[
           ["Borrower", "Designation", "City", "Employer Name"]].apply(lambda x: x.str.lower())

    # Experience columns  
    output[["Total Experience", "Working Since"]] = output[["Total Experience", "Working Since"]].applymap(exp_parser)

    # Date columns
    date_cols = ["Disbursement Date", "EMI Start Date", "First Loan Availment Date", "Last Payment Date"]
    output[date_cols] = output[date_cols].apply(lambda x: pd.to_datetime(x.replace("-", pd.NaT), format = "%d/%m/%Y").dt.strftime("%d-%b-%Y").replace("NaT", np.nan))
    output["Last Default Date"] = pd.to_datetime(output["Last Default Date"], format = "%Y-%m-%d").dt.strftime("%d-%b-%Y").replace("NaT", np.nan)

    # Loan Purpose
    output.loc[output["Loan Purpose"] == output["LoanID"], "Loan Purpose"] = np.nan

    ## Creating variables

    # Number of loans as in comment
    output.loc[output["LenDen Comment"].notna(), "Comment Loans"] = output.loc[
        output["LenDen Comment"].notna(), "LenDen Comment"].apply(
        lambda x: [int(x) for x in x.split() if x.isdigit()]).apply(
        lambda x: x[0] if len(x) > 0 else np.nan) # Extratcing digit from comment

    # Good loan/Bad Loans
    output.loc[output["Status"].isin(["delayed 2", "delayed 3", "default", "written off", "npa"]), "Default"] = "Yes"
    output["Default"].fillna("No", inplace = True)

    # Debt to Income ratio
    output["DTI"] = output[["Current EMI", "EMI Amount"]].sum(axis = 1)/output["Monthly Income"]

    # Risk Category
    bins = [0, 0.150, 0.200, 0.250, 0.300, 0.350, 0.400, np.Inf]
    names = ['Very Low', 'Low', 'Moderate', 'High', 'Very High', 'Ultra High', 'Unidentified']
    output['Risk Category'] = pd.cut(output['Interest Rate'], bins, labels=names)

    # Earning to total family memeber ratio
    output["Dependents ratio"] = (output["Total Family Members"] - output["Earning Family Members"])/output["Total Family Members"]

    # Number of Loans paid
    output["Loans Paid"] = output["Total Loans"] - output["Current Loans"]

    # % repaid by tenure
    output["EMI Paid %"] = output["Paid EMI Count"]*100/output["Tenure (months)"]

    # Disbursement month, year, week of month, day of week
    output["Disbursement Day"] = pd.to_datetime(output["Disbursement Date"], format = "%d-%b-%Y").dt.day_name()
    output["Disbursement Month"] = pd.to_datetime(output["Disbursement Date"], format = "%d-%b-%Y").dt.month_name()
    output["Disbursement Year"] = pd.to_datetime(output["Disbursement Date"], format = "%d-%b-%Y").dt.year
    output["Disbursement Weekofmonth"] = (pd.to_datetime(output["Disbursement Date"], format = "%d-%b-%Y").dt.day-1)//7 + 1
    
    return output

#%% Processing loan data

loan_details_dad = data_prep(investment_his_dad, loan_details_dad)
loan_details_ss = data_prep(investment_his_ss, loan_details_ss)

loan_details_dad["Profile"] = 'Dad'
loan_details_ss["Profile"] = "Srungeer"

loan_details = pd.concat([loan_details_dad, loan_details_ss], sort = False).reset_index(drop = True)

#%% Data export

loan_details.to_excel("loan_details_combined.xlsx", index = False)

#%% Scratch area

#loan_details = pd.read_excel("loan_details_combined.xlsx")