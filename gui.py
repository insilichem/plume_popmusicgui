#!/usr/bin/env python
# encoding: utf-8

# Get used to importing this in your Py27 projects!
from __future__ import print_function, division
# Python stdlib
import Tkinter as tk
from tkFileDialog import askopenfilename
import os
from operator import itemgetter
import webbrowser as web
# Chimera stuff
import chimera
from chimera.widgets import MoleculeScrolledListBox, SortableTable
from chimera.baseDialog import ModelessDialog
from ShowAttr import ShowAttrDialog
# Additional 3rd parties

# Own
from core import Controller, Model

"""
The gui.py module contains the interface code, and only that. 
It should only 'draw' the window, and should NOT contain any
business logic like parsing files or applying modifications
to the opened molecules. That belongs to core.py.
"""

# This is a Chimera thing. Do it, and deal with it.
ui = None
def showUI(callback=None):
    """
    Requested by Chimera way-of-doing-things
    """
    if chimera.nogui:
        tk.Tk().withdraw()
    global ui
    if not ui:  # Edit this to reflect the name of the class!
        ui = PoPMuSiCExtension()
    model = Model(gui=ui)
    controller = Controller(gui=ui, model=model)
    ui.enter()
    if callback:
        ui.addCallback(callback)

ENTRY_STYLE = {
    'background': 'white',
    'borderwidth': 1,
    'highlightthickness': 0,
    'insertwidth': 1,
}
BUTTON_STYLE = {
    'borderwidth': 1,
    'highlightthickness': 0,
}


class PoPMuSiCExtension(ModelessDialog):

    """
    To display a new dialog on the interface, you will normally inherit from
    ModelessDialog class of chimera.baseDialog module. Being modeless means
    you can have this dialog open while using other parts of the interface.
    If you don't want this behaviour and instead you want your extension to 
    claim exclusive usage, use ModalDialog.
    """

    buttons = ('Run', 'Close')
    default = None
    help = 'https://www.insilichem.com'

    def __init__(self, *args, **kwarg):
        # GUI init
        self.title = 'Plume PoPMuSiC input'
        self.controller = None

        # Variables
        self._popsfile = tk.StringVar()
        self._popfile = tk.StringVar()

        # Fire up
        ModelessDialog.__init__(self)
        if not chimera.nogui:  # avoid useless errors during development
            chimera.extension.manager.registerInstance(self)

    def _initialPositionCheck(self, *args):
        try:
            ModelessDialog._initialPositionCheck(self, *args)
        except Exception as e:
            if not chimera.nogui:  # avoid useless errors during development
                raise e

    def fillInUI(self, parent):
        """
        This is the main part of the interface. With this method you code
        the whole dialog, buttons, textareas and everything.
        """
        # Create main window
        self.parent = parent
        self.canvas = tk.Frame(parent)
        self.canvas.pack(expand=True, fill='both')

        note_frame = tk.LabelFrame(self.canvas, text='How to run PoPMuSiC')
        tk.Label(note_frame, text="PoPMuSiC is a web service!\nYou must register " 
                                  "and run the jobs from:").pack(padx=5, pady=5)
        tk.Button(note_frame, text="PoPMuSiC web interface",
                  command=lambda *a: web.open_new(r"http://soft.dezyme.com/"),
                  **BUTTON_STYLE).pack(padx=5, pady=5)

        input_frame = tk.LabelFrame(self.canvas, text='Select molecule and PoPMuSiC output files')
        input_frame.rowconfigure(0, weight=1)
        input_frame.columnconfigure(1, weight=1)
        self.molecules = MoleculeScrolledListBox(input_frame)
        self.molecules.grid(row=0, columnspan=3, padx=5, pady=5, sticky='news')
        entries = [('popfile', 'POP file', '.pop'), ('popsfile', 'POPS file', '.pops')]
        for i, (var, label, ext) in enumerate(entries):
            # Label
            tk.Label(input_frame, text=label).grid(row=i+1, column=0, padx=3, pady=3, sticky='e')
            # Field entry
            stringvar = getattr(self, '_' + var)
            entry = tk.Entry(input_frame, textvariable=stringvar, **ENTRY_STYLE)
            entry.grid(row=i+1, column=1, padx=3, pady=3, sticky='news')
            setattr(self, var + '_entry', entry)
            # Button
            button = tk.Button(input_frame, text='...', **BUTTON_STYLE)
            button.configure(command=lambda v=stringvar, e=ext: self._browse_cb(v, e))
            button.grid(row=i+1, column=2, padx=3, pady=3)
            setattr(self, var + '_button', button)
        
        note_frame.pack(fill='x', padx=5, pady=5)
        input_frame.pack(expand=True, fill='both', padx=5, pady=5)

    def Run(self):
        """
        Default! Triggered action if you click on an Apply button
        """
        pass

    def Close(self):
        """
        Default! Triggered action if you click on the Close button
        """
        global ui
        ui = None
        ModelessDialog.Close(self)
        self.destroy()

    # Below this line, implement all your custom methods for the GUI.
    def _browse_cb(self, var, extension):
        path = askopenfilename(parent=self.parent)
        if os.path.isfile(path):
            var.set(path)

class PoPMuSiCResultsDialog(ModelessDialog):

    buttons = ('Close')
    _show_attr_dialog = None

    def __init__(self, parent=None, molecule=None, *args, **kwargs):
        self.parent = parent
        self.molecule = molecule
        self.title = 'PropKa results'
        if molecule:
            self.title += ' for {}'.format(molecule.name)
        
        # Private attrs
        self._data = None
        
        # Fire up
        ModelessDialog.__init__(self, *args, **kwargs)
        if not chimera.nogui:
            chimera.extension.manager.registerInstance(self)

    def _initialPositionCheck(self, *args):
        try:
            ModelessDialog._initialPositionCheck(self, *args)
        except Exception as e:
            if not chimera.nogui:
                raise e

    def fillInUI(self, parent):
        self.canvas = tk.Frame(parent, width=800)
        self.canvas.pack(expand=True, fill='both', padx=5, pady=5)
        self.canvas.columnconfigure(0, weight=1)

        self.table_frame = tk.LabelFrame(master=self.canvas, text='Per-residue information')
        self.table_menu = tk.OptionMenu
        self.table = SortableTable(self.table_frame)

        self.actions_frame = tk.LabelFrame(self.canvas, text='Actions')
        self.actions = [tk.Button(self.actions_frame, text='Color by ddG', command=self.color_by_ddg),
                        tk.Button(self.actions_frame, text='Color by SASA', command=self.color_by_sasa),
                        tk.Button(self.actions_frame, text='Reset color', command=self.reset_colors)]


        # Pack and grid
        self.table_frame.grid(row=0, columnspan=1, sticky='news', padx=5, pady=5)
        self.table.pack(expand=True, fill='both', padx=5, pady=5)

        self.actions_frame.grid(row=0, column=1, sticky='news', padx=5, pady=5)
        for button in self.actions:
            button.pack(padx=5, pady=5, fill='x')

    def fillInData(self, data):
        self._data = data
        self._populate_table()

    def _populate_table(self, data=None):
        if data is None:
            data = self._data

        columns = ['#', 'Residue', 'Solvent Accessibility', 'ddG', 'Neg. score', 'Pos. score']
        for i, column in enumerate(columns):
            self.table.addColumn(column, itemgetter(i))
        
        table_data = []
        for i, res in enumerate(data):
            entry = [i+1, ':{}.{} {}'.format(res.id, res.chain, res.residue_type)]
            entry.append(res.solvent_accessibility)
            entry.extend([res.ddG, res.negative_score, res.positive_score])
            table_data.append(entry)
        
        self.table.setData(table_data)
        try: 
            self.table.launch()
        except tk.TclError: 
            self.table.refresh(rebuild=True)

    def color_by_ddg(self):
        self.render_by_attr('popmusic_ddG', colormap='Rainbow')

    def color_by_sasa(self):
        self.render_by_attr('popmusic_solvent_accessibility', colormap='Rainbow')
    
    def render_by_attr(self, attr, colormap='Blue-Red', histogram_values=None):
        if self._show_attr_dialog is None:
            self._show_attr_dialog = ShowAttrDialog()

        d = self._show_attr_dialog
        d.enter()
        d.configure(models=[self.molecule], attrsOf='residues', attrName=attr)
        if isinstance(histogram_values, list) and len(histogram_values) == 2:
            d.histogram()['datasource'] = histogram_values + [lambda n: d._makeBins(n, 'Render')]
        d.colorAtomsVar.set(0)
        d.setPalette(colormap)
        d.paletteMenu.setvalue(colormap)
        d.paletteMenu.invoke()
        # Let the histogram end its calculations; otherwise errors will ocurr
        d.uiMaster().after(500, d.Apply)

    def reset_colors(self):
        for r in self.molecule.residues:
            r.ribbonColor = None