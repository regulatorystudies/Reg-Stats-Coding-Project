#%% Import packages
import pandas as pd
import os
import sys
from datetime import date
from dateutil.relativedelta import relativedelta

# %% A function to update data for an administration
def update_admin(df,df_fr,admin,update_start_date,update_end_date,rule_type='es',type='cumulative'):

    # Refine FR tracking data
    df_fr = df_fr[(df_fr['publication_date'] >= update_start_date) & (df_fr['publication_date'] <= update_end_date)]

    if rule_type=='es':
        # Count monthly economically/section 3(f)(1) significant rules
        if min(df_fr['publication_date']) < date(2023, 4, 6) < max(df_fr['publication_date']):
            df_fr_update1 = df_fr[df_fr['publication_date'] < date(2023, 4, 6)][
                ['publication_year', 'publication_month', 'econ_significant']]. \
                groupby(['publication_year', 'publication_month']).sum().reset_index()
            df_fr_update1.rename(columns={'econ_significant': 'count'}, inplace=True)
            df_fr_update2 = df_fr[df_fr['publication_date'] >= date(2023, 4, 6)][
                ['publication_year', 'publication_month', '3(f)(1) significant']]. \
                groupby(['publication_year', 'publication_month']).sum().reset_index()
            df_fr_update2.rename(columns={'3(f)(1) significant': 'count'}, inplace=True)
            df_fr_update = pd.concat([df_fr_update1,df_fr_update2],ignore_index=True)
            df_fr_update=df_fr_update.groupby(['publication_year', 'publication_month']).sum()  #combine April 2023 data
        elif max(df_fr['publication_date']) < date(2023, 4, 6):
            df_fr_update = df_fr[['publication_year', 'publication_month', 'econ_significant']]. \
                groupby(['publication_year', 'publication_month']).sum()
            df_fr_update.rename(columns={'econ_significant': 'count'}, inplace=True)
        else:
            df_fr_update = df_fr[['publication_year', 'publication_month', '3(f)(1) significant']]. \
                groupby(['publication_year', 'publication_month']).sum()
            df_fr_update.rename(columns={'3(f)(1) significant': 'count'}, inplace=True)

    elif rule_type=='sig':
        df_fr_update = df_fr[['publication_year', 'publication_month', 'significant']]. \
            groupby(['publication_year', 'publication_month']).sum()
        df_fr_update.rename(columns={'significant': 'count'}, inplace=True)

    # Append new data to the current dataset
    first_month_no_data = df[df[admin].isnull()]['Months in Office'].values[0]
    if type=='cumulative':
        cum_count=0 if first_month_no_data==0 else df[df[admin].notnull()][admin].iloc[-1]
        for x in df_fr_update['count']:
            cum_count = cum_count + x
            df.loc[df['Months in Office'] == first_month_no_data, admin] = cum_count
            first_month_no_data += 1
    elif type=='monthly':
        for x in df_fr_update['count']:
            df.loc[df['Months in Office'] == first_month_no_data, admin] = x
            first_month_no_data += 1

    return df

#%% A function to check for partial data
# (in case the data collection for the most recent month has not been completed)
def check_partial_month(df_fr,update_end_date):
    if max(df_fr['publication_date'])>=update_end_date:
        pass
    elif update_end_date.weekday()>=5:  # if end of month is a Saturday (5) or Sunday (6)
        if max(df_fr['publication_date']) >= update_end_date - relativedelta(days=update_end_date.weekday()-4):
            pass
        else:
            print(f'WARNING: The FR tracking data for {update_end_date.year}-{update_end_date.month} is not complete.')
            update_end_date = update_end_date.replace(day=1) - relativedelta(days=1)
    else:
        print(f'WARNING: The FR tracking data for {update_end_date.year}-{update_end_date.month} is not complete.')
        update_end_date=update_end_date.replace(day=1) - relativedelta(days=1)

    return update_end_date

#%% The main function
def main(dir_path,file_path,rule_type='es',type='cumulative'):
    # Define administrations and their start & end years
    # If there is a new administration, add {president name: [start year, end year]} to the dictionary below.
    admin_year = {'Reagan': [1981, 1989],
                  'Bush 41': [1989, 1993],
                  'Clinton': [1993, 2001],
                  'Bush 43': [2001, 2009],
                  'Obama': [2009, 2017],
                  'Trump': [2017, 2021],
                  'Biden': [2021, ]}
    print(f"The current dataset covers the {', '.join(list(admin_year.keys()))} administrations.\n"
          f"If there is a new administration, revise the admin_year dictionary in frcount.main and re-run the code.")

    # Import the current dataset
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        print('Error: no existing dataset.')
        sys.exit(0)

    # %% Create a new column if there is a new administration
    new_admin = [x for x in admin_year.keys() if x not in df.columns]
    if len(new_admin) > 0:
        for x in new_admin:
            df[x] = None
    else:
        pass

    # %% Import FR tracking data
    df_fr = pd.read_csv(f'{dir_path}/../fr_tracking/fr_tracking.csv', encoding="ISO-8859-1")

    # Add a row to account for missing data
    df_fr = pd.concat([df_fr, pd.DataFrame(data={'publication_date': ['1/21/2021']})], ignore_index=True)

    # Change data type
    df_fr['publication_date'] = pd.to_datetime(df_fr['publication_date'], format="mixed").dt.date
    df_fr['publication_year'] = pd.to_datetime(df_fr['publication_date']).dt.year
    df_fr['publication_month'] = pd.to_datetime(df_fr['publication_date']).dt.month
    df_fr['significant'] = pd.to_numeric(df_fr['significant'], errors='coerce')
    df_fr['econ_significant'] = pd.to_numeric(df_fr['econ_significant'], errors='coerce')
    df_fr['3(f)(1) significant'] = pd.to_numeric(df_fr['3(f)(1) significant'], errors='coerce')

    # %% Check previous administrations (starting from Biden)
    for admin in df.columns[8:-1]:
        first_month_no_data = df[df[admin].isnull()]['Months in Office'].values[0]
        update_start_date = date(admin_year[admin][0], 1, 1) + relativedelta(months=first_month_no_data)

        if (update_start_date.year == admin_year[admin][1]) and (update_start_date.month == 2):
            print(f'The {admin} administration data is up-to-date.')
            pass

        else:
            # update start date
            if first_month_no_data == 0: update_start_date = update_start_date.replace(day=21)
            # update end date
            update_end_date = date(admin_year[admin][1], 1, 20)

            # update data
            print(f'Updating data from {update_start_date} to {update_end_date}...')
            df = update_admin(df, df_fr, admin, update_start_date, update_end_date, rule_type, type)
            print(f'The {admin} administration data has been updated.')

    # %% Check current administration (starting from Biden)
    admin = df.columns[-1]
    first_month_no_data = df[df[admin].isnull()]['Months in Office'].values[0]

    # update start date
    update_start_date = date(admin_year[admin][0], 1, 1) + relativedelta(months=first_month_no_data)
    if first_month_no_data == 0: update_start_date = update_start_date.replace(day=21)
    # update end date
    update_end_date = date.today().replace(day=1) - relativedelta(days=1)
    if len(admin_year[admin]) > 1:
        if (update_end_date.year == admin_year[admin][1]) and (update_end_date.month == 1):
            update_end_date = update_end_date.replace(day=20)

    # check for partial month
    update_end_date = check_partial_month(df_fr, update_end_date)

    # update data
    if update_start_date > update_end_date:
        print(f'The {admin} administration data is up-to-date.')
        pass
    else:
        print(f'Updating data from {update_start_date} to {update_end_date}...')
        df = update_admin(df, df_fr, admin, update_start_date, update_end_date, rule_type, type)
        print(f'The {admin} administration data has been updated.')

    return df