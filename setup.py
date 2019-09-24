######### setup.py for cx_Freeze ##########

import sys
from cx_Freeze import setup, Executable
import os

os.environ['TCL_LIBRARY'] = "C:\\Anaconda3\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\Anaconda3\\tcl\\tk8.6"

build_exe_options = {"packages": ["pandas","numpy"], "excludes": []}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name = "PDF Extraction Tool",
    version = "0.1",
    description = "A tool to automatically extract information from PDF and export as CSV/Excel tables",
    options={"build_exe": build_exe_options},
    executables = [Executable("GUI.py", base=base)])



# ########## setup.py for py2exe ########## TODO: py2exe not working
# from distutils.core import setup
# import py2exe
#
# setup(
#     console=['setup.py'],
#     options = {
#         'py2exe': {
#             'optimize': 2,
#             'includes': ['extract_pdf_fields.py', 'Utils.py'],
#             'packages': ['ExtractPdfFields', 'Settings']
#         }
#     }
# )