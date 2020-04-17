'''
get risk profile and organize for easy computing risk score in extrac_pdf_fields.py
for Wave-2 BPCI ACQ
chris zhang 4/16/2020
'''
import pandas as pd
pd.set_option('max_colwidth', 100)
pd.set_option('display.max_columns', 999)
pd.set_option('display.width', 200)
pd.set_option('display.max_rows', 200)
import numpy as np

# Read in question level data
questions = pd.read_excel('./input_mar2020/ACQ Data Template 3.16.20.xlsx',
                          sheet_name='Question Characteristics')
questions = questions.drop(columns=['Old ID', 'New ID', 'Source'])
# Read in response level data
responses = pd.read_excel('./input_mar2020/ACQ Data Template 3.16.20.xlsx',
                          sheet_name='Response Weights')
responses = responses.drop(columns=['Old ID', 'New ID', 'Source', 'N/A'])
# Merge questions to responses
risk_profile = pd.merge(responses, questions, how='left', on='New ID v2')
# TODO: remove code below (wave 2 has NEW ID v2 matching id in items.csv)
# save as excel
# responses.to_excel('./risk_profile_to_edit.xlsx', index=False)
# # ... manually add in item ID (from GUI output files) to above risk profile
# # Read in edited risk profile
# risk_profile = pd.read_excel('./risk_profile.xlsx')


# drop rows with missing response weights (not valid response to question)
# or with missing ID (not considered in output, eg Salesforce questions)
risk_profile = risk_profile[risk_profile['Response Weights'].notna()]
risk_profile = risk_profile[risk_profile['New ID v2'].notna()]

# organize cols
risk_profile = risk_profile[['New ID v2', 'Response Weights', 'Risk Level',
                             'Topic', 'Question', 'Response Option']]

# export a reduced risk profile
risk_profile.to_excel('./risk_profile_reduced_wave2.xlsx', index=False)

# ...manually check following
# (i)if response option strings match exactly the option strings in PDF, correct strings in risk profile spreadsheet
# (ii)grouped responses in template - NT breakdown as indiv responses in risk_profile, eg strongly agree & agree..

############################################################################
## TODO: run code below if Joe has any ADDITIONAL risk_profile-related issues with tool. Fix and save final Excel.
# clean up risk_profile_reduced_option_string_checked.xlsx
# risk_profile = pd.read_excel('./risk_profile_reduced_option_string_checked.xlsx')
# risk_profile = risk_profile.rename(columns={'ID_in_GUI_output':'id_in_info_json'})
# # manual fix - update some missed inconsistent Response Option strings to match those in questionnaire
# # below standardizes 'N/A' to 'NA' in Response Option
# risk_profile.loc[risk_profile['Response Option'].str.contains('N/A'), 'Response Option'] = \
#     [x.replace('N/A', 'NA') for x in risk_profile.loc[risk_profile['Response Option'].str.contains('N/A'), 'Response Option']]
# # 'agreement' vs 'arrangement'
# risk_profile.loc[risk_profile['Response Option']=='NA; already in a financial agreement(s)', 'Response Option'] =\
#     'NA; already in a financial arrangement(s)'

# Save final risk profile excel
risk_profile = pd.read_excel('./risk_profile_reduced_wave2.xlsx')
risk_profile.to_excel('./risk_profile_master_wave2.xlsx', index=False)

# now convert risk_profile to a dict - mapping [id_in_info_json][Response Option]
# to (Response Weights, Risk Level, risk_score)

# read in master and get risk score
risk_profile = pd.read_excel('./risk_profile_master_wave2.xlsx')
risk_profile['risk_score'] = risk_profile['Response Weights'] * risk_profile['Risk Level']
# drop rows if risk score=0 (some response option is NA or missing)
risk_profile = risk_profile[risk_profile['risk_score']!=0]
# keep cols
risk_profile = risk_profile[['New ID v2','Response Option', 'Response Weights', 'Risk Level', 'risk_score']]
risk_profile['New ID v2'] = risk_profile['New ID v2'].astype(float) # to match float id's in info.json
# update dct_risk - use all lower cases for response option strings, standardize unicode quotations if any
dct_risk = {}
for id in set(risk_profile['New ID v2'].values):
    dct_risk[id] = {}
    for i, row in risk_profile[risk_profile['New ID v2']==id].iterrows():
        response_option_string = row['Response Option'].lower().replace("\u2018", "'").replace("\u2019", "'").strip()
        dct_risk[id][response_option_string] = {'Response Weights':row['Response Weights'],
                                                'Risk Level':row['Risk Level'],
                                                'risk_score':row['risk_score']}
# save dct_risk as json

import json
with open('./risk_profile_wave2.json', 'w') as f:
    json.dump(dct_risk, f, sort_keys=True, indent=4)

# TODO - check for \u2019, \u2018 in risk_profile.json, it's mixing with "'" causing KeyError ...


#########################################
# in extract_pdf_fields - load json and convert keys to float
# with open('./risk_profile.json', 'r') as f:
#     rp = json.load(f)
#
# rp = {float(k):v for k, v in rp.items()}