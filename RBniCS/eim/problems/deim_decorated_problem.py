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
## @file eim.py
#  @brief Implementation of the empirical interpolation method for the interpolation of parametrized functions
#
#  @author Francesco Ballarin <francesco.ballarin@sissa.it>
#  @author Gianluigi Rozza    <gianluigi.rozza@sissa.it>
#  @author Alberto   Sartori  <alberto.sartori@sissa.it>

from itertools import product as cartesian_product
from RBniCS.backends import ParametrizedTensorFactory, SeparatedParametrizedForm
from RBniCS.utils.decorators import Extends, override, ProblemDecoratorFor
from RBniCS.eim.problems.eim_approximation import EIMApproximation as DEIMApproximation
from RBniCS.eim.problems.time_dependent_eim_approximation import TimeDependentEIMApproximation as TimeDependentDEIMApproximation

def DEIMDecoratedProblem(
    basis_generation="POD",
    **decorator_kwargs
):
    from RBniCS.eim.problems.exact_parametrized_functions import ExactParametrizedFunctions
    from RBniCS.eim.problems.deim import DEIM
    
    @ProblemDecoratorFor(DEIM, ExactAlgorithm=ExactParametrizedFunctions)
    def DEIMDecoratedProblem_Decorator(ParametrizedDifferentialProblem_DerivedClass):
                
        @Extends(ParametrizedDifferentialProblem_DerivedClass, preserve_class_name=True)
        class DEIMDecoratedProblem_Class(ParametrizedDifferentialProblem_DerivedClass):
            
            ## Default initialization of members
            @override
            def __init__(self, V, **kwargs):
                # Call the parent initialization
                ParametrizedDifferentialProblem_DerivedClass.__init__(self, V, **kwargs)
                # Storage for DEIM reduced problems
                self.DEIM_approximations = dict() # from term to dict of DEIMApproximation
                self.non_DEIM_forms = dict() # from term to dict of forms
                
                # Store value of N_DEIM passed to solve
                self._N_DEIM = None
                
                # Avoid useless assignments
                self._update_N_DEIM__previous_kwargs = None
                
            @override
            def set_mu_range(self, mu_range):
                # Call to parent
                ParametrizedDifferentialProblem_DerivedClass.set_mu_range(self, mu_range)
                
                # Preprocess each term in the affine expansions
                # Note that this cannot be done in __init__ because operators may depend on self.mu,
                # which is not defined at __init__ time
                for term in self.terms:
                    forms = ParametrizedDifferentialProblem_DerivedClass.assemble_operator(self, term)
                    self.DEIM_approximations[term] = dict()
                    self.non_DEIM_forms[term] = dict()
                    for (q, form_q) in enumerate(forms):
                        factory_form_q = ParametrizedTensorFactory(self, form_q)
                        if factory_form_q.is_parametrized():
                            if factory_form_q.is_time_dependent():
                                DEIMApproximationType = TimeDependentDEIMApproximation
                            else:
                                DEIMApproximationType = DEIMApproximation
                            self.DEIM_approximations[term][q] = DEIMApproximationType(self, factory_form_q, type(self).__name__ + "/deim/" + factory_form_q.name(), basis_generation)
                        else:
                            self.non_DEIM_forms[term][q] = form_q
                
            @override
            def solve(self, **kwargs):
                self._update_N_DEIM(**kwargs)
                return ParametrizedDifferentialProblem_DerivedClass.solve(self, **kwargs)
            
            def _update_N_DEIM(self, **kwargs):
                if kwargs != self._update_N_DEIM__previous_kwargs:
                    if "DEIM" in kwargs:
                        N_DEIM = kwargs["DEIM"]
                        assert isinstance(N_DEIM, (dict, int))
                        if isinstance(N_DEIM, int):
                            N_DEIM_dict = dict()
                            for term in self.terms:
                                N_DEIM_dict[term] = dict()
                                for q in self.DEIM_approximations[term]:
                                    N_DEIM_dict[term][q] = N_DEIM
                            self._N_DEIM = N_DEIM_dict
                        else:
                            self._N_DEIM = N_DEIM
                    else:
                        self._N_DEIM = None
                    self._update_N_DEIM__previous_kwargs = kwargs
                
                
            ###########################     PROBLEM SPECIFIC     ########################### 
            ## @defgroup ProblemSpecific Problem specific methods
            #  @{
            
            @override
            def assemble_operator(self, term):
                if term in self.terms:
                    deim_forms = list()
                    # Append forms computed with DEIM, if applicable
                    for (_, deim_approximation) in self.DEIM_approximations[term].iteritems():
                        deim_forms.extend(deim_approximation.Z)
                    # Append forms which did not require DEIM, if applicable
                    for (_, non_deim_form) in self.non_DEIM_forms[term].iteritems():
                        deim_forms.append(non_deim_form)
                    return tuple(deim_forms)
                else:
                    return ParametrizedDifferentialProblem_DerivedClass.assemble_operator(self, term) # may raise an exception
                    
            @override
            def compute_theta(self, term):
                original_thetas = ParametrizedDifferentialProblem_DerivedClass.compute_theta(self, term) # may raise an exception
                if term in self.terms:
                    deim_thetas = list()
                    assert len(self.DEIM_approximations[term]) + len(self.non_DEIM_forms[term]) == len(original_thetas)
                    if self._N_DEIM is not None:
                        assert term in self._N_DEIM 
                        assert len(self.DEIM_approximations[term]) == len(self._N_DEIM[term])
                    # Append forms computed with DEIM, if applicable
                    for (q, deim_approximation) in self.DEIM_approximations[term].iteritems():
                        N_DEIM = None
                        if self._N_DEIM is not None:
                            N_DEIM = self._N_DEIM[term][q]
                        deim_thetas_q = map(lambda v: v*original_thetas[q], deim_approximation.compute_interpolated_theta(N_DEIM))
                        deim_thetas.extend(deim_thetas_q)
                    # Append forms which did not require DEIM, if applicable
                    for q in self.non_DEIM_forms[term]:
                        deim_thetas.append(original_thetas[q])
                    return tuple(deim_thetas)
                else:
                    return original_thetas
            #  @}
            ########################### end - PROBLEM SPECIFIC - end ########################### 
            
        # return value (a class) for the decorator
        return DEIMDecoratedProblem_Class
        
    # return the decorator itself
    return DEIMDecoratedProblem_Decorator
