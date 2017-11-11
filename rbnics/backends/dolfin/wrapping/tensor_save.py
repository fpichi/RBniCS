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

import os
from petsc4py import PETSc
from ufl import Form
from dolfin import as_backend_type, has_pybind11
from mpi4py.MPI import Op
from rbnics.utils.mpi import is_io_process
from rbnics.utils.io import Folders, PickleIO
from rbnics.utils.decorators import overload

def basic_tensor_save(backend, wrapping):
    def _basic_tensor_save(tensor, directory, filename):
        mpi_comm = tensor.mpi_comm()
        if not has_pybind11():
            mpi_comm = mpi_comm.tompi4py()
        form = tensor.generator._form
        # Write out generator
        assert hasattr(tensor, "generator")
        full_filename_generator = os.path.join(str(directory), filename + ".generator")
        form_name = wrapping.form_name(form)
        if is_io_process(mpi_comm):
            with open(full_filename_generator, "w") as generator_file:
                generator_file.write(form_name)
        # Write out generator mpi size
        full_filename_generator_mpi_size = os.path.join(str(directory), filename + ".generator_mpi_size")
        if is_io_process(mpi_comm):
            with open(full_filename_generator_mpi_size, "w") as generator_mpi_size_file:
                generator_mpi_size_file.write(str(mpi_comm.size))
        # Write out generator mapping from processor dependent indices to processor independent (global_cell_index, cell_dof) tuple
        _permutation_save(tensor, directory, form, form_name + "_" + str(mpi_comm.size), mpi_comm)
        # Write out content
        _tensor_save(tensor, directory, filename)
            
    @overload(backend.Matrix.Type(), (Folders.Folder, str), Form, str, object)
    def _permutation_save(tensor, directory, form, form_name, mpi_comm):
        if not PickleIO.exists_file(directory, "." + form_name):
            V_0 = wrapping.form_argument_space(form, 0)
            V_1 = wrapping.form_argument_space(form, 1)
            V_0__dof_map_writer_mapping = wrapping.build_dof_map_writer_mapping(V_0)
            V_1__dof_map_writer_mapping = wrapping.build_dof_map_writer_mapping(V_1)
            matrix_row_mapping = dict() # from processor dependent row indices to processor independent tuple
            matrix_col_mapping = dict() # from processor dependent col indices to processor independent tuple
            mat = as_backend_type(tensor).mat()
            row_start, row_end = mat.getOwnershipRange()
            for row in range(row_start, row_end):
                matrix_row_mapping[row] = V_0__dof_map_writer_mapping[row]
                cols, _ = mat.getRow(row)
                for col in cols:
                    if col not in matrix_col_mapping:
                        matrix_col_mapping[col] = V_1__dof_map_writer_mapping[col]
            gathered_matrix_row_mapping = mpi_comm.reduce(matrix_row_mapping, root=is_io_process.root, op=_dict_update_op)
            gathered_matrix_col_mapping = mpi_comm.reduce(matrix_col_mapping, root=is_io_process.root, op=_dict_update_op)
            gathered_matrix_mapping = (gathered_matrix_row_mapping, gathered_matrix_col_mapping)
            PickleIO.save_file(gathered_matrix_mapping, directory, "." + form_name)
                
    @overload(backend.Vector.Type(), (Folders.Folder, str), Form, str, object)
    def _permutation_save(tensor, directory, form, form_name, mpi_comm):
        if not PickleIO.exists_file(directory, "." + form_name):
            V_0 = wrapping.form_argument_space(form, 0)
            V_0__dof_map_writer_mapping = wrapping.build_dof_map_writer_mapping(V_0)
            vector_mapping = dict() # from processor dependent indices to processor independent tuple
            vec = as_backend_type(tensor).vec()
            row_start, row_end = vec.getOwnershipRange()
            for row in range(row_start, row_end):
                vector_mapping[row] = V_0__dof_map_writer_mapping[row]
            gathered_vector_mapping = mpi_comm.reduce(vector_mapping, root=is_io_process.root, op=_dict_update_op)
            PickleIO.save_file(gathered_vector_mapping, directory, "." + form_name)
    
    @overload(backend.Matrix.Type(), (Folders.Folder, str), str)
    def _tensor_save(tensor, directory, filename):
        _matrix_save(tensor, directory, filename)
        
    @overload(backend.Vector.Type(), (Folders.Folder, str), str)
    def _tensor_save(tensor, directory, filename):
        _vector_save(tensor, directory, filename)
            
    def _matrix_save(matrix, directory, filename):
        mat = as_backend_type(matrix).mat()
        viewer = PETSc.Viewer().createBinary(os.path.join(str(directory), filename + ".dat"), "w")
        viewer.view(mat)
        
    def _vector_save(vector, directory, filename):
        vec = as_backend_type(vector).vec()
        viewer = PETSc.Viewer().createBinary(os.path.join(str(directory), filename + ".dat"), "w")
        viewer.view(vec)
        
    def _dict_update(dict1, dict2, datatype):
        dict1.update(dict2)
        return dict1

    _dict_update_op = Op.Create(_dict_update, commute=True)
    
    return _basic_tensor_save

# No explicit instantiation for backend = rbnics.backends.dolfin for symmetry
# with tensor_load. The concrete instatiation will be carried out in
# rbnics.backends.function.export
