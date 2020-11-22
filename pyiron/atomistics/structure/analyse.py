# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import numpy as np
from pyiron_base import Settings
from sklearn.cluster import AgglomerativeClustering

__author__ = "Joerg Neugebauer, Sam Waseda"
__copyright__ = (
    "Copyright 2020, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "1.0"
__maintainer__ = "Sam Waseda"
__email__ = "waseda@mpie.de"
__status__ = "production"
__date__ = "Sep 1, 2017"

s = Settings()

class Analyse:
    """ Class to analyse atom structure.  """
    def __init__(self, structure):
        """
        Args:
            structure (pyiron.atomistics.structure.atoms.Atoms): reference Atom structure
        """
        self._structure = structure

    def get_layers(self, distance_threshold=0.01, id_list=None, wrap_atoms=True, planes=None):
        """
        Get an array of layer numbers.

        Args:
            distance_threshold (float): Distance below which two points are
                considered to belong to the same layer. For detailed
                description: sklearn.cluster.AgglomerativeClustering
            id_list (list/numpy.ndarray): List of atoms for which the layers
                should be considered.
            planes (list/numpy.ndarray): Planes along which the layers are calculated. Planes are
                given in vectors, i.e. [1, 0, 0] gives the layers along the x-axis. Default planes
                are orthogonal unit vectors: [[1, 0, 0], [0, 1, 0], [0, 0, 1]]. If you have a
                tilted box and want to calculate the layers along the directions of the cell
                vectors, use `planes=np.linalg.inv(structure.cell).T`. Whatever values are
                inserted, they are internally normalized, so whether [1, 0, 0] is entered or
                [2, 0, 0], the results will be the same.

        Returns: Array of layer numbers (same shape as structure.positions)

        Example I - how to get the number of layers in each direction:

        >>> structure = Project('.').create_structure('Fe', 'bcc', 2.83).repeat(5)
        >>> print('Numbers of layers:', np.max(structure.analyse.get_layers(), axis=0)+1)

        Example II - get layers of only one species:

        >>> print('Iron layers:', structure.analyse.get_layers(
        ...       id_list=structure.select_index('Fe')))
        """
        if distance_threshold <= 0:
            raise ValueError('distance_threshold must be a positive float')
        if id_list is None:
            id_list = np.arange(len(self._structure))
        if len(id_list)==0:
            raise ValueError('id_list must contain at least one id')
        positions = self._structure.positions[np.array(id_list)]
        if wrap_atoms:
            positions = self._structure.get_wrapped_coordinates(positions)
        if planes is not None:
            mat = np.asarray(planes).reshape(-1, 3)
            positions = np.einsum('ij,i,nj->ni', mat, 1/np.linalg.norm(mat, axis=-1), positions)
        layers = []
        for x in positions.T:
            cluster = AgglomerativeClustering(
                linkage='complete',
                n_clusters=None,
                distance_threshold=distance_threshold
            ).fit(x.reshape(-1,1))
            first_occurrences = np.unique(cluster.labels_, return_index=True)[1]
            permutation = x[first_occurrences].argsort().argsort()
            layers.append(permutation[cluster.labels_])
        if planes is not None and len(np.asarray(planes).shape)==1:
            return np.asarray(layers).flatten()
        return np.vstack(layers).T
