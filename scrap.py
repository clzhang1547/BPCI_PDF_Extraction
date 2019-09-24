import csv
import datetime
import json
import os
import pandas as pd
import PyPDF3
import sys
import warnings
warnings.filterwarnings("ignore", message="Xref table not zero-indexed. ID numbers for objects will be corrected.")

pdf_file_path= 'C:/workfiles/PDF_Extraction/input/Annual Check-in Questionnaire 09.05.19_Added_example_1.pdf'
fields = PyPDF3.PdfFileReader(pdf_file_path).getFields()

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