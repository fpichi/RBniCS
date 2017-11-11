# Copyright (C) 2015-2017 by the RBniCS authors
#
# This file is part of RBniCS.
#
# RBniCS is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RBniCS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with RBniCS. If not, see <http://www.gnu.org/licenses/>.
#

# Check that dolfin has been compiled with PETSc and SLEPc
from dolfin import has_petsc, has_linear_algebra_backend, parameters, has_slepc
assert has_petsc()
assert has_linear_algebra_backend("PETSc")
assert parameters["linear_algebra_backend"] == "PETSc"
assert has_slepc()

# Import modules
from rbnics.backends.dolfin.abs import abs
from rbnics.backends.dolfin.adjoint import adjoint
from rbnics.backends.dolfin.affine_expansion_storage import AffineExpansionStorage
from rbnics.backends.dolfin.assign import assign
from rbnics.backends.dolfin.basis_functions_matrix import BasisFunctionsMatrix
from rbnics.backends.dolfin.copy import copy
from rbnics.backends.dolfin.eigen_solver import EigenSolver
from rbnics.backends.dolfin.evaluate import evaluate
from rbnics.backends.dolfin.export import export
from rbnics.backends.dolfin.function import Function
from rbnics.backends.dolfin.functions_list import FunctionsList
from rbnics.backends.dolfin.gram_schmidt import GramSchmidt
from rbnics.backends.dolfin.high_order_proper_orthogonal_decomposition import HighOrderProperOrthogonalDecomposition
from rbnics.backends.dolfin.import_ import import_
from rbnics.backends.dolfin.linear_solver import LinearSolver
from rbnics.backends.dolfin.matrix import Matrix
from rbnics.backends.dolfin.max import max
from rbnics.backends.dolfin.mesh_motion import MeshMotion
from rbnics.backends.dolfin.nonlinear_solver import NonlinearSolver
from rbnics.backends.dolfin.parametrized_expression_factory import ParametrizedExpressionFactory
from rbnics.backends.dolfin.parametrized_tensor_factory import ParametrizedTensorFactory
from rbnics.backends.dolfin.product import product
from rbnics.backends.dolfin.proper_orthogonal_decomposition import ProperOrthogonalDecomposition
from rbnics.backends.dolfin.reduced_mesh import ReducedMesh
from rbnics.backends.dolfin.reduced_vertices import ReducedVertices
from rbnics.backends.dolfin.separated_parametrized_form import SeparatedParametrizedForm
from rbnics.backends.dolfin.snapshots_matrix import SnapshotsMatrix
from rbnics.backends.dolfin.sum import sum
from rbnics.backends.dolfin.symbolic_parameters import SymbolicParameters
from rbnics.backends.dolfin.tensor_basis_list import TensorBasisList
from rbnics.backends.dolfin.tensor_snapshots_list import TensorSnapshotsList
from rbnics.backends.dolfin.tensors_list import TensorsList
from rbnics.backends.dolfin.time_quadrature import TimeQuadrature
from rbnics.backends.dolfin.time_stepping import TimeStepping
from rbnics.backends.dolfin.transpose import transpose
from rbnics.backends.dolfin.vector import Vector

__all__ = [
    'abs',
    'adjoint',
    'AffineExpansionStorage',
    'assign',
    'BasisFunctionsMatrix',
    'copy',
    'EigenSolver',
    'evaluate',
    'export',
    'Function',
    'FunctionsList',
    'GramSchmidt',
    'HighOrderProperOrthogonalDecomposition',
    'import_',
    'LinearSolver',
    'Matrix',
    'max',
    'MeshMotion',
    'NonlinearSolver',
    'ParametrizedExpressionFactory',
    'ParametrizedTensorFactory',
    'product',
    'ProperOrthogonalDecomposition',
    'ReducedMesh',
    'ReducedVertices',
    'SeparatedParametrizedForm',
    'SnapshotsMatrix',
    'sum',
    'SymbolicParameters',
    'TensorBasisList',
    'TensorSnapshotsList',
    'TensorsList',
    'TimeQuadrature',
    'TimeStepping',
    'transpose',
    'Vector'
]
