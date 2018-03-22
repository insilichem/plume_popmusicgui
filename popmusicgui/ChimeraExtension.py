#!/usr/bin/env python
# encoding: utf-8


from __future__ import print_function, division
import chimera.extension


class PoPMuSiCExtension(chimera.extension.EMO):

    def name(self):
        return 'Tangram PoPMuSiC'

    def description(self):
        return "Design mutant proteins with controlled thermodynamic stability properties"

    def categories(self):
        return ['InsiliChem']

    def icon(self):
        return

    def activate(self):
        self.module('gui').showUI()


chimera.extension.manager.registerExtension(PoPMuSiCExtension(__file__))
