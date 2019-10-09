#!/usr/bin/python3

"""
Tue 18 Jun 2019 09:03:02 AM PDT

@author: aaron heuser

get_pdf_fields.py
"""


import csv
import os
import json
import PyPDF3
import shutil
import warnings
import codecs

class GetPdfFields:
    """
    Class used to determine the fields associated to each entry in a PDF.
    """

    def __init__(self, pdf_fp, items_fp):
        """
        Parameters: fp: str
                        The path to the PDF file.
        Returns:    None
        """

        # Set the PDF file path.
        self.pdf_file_path = pdf_fp
        self.pdf_basename = os.path.basename(pdf_fp)
        # Remove any existing folder structure.
        self.cleanup()
        # Set up the system.
        self._setup()
        # Import the info on the PDF items.
        self.item_file_path = items_fp
        self._import_items()
        # Set the current item to learn. As each item is learned, this will
        # advance through the list.
        self._set_current_item()

    def _check_differences(self):
        """
        Parameters: None
        Returns:    w: list
                        The list of keys that have differing values in the
                        original and copy PDFs.
        """

        # Check for differences in the two PDF fields.
        w = []
        for key, val in self.pdf_fields['o'].items():
            copy_val = self.pdf_fields['c'][key]
            if '/V' in val.keys():
                if '/V' in copy_val.keys():
                    if val['/V'] != copy_val['/V']:
                        w += [key]
                else:
                    # In this case there is a value added, that did not exist
                    # before, so a change has been made.
                    w += [key]
        return w

    def _copy_pdf(self):
        """
        Parameters: None
        Returns:    None
        """

        # Make a temporary folder.
        if not os.path.exists('./.tmp'):
            os.mkdir('./.tmp')
        # Copy the PDF.
        shutil.copy(self.pdf_file_path, './.tmp/tmp.pdf')
        # Make a backup of the original. 
        shutil.copy(self.pdf_file_path, './.tmp/' + self.pdf_basename)
        # Set the location property.
        self.pdf_copy_file_path = './.tmp/tmp.pdf'

    def _import_items(self):
        """
        Parameters: None
        Returns:    None
        """

        items = {}
        with open(self.item_file_path, 'r') as f:
            reader = csv.reader(f)
            # Get the column indices.
            cols = next(reader)
            cols_idx = {}
            for col in ['num', 'local', 'text', 'group', 'id']:
                cols_idx[col] = cols.index(col)
            for row in reader:
                num = int(row[cols_idx['num']])
                items[num] = {}
                for col in ['local', 'text', 'group', 'id']:
                    val = row[cols_idx[col]]
                    if col == 'local':
                        val = int(val)
                    if col == 'id':
                        if val[:-2]=='.0':
                            val = int(val)
                        elif len(val)>0:
                            val = float(val)
                    items[num][col] = val
        # Set self._items.
        self.items = items

    def _import_pdf_fields(self):
        """
        Parameters: None
        Returns:    None
        """

        self.pdf_fields = {}
        # Import the original PDF.
        pdf = self.pdf_file_path
        #pdf = codecs.open(self.pdf_file_path, 'rb', encoding='utf-8')
        # Set the PDF fields.
        self.pdf_fields['o'] = PyPDF3.PdfFileReader(pdf).getFields()
        # Import the copy PDF.
        pdf = self.pdf_copy_file_path
        #pdf = codecs.open(self.pdf_copy_file_path, 'rb', encoding='utf-8')
        # Set the PDF fields.
        self.pdf_fields['c'] = PyPDF3.PdfFileReader(pdf).getFields()

    def _set_current_item(self):
        """
        Parameters: None
        Returns:    None
        """

        # Go through the list of items and find the first one for which the
        # field map has not yet learned.
        current_nums = [x['num'] for x in self.field_map.values()]
        current_item = []
        for num in sorted(self.items.keys()):
            if not num in current_nums:
                current_item += [num]
                for key in ['local', 'text', 'group', 'id']:
                    current_item += [self.items[num][key]]
                break
        self.current_item = current_item

    def _setup(self, force=False):
        """
        Parameters: force: bool
                        If True, recreate the temporary folder regardless of
                        any existing files.
        Returns:    None
        """

        # This method is called when any operations are made on the PDF fields.
        # It will first check if the temporary folder exists, and if not,
        # complete the needed setup.
        if force:
            self.cleanup()
        check = [os.path.exists('./.tmp')]
        check += [os.path.exists('./.tmp/' + self.pdf_basename)]
        check += [os.path.exists('./.tmp/tmp.pdf')]
        if not all(check):
            self._copy_pdf()
            self._field_map = {}
        # We always reimport the PDF fields, since they can change at any time
        # (due to human interaction).
        self._import_pdf_fields()

    def cleanup(self):
        """
        Parameters: None
        Returns:    None
        """

        # Delete the temporary directory.
        if os.path.exists('./.tmp'):
            shutil.rmtree('./.tmp')

    def set_field(self):
        """
        Parameters: None
        Returns:    None
        """

        # Ensure a proper file structure exists.
        self._setup()
        # We need to get the field key associated to the known information.
        diffs = self._check_differences()
        # There should be one and only one difference.
        if len(diffs) < 1:
            msg = 'No differences found, so no field set.\nPlease ensure that '
            msg += 'a field was changed and the PDF saved.'
            print(msg)
            return
        elif len(diffs) > 1:
            msg = 'Multiple differences found, so no field set.\nPlease '
            msg += 'ensure that one and only one field was changed.\nThe PDF '
            msg += 'will now be replaced with the unedited original.'
            os.remove(self.pdf_file_path)
            shutil.copy('./.tmp/' + self.pdf_basename, self.pdf_file_path)
            print(msg)
            return
        # We know at this point that only one item has been changed, and we can
        # get the respective key.
        self.field_map[diffs[0]] = {}
        self.field_map[diffs[0]]['num'] = self.current_item[0]
        self.field_map[diffs[0]]['local'] = self.current_item[1]
        self.field_map[diffs[0]]['text'] = self.current_item[2]
        self.field_map[diffs[0]]['group'] = self.current_item[3]
        self.field_map[diffs[0]]['id'] = self.current_item[4]
        # Set the next current item.
        self._set_current_item()
        # print message to inform current item
        group = self.current_item[3]
        local = self.current_item[1]
        print('--- Next field to be set for group %s local %s' % (group, local))
        # Since a field has been set, we copy over the edited PDF to the
        # temporary PDF. This allows us to keep changing fields without having
        # to reset everything with each step.
        os.remove('./.tmp/tmp.pdf')
        shutil.copy(self.pdf_file_path, './.tmp/tmp.pdf')

    def write(self, reset=True, purge=False):
        """
        Parameters: reset: bool
                        If True, replace the edited file with the original
                        unedited version.
                    purge: bool
                        If True, do not recreate the temporary directory.
        Returns:    None
        """

        # Write the field map to file. First define the file name.
        fname = './{0}.json'.format(os.path.splitext(self.pdf_basename)[0])
        with open(fname, 'w') as out:
            json.dump(self.field_map, out, indent=2)
        if reset:
            # Remove the edited file.
            os.remove(self.pdf_file_path)
            # Copy the backup file.
            shutil.copy('./.tmp/' + self.pdf_basename, self.pdf_file_path)
            # Remove the temporary directory.
            shutil.rmtree('./.tmp')
            if not purge:
                # Recreate the temporary directory.
                self._copy_pdf()

    # Read-only properties.
    @property
    def field_map(self):
        """
        Parameters: None
        Returns:    field_map: dict
                        The map of field keys to associated information.
        """

        return self._field_map

    # Properties with read/write access.
    @property
    def current_item(self):
        """
        Parameters: None
        Returns:    val: list
                        The current item.
        """

        return self._current_item

    @current_item.setter
    def current_item(self, val):
        """
        Parameters: val: list
                        The list defined by [num, local, text, group].
        Returns:    None
        """

        warnings.simplefilter('always', UserWarning)
        # Check that we have a list of length 5.
        if not len(val) == 5:
            print(val)
            msg = 'Attempting to set current item list of incorrect length.'
            warnings.warn(msg)
            return
        # Ensure that the first two elements are int and the last two are str.
        if not isinstance(val[0], int):
            msg = 'Attempting to set current item number as a non-integer '
            msg += 'value.'
            warnings.warn(msg)
            return
        if not isinstance(val[1], int):
            msg = 'Attempting to set current item local number as a '
            msg += 'non-integer value.'
            warnings.warn(msg)
            return
        if not isinstance(val[2], str):
            msg = 'Attempting to set current item text as a non-string value.'
            warnings.warn(msg)
            return
        if not isinstance(val[3], str):
            msg = 'Attempting to set current item group as a non-string value.'
            warnings.warn(msg)
            return
        self._current_item = val
        warnings.simplefilter('default', UserWarning)

    @property
    def item_file_path(self):
        """
        Parameters: None
        Returns:    item_file_path: str
                        The path to the item CSV file.
        """

        return self._item_file_path

    @item_file_path.setter
    def item_file_path(self, val):
        """
        Parameters: val: str
                        The path to a CSV file.
        Returns:    None
        """

        # We want these warnings to always be shown.
        warnings.simplefilter('always', UserWarning)
        # Ensure that val exists.
        if not os.path.exists(val):
            warnings.warn('Trying to set non-existing CSV file.')
            return
        # Ensure that the file is a CSV.
        if not os.path.splitext(val)[1].lower() == '.csv':
            warnings.warn('Trying to set non-CSV file.')
            return
        # Since the above two tests have passed, set the pdf.
        self._item_file_path = val
        # Reset the warnings filter.
        warnings.simplefilter('default', UserWarning)

    @property
    def items(self):
        """
        Parameters: None
        Returns:    items: dict
                        The items information dictionary.
        """

        return self._items

    @items.setter
    def items(self, val):
        """
        Parameters: val: dict
                        An item information dictionary.
        Returns:    None
        """

        warnings.simplefilter('always', UserWarning)
        # Ensure it is a dictionary.
        if not isinstance(val, dict):
            warnings.warn('Attempting to set non-dict object as items.')
            return
        # We know it is a dictionary, so set the property.
        self._items = val
        warnings.simplefilter('default', UserWarning)

    @property
    def pdf_basename(self):
        """
        Parameters: None
        Returns:    basename: str
                        The name of the PDF file without the folder path.
        """

        return self._pdf_basename

    @pdf_basename.setter
    def pdf_basename(self, val):
        """
        Parameters: val: str
                        The PDF name.
        Returns:    None
        """

        self._pdf_basename = val

    @property
    def pdf_copy_file_path(self):
        """
        Parameters: None
        Returns:    pdf_file_path: str
                        The path to the PDF file.
        """

        return self._pdf_copy_file_path

    @pdf_copy_file_path.setter
    def pdf_copy_file_path(self, val):
        """
        Parameters: val: str
                        The path to a PDF file.
        Returns:    None
        """

        # We want these warnings to always be shown.
        warnings.simplefilter('always', UserWarning)
        # Ensure that val exists.
        if not os.path.exists(val):
            warnings.warn('Trying to set non-existing PDF file.')
            return
        # Ensure that the file is a PDF.
        if not os.path.splitext(val)[1].lower() == '.pdf':
            warnings.warn('Trying to set non-PDF file.')
            return
        # Since the above two tests have passed, set the pdf.
        self._pdf_copy_file_path = val
        # Reset the warnings filter.
        warnings.simplefilter('default', UserWarning)

    @property
    def pdf_file_path(self):
        """
        Parameters: None
        Returns:    pdf_file_path: str
                        The path to the PDF file.
        """

        return self._pdf_file_path

    @pdf_file_path.setter
    def pdf_file_path(self, val):
        """
        Parameters: val: str
                        The path to a PDF file.
        Returns:    None
        """

        # We want these warnings to always be shown.
        warnings.simplefilter('always', UserWarning)
        # Ensure that val exists.
        if not os.path.exists(val):
            warnings.warn('Trying to set non-existing PDF file.')
            return
        # Ensure that the file is a PDF.
        if not os.path.splitext(val)[1].lower() == '.pdf':
            warnings.warn('Trying to set non-PDF file.')
            return
        # Since the above two tests have passed, set the pdf.
        self._pdf_file_path = val
        # Reset the warnings filter.
        warnings.simplefilter('default', UserWarning)

    @property
    def pdf_fields(self):
        """
        Parameters: None
        Returns:    pdf_fields: str
                        The dictionary of PDF fields..
        """

        return self._pdf_fields

    @pdf_fields.setter
    def pdf_fields(self, val):
        """
        Parameters: val: dict
                        The PDF fields dictionary.
        Returns:    None
        """

        warnings.simplefilter('always', UserWarning)
        # Ensure it is a dictionary.
        if not isinstance(val, dict):
            warnings.warn('Attempting to set non-dict object as PDF fields.')
            return
        # We know it is a dictionary, so set the property.
        self._pdf_fields = val
        warnings.simplefilter('default', UserWarning)
