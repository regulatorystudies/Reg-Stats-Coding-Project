print('NOTE: The current code can only update data for the Biden and following administrations.')

import pandas as pd
import os
import sys
from datetime import date
from dateutil.relativedelta import relativedelta

#%% Define administrations and their start & end years
# If there is a new administration, add {president name: [start year, end year]} to the dictionary below.
admin_year={'Reagan':[1981,1989],
            'Bush 41':[1989,1993],
            'Clinton':[1993,2001],
            'Bush 43':[2001,2009],
            'Obama':[2009,2017],
            'Trump':[2017,2021],
            'Biden':[2021,]}
print(f"The current dataset covers the {list(admin_year.keys())} administrations.\n"
      f"If there is a new administration, revise the admin_year dictionary and re-run the code.")

#%% Import the current dataset
dir_path=os.path.dirname(os.path.realpath(__file__))
file_path=f'{dir_path}/cumulative_econ_significant_rules_by_presidential_month.csv'

if os.path.exists(file_path):
    df=pd.read_csv(file_path)
else:
    print('Error: no existing dataset.')
    sys.exit(0)

#%% Create a new column if there is a new administration
new_admin=[x for x in admin_year.keys() if x not in df.columns]
if len(new_admin)>0:
    for x in new_admin:
        df[x]=None
else:
    pass

# %% A function to update data for an administration
def update_admin(admin,update_start_date,update_end_date):

    # Import FR tracking data
    df_fr = pd.read_csv(f'{dir_path}/../fr_tracking/fr_tracking.csv', encoding="ISO-8859-1")

    # Add a row to account for missing data
    df_fr = pd.concat([df_fr, pd.DataFrame(data={'publication_date': ['1/21/2021']})], ignore_index=True)

    # Change data type
    df_fr['publication_date'] = pd.to_datetime(df_fr['publication_date']).dt.date
    df_fr['publication_year'] = pd.to_datetime(df_fr['publication_date']).dt.year
    df_fr['publication_month'] = pd.to_datetime(df_fr['publication_date']).dt.month
    df_fr['econ_significant'] = pd.to_numeric(df_fr['econ_significant'], errors='coerce')
    df_fr['3(f)(1) significant'] = pd.to_numeric(df_fr['3(f)(1) significant'], errors='coerce')

    # Refine FR tracking data
    df_fr = df_fr[(df_fr['publication_date'] >= update_start_date) & (df_fr['publication_date'] <= update_end_date)]

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

    # Append new data to the current dataset
    first_month_no_data = df[df[admin].isnull()]['Months in Office'].values[0]
    cum_count=0 if first_month_no_data==0 else df[df[admin].notnull()][admin].iloc[-1]
    for x in df_fr_update['count']:
        cum_count = cum_count + x
        df.loc[df['Months in Office'] == first_month_no_data, admin] = cum_count
        first_month_no_data += 1

    return df

#%% Check previous administrations (starting from Biden)
for admin in df.columns[8:-1]:
    first_month_no_data = df[df[admin].isnull()]['Months in Office'].values[0]
    update_start_date = date(admin_year[admin][0], 1, 1) + relativedelta(months=first_month_no_data)

    if (update_start_date.year==admin_year[admin][1]) and (update_start_date.month==2):
        print(f'The {admin} administration data is up-to-date.')
        pass

    else:
        # update start date
        if first_month_no_data==0: update_start_date = update_start_date.replace(day=21)
        # update end date
        update_end_date = date(admin_year[admin][1],1,20)

        print(f'Updating data from {update_start_date} to {update_end_date}...')
        df=update_admin(admin, update_start_date,update_end_date)
        print(f'The {admin} administration data has been updated.')

#%% Check current administration (starting from Biden)
admin=df.columns[-1]
first_month_no_data = df[df[admin].isnull()]['Months in Office'].values[0]

# update start date
update_start_date = date(admin_year[admin][0], 1, 1) + relativedelta(months=first_month_no_data)
if first_month_no_data == 0: update_start_date = update_start_date.replace(day=21)
# update end date
update_end_date = date.today().replace(day=1) - relativedelta(days=1)
if len(admin_year[admin])>1:
    if (update_end_date.year==admin_year[admin][1]) and (update_end_date.month==1):
        update_end_date=update_end_date.replace(day=20)

if update_start_date>update_end_date:
    print(f'The {admin} administration data is up-to-date.')
    pass
else:
    print(f'Updating data from {update_start_date} to {update_end_date}...')
    df=update_admin(admin,update_start_date,update_end_date)
    print(f'The {admin} administration data has been updated.')

#%% Export
df.to_csv(file_path, index=False)
print('The dataset has been updated and saved. End of execution.')