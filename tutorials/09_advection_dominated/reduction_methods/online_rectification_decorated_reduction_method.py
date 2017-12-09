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

from rbnics.utils.decorators import PreserveClassName, ReductionMethodDecoratorFor
from problems import OnlineRectification

@ReductionMethodDecoratorFor(OnlineRectification)
def OnlineRectificationDecoratedReductionMethod(EllipticCoerciveReductionMethod_DerivedClass):
    
    @PreserveClassName
    class OnlineRectificationDecoratedReductionMethod_Class(EllipticCoerciveReductionMethod_DerivedClass):
        def __init__(self, truth_problem, **kwargs):
            # Call to parent
            EllipticCoerciveReductionMethod_DerivedClass.__init__(self, truth_problem, **kwargs)
            
        def _offline(self):
            # Call standard offline phase
            EllipticCoerciveReductionMethod_DerivedClass._offline(self)
            
            print("==============================================================")
            print("=" + "{:^60}".format(self.label + " offline rectification postprocessing phase begins") + "=")
            print("==============================================================")
            print("")
            
            # Compute projection of truth and reduced snapshots
            print("build projection truth snapshots for rectification")
            for n in range(1, self.reduced_problem.N + 1):
                self.reduced_problem.operator["projection_truth_snapshots_" + str(n)] = self.reduced_problem.assemble_operator("projection_truth_snapshots_" + str(n), "offline")
            print("build projection reduced snapshots for rectification")
            for n in range(1, self.reduced_problem.N + 1):
                self.reduced_problem.operator["projection_reduced_snapshots_" + str(n)] = self.reduced_problem.assemble_operator("projection_reduced_snapshots_" + str(n), "offline")
            
            print("==============================================================")
            print("=" + "{:^60}".format(self.label + " offline rectification postprocessing phase ends") + "=")
            print("==============================================================")
            print("")
            
        def update_basis_matrix(self, snapshot):
            # Store
            self.reduced_problem.snapshots_mu.append(self.truth_problem.mu)
            self.reduced_problem.snapshots.enrich(snapshot)
            # Call Parent
            EllipticCoerciveReductionMethod_DerivedClass.update_basis_matrix(self, snapshot)
            
    # return value (a class) for the decorator
    return OnlineRectificationDecoratedReductionMethod_Class
