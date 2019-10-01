#!/usr/bin/python3

"""
Tue 09 Jul 2019 01:15:30 PM PDT

@author: aaron heuser

extract_pdf_fields.py
"""



import csv
import datetime
import json
import os
import pandas as pd
import numpy as np
import PyPDF3
import sys
import warnings
warnings.filterwarnings("ignore", message="Xref table not zero-indexed. ID numbers for objects will be corrected.")
import unicodedata

class ExtractPdfFields:
    """
    Class used to extract fields from a PDF. Input consists of the PDF file
    path, as well as the path to a JSON file that defines the PDF fields. The
    JSON file has as keys the text keys for each PDF field, and as values the
    descriptive information associated to the field.
    """

    def __init__(self, pdf_fp, info_fp, out_fp, now):
        """
        Parameters: pdf_fp: str
                        The path to the PDF file.
                    info_fp: str
                        The path to the JSON info file.
                    out_fp: str
                        The path to output
                    now: str
		    	The timestamp string.
        Returns:    None
        """
        # Set the imported properties.
        self._info_file_path = info_fp
        self._pdf_file_path = pdf_fp
        self._out_file_path = out_fp
        self._now = now
        # Radio button mapping
        self.dict_radio_button = {
            'RadioButton1':{
                '0': 'Strongly Agree',
                '4': 'Agree',
                '3': 'Neutral',
                '2': 'Disagree',
                '1': 'Strongly disagree',
            },
            'RadioButton2':{
                '0': 'Strongly Agree',
                '5': 'Agree',
                '4': 'Neutral',
                '3': 'Disagree',
                '2': 'Strongly disagree',
                '1': 'Unsure',
                '6': 'N/A; we have not yet implemented a system for monitoring and responding to beneficiary complaints',
            }
        }
        # get risk profile
        self.risk_profile = self.import_risk_profile()
        # Extract the needed file information
        self._import()
        # Parse the field info.
        print('Now parsing %s' % self._pdf_file_path)
        self._parse_fields()

    def import_risk_profile(self):
        with open('./risk_profile.json', 'r') as f:
            rp = json.load(f)
        # convert keys (id) to float to match id in info.json
        rp = {float(k): v for k, v in rp.items()}
        return rp


    def _find_bpci_id(self):
        """
        Parameters: None
        Returns:    bpci_id: str
                        The BPCI ID.
        """

        bpci_list = [x for x in self.info.items() if x[1]['text'] == 'BPID']
        if len(bpci_list) > 0:
            bpci_item = self.fields[bpci_list[0][0]]
            if '/V' in bpci_item.keys():
                return bpci_item['/V']
            else:
                return ''
        else:
            return ''

    def _find_organization_name(self):
        """
        Parameters: None
        Returns:    name: str
                        The organization name.
        """

        text = 'Organization Legal Name'
        name_list = [x for x in self.info.items() if x[1]['text'] == text]
        if len(name_list) > 0:
            name_item = self.fields[name_list[0][0]]
            if '/V' in name_item.keys():
                name = name_item['/V']
                # some org legal name can have '-' chars, causing above org to be bytes, so decode in utf-8
                if isinstance(name, bytes):
                    name = name.decode('utf-8', errors='ignore').strip()
                return name
            else:
                return ''
        else:
            return ''

    def _get_fields(self):
        """
        Parameters: None
        Returns:    None
        """

        # Import the PDF fields as a dictionary.
        self._fields = PyPDF3.PdfFileReader(self.pdf_file_path).getFields()

    def _get_info(self):
        """
        Parameters: None
        Returns:    None
        """

        # Import the JSON file as a dictionary.
        with open(self.info_file_path, 'r') as f:
            self._info = json.load(f)

    def _import(self):
        """
        Parameters: None
        Returns:    None
        """

        # Import the PDF fields and the associated PDF field info.
        self._get_info()
        self._get_fields()

    def _parse_fields(self):
        """
        Parameters: None
        Returns:    None
        """

        # Generate a DataFrame from the imported fields.
        cols = ['BPCI ID', 'ID', 'Response', 'Response Weight', 'Risk Level', 'Risk Score']
        cols_raw = ['BPCI ID', 'Global Number', 'Topic Number', 'Topic']
        cols_raw += ['Text', 'Response', 'ID']
        # Get the BPCI ID and the Organization name.
        self._bpci_id = self._find_bpci_id()
        self._organization_name = self._find_organization_name()
        # Loop through each field and fill in the data.
        data = []
        data_raw = []
        for key, val in self.fields.items():
            # We only want key, val pairs for which we have info.
            if key in self.info.keys():
                # Each of the fields for which we need data have a key 'id'.
                if 'id' in self.info[key].keys():
                    item_id = self.info[key]['id']
                    row = [self.bpci_id]
                    row += [self.info[key]['id']]
                    # Get any response that may exist.
                    if '/V' in val.keys():
                        if key[:11]!='RadioButton':
                            content = val['/V']
                            if isinstance(content, PyPDF3.generic.ByteStringObject):
                                # print('--- content before decode = \n%s ' % content)
                                # line breakers in text input may make content as bytes, decode and remove \r, \n, etc.

                                content = content.decode('utf-8', errors='ignore').replace('\r', '').replace('\n', '')
                            else:
                                pass
                            content = content.lstrip('/')
                            response = self._parse_response(content, row[1])
                            row += [response]
                        else:
                            radio_button_code = val['/V'].lstrip('/')
                            radio_button_content = self.dict_radio_button[key][radio_button_code]
                            response = self._parse_response(radio_button_content, row[1])
                            row += [response]
                    else:
                        response = ''
                        row += [response]

                    # Append the risk. - 'Response Weight', 'Risk Level', 'Risk Score'
                    # missing response in PDF could be '---' or something similar (any length)
                    if len(response)>0 and set(response)!={'-'}:
                        if self.info[key]['id'] in self.risk_profile.keys():
                            row += [self.risk_profile[self.info[key]['id']][response.lower()]['Response Weights'],
                                    self.risk_profile[self.info[key]['id']][response.lower()]['Risk Level'],
                                    self.risk_profile[self.info[key]['id']][response.lower()]['risk_score']]
                        else:
                            row += [np.nan, np.nan, np.nan]
                    else:
                        row += [np.nan, np.nan, np.nan]
                    # Append the row to the data.
                    data += [row]

                    # Now for the raw data.
                    # 'num' is 0-ordered in items.csv when set_field() for PDF.
                    # With 2 id-check questions (ID, Org Name) at beginning, num=2 in item.csv
                    # will need Global Number = 1, thus minus 1 from self.info[key]['num']
                    # which gets item by num in info.json.
                    row = [self.bpci_id, self.info[key]['num'] - 1]
                    row += [self.info[key]['local'], self.info[key]['group']]
                    row += [self.info[key]['text']]
                    # Now the response.
                    if '/V' in val.keys():
                        if key[:11]!='RadioButton':
                            content = val['/V']
                            if isinstance(content, PyPDF3.generic.ByteStringObject):
                                # line breakers in text input may make content as bytes, decode and remove \r, \n, etc.
                                content = content.decode('utf-8', errors='ignore').replace('\r', '').replace('\n', '')
                            else:
                                pass
                            content = content.lstrip('/')
                            row += [self._parse_response(content, item_id)]
                        else:
                            radio_button_code = val['/V'].lstrip('/')
                            radio_button_content = self.dict_radio_button[key][radio_button_code]
                            row += [self._parse_response(radio_button_content, row[1])]
                    else:
                        row += ['Not Selected/ Not Answered']
                    # Temporarily append the id for sorting purposes.
                    row += [item_id]
                    data_raw += [row]
        # Sort the data according to the ID.
        data = sorted(data, key=lambda x: x[1])
        data_raw = sorted(data_raw, key=lambda x: x[-1])
        # Now generate the data frame.
        self._response_data = pd.DataFrame(data, columns=cols)
        self._response_data_raw = pd.DataFrame(data_raw, columns=cols_raw)
        # Drop the ID from the raw data.
        self._response_data_raw.drop('ID', axis=1, inplace=True)

    def _parse_response(self, response, item_id):
        """
        Parameters: response: str
                        The response to an item.
                    item_id: int
                        The ID of the item to which the response was made.
        Returns:    w: str
                        The parsed response.
        """

        # Find the info associated to this item ID.
        check_id = lambda x: 'id' in x.keys() and x['id'] == item_id
        info = [x for x in self.info.values() if check_id(x)]
        w = response
        if len(info) > 0:
            if 'values' in info[0] and response in info[0]['values']:
                w = info[0]['values'][response]
        w = w.replace("\u2018", "'").replace("\u2019", "'").strip()
        w = w.replace('N/A', 'NA')
        return w

    def export(self):
        """
        Parameters: None
        Returns:    None
        """

        # # Generate an output directory, if needed.
        # if not os.path.exists('./out'):
        #     os.mkdir('./out')
        org = self.organization_name.lower().strip()
        # some org name has chars not allowed for windows file names, replace as '-'
        bad_fn_chars = ['\\', '/', ':', '*', '?', '\"', '<', '>', '|']
        any_bad_fn_chars = sum([x in org for x in bad_fn_chars])
        if any_bad_fn_chars > 0:
            for char in bad_fn_chars:
                org = org.replace(char, '-')
        bpci = self.bpci_id.lower().strip()
        # Begin with the response file name without extension.
        out = self._out_file_path + '/responses_' + org + '_' + bpci
        # Write responses to XLSX.
        self.response_data.to_excel(out + '.xlsx', index=False)
        # Write responses to CSV.
        self.response_data.to_csv(out + '.csv', index=False, encoding='utf-8-sig')
        # Append to the master file.
        out_m = self._out_file_path + '/response_master_%s.csv' % self.now
        if not os.path.exists(out_m):
            self.response_data.to_csv(out_m, index=False, encoding='utf-8-sig')
        else:
            csv_in = {'mode':'a', 'header':False, 'index':False, 'encoding':'utf-8-sig'}
            self.response_data.to_csv(out_m, **csv_in)
        # Append to the master info file.
        info_m = self._out_file_path + '/info_%s.csv' % self.now
        if not os.path.exists(info_m):
            with open(info_m, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['organization', 'bpci_id'])
                writer.writerow([org, bpci])
        else:
            with open(info_m, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([org, bpci])
        # Begin with the raw response file name without extension.
        out = self._out_file_path + '/responses_raw_' + org
        out += '_' + self.bpci_id.lower().strip()
        # Write responses to XLSX.
        self.response_data_raw.to_excel(out + '.xlsx', index=False)
        # Write responses to CSV.
        self.response_data_raw.to_csv(out + '.csv', index=False, encoding='utf-8-sig')
        # Append to the master file. 
        out_m = self._out_file_path + '/response_raw_master_%s.csv' % self.now
        if not os.path.exists(out_m):
            self.response_data_raw.to_csv(out_m, index=False, encoding='utf-8-sig')
        else:
            csv_in = {'mode':'a', 'header':False, 'index':False, 'encoding':'utf-8-sig'}
            self.response_data_raw.to_csv(out_m, **csv_in)

    # Read-only properties.
    @property
    def bpci_id(self):
        return self._bpci_id

    @property
    def fields(self):
        return self._fields

    @property
    def info(self):
        return self._info

    @property
    def info_file_path(self):
        return self._info_file_path

    @property
    def now(self):
        return self._now

    @property
    def organization_name(self):
        return self._organization_name

    @property
    def pdf_file_path(self):
        return self._pdf_file_path

    @property
    def response_data(self):
        return self._response_data

    @property
    def response_data_raw(self):
        return self._response_data_raw


# def main():
#     """
#     Parameters: None
#     Returns:    None
#     """
#
#     # We first determine the names of the PDF and JSON files from the terminal
#     # input. The format of the terminal input should be:
#     # extract_pdf_fields -p <pdf_file_path> -j <json_file_path>
#     args = sys.argv[1:]
#     syntax = 'extract_pdf_fields -p <pdf_file_path> -j <json_file_path>'
#     is_file = False
#     # Get the PDF file path.
#     if ('-p' in args) and (len(args) > args.index('-p') + 1):
#         # In this case, '-p' is in the arguments and has an element following
#         # it. We thus extract that element.
#         pdf_file_path = args[args.index('-p') + 1]
#         # Ensure that that file exists.
#         if not os.path.exists(pdf_file_path):
#             # If it does not exist, we raise an error and exit.
#             msg = 'PDF file does not exist.'
#             raise ValueError(msg)
#         # If a file, ensure that the file is a PDF.
#         if os.path.isfile(pdf_file_path):
#             # We denote that the PDF file path is a file.
#             is_file = True
#             if not os.path.splitext(pdf_file_path)[1].lower() == '.pdf':
#                 # The file exists, but is not a PDF, so raise an error.
#                 msg = 'PDF file must have extension .pdf.'
#                 raise ValueError(msg)
#         # If a folder, get list of contained PDF files.
#         else:
#             # The PDF file path is a folder.
#             if_file = False
#             # The list of files in the folder.
#             fs = os.listdir(pdf_file_path)
#             # The list of PDF files in the folder.
#             pdfs = [x for x in fs if os.path.splitext(x)[1].lower() == '.pdf']
#             if len(pdfs) < 1:
#                 # If there are no PDF files in the folder, raise exception.
#                 msg = 'PDF folder does not contain and PDFs.'
#                 raise ValueError(msg)
#     else:
#         # In this case either the pdf file was not specified, or the flag '-p'
#         # was not used.
#         msg = 'PDF file path must be specified. \n'
#         msg += 'Proper syntax: \n' + syntax
#         raise ValueError(msg)
#     # Get the JSON file path.
#     if ('-j' in args) and (len(args) > args.index('-j') + 1):
#         # In this case, '-j' is in the arguments and has an element following
#         # it. We thus extract that element.
#         json_file_path = args[args.index('-j') + 1]
#         # Ensure that that file exists.
#         if not os.path.exists(json_file_path):
#             # If it does not exist, we raise an error and exit.
#             msg = 'JSON file does not exist.'
#             raise ValueError(msg)
#         # Ensure that the file is a JSON.
#         if not os.path.splitext(json_file_path)[1].lower() == '.json':
#             # The file exists, but is not a JSON, so raise an error.
#             msg = 'JSON file must have extension .json.'
#             raise ValueError(msg)
#     else:
#         # In this case either the json file was not specified, or the flag '-j'
#         # was not used.
#         msg = 'JSON file path must be specified. \n'
#         msg += 'Proper syntax: \n' + syntax
#         raise ValueError(msg)
#     # Having now the two needed file paths, we can initiate the extraction
#     # class. If dealing with one file, extract from it. If dealing with folder,
#     # extract from all files in the folder.
#     now = datetime.datetime.now().strftime('%Y%m%d')
#     if is_file:
#         epf = ExtractPdfFields(pdf_file_path, json_file_path, now)
#         # Write the results to PDF.
#         epf.export()
#     else:
#         for pdf in pdfs:
#             pdf_fp = pdf_file_path + '/' + pdf
#             epf = ExtractPdfFields(pdf_fp, json_file_path, now)
#             # Write the results to PDF.
#             epf.export()
#             # Generate Excel files from the CSV master files.
#             fp = './out/response_master_%s.csv' % epf.now
#             df = pd.read_csv(fp)
#             fp = './out/response_master_%s.xlsx' % epf.now
#             df.to_excel(fp, index=False)
#             fp = './out/response_raw_master_%s.csv' % epf.now
#             df = pd.read_csv(fp)
#             fp = './out/response_raw_master_%s.xlsx' % epf.now
#             df.to_excel(fp, index=False)
#
#
# if __name__ == '__main__':
#     main()
