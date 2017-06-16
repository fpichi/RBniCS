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

from __future__ import print_function
from rbnics.problems.base import LinearReducedProblem
from rbnics.problems.stokes.stokes_problem import StokesProblem
from rbnics.backends import LinearSolver, product, sum, transpose
from rbnics.backends.online import OnlineFunction
from rbnics.utils.decorators import Extends, override
from rbnics.reduction_methods.stokes import StokesReductionMethod
from rbnics.utils.mpi import print

def StokesReducedProblem(ParametrizedReducedDifferentialProblem_DerivedClass):

    StokesReducedProblem_Base = LinearReducedProblem(ParametrizedReducedDifferentialProblem_DerivedClass)

    # Base class containing the interface of a projection based ROM
    # for saddle point problems.
    @Extends(StokesReducedProblem_Base)
    class StokesReducedProblem_Class(StokesReducedProblem_Base):
            
        class ProblemSolver(StokesReducedProblem_Base.ProblemSolver):
            def matrix_eval(self):
                problem = self.problem
                N = self.N
                assembled_operator = dict()
                for term in ("a", "b", "bt"):
                    assembled_operator[term] = sum(product(self.compute_theta(term), self.operator[term][:N, :N]))
                return assembled_operator["a"] + assembled_operator["b"] + assembled_operator["bt"]
                
            def vector_eval(self):
                problem = self.problem
                N = self.N
                assembled_operator = dict()
                for term in ("f", "g"):
                    assembled_operator[term] = sum(product(self.compute_theta(term), self.operator[term][:N]))
                return assembled_operator["f"] + assembled_operator["g"]
                
            # Custom combination of boundary conditions *not* to add BCs of supremizers
            def bc_eval(self):
                problem = self.problem
                # Temporarily change problem.components
                components_bak = problem.components
                problem.components = ["u", "p"]
                # Call Parent
                StokesReducedProblem_Base.ProblemSolver.bc_eval(self)
                # Restore
                problem.components = components_bak
        
        # Internal method for error computation
        @override
        def _compute_error(self, **kwargs):
            components = ["u", "p"] # but not "s"
            if "components" not in kwargs:
                kwargs["components"] = components
            else:
                assert kwargs["components"] == components
            return StokesReducedProblem_Base._compute_error(self, **kwargs)
            
        # Internal method for relative error computation
        @override
        def _compute_relative_error(self, absolute_error, **kwargs):
            components = ["u", "p"] # but not "s"
            if "components" not in kwargs:
                kwargs["components"] = components
            else:
                assert kwargs["components"] == components
            return StokesReducedProblem_Base._compute_relative_error(self, absolute_error, **kwargs)
            
        ## Assemble the reduced order affine expansion
        def assemble_operator(self, term, current_stage="online"):
            if term == "bt_restricted":
                self.operator["bt_restricted"] = self.operator["bt"]
                return self.operator["bt_restricted"]
            elif term == "inner_product_s":
                self.inner_product["s"] = self.inner_product["u"]
                return self.inner_product["s"]
            else:
                return StokesReducedProblem_Base.assemble_operator(self, term, current_stage)
                
        # Custom combination of inner products *not* to add inner product corresponding to supremizers
        def _combine_all_inner_products(self):
            # Temporarily change self.components
            components_bak = self.components
            self.components = ["u", "p"]
            # Call Parent
            StokesReducedProblem_Base._combine_all_inner_products(self)
            # Restore
            self.components = components_bak
            
        # Custom combination of inner products *not* to add projection inner product corresponding to supremizers
        def _combine_all_projection_inner_products(self):
            # Temporarily change self.components
            components_bak = self.components
            self.components = ["u", "p"]
            # Call Parent
            StokesReducedProblem_Base._combine_all_projection_inner_products(self)
            # Restore
            self.components = components_bak
        
    # return value (a class) for the decorator
    return StokesReducedProblem_Class