#!/usr/bin/env python
# encoding: uft-8

# Python
import Tkinter
# Chimera
import chimera
from chimera.baseDialog import ModelessDialog
# Own
from core import Controller, Model

ui = None


def showUI(callback=None):
    """
    Requested by Chimera way-of-doing-things
    """
    global ui
    if not ui:
        ui = PoPMuSiCDialog()
    ui.enter()
    if callback:
        ui.addCallback(callback)


class PoPMuSiCDialog(ModelessDialog):

    """
    Displays main GUI and initializes models and controllers
    for the respective file format.
    """

    buttons = ('OK', 'Close')
    default = None
    help = 'https://bitbucket.org/insilichem'

    def __init__(self, path, filetype, *args, **kwarg):
        # GUI init
        self.title = 'PoPMuSiC-GUI'
        self.path = path
        self.controller = Controller(path, filetype)

        # Fire up
        ModelessDialog.__init__(self)
        chimera.extension.manager.registerInstance(self)

    def fillInUI(self, parent):
        # Create main window
        self.tframe = Tkinter.Frame(parent)
        self.tframe.pack(expand=True, fill='both')

    def Apply(self):
        """
        Close unselected entries
        """
        pass

    def OK(self):
        self.Apply()
        self.destroy()

    def Close(self):
        """
        Close everything amd exit
        """
        self.destroy()
