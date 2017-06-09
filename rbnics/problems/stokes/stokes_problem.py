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

from rbnics.problems.base import ParametrizedDifferentialProblem
from rbnics.backends import Function, LinearSolver, product, sum, transpose
from rbnics.utils.decorators import Extends, override

# Base class containing the definition of saddle point problems
@Extends(ParametrizedDifferentialProblem)
class StokesProblem(ParametrizedDifferentialProblem):
    
    ## Default initialization of members
    @override
    def __init__(self, V, **kwargs):
        # Call to parent
        ParametrizedDifferentialProblem.__init__(self, V, **kwargs)
        
        # Form names for saddle point problems
        self.terms = [
            "a", "b", "bt", "f", "g",
            # Auxiliary terms for supremizer enrichment
            "bt_restricted"
        ]
        self.terms_order = {
            "a": 2, "b": 2, "bt": 2, "f": 1, "g": 1,
            # Auxiliary terms for supremizer enrichment
            "bt_restricted": 2
        }
        self.components = ["u", "s", "p"]
        
        # Auxiliary storage for supremizer enrichment, using a subspace of V
        self._supremizer = Function(V, "s")
        
    ## Perform a truth solve
    @override
    def _solve(self, **kwargs):
        assembled_operator = dict()
        for term in ("a", "b", "bt", "f", "g"):
            assembled_operator[term] = sum(product(self.compute_theta(term), self.operator[term]))
        assembled_dirichlet_bc = dict()
        for component in ("u", "p"):
            if self.dirichlet_bc[component] is not None:
                assembled_dirichlet_bc[component] = sum(product(self.compute_theta("dirichlet_bc_" + component), self.dirichlet_bc[component]))
        if len(assembled_dirichlet_bc) == 0:
            assembled_dirichlet_bc = None
        solver = LinearSolver(
            assembled_operator["a"] + assembled_operator["b"] + assembled_operator["bt"],
            self._solution,
            assembled_operator["f"] + assembled_operator["g"],
            assembled_dirichlet_bc
        )
        solver.solve()
    
    def solve_supremizer(self):
        assert len(self.inner_product["s"]) == 1 # the affine expansion storage contains only the inner product matrix
        assembled_operator_lhs = self.inner_product["s"][0]
        assembled_operator_bt = sum(product(self.compute_theta("bt_restricted"), self.operator["bt_restricted"]))
        assembled_operator_rhs = assembled_operator_bt*self._solution
        if self.dirichlet_bc["s"] is not None:
            assembled_dirichlet_bc = sum(product(self.compute_theta("dirichlet_bc_s"), self.dirichlet_bc["s"]))
        else:
            assembled_dirichlet_bc = None
        solver = LinearSolver(
            assembled_operator_lhs,
            self._supremizer,
            assembled_operator_rhs,
            assembled_dirichlet_bc
        )
        solver.solve()
        return self._supremizer
        
    ## Export solution to file
    @override
    def export_solution(self, folder, filename, solution=None, component=None, suffix=None):
        if component is None:
            component = ["u", "p"] # but not "s"
        ParametrizedDifferentialProblem.export_solution(self, folder, filename, solution=solution, component=component, suffix=suffix)
    
    # Custom combination of inner products *not* to add inner product corresponding to supremizers
    def _combine_all_inner_products(self):
        # Temporarily change self.components
        components_bak = self.components
        self.components = ["u", "p"]
        # Call Parent
        StokesProblem_Base._combine_all_inner_products(self)
        # Restore
        self.components = components_bak
        
    # Custom combination of inner products *not* to add projection inner product corresponding to supremizers
    def _combine_all_projection_inner_products(self):
        # Temporarily change self.components
        components_bak = self.components
        self.components = ["u", "p"]
        # Call Parent
        StokesProblem_Base._combine_all_projection_inner_products(self)
        # Restore
        self.components = components_bak
        
    # Custom combination of Dirichlet BCs *not* to add BCs corresponding to supremizers
    def _combine_and_homogenize_all_dirichlet_bcs(self):
        # Temporarily change self.components
        components_bak = self.components
        self.components = ["u", "p"]
        # Call Parent
        StokesProblem_Base._combine_and_homogenize_all_dirichlet_bcs(self)
        # Restore
        self.components = components_bak
            
