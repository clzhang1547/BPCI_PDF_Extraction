import importlib
import get_pdf_fields
import pandas as pd
pd.set_option('max_colwidth', 100)
pd.set_option('display.max_columns', 999)
pd.set_option('display.width', 200)
import numpy as np

# Determine the fields corresponding to each entry in a PDF.
importlib.reload(get_pdf_fields)
pdf_fp = './Annual Check-in Questionnaire 09.05.19_Added.pdf'
items_fp = './items.csv'
gpf = get_pdf_fields.GetPdfFields(pdf_fp, items_fp)

########################################################################

# order JSON by id
d = pd.read_json('./Annual Check-in Questionnaire 09.05.19_Added.json', orient='index')
d.loc[(d['group']=='General Information') &
      (d['text']=='BPID'), 'id'] = 0.0
d.loc[(d['group']=='General Information') &
      (d['text']=='Organization Legal Name'), 'id'] = 0.1
d = d.sort_values(by=['id'])
d = d.reset_index()
d = d.rename(columns={'index':'field_id'})
d['field_type'] = [''.join([i for i in s if not i.isdigit()]) for s in d['field_id']]

# export as excel
d.to_excel('./temp_json.xlsx', index=False)

# TODO: FIX temp_json.xlsx MANUALLY
d = pd.read_excel('./temp_json.xlsx', index_col='field_id')
d = d.sort_values(by=['id'])
del d['field_type']
# output as JSON
with open('temp_json.json', 'w') as f:
    f.write(d.to_json(orient='index'))

# save a nice layout of info.json
import json
from collections import OrderedDict

with open('./info.json', 'r') as f:
    info = json.load(f)

info_list = [(k, v) for k, v in info.items()]
info_list = sorted(info_list, key=lambda x: x[1]['id'])
info = {k:v for k, v in info_list}

info = OrderedDict(info_list, key=lambda x: x[1]['id'])
info.pop('key')
with open('./info.json', 'w') as f:
    json.dump(info, f, indent=4)