# python extract_pdf_fields.py -p input/input_file_0.pdf -j info.json

from tkinter import *
from tkinter import ttk, filedialog, messagebox
from extract_pdf_fields import ExtractPdfFields
from Utils import Settings
from datetime import datetime
import os
import sys
import time

version = sys.version_info

class EPFGUI(Tk):

    def __init__(self, master=None):
        super(EPFGUI, self).__init__(master)

        self.finished = False # indicator of completion of PDF extraction job
        self.n_pdf_processed = 0 # number of PDF files processed
        self.dark_bg = '#333333'
        self.light_font = '#f2f2f2'
        self.theme_color = '#0074BF'
        self.cwd = os.getcwd()

        self.title('PDF Extraction Tool')
        self.resizable(width=False, height=False)
        self.json_ftypes = [('JSON', '*.json')]

        # ------------------------------------------- General Settings ----------------------------------------------
        # The content frame will hold all widgets
        self.content = Frame(self, padx=15, pady=15, bg=self.dark_bg)
        # This frame holds general settings
        self.main_frame = Frame(self.content, bg=self.dark_bg)

        # These are the variables that the users will update. These will be passed to the extract_pdf_fields.
        self.pdf_dir = StringVar()
        self.json_dir = StringVar()
        self.out_dir = StringVar()

        # When the file location entries are modified, check to see if they all have some value
        # If they do, enable the run button
        if version[1] < 6:
            self.pdf_dir.trace("w", self.check_file_entries)
            self.json_dir.trace("w", self.check_file_entries)
            self.out_dir.trace("w", self.check_file_entries)
        else:
            self.pdf_dir.trace_add("write", self.check_file_entries)
            self.json_dir.trace_add("write", self.check_file_entries)
            self.out_dir.trace_add("write", self.check_file_entries)

        # ------------------------------------------- General Settings ----------------------------------------------
        self.pdf_label = Label(self.main_frame, text='PDF Directory:', bg=self.dark_bg, fg=self.light_font, anchor=N)
        self.pdf_input = EPFEntry(self.main_frame, textvariable=self.pdf_dir, width=45)
        self.pdf_button = EPFButton(self.main_frame, text='Browse',
                                   command=lambda: self.browse_directory(self.pdf_input))
        self.json_label = Label(self.main_frame, text='Supplement File Directory:', bg=self.dark_bg, fg=self.light_font, anchor=N)
        self.json_input = EPFEntry(self.main_frame, textvariable=self.json_dir, width=45)
        self.json_button = EPFButton(self.main_frame, text='Browse',
                                   command=lambda: self.browse_file(self.json_input))
        self.out_label = Label(self.main_frame, text='Output Directory:', bg=self.dark_bg, fg=self.light_font, anchor=N)
        self.out_input = EPFEntry(self.main_frame, textvariable=self.out_dir, width=45)
        self.out_button = EPFButton(self.main_frame, text='Browse',
                                   command=lambda: self.browse_directory(self.out_input))

        self.file_dir_inputs = (self.pdf_input, self.json_input, self.out_input)
        self.run_button = EPFRunButton(self.content, text='Run', command=self.run_pdf_extraction)
        self.reset_button = EPFButton(self.content, text='Reset', command=self.reset_input)
        self.progress = ttk.Progressbar(self.content, orient=HORIZONTAL, length=100, mode='determinate') # progress bar

        # ----------------------------------------- Add Widgets to Window --------------------------------------------
        padx, pady = 4, 4
        self.content.pack(expand=True, fill=BOTH)
        self.main_frame.pack(fill=X)
        self.run_button.pack(side=RIGHT, anchor=E, pady=(pady, 0))
        self.reset_button.pack(side=RIGHT, anchor=E, padx=(0, padx), pady=(pady, 0))

        CreateToolTip(self.reset_button, 'Reset all directories to empty')

        self.pdf_label.grid(column=0, row=0, sticky=W)
        CreateToolTip(self.pdf_label, 'Directory of PDF files')
        self.pdf_input.grid(column=1, row=0, sticky=(E, W), padx=padx, pady=pady)
        self.pdf_button.grid(column=4, row=0, sticky=W, pady=pady)
        self.json_label.grid(column=0, row=1, sticky=W)
        CreateToolTip(self.json_label, 'JSON file storing structural information of PDF questionnaire')
        self.json_input.grid(column=1, row=1, sticky=(E, W), padx=padx, pady=pady)
        self.json_button.grid(column=4, row=1, sticky=W, pady=pady)
        self.out_label.grid(column=0, row=2, sticky=W)
        CreateToolTip(self.out_label, 'Directory of output files')
        self.out_input.grid(column=1, row=2, sticky=(E, W), padx=padx, pady=pady)
        self.out_button.grid(column=4, row=2, sticky=W, pady=pady)

        self.set_screen_position()

        # # TODO: Remove
        # ----------- TEST ONLY ----------------
        self.pdf_dir.set('C:/workfiles/PDF_Extraction/input')
        self.json_dir.set('C:/workfiles/PDF_Extraction/info.json')
        self.out_dir.set('C:/workfiles/PDF_Extraction/out')


    def run_pdf_extraction(self):
        self.n_pdf_processed = 0
        self.progress['value'] = 0
        self.progress.pack(side=RIGHT, anchor=E, padx=(0, 4), pady=(4, 0))
        settings = self.create_settings()
        pdf_fp = settings.pdf_dir
        info_fp = settings.json_dir
        out_fp = settings.out_dir
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        # if pdf_fp is a single PDF file dir, export once
        if os.path.isfile(pdf_fp):
            epf = ExtractPdfFields(pdf_fp, info_fp, out_fp, now)
            epf.export()
            self.n_pdf_processed+=1
            self.finished = True
        elif os.path.isdir(pdf_fp):
            # The list of files in the folder.
            fs = os.listdir(pdf_fp)
            # The list of PDF files in the folder.
            pdfs = [x for x in fs if os.path.splitext(x)[1].lower() == '.pdf']
            for pdf in pdfs:
                pdf_fp_file = pdf_fp + '/' + pdf
                epf = ExtractPdfFields(pdf_fp_file, info_fp, out_fp, now)
                epf.export()
                self.n_pdf_processed += 1
                self.progress['value']+=100*self.n_pdf_processed/len(pdfs)
                self.update_idletasks()
            self.progress['value']=100
            self.finished = True

        else:
            pass
        self.check_process()
        return None

    def create_settings(self):
        # The inputs are linked to a tkinter variable. Those values will have to be retrieved from each variable
        # and passed on to the settings objects
        return Settings(self.pdf_dir.get(), self.json_dir.get(), self.out_dir.get())

    def browse_file(self, file_input):
        file_name = filedialog.askopenfilename(initialdir=self.cwd, filetype=self.json_ftypes)
        file_input.delete(0, END)
        file_input.insert(0, file_name)

    def browse_directory(self, dir_input):
        dir_name = filedialog.askdirectory(initialdir=self.cwd)
        dir_input.delete(0, END)
        dir_input.insert(0, dir_name)

    def check_file_entries(self, *_):
        if self.pdf_input.get() and self.json_input.get() and self.out_input.get() and\
                os.path.exists(self.pdf_input.get()) and \
                os.path.exists(self.json_input.get()) and \
                os.path.exists(self.out_input.get()):
            self.run_button.config(state=NORMAL, bg=self.theme_color)
        else:
            self.run_button.config(state=DISABLED, bg='#99d6ff')

    def reset_input(self):
        for input in self.file_dir_inputs:
            input.delete(0, END)
        self.progress.pack_forget()

    def set_screen_position(self):
        self.update()
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        w, h = self.winfo_width(), self.winfo_height()
        x, y = ws/2 - w/2, hs/3 - h/2
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def check_process(self):
        # Check every 1000 ms whether the process is finished
        if self.finished:
            messagebox.showinfo('', 'Extraction completed: %s PDF files processed.'
                                    '\nOutput saved at %s' % (self.n_pdf_processed, self.out_dir.get()))
        else:
            self.after(1000, self.check_process)

class EPFEntry(Entry):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, borderwidth=2, highlightbackground='#FFFFFF', relief='flat',
                         highlightthickness=1,
                         font='-size 11', **kwargs)

class EPFButton(Button):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, foreground='#FFFFFF', background='#808080', font='-size 11', width=6,
                         relief='flat', activebackground='#FFFFFF', pady=0, bd=1, **kwargs)

class EPFRunButton(Button):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, foreground='#FFFFFF', background='#ccebff', font='-size 11', width=6,
                         relief='flat', activebackground='#FFFFFF', pady=0, bd=1, disabledforeground='#FFFFFF', state=DISABLED,
                         **kwargs)

# From StackOverflow: https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
class CreateToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.waittime = 500  # milliseconds
        self.wraplength = 180  # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tw, text=self.text, justify='left', background="#ffffff", relief='solid',
                      borderwidth=1, wraplength=self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()

gui = EPFGUI()
gui.mainloop()

# TODO: allow pdf input to be either file or directory - hard