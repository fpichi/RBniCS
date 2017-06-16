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

from rbnics.backends import assign, NonlinearProblemWrapper, NonlinearSolver
from rbnics.utils.decorators import Extends, override, RequiredBaseDecorators

@RequiredBaseDecorators(None)
def NonlinearProblem(ParametrizedDifferentialProblem_DerivedClass):
    
    @Extends(ParametrizedDifferentialProblem_DerivedClass, preserve_class_name=True)
    class NonlinearProblem_Class(ParametrizedDifferentialProblem_DerivedClass):
        
        ## Default initialization of members
        @override
        def __init__(self, V, **kwargs):
            # Call to parent
            ParametrizedDifferentialProblem_DerivedClass.__init__(self, V, **kwargs)
            
            # Nonlinear solver parameters
            self._nonlinear_solver_parameters = dict()
        
        class ProblemSolver(ParametrizedDifferentialProblem_DerivedClass.ProblemSolver, NonlinearProblemWrapper):
            # Store solution while solving the nonlinear problem
            def store_solution(self, solution):
                assign(self.problem._solution, solution)
                
            def solve(self):
                problem = self.problem
                solver = NonlinearSolver(self, problem._solution)
                solver.set_parameters(problem._nonlinear_solver_parameters)
                solver.solve()
            
    # return value (a class) for the decorator
    return NonlinearProblem_Class
    