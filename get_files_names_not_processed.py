'''
get file names of PDFs in the 'not procssed' folder

chris zhang 10/3/2019
'''

import pandas as pd
import os

fs = [f for f in os.listdir('./input_not_processed') if f.endswith('.pdf')]
fs = pd.DataFrame(fs)
fs.columns= ['file_name']
fs.to_csv('./pdfs_not_processed.csv', index=False)

fs = pd.read_csv('./pdfs_not_processed.csv')
# check if input and input_not_processed have overlap
fs_not_processed = [f for f in os.listdir('./input_not_processed') if f.endswith('.pdf')]
fs_processed = [f for f in os.listdir('./input') if f.endswith('.pdf')]

set(fs_not_processed).intersection(set(fs_processed))