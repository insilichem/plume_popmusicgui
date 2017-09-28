#!/usr/bin/env python
# encoding: utf-8


from __future__ import print_function, division
# Python stdlib
import Tkinter as tk
from tkFileDialog import askopenfilename
import os
from operator import itemgetter
import webbrowser as web
import Tix
import types
# Chimera stuff
import chimera
from chimera.widgets import MoleculeScrolledListBox, SortableTable
from chimera.baseDialog import ModelessDialog
from ShowAttr import ShowAttrDialog
# Additional 3rd parties

# Own
from plumesuite.ui import PlumeBaseDialog
from core import Controller, Model


ui = None
def showUI(callback=None):
    if chimera.nogui:
        tk.Tk().withdraw()
    global ui
    if not ui:
        ui = PoPMuSiCExtension()
    model = Model(gui=ui)
    controller = Controller(gui=ui, model=model)
    ui.enter()
    if callback:
        ui.addCallback(callback)


class PoPMuSiCExtension(PlumeBaseDialog):

    buttons = ('Run', 'Close')

    def __init__(self, *args, **kwargs):
        # GUI init
        self.title = 'Plume PoPMuSiC input'
        self.controller = None

        # Variables
        self._popsfile = tk.StringVar()
        self._popfile = tk.StringVar()

        # Fire up
        super(PoPMuSiCExtension, self).__init__(self, *args, **kwargs)

    def fill_in_ui(self, parent):
        note_frame = tk.LabelFrame(self.canvas, text='How to run PoPMuSiC')
        tk.Label(note_frame, text="PoPMuSiC is a web service!\nYou must register "
                                  "and run the jobs from:").pack(padx=5, pady=5)
        self.ui_web_btn = tk.Button(note_frame, text="PoPMuSiC web interface",
                  command=lambda *a: web.open_new(r"http://soft.dezyme.com/"))
        self.ui_web_btn.pack(padx=5, pady=5)

        input_frame = tk.LabelFrame(self.canvas, text='Select molecule and PoPMuSiC output files')
        input_frame.rowconfigure(0, weight=1)
        input_frame.columnconfigure(1, weight=1)
        self.ui_molecules = MoleculeScrolledListBox(input_frame)
        self.ui_molecules.grid(row=0, columnspan=3, padx=5, pady=5, sticky='news')
        entries = [('popfile', 'POP file', '.pop'), ('popsfile', 'POPS file', '.pops')]
        for i, (var, label, ext) in enumerate(entries):
            # Label
            tk.Label(input_frame, text=label).grid(row=i+1, column=0, padx=3, pady=3, sticky='e')
            # Field entry
            stringvar = getattr(self, '_' + var)
            entry = tk.Entry(input_frame, textvariable=stringvar)
            entry.grid(row=i+1, column=1, padx=3, pady=3, sticky='news')
            setattr(self, 'ui_' + var + '_entry', entry)
            # Button
            button = tk.Button(input_frame, text='...',
                    command=lambda v=stringvar, e=ext: self._browse_cb(v, e))
            button.grid(row=i+1, column=2, padx=3, pady=3)
            setattr(self, 'ui_' + var + '_button', button)

        note_frame.pack(fill='x', padx=5, pady=5)
        input_frame.pack(expand=True, fill='both', padx=5, pady=5)

    def Run(self):
        pass

    def Close(self):
        global ui
        ui = None
        super(PoPMuSiCExtension, self).Close()

    def _browse_cb(self, var, extension):
        path = askopenfilename()
        if os.path.isfile(path):
            var.set(path)


class PoPMuSiCResultsDialog(PlumeBaseDialog):

    buttons = ('Close',)
    _show_attr_dialog = None

    def __init__(self, molecule=None, controller=None, *args, **kwargs):
        self.molecule = molecule
        self.controller = controller
        self.title = 'PoPMuSiC results'
        if molecule:
            self.title += ' for {}'.format(molecule.name)

        # Private attrs
        self._data = None
        self._keys = None
        self._mutations = None
        self._previously_selected_residue = None
        # Fire up
        super(PoPMuSiCResultsDialog, self).__init__(self, *args, **kwargs)

    def fill_in_ui(self, parent):
        self.canvas.columnconfigure(0, weight=1)

        # Summary
        self.ui_summary_frame = tk.LabelFrame(master=self.canvas, text='Summary', width=1000)
        self.ui_summary_table = SortableTable(self.ui_summary_frame)

        self.ui_summary_actions_frame = tk.LabelFrame(self.canvas, text='Actions')
        self.ui_summary_actions_0 = tk.Button(self.ui_summary_actions_frame, text='Color by ddG',
                                          command=self.color_by_ddg)
        self.ui_summary_actions_1 = tk.Button(self.ui_summary_actions_frame, text='Color by SASA',
                                          command=self.color_by_sasa)
        self.ui_summary_actions_2 = tk.Button(self.ui_summary_actions_frame, text='Reset color',
                                          command=self.reset_colors)

        # Mutations
        self.ui_mutations_frame = tk.LabelFrame(master=self.canvas, text='Mutations')
        self.ui_mutations_table = SortableTable(self.ui_mutations_frame)

        self.ui_mutations_actions_frame = tk.LabelFrame(self.canvas, text='Actions')
        self.ui_mutations_actions_0 = tk.Button(self.ui_mutations_actions_frame, text='Apply suggested mutations',
                                            command=self.mutate_suggested)
        self.ui_mutations_actions_1 = tk.Button(self.ui_mutations_actions_frame, text='Apply selected mutation',
                                            command=self.mutate_selected)
        # Pack and grid
        self.ui_summary_frame.grid(row=0, column=0, sticky='news', padx=5, pady=5)
        self.ui_summary_table.pack(expand=True, fill='both', padx=5, pady=5)
        self.ui_summary_actions_frame.grid(row=0, column=1, sticky='news', padx=5, pady=5)
        self.ui_summary_actions_0.pack(padx=5, pady=5, fill='x')
        self.ui_summary_actions_1.pack(padx=5, pady=5, fill='x')
        self.ui_summary_actions_2.pack(padx=5, pady=5, fill='x')

        self.ui_mutations_frame.grid(row=1, column=0, sticky='news', padx=5, pady=5)
        self.ui_mutations_table.pack(expand=True, fill='both', padx=5, pady=5)
        self.ui_mutations_actions_frame.grid(row=1, column=1, sticky='news', padx=5, pady=5)
        self.ui_mutations_actions_0.pack(padx=5, pady=5, fill='x')
        self.ui_mutations_actions_1.pack(padx=5, pady=5, fill='x')


    def fillInData(self, data):
        if self._data is not None:
            raise ValueError("Dialog is already filled. Create another one if desired.")
        self._data = data

        # Patch and register the color callbacks before populating the tables
        self._table_monkey_patches()
        self.ui_mutations_table._callbacks.append(
            lambda: self.color_table(self.ui_mutations_table, self._color_mutations_table))
        self.ui_summary_table._callbacks.append(
            lambda: self.color_table(self.ui_summary_table, self._color_summary_table))
        # Go!
        self._populate()

    def _populate(self, data=None):
        if data is None:
            data = self._data

        summary, mutations, keys = [], {}, []
        for i, res in enumerate(data):
            entry = [i+1]
            key = ':{}.{} {}'.format(res.id, res.chain, res.residue_type)
            entry.append(key)
            entry.append(res.solvent_accessibility)
            entry.extend([res.ddG, res.negative_score, res.positive_score])
            summary.append(entry)
            keys.append(key)
            mutations[key] = res.mutations

        # Summary
        self._init_summary()
        self.ui_summary_table.setData(summary)
        try:
            self.ui_summary_table.launch(browseCmd=self.on_selection_cb, selectMode='single')
        except tk.TclError:
            self.ui_summary_table.refresh(rebuild=True)
        self.canvas.after(100, self.ui_summary_table.requestFullWidth)
        # self.canvas.after(100, lambda: self.color_table(self.ui_summary_table, self._color_summary_table))

        # Mutations
        self._init_mutations(keys)
        self._mutations = mutations

    def _init_summary(self):
        columns = ['#', 'Residue', 'Solvent Accessibility', 'ddG', 'Neg. score', 'Pos. score']
        for i, column in enumerate(columns):
            font, anchor, format_ = 'TkTextFont', 'center', '%s'
            if i > 1:
                font, anchor, format_ = ('Courier', 10), 'e', '%.2f'
            self.ui_summary_table.addColumn(column, itemgetter(i), font=font, anchor=anchor,
                                         headerAnchor='center', format=format_)

    def _init_mutations(self, residues):
        font, anchor, format_ = ('Courier', 10), 'e', '%.2f'
        self.ui_mutations_table.addColumn('Mutation', itemgetter(0))
        self.ui_mutations_table.addColumn('Solvent Accessibility', itemgetter(1), font=font, anchor=anchor,
                                         headerAnchor='center', format=format_)
        self.ui_mutations_table.addColumn('ddG', itemgetter(2), font=font, anchor=anchor,
                                         headerAnchor='center', format=format_)
        self.ui_mutations_table.setData([])
        self.ui_mutations_table.launch(selectMode="single")    

    def _populate_mutations(self, key):
        data = [(r, m[0], m[1]) for r, m in self._mutations[key].items()]
        self.ui_mutations_table.setData(data)
        self.ui_mutations_table.refresh(rebuild=True)

    @staticmethod
    def _color_summary_table(row):
        neg, pos = row[-2:]
        diff = neg + pos
        if diff < -0.5:
            return 'ForestGreen'

    @staticmethod
    def _color_mutations_table(row):
        ddg = row[-1]
        if ddg < 0:
            return 'ForestGreen' 

    # Callbacks
    def on_selection_cb(self, selected):
        key = selected[1] # Residue info is in 2nd cell
        self._populate_mutations(key)
        # Parse the residue number from key :123.A ASP, where 123 is what we want
        residue = next(r for r in self.molecule.residues if r.id.position == int(key.split('.')[0][1:]))
        if self._previously_selected_residue:
            for a in self._previously_selected_residue.atoms:
                a.display = False
        self._previously_selected_residue = residue
        for a in residue.atoms:
            a.display = True

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

    def mutate_suggested(self):
        self.controller.apply_favourable_mutations(conservative=True)

    def mutate_selected(self):
        # Get 2nd cell, and parse residue number
        resnum = int(self.ui_summary_table.selected()[1].split('.')[0][1:])
        mutation = self.ui_mutations_table.selected()[0]  # Mutation is 1st cell
        residue = self.molecule.findResidue(resnum)
        self.controller.apply_mutation(residue, mutation, criteria='chp')

    def color_table(self, table, color):
        if table.tixTable is None:
            return
        for i, row in enumerate(table._sortedData()):
            row_color = color(row)
            if not row_color:
                continue
            for j, col in enumerate(table.columns):
                col_style = {'anchor': getattr(col, 'anchor', None),
                             'wraplength': getattr(col, 'wrapLength', None),
                             'padx': col.textStyle['padx'],
                             'pady': col.textStyle['pady'],
                             'font': (col.fontFamily, col.fontSize)}
                style = Tix.DisplayStyle('text', foreground=row_color, **col_style)
                table.tixTable.subwidget_list['hlist'].item_configure(i, j, style=style)

    def _table_monkey_patches(self):
        """
        Apply patches to SortableTable instances to include callbacks on .refresh().
        Nasty, ugly, and functional :3
        """
        # Backup original refresh methods
        self.ui_mutations_table._old_refresh = self.ui_mutations_table.refresh
        self.ui_summary_table._old_refresh = self.ui_summary_table.refresh
        # Create callbacks list in both instances
        self.ui_mutations_table._callbacks = []
        self.ui_summary_table._callbacks = []
        def patched_refresh(obj, *args, **kwargs): 
            """ The patched refresh method """
            obj._old_refresh(*args, **kwargs)
            for cb in obj._callbacks:
                cb()
        # Bound the patched refresh to the instance with `types.MethodType`        
        self.ui_mutations_table.refresh = types.MethodType(patched_refresh, self.ui_mutations_table)
        self.ui_summary_table.refresh = types.MethodType(patched_refresh, self.ui_summary_table)