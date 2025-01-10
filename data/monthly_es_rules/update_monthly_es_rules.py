print('NOTE: The current code can only update data for the Biden and following administrations.')

#%% Import packages
import os
import sys

# Import customized functions
dir_path=os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, f'{dir_path}/../py_funcs')
import frcount

#%% Specify the file path of the current dataset
file_path=f'{dir_path}/monthly_econ_significant_rules_by_presidential_month.csv'
file_path2=f'{dir_path}/monthly_econ_significant_rules_by_presidential_month.xlsx'

#%% Run functions to update the data
df=frcount.main(dir_path,file_path,rule_type='es',type='monthly')

#%% Export
df.to_csv(file_path, index=False)
df.to_excel(file_path2, index=False)
print('The dataset has been updated and saved. End of execution.')

#%% Count significant rules under Biden
file_path=f'{dir_path}/monthly_significant_rules_biden.csv'
df_sig=frcount.main(dir_path,file_path,rule_type='sig',type='monthly')
df_sig=df_sig[df_sig['Biden'].notnull()][['Month','Months in Office','Biden']]
df_sig.rename(columns={'Biden':'Significant'},inplace=True)

df_es=df[df['Biden'].notnull()][['Months in Office','Biden']]
df_es.rename(columns={'Biden':'Economically Significant'},inplace=True)

df_sig=df_sig.merge(df_es,on='Months in Office',how='left')
df_sig['Other Significant']=df_sig['Significant']-df_sig['Economically Significant']

df_sig.to_csv(file_path,index=False)