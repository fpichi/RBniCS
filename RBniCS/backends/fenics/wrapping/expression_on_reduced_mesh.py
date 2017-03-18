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
## @file
#  @brief
#
#  @author Francesco Ballarin <francesco.ballarin@sissa.it>
#  @author Gianluigi Rozza    <gianluigi.rozza@sissa.it>
#  @author Alberto   Sartori  <alberto.sartori@sissa.it>

from ufl import replace
from ufl.algorithms.traversal import iter_expressions
from ufl.core.operator import Operator
from ufl.corealg.traversal import traverse_unique_terminals
from ufl.geometry import GeometricQuantity
from dolfin import assign, Expression, Function, project
from RBniCS.backends.fenics.wrapping.function_from_subfunction_if_any import function_from_subfunction_if_any
from RBniCS.utils.decorators import exact_problem, get_problem_from_solution, get_reduced_problem_from_problem, is_problem_solution, is_training_finished
from RBniCS.utils.mpi import log, PROGRESS
from RBniCS.eim.utils.decorators import get_EIM_approximation_from_parametrized_expression

def expression_on_reduced_mesh(expression_wrapper, at):
    expression = expression_wrapper._expression
    EIM_approximation = get_EIM_approximation_from_parametrized_expression(expression_wrapper)
    reduced_mesh = at.get_reduced_mesh()
    reduced_V = at.get_reduced_function_space()
    
    if (expression, reduced_mesh) not in expression_on_reduced_mesh__expression_cache:
        replacements = dict()
        truth_problem_to_reduced_mesh_solution = dict()
        truth_problem_to_reduced_mesh_interpolator = dict()
        reduced_problem_to_reduced_mesh_solution = dict()
        reduced_problem_to_reduced_Z = dict()
        
        # Look for terminals on truth mesh
        for subexpression in iter_expressions(expression):
            for node in traverse_unique_terminals(subexpression):
                node = function_from_subfunction_if_any(node)
                if node in replacements:
                    continue
                # ... problem solutions related to nonlinear terms
                elif isinstance(node, Function) and is_problem_solution(node):
                    truth_problem = get_problem_from_solution(node)
                    # Get the function space corresponding to node on the reduced mesh
                    auxiliary_reduced_V = at.get_auxiliary_reduced_function_space(truth_problem)
                    # Define a replacement
                    replacements[node] = Function(auxiliary_reduced_V)
                    if is_training_finished(truth_problem):
                        reduced_problem = get_reduced_problem_from_problem(truth_problem)
                        # Store the replacement
                        reduced_problem_to_reduced_mesh_solution[reduced_problem] = replacements[node]
                        # Get reduced problem basis functions on reduced mesh
                        reduced_problem_to_reduced_Z[reduced_problem] = at.get_auxiliary_basis_functions_matrix(truth_problem, reduced_problem)
                    else:
                        if not hasattr(truth_problem, "_is_solving"):
                            exact_truth_problem = exact_problem(truth_problem)
                            exact_truth_problem.init()
                            # Store the replacement
                            truth_problem_to_reduced_mesh_solution[exact_truth_problem] = replacements[node]
                            # Get interpolator on reduced mesh
                            truth_problem_to_reduced_mesh_interpolator[exact_truth_problem] = at.get_auxiliary_function_interpolator(exact_truth_problem)
                        else:
                            # Store the replacement
                            truth_problem_to_reduced_mesh_solution[truth_problem] = replacements[node]
                            # Get interpolator on reduced mesh
                            truth_problem_to_reduced_mesh_interpolator[truth_problem] = at.get_auxiliary_function_interpolator(truth_problem)
                # ... geometric quantities
                elif isinstance(node, GeometricQuantity):
                    replacements[node] = type(node)(reduced_mesh)
        # ... and replace them
        replaced_expression = replace(expression, replacements)
        
        # Cache the resulting dicts
        expression_on_reduced_mesh__expression_cache[(expression, reduced_mesh)] = replaced_expression
        expression_on_reduced_mesh__truth_problem_to_reduced_mesh_solution_cache[(expression, reduced_mesh)] = truth_problem_to_reduced_mesh_solution
        expression_on_reduced_mesh__truth_problem_to_reduced_mesh_interpolator_cache[(expression, reduced_mesh)] = truth_problem_to_reduced_mesh_interpolator
        expression_on_reduced_mesh__reduced_problem_to_reduced_mesh_solution_cache[(expression, reduced_mesh)] = reduced_problem_to_reduced_mesh_solution
        expression_on_reduced_mesh__reduced_problem_to_reduced_Z_cache[(expression, reduced_mesh)] = reduced_problem_to_reduced_Z
        
    # Extract from cache
    replaced_expression = expression_on_reduced_mesh__expression_cache[(expression, reduced_mesh)]
    truth_problem_to_reduced_mesh_solution = expression_on_reduced_mesh__truth_problem_to_reduced_mesh_solution_cache[(expression, reduced_mesh)]
    truth_problem_to_reduced_mesh_interpolator = expression_on_reduced_mesh__truth_problem_to_reduced_mesh_interpolator_cache[(expression, reduced_mesh)]
    reduced_problem_to_reduced_mesh_solution = expression_on_reduced_mesh__reduced_problem_to_reduced_mesh_solution_cache[(expression, reduced_mesh)]
    reduced_problem_to_reduced_Z = expression_on_reduced_mesh__reduced_problem_to_reduced_Z_cache[(expression, reduced_mesh)]
    
    # Solve truth problems (which have not been reduced yet) associated to nonlinear terms
    for (truth_problem, reduced_mesh_solution) in truth_problem_to_reduced_mesh_solution.iteritems():
        truth_problem.set_mu(EIM_approximation.mu)
        if not hasattr(truth_problem, "_is_solving"):
            log(PROGRESS, "In expression_on_reduced_mesh, requiring truth problem solve for problem " + str(truth_problem))
            truth_solution = truth_problem.solve()
        else:
            log(PROGRESS, "In expression_on_reduced_mesh, loading truth problem solution for problem " + str(truth_problem))
            truth_solution = truth_problem._solution
        reduced_mesh_interpolator = truth_problem_to_reduced_mesh_interpolator[truth_problem]
        assign(reduced_mesh_solution, reduced_mesh_interpolator(truth_solution))
    
    # Solve reduced problems associated to nonlinear terms
    for (reduced_problem, reduced_mesh_solution) in reduced_problem_to_reduced_mesh_solution.iteritems():
        reduced_problem.set_mu(EIM_approximation.mu)
        if not hasattr(reduced_problem, "_is_solving"):
            log(PROGRESS, "In expression_on_reduced_mesh, requiring reduced problem solve for problem " + str(reduced_problem))
            reduced_solution = reduced_problem.solve()
        else:
            log(PROGRESS, "In expression_on_reduced_mesh, loading reduced problem solution for problem " + str(reduced_problem))
            reduced_solution = reduced_problem._solution
        reduced_Z = reduced_problem_to_reduced_Z[reduced_problem]
        assign(reduced_mesh_solution, reduced_Z[:reduced_solution.N]*reduced_solution)
        
    assert isinstance(expression, (Expression, Function, Operator))
    if isinstance(expression, (Expression, Function)):
        return replaced_expression
    elif isinstance(expression, Operator):
        return project(replaced_expression, reduced_V)
    else:
        raise AssertionError("Invalid expression in expression_on_reduced_mesh.")

expression_on_reduced_mesh__expression_cache = dict()
expression_on_reduced_mesh__truth_problem_to_reduced_mesh_solution_cache = dict()
expression_on_reduced_mesh__truth_problem_to_reduced_mesh_interpolator_cache = dict()
expression_on_reduced_mesh__reduced_problem_to_reduced_mesh_solution_cache = dict()
expression_on_reduced_mesh__reduced_problem_to_reduced_Z_cache = dict()
