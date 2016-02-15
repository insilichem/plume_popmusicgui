#!/usr/bin/env python
# encoding: utf-8

import os
from collections import namedtuple
import chimera
from Rotamers import useBestRotamers



class Controller(object):

    def __init__(self, molecule, path, *args, **kwargs):
        self.molecule = molecule
        self.model = Model(path)
        if self.check():
            self.set_attributes()

    def check(self):
        """
        Basic tests to assert everything is in order.

        Test 1 - Number of residues in molecule should be the same in PoPMuSiC summary
        Test 2 - Sequence of those residues should be the same in both cases
        """
        if len(self.molecule.residues) != len(self.model.residues):
            raise ValueError("Number of residues do not match")
        if any(res.type != row.residue for (res, row) in zip(self.molecule.residues, self.model.residues)):
            raise ValueError("Sequences do not match")
        return True

    def set_attributes(self):
        """
        Copy PoPMuSiC data into each residue attributes. They will be
        prefixed with 'popmusic_'.
        """
        for res, row in zip(self.molecule.residues, self.model.residues):
            for name, value in zip(row._fields, row):
                if isinstance(value, float):
                    setattr(res, 'popmusic_' + name, value)

    def render_labels(self, field='ddG', color=None):
        """
        Add labels to each residue in molecule

        Parameters
        ----------
        field : str, optional
            Name of the popmusic field to render

        color : chimera.Color, optional
            Color of the label text
        """
        for res, row in zip(self.molecule.residues, self.model.residues):
            res.label = str(getattr(row, 'popmusic_' + field, ''))
            res.labelColor = color

    def clear_labels(self):
        """
        Remove all existing labels in molecule
        """
        for res in self.molecule.residues:
            res.label, res.labelColor = '', None

    def apply_favourable_mutations(self, conservative=True):
        """
        Find most favourable mutations in model and apply them. 

        Parameters
        ----------
        conservative: bool, optional
            Only those with an overall negative ddG will be candidates.
        """
        candidates = self.residues
        if conservative:
            candidates = [r for r in self.model.residues if (r.negative + r.positive) < 0]

        for c in candidates:
            new_type, values = min(c.mutations.iteritems(), key=lambda k, v: v.ddG)
            if values.ddG < 0:
                residue = self.molecule.findResidue(c.id)
                self.apply_mutation(residue, new_type)

    def apply_mutation(residue, new_type, criteria='cp'):
        """
        Apply requested mutation to residue using the best rotamer according to criteria.

        Parameters
        ----------
        residue : chimera.Residue
        new_type : str
            Desired mutation, with 3-letter code
        criteria : str, optional
            Optimization targets. Must be a string of four letters max. Each letter represents
            a method to be used, in the order of the string.
            d -> density, h-> H-bonds maximization, c-> clash minimization, p-> probability.
            Allowed combinations would be `dhcp`, `cp`, or even `p`.
        """
        useBestRotamers(new_type, [residue], criteria=criteria)


class Model(object):

    """
    Load .pop and .pops files into the same data object, with this structure:

    Model: list
    - residue: namedtuple
        - chain: str
        - id: int 
        - residue_type: str
        - secondary_structure: str
        - solvent_accesibility: float
        - ddG: float
        - negative_score: float
        - positive_score: float
        - mutations: dict
            - residue_type, ddG: str, float

    """

    def __init__(self, path):
        self.path = path
        self.residues = self.load_data()

    def keys(self):
        return self.residues[0]._fields

    def load_data(self):
        files = os.listdir(self.path)
        pop = next(f for f in files if f.endswith('.pop'))
        pops = next(f for f in files if f.endswith('.pops'))

        return list(self.parse(os.path.join(self.path, pops), os.path.join(self.path, pop)))

    @staticmethod
    def parse(pops, pop):
        """
        Load PoPMuSiC data from .pops and .pop file (summary and individual data)
        into a single object representation

        Parameters
        ----------
        pops, pop : str
            Path to .pops and .pop files, respectively

        Yields
        ------
        NamedResidue : namedtuple
            NamedResidue instances for each line in .pops file, and, subsequently,
            for each residue in molecule
        """
        datapop = list(parse_pop(pop))
        for line in iterlines(pops):
            chain, i, res, ss, sa, ddg, neg, pos = line.split()
            i = int(i)
            sa, ddg, neg, pos = map(float, (sa, ddg, neg, pos))
            mutation_list = [m for m in datapop if m.chain == chain and m.id == i]
            mutations = {m.residue_mutated: NamedMutation(m.sa, m.ddG)
                         for m in mutation_list}
            yield NamedResidue(chain, i, res, ss, sa, ddg, neg, pos, mutations)


###
# Helpers
###


def parse_pop(path):
    """
    Parse a .pop file

    Yields
    ------
    PopTuple : namedtuple
        PopTuple instances for each line in file
    """
    for line in iterlines(path):
        chain, i, wt, mt, ss, sa, ddg = line.split()
        i, sa, ddg = int(i), float(sa), float(ddg)
        yield PopTuple(chain, i, wt, mt, ss, sa, ddg)


def iterlines(path):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                yield line

PopTuple = namedtuple('PopMusicPOP', ['chain', 'id', 'residue_wildtype', 'residue_mutated',
                                      'ss', 'sa', 'ddG'])
NamedResidue = namedtuple("NamedResidue",
                          ['chain', 'id', 'residue', 'secondary_structure',
                           'solvent_accesibility', 'ddG', 'negative', 'positive', 'mutations'])
NamedMutation = namedtuple("NamedMutation", ['solvent_accesibility', 'ddG'])
