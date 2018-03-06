# Copyright (C) 2015-2018 by the RBniCS authors
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

from numbers import Number
from numpy import zeros
from dolfin import Constant, DirichletBC, has_pybind11
if has_pybind11():
    from dolfin.cpp.mesh import MeshFunctionSizet

original_DirichletBC__init__ = DirichletBC.__init__
def custom_DirichletBC__init__(self, *args, **kwargs):
    # Call the constructor
    original_DirichletBC__init__(self, *args, **kwargs)
    # Deduce private variable values from arguments
    if len(args) == 1 and isinstance(args[0], DirichletBC):
        assert len(kwargs) == 0
        _value = args[0]._value
        _function_space = args[0]._function_space
        _domain = args[0]._domain
        _sorted_kwargs = args[0]._sorted_kwargs
        _identifier = args[0]._identifier
    else:
        _value = args[1]
        _function_space = args[0]
        if has_pybind11():
            if isinstance(args[2], MeshFunctionSizet):
                _domain = args[2:]
            else:
                assert hasattr(self, "sub_domain")
                _domain = (self.sub_domain, ) + args[3:]
        else:
            _domain = self.domain_args
        _sorted_kwargs = list()
        for key in ["method", "check_midpoint"]:
            if key in kwargs:
                _sorted_kwargs.append(kwargs[key])
        _identifier = list()
        _identifier.append(_function_space)
        _identifier.append(_domain)
        _identifier.extend(_sorted_kwargs)
        _identifier = tuple(_identifier)
    # Assign private variable values
    self._value = _value
    self._function_space = _function_space
    self._domain = _domain
    self._sorted_kwargs = _sorted_kwargs
    self._identifier = _identifier
DirichletBC.__init__ = custom_DirichletBC__init__

# Override the value(), set_value() and homogenize() methods. These are already available in the public interface,
# but it is cast the value to a base type (GenericFunction), which makes it not possible to perform the sum
def custom_DirichletBC_value(self):
    return self._value
DirichletBC.value = custom_DirichletBC_value
original_DirichletBC_set_value = DirichletBC.set_value
def custom_DirichletBC_set_value(self, g):
    self._value = g
    original_DirichletBC_set_value(self, g)
DirichletBC.set_value = custom_DirichletBC_set_value
original_DirichletBC_homogenize = DirichletBC.homogenize
def custom_DirichletBC_homogenize(self):
    self._value = Constant(zeros(self._value.ufl_shape))
    original_DirichletBC_homogenize(self, self._value)
DirichletBC.homogenize = custom_DirichletBC_homogenize

# Override the function_space() method. This is already available in the public interface,
# but it casts the function space to a C++ FunctionSpace and then wraps it into a python FunctionSpace,
# losing all the customization that we have done in the function_space.py file
def custom_DirichletBC_function_space(self):
    return self._function_space
DirichletBC.function_space = custom_DirichletBC_function_space

# Define an identifier() method, that identifies whether BCs are defined on the same boundary
def custom_DirichletBC_identifier(self):
    return self._identifier
DirichletBC.identifier = custom_DirichletBC_identifier

# Add a multiplication operator by a scalar
def custom_DirichletBC_mul_by_scalar(self, other):
    if isinstance(other, Number):
        args = list()
        args.append(self.function_space())
        args.append(Constant(other)*self.value())
        args.append(self._domain)
        args.extend(self._sorted_kwargs)
        return DirichletBC(*args)
    else:
        return NotImplemented
DirichletBC.__mul__ = custom_DirichletBC_mul_by_scalar
DirichletBC.__rmul__ = custom_DirichletBC_mul_by_scalar

class ProductOutputDirichletBC(list):
    # Define the __invert__ operator to be used in combination with __and__ operator of Matrix
    # to zero rows and columns associated to Dirichlet BCs
    def __invert__(self):
        return InvertProductOutputDirichletBC(self)
        
    def __eq__(self, other):
        assert isinstance(other, ProductOutputDirichletBC)
        return list.__eq__(self, other)
        
    def __hash__(self):
        return hash(tuple(self))
        
class InvertProductOutputDirichletBC(object):
    def __init__(self, bc_list):
        self.bc_list = bc_list
        
    def __eq__(self, other):
        assert isinstance(other, InvertProductOutputDirichletBC)
        return self.bc_list == other.bc_list
        
    def __hash__(self):
        return hash(self.bc_list)
