#!/usr/bin/env python
# encoding: uft-8

import chimera.extension


class PoPMuSiCExtension(chimera.extension.EMO):

    def name(self):
        return 'PoPMuSiC-GUI'

    def description(self):
        return "Visual analysis of Dezyme's PoPMuSiC results"

    def categories(self):
        return ['InsiliChem']

    def icon(self):
        return

    def activate(self):
        self.module('gui').launch()

# Register an instance of 'MainChainEMO' with the Chimera
# extension manager.
chimera.extension.manager.registerExtension(PoPMuSiCExtension(__file__))
