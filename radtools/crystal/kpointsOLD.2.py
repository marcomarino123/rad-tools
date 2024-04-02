# RAD-tools - program for spin Hamiltonian and magnons.
# Copyright (C) 2022-2023  Andrey Rybakov
#
# e-mail: anry@uv.es, web: adrybakov.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

r"""
General 3D lattice.
"""

from typing import Iterable
from collections import Counter
import numpy as np
import scipy
from scipy.interpolate import griddata
from scipy.spatial.transform import Rotation
from scipy.spatial import Delaunay
from radtools.geometry import absolute_to_relative
from scipy.spatial.distance import cdist
import math
from operator import itemgetter

__all__ = ["Kpoints"]


class Kpoints:
    r"""
    K-point path.

    Parameters
    ----------
    b1 : (3,) array_like
        First reciprocal lattice vector :math:`\mathbf{b}_1`.
    b2 : (3,) array_like
        Second reciprocal lattice vector :math:`\mathbf{b}_2`.
    b3 : (3,) array_like
        Third reciprocal lattice vector :math:`\mathbf{b}_3`.
    coordinates : list, optional
        Coordinates are given in relative coordinates in reciprocal space.
    names: list, optional
        Names of the high symmetry points. Used for programming, not for plotting.
    labels : list, optional
        Dictionary of the high symmetry points labels for plotting.
        Has to have the same length as ``coordinates``.
    path : str, optional
        K points path.
    n : int
        Number of points between each pair of the high symmetry points
        (high symmetry points excluded).

    Attributes
    ----------
    b1 : (3,) :numpy:`ndarray`
        First reciprocal lattice vector :math:`\mathbf{b}_1`.
    b2 : (3,) :numpy:`ndarray`
        Second reciprocal lattice vector :math:`\mathbf{b}_2`.
    b3 : (3,) :numpy:`ndarray`
        Third reciprocal lattice vector :math:`\mathbf{b}_3`.
    hs_names : list
        Names of the high symmetry points. Used for programming, not for plotting.
    hs_coordinates : dict
        Dictionary of the high symmetry points coordinates.

        .. code-block:: python

            {"name": [k_a, k_b, k_c], ... }

    hs_labels : dict
        Dictionary of the high symmetry points labels for plotting.

        .. code-block:: python

            {"name": "label", ... }
    """

    def __init__(
        self, b1, b2, b3, coordinates=None, names=None, labels=None, path=None, n=100
    ) -> None:
        self.b1 = np.array(b1)
        self.b2 = np.array(b2)
        self.b3 = np.array(b3)

        if coordinates is None:
            coordinates = []

        # Fill names and labels with defaults
        if names is None:
            names = [f"K{i+1}" for i in range(len(coordinates))]
            if labels is None:
                labels = [f"K$_{i+1}$" for i in range(len(coordinates))]
        if labels is None:
            labels = [name for name in names]
        else:
            if len(labels) != len(coordinates):
                raise ValueError(
                    f"Amount of labels ({len(labels)}) does not match amount of points ({len(coordinates)})."
                )

        # Define high symmetry points attributes
        self.hs_coordinates = dict(
            [(names[i], np.array(coordinates[i])) for i in range(len(coordinates))]
        )
        self.hs_labels = dict([(names[i], labels[i]) for i in range(len(coordinates))])
        self.hs_names = names

        self._n = n

        self._path = None
        if path is None:
            if len(self.hs_names) > 0:
                path = [self.hs_names[0]]
            else:
                path = []
            for point in self.hs_names[1:]:
                path.append(f"-{point}")
            path = "".join(path)
        self.path = path

    def add_hs_point(self, name, coordinates, label, relative=True):
        r"""
        Add high symmetry point.

        Parameters
        ----------
        name : str
            Name of the high symmetry point.
        coordinates : (3,) array_like
            Coordinates of the high symmetry point.
        label : str
            Label of the high symmetry point, ready to be plotted.
        relative : bool, optional
            Whether to interpret coordinates as relative or absolute.
        """

        if name in self.hs_names:
            raise ValueError(f"Point '{name}' already defined.")

        if not relative:
            coordinates = absolute_to_relative(
                np.array([self.b1, self.b2, self.b3]), coordinates
            )

        self.hs_names.append(name)
        self.hs_coordinates[name] = np.array(coordinates)
        self.hs_labels[name] = label

    @property
    def path(self):
        r"""
        K points path.

        Returns
        -------
        path : list of list of str
            K points path. Each subpath is a list of the high symmetry points.
        """

        return self._path

    @path.setter
    def path(self, new_path):
        if isinstance(new_path, str):
            tmp_path = new_path.split("|")
            new_path = []
            for i in range(len(tmp_path)):
                subpath = tmp_path[i].split("-")
                # Each subpath has to contain at least two points.
                if len(subpath) != 1:
                    new_path.append(subpath)
        elif isinstance(new_path, Iterable):
            tmp_path = new_path
            new_path = []
            for subpath in tmp_path:
                if isinstance(subpath, str) and "-" in subpath:
                    subpath = subpath.split("-")
                    # Each subpath has to contain at least two points.
                    if len(subpath) != 1:
                        new_path.append(subpath)
                elif (
                    not isinstance(subpath, str)
                    and isinstance(subpath, Iterable)
                    and len(subpath) != 1
                ):
                    new_path.append(subpath)
                else:
                    new_path = [tmp_path]
                    break
        # Check if all points are defined.
        for subpath in new_path:
            for point in subpath:
                if point not in self.hs_names:
                    message = f"Point '{point}' is not defined. Defined points are:"
                    for defined_name in self.hs_names:
                        message += (
                            f"\n  {defined_name} : {self.hs_coordinates[defined_name]}"
                        )
                    raise ValueError(message)
        self._path = new_path

    @property
    def path_string(self):
        r"""
        K points path as a string.

        Returns
        -------
        path : str
        """

        result = ""
        for s_i, subpath in enumerate(self.path):
            for i, name in enumerate(subpath):
                if i != 0:
                    result += "-"
                result += name
            if s_i != len(self.path) - 1:
                result += "|"

        return result

    @property
    def n(self):
        r"""
        Amount of points between each pair of the high symmetry points
        (high symmetry points excluded).

        Returns
        -------
        n : int
        """

        return self._n

    @n.setter
    def n(self, new_n):
        if not isinstance(new_n, int):
            raise ValueError(
                f"n has to be integer. Given: {new_n}, type = {type(new_n)}"
            )
        self._n = new_n

    @property
    def labels(self):
        r"""
        Labels of high symmetry points, ready to be plotted.

        For example for point "Gamma" it returns r"$\Gamma$".

        If there are two high symmetry points following one another in the path,
        it returns "X|Y" where X and Y are the labels of the two high symmetry points.

        Returns
        -------
        labels : list of str
            Labels, ready to be plotted. Same length as :py:attr:`.coordinates`.
        """

        labels = []
        for s_i, subpath in enumerate(self.path):
            if s_i != 0:
                labels[-1] += "|" + self.hs_labels[subpath[0]]
            else:
                labels.append(self.hs_labels[subpath[0]])
            for name in subpath[1:]:
                labels.append(self.hs_labels[name])

        return labels

    def coordinates(self, relative=False):
        r"""
        Flatten coordinates of the high symmetry points, ready to be plotted.

        Parameters
        ----------
        relative : bool, optional
            Whether to use relative coordinates instead of the absolute ones.
        Returns
        -------
        coordinates : :numpy:`ndarray`
            Coordinates, ready to be plotted. Same length as :py:attr:`.labels`.
        """

        if relative:
            cell = np.eye(3)
        else:
            cell = np.array([self.b1, self.b2, self.b3])

        coordinates = []
        for s_i, subpath in enumerate(self.path):
            if s_i == 0:
                coordinates.append(0)
            for i, name in enumerate(subpath[1:]):
                coordinates.append(
                    np.linalg.norm(
                        self.hs_coordinates[name] @ cell
                        - self.hs_coordinates[subpath[i]] @ cell
                    )
                    + coordinates[-1]
                )

        return np.array(coordinates)

    def points(self, relative=False):
        r"""
        Coordinates of all points with n points between each pair of the high
        symmetry points (high symmetry points excluded).

        Parameters
        ----------
        relative : bool, optional
            Whether to use relative coordinates instead of the absolute ones.

        Returns
        -------
        points : (N, 3) :numpy:`ndarray`
            Coordinates of all points.
        """

        if relative:
            cell = np.eye(3)
        else:
            cell = np.array([self.b1, self.b2, self.b3])

        points = None
        for subpath in self.path:
            for i in range(len(subpath) - 1):
                name = subpath[i]
                next_name = subpath[i + 1]
                new_points = np.linspace(
                    self.hs_coordinates[name] @ cell,
                    self.hs_coordinates[next_name] @ cell,
                    self._n + 2,
                )
                if points is None:
                    points = new_points
                else:
                    points = np.concatenate((points, new_points))
        return points

    # It can not just call for points and flatten them, because it has to treat "|" as a special case.
    def flatten_points(self, relative=False):
        r"""
        Flatten coordinates of all points with n points between each pair of the high
        symmetry points (high symmetry points excluded). Used to plot band structure, dispersion, etc.

        Parameters
        ----------
        relative : bool, optional
            Whether to use relative coordinates instead of the absolute ones.

        Returns
        -------
        flatten_points : (N, 3) :numpy:`ndarray`
            Flatten coordinates of all points.
        """

        if relative:
            cell = np.eye(3)
        else:
            cell = np.array([self.b1, self.b2, self.b3])

        flatten_points = None
        for s_i, subpath in enumerate(self.path):
            for i in range(len(subpath) - 1):
                name = subpath[i]
                next_name = subpath[i + 1]
                points = (
                    np.linspace(
                        self.hs_coordinates[name] @ cell,
                        self.hs_coordinates[next_name] @ cell,
                        self._n + 2,
                    )
                    - self.hs_coordinates[name] @ cell
                )
                delta = np.linalg.norm(points, axis=1)
                if s_i == 0 and i == 0:
                    flatten_points = delta
                else:
                    delta += flatten_points[-1]
                    flatten_points = np.concatenate((flatten_points, delta))
        return flatten_points

#function checking if the k points in the list k_list are inside the Brillouin zone
def downfold_inside_brillouin_zone(
    k_point_list,
    brillouin_primitive_vectors_3d):
    r"""
        check if any point in a list is inside the first brillouin zone, in case the point is outside it is shifted back to the first brillouin zone
        Parameters
        ----------
        k_point_list: (N, 3) :|array_like| kx,ky,kz (k points are given in cartesian coordinates)
        brillouin_primitive_vectors_3d: (3,3) :|array_like| columns: kx,ky,kz, rows: b1,b2,b3
        Returns
        -------
        transformed_k_point_list: (N, 3) :|array_like| kx,ky,kz (k points are given in cartesian coordinates)
        """
    matrix_transformation_crystal_to_cartesian=np.zeros((3,3))
    matrix_transformation_cartesian_to_crystal=np.zeros((3,3))
    number_k_point_elements = k_point_list.shape[0]
    transformed_k_point_list = np.zeros((number_k_point_elements,3),dtype=float)
    matrix_transformation_crystal_to_cartesian=np.matrix(brillouin_primitive_vectors_3d).transpose()
    matrix_transformation_cartesian_to_crystal=np.linalg.inv(matrix_transformation_crystal_to_cartesian)

    # writing k points in crystal coordinates
    for i in range(number_k_point_elements):
        transformed_k_point_list[i,:]=matrix_transformation_cartesian_to_crystal@k_point_list[i,:]

    # checking if any point of the list is outside the first brillouin zone
    #to each k point is associated a int 0,1,2,3 if it goes over the bonds
    indices=[]
    for i in range(number_k_point_elements):
        count=0
        for r in range(3):
            if transformed_k_point_list[i,r] >= 1.0 or transformed_k_point_list[i,r] < 0:
                count+=r
                for d in range(3):
                    k_point_list[i,d]=k_point_list[i,d]-brillouin_primitive_vectors_3d[r,d]*np.sign(transformed_k_point_list[i,r])
        indices.append(count)
    indices=np.reshape(indices,(number_k_point_elements,1))
    return k_point_list,indices

# function applying symmetry analysis to a list of k points, the symmetry operations considered are the point group ones
# the fixed point is given; the analysis aim is to redistribute the fixed point weight between the list of k points
# the found symmetry orbits are counted in the redistribution of the fixed point weight a number of times equal to the number of k points inside the orbit itself
def symmetry_analysis(
    k_origin,
    k_origin_weight,
    k_list,
    symmetries,
    threshold,
):
    r"""
    Given a list of k points "k_list" and an origin "k_origin" with a certain weight "k_origin_weight", different symmetry operations are applied to the list of k points, keeping the origin fixed.
    The origin weight is propelry distributed between the points:
        the orbits of the symmetry operations acquire a certain percentage of the origin weight, which takes into account how many orbits are found 
        of the orbits one k point (from the k list) is chosen as representative, and the weight of the orbit is assigned only to it
    Parameters
    ----------
    k_origin:(3) |array_like| fixed point coordinates (kx,ky,kz), fixed point considered in the point-group symmetry operations
    k_origin_weight : |float|  weight to distribute between the k points of the list 
    k_list : (N, 3) |array_like| list of k points considered in the symmetry analysis (kx,ky,kz)
    symmetries : list of lists, a symmetry is a list of 3 elements (the versor is the axis of rotation, while the modulus is the angle).
    threshold : |float| threshold to recognize a symmetry.
    Returns
    -------
    new_k_list: (N,4) :|array_like| list of k points coordinates with respcetive weights from the symmetry analysis
    """
    number_elements = k_list.shape[0]  

    new_k_list = np.c_[ k_list, (k_origin_weight / number_elements) * np.ones(number_elements, dtype=float)]
    # if there are no symmetry operations, than the weight on each k point is exactly 1/N of the original weight
    if symmetries is None or (symmetries[0][0] == symmetries[0][1] == symmetries[0][2] == 0):
        return new_k_list

    # defining a matrix to save the degeneracies, after each symmetry operation
    check_degeneracy = np.zeros((number_elements, number_elements), dtype=bool)
    # saving flag if no degeneracy is detected
    no_degeneracy = True
    
    k_eigenspaces=np.zeros(number_elements)
    for i in range(number_elements):
        k_eigenspaces[i]=i

    # each k point is compared to each other k point after each of the symmetry operations has been applied
    for i in range(number_elements - 1):
        for j in range(i + 1, number_elements):
            # for each pair considering all the symmetry operations
            for rotvec in symmetries:
                k_point_transformed = (
                    Rotation.from_rotvec(rotvec).as_matrix()
                    @ (k_list[j] - k_origin)
                    + k_origin
                )
                # if any degeneracy is detected, the check on all the symmetry operations given is stopped
                if np.allclose(
                    k_list[i], k_point_transformed, atol=threshold
                ):
                    check_degeneracy[i][j] = True
                    no_degeneracy = False
                    break

    # if no degeneracy is detected, the no-symmetry-operations result is given
    if no_degeneracy:
        return new_k_list
    else:
        # if degeneracy is detected, of the degenerate points only one is chosen as representative of the respective orbit (the first to appear in the k list)
        # assuming all k points as not-degenerate, and creating a dictionary
        # where to each eigenspace (orbit) is associated a not null k_point
        for i in range(0,number_elements-1):
            for j in range(i+1,number_elements):
                if check_degeneracy[i][j]==True:
                    min_value=min(i,j)
                    max_value=max(i,j)
                    k_eigenspaces[k_eigenspaces==max_value]=min_value

        # counting number of different eigenspaces
        number_eigenspaces=len(np.unique(k_eigenspaces))
        weights=k_origin_weight/number_eigenspaces

        # ordering eigenspaces values
        ordered_k_eigenspaces=np.zeros(number_elements)
        counting=0
        assigned_indices=[]
        for i in range(number_elements):
            if k_eigenspaces[i] not in assigned_indices:
                if counting<number_eigenspaces:
                    ordered_k_eigenspaces[k_eigenspaces==k_eigenspaces[i]]=counting
                    assigned_indices.extend([r for r in range(number_elements) if k_eigenspaces[r]==k_eigenspaces[i]])
                    counting+=1
        # considering a representative for each eigenspace
        for i in range(number_eigenspaces):
            list_positions=[r for r in range(number_elements) if ordered_k_eigenspaces[r]==i]
            if len(list_positions)!=0:
                new_k_list[list_positions[0],3]=weights
                new_k_list[list_positions[1:],3]=0
            else:
                break

        # returning the matrix with the respective weights
        return new_k_list

# local refinment of the k list in the plane (parallelepiped) pointed out by the brillouin primitive vectors given (it can be 2D, 3D or ..)
def local_refinment_with_symmetry_analysis(
    new_k_list,
    old_k_list,
    refinment_spacing,
    refinment_iteration,
    symmetries,
    threshold,
    brillouin_primitive_vectors_3d,
    brillouin_primitive_vectors_2d,
    normalized_brillouin_primitive_vectors_2d,
    downfold
):
    r"""
    Starting from a set of k points (old_k_list) with certain weights, to each k point iteratively (refinment_iteration) a new subset of k points is associated,
    a symmetry analysis (symmetry) is performed on the subset, and consequently the initial weight of the k point is distributed in the subset of k points.
    This procedure goes on for the given number of refinment iterations.
    At each iteration for each k point four new k points are generated along the reciprocal primitive vectors of the selcted plane (2d refinment), at a distance from the original k point 
    equal to the refinment spacing (the refinment spacing is halved at each iteration).
    Obviously no refinment is applied to k points with null weight.

    if check_inside_dominion == True instead of checking that the point is inside the 2d plane of the brillouin zone, it is checked that it is inside a circle of a certain radius
    (radius), and if it is outside the circle it is downfolded back 

    Parameters
    ----------
    new_k_list: (,4) |array_like| list of values produced by the refinment procedure (expected to be empty at the beginning of the refinment procedure)
    old_k_list: (,4) |list| list of values give to the refinment procedure (kx,ky,kz,weight)
    refinment_spacing: |double| initial spacing given to generate the refinment, half of the preceding refinment spacing is considered at each refinment iteration
    refinment_iteration: |int| number of refinment iterations considered
    symmetry: |list of lists| a symmetry is a list of 3 elements (the versor is the axis of rotation, while the modulus is the angle)
    threshold: |double| threshold to recognize a symmetry
    brillouin_primitive_vectors : (2,3) |array_like| vectors definining the 2D plane in the reciprocal space, chosen for the refinment procedure
    brillouin_primitive_vectors_all: (3,3) |array_like| vectors definining the 3D reciprocal space
    (the k points of the list are expected to be in the same 2D plane)
    """
    length_old_k_list=old_k_list.shape[0]
    if refinment_iteration == 0:
        if downfold == True:
            old_k_list[:,:3]= downfold_inside_brillouin_zone(
                old_k_list[:,:3],
                brillouin_primitive_vectors_3d,
            )
        for i in range(length_old_k_list):
            if old_k_list[i,3]!=0:
                new_k_list.extend(old_k_list[i,:])
    else:
        iter = 0
        while iter != length_old_k_list:
            # reading the k points inside the list and refine around them
            if length_old_k_list == 1:
                k_tmp = old_k_list[0,:3]
                k_tmp_weight = old_k_list[0,3]
                iter = length_old_k_list
            else:
                k_tmp = old_k_list[iter,:3]
                k_tmp_weight = old_k_list[iter,3]
                iter = iter + 1
            # refinment procedure is applied to the single k point if its weight is not null
            if k_tmp_weight != 0:
                # a subgrid of points is associated to each k point
                k_tmp_subgrid = np.zeros((4, 4))
                k_tmp_subgrid[:,:3] = k_tmp
                k_tmp_subgrid[0,:3] +=  normalized_brillouin_primitive_vectors_2d[0,:]*refinment_spacing
                k_tmp_subgrid[1,:3] -=  normalized_brillouin_primitive_vectors_2d[0,:]*refinment_spacing
                k_tmp_subgrid[2,:3] +=  normalized_brillouin_primitive_vectors_2d[1,:]*refinment_spacing
                k_tmp_subgrid[3,:3] -=  normalized_brillouin_primitive_vectors_2d[1,:]*refinment_spacing
                
                k_tmp_subgrid = symmetry_analysis(
                    k_tmp,
                    k_tmp_weight,
                    k_tmp_subgrid[:,:3],
                    symmetries,
                    threshold
                )
                
                k_tmp_subgrid=np.delete(k_tmp_subgrid, np.where(k_tmp_subgrid[:,3]==0),axis=0)
                if downfold == True:
                    k_tmp_subgrid[:,:3]=downfold_inside_brillouin_zone(
                        k_tmp_subgrid[:,:3],
                        brillouin_primitive_vectors_3d,
                    )
                # applying to the points of the subgrid to the refinment procedure
                new_refinment_spacing = refinment_spacing / 2
                
                local_refinment_with_symmetry_analysis(
                    new_k_list,
                    k_tmp_subgrid,
                    new_refinment_spacing,
                    refinment_iteration-1,
                    symmetries,
                    threshold,
                    brillouin_primitive_vectors_3d,
                    brillouin_primitive_vectors_2d,
                    normalized_brillouin_primitive_vectors_2d,
                    downfold
                )

def k_points_triangulation_2d(
    k_points_list,
    brillouin_primitive_vectors_2d,
    count
):
    r"""
    the sparse k points (kx,ky,kz,w) are linked togheter through a triangulation procedure (Delaunay procedure)
    the so-built triangles are listed, each triangle is characterized by three indices pointing to the vertices position in the k poins list  
    the ordering of the vertices is so to assure a cloack-wise path along the triangles

    the periodicity of the BZ is properly taken into account:
        the points at the left border or bottom border are considered twice in the triangulation
        once on their proper border, then on the opposite border (translation of a reciprocal vector)
        the index of the triangulation is the same both times, this assures the periodicity condition
    
    Parameters
    ---------
    k_points_list: (n,4) |array_like| (kx,ky,kz,w)
    brillouin_primitive_vectors_2d: (2,3) |array_like|
    count: (int) taking into account if the k points need to be added to a list, so numbering properly the vertices, in order to be able to use these triangles with the new list
    border_count: (int) taking into account if the first k points in k_points_list are from the border and are not neeeded to be added to the list  

    Returns
    ---------
    k_points_list: (n,4) |array_like| (kx,ky,kz,w)
    triangles: (s,3) |array_like| 
    left_border_points, bottom_border_points indices of the points at the border of the BZ
    """

    number_elements=k_points_list.shape[0]
    k_points_list_projections=np.zeros((number_elements,2),dtype=float)
    #choosing one point as an origin in the 2d brillouin plane
    origin=np.zeros(3,dtype=float)
    #calculating the projections of the different k points on the primitive vectors
    vector_0=np.zeros((number_elements,2),dtype=float)
    vector_1=np.zeros((number_elements,2),dtype=float)
    vector_2=np.ones((number_elements,2),dtype=float)
    for i in range(number_elements):
        vector_0[i,0]=1
        vector_1[i,1]=1
        for j in range(2):
            k_points_list_projections[i,j]=(k_points_list[i,:3]-origin)@brillouin_primitive_vectors_2d[j,:]
    
    #considering the periodic images
    k_points_list_projections_periodic_images=np.zeros((4*number_elements,2),dtype=float)
    k_points_list_projections_periodic_images[:number_elements,:]=k_points_list_projections
    k_points_list_projections_periodic_images[number_elements:2*number_elements,:]=k_points_list_projections+vector_0
    k_points_list_projections_periodic_images[2*number_elements:3*number_elements,:]=k_points_list_projections+vector_1
    k_points_list_projections_periodic_images[3*number_elements:,:]=k_points_list_projections+vector_2
    
    #triangulation of the set of points
    old_triangles_tmp = Delaunay(k_points_list_projections_periodic_images,qhull_options="QJ")
    print(old_triangles_tmp.add_points)

    old_triangles_tmp=old_triangles_tmp.simplices
    number_triangles = int(len(old_triangles_tmp))
    old_triangles=[]
    for i in range(number_triangles):
        triangle=np.zeros((3,2),dtype=int)
        count_element=0
        count_outside=0
        for element in old_triangles_tmp[i]:
            if element<number_elements:
                triangle[count_element,1]=0
                triangle[count_element,0]=element
            elif element>=number_elements and element<2*number_elements:
                triangle[count_element,1]=1
                count_outside+=1
                triangle[count_element,0]=element-number_elements
            elif element>=2*number_elements and element<3*number_elements:
                triangle[count_element,1]=2
                count_outside+=1
                triangle[count_element,0]=element-2*number_elements
            else:
                triangle[count_element,1]=3
                count_outside+=1
                triangle[count_element,0]=element-3*number_elements
            count_element+=1
        if count_outside < 3:
            old_triangles.append(triangle)
    number_triangles = int(len(old_triangles))

    #the projections along the two axis can be used to properly order the vertices of the triangls
    new_triangles = []
    vertices_projections = np.zeros((3,2),dtype=float)
    one=[1,0]
    two=[0,1]
    three=[1,1]
    for i in range(number_triangles):
        ##print(i,number_triangles)
        ##print(old_triangles[i])
        vertices=old_triangles[i]
        ##for r in range(3):
        ##    if vertices[r,1]==0:
        ##        vertices_projections[r]=k_points_list_projections[vertices[r,0]]
        ##    elif vertices[r,1]==1:
        ##        vertices_projections[r]=k_points_list_projections[vertices[r,0]]+one
        ##    elif vertices[r,1]==2:
        ##        vertices_projections[r]=k_points_list_projections[vertices[r,0]]+two
        ##    else:
        ##        vertices_projections[r]=k_points_list_projections[vertices[r,0]]+three
        ##indices=[tup[0] for tup in sorted(enumerate(vertices_projections[:,1]))]
        ##vertices_projections=vertices_projections[indices]
        ##if vertices_projections[0,1]==np.min(vertices_projections[:,0]):
        ##    indices=[tup[0] for tup in sorted(enumerate(vertices_projections[:,0]))]
        ##    vertices_projections=vertices_projections[indices]
        ##vertices=vertices[indices]
        #considering the case the function is called on an existing list (the existing list has length equal to count)
        ##for s in range(3):
        ##    if  vertices[s,0]> count:
        ##        vertices[s,0]+=count
        new_triangles.append(vertices)
       
    #for each triangle the ordering of the vertices is now clock-wise
    return k_points_list,new_triangles

#generation of a 2D k points grid 
def k_points_generator_2D(
    brillouin_primitive_vectors_3d,
    other_brillouin_primitive_vectors_3d,
    initial_grid_spacing,
    chosen_plane,
    brillouin_primitive_vectors_2d,
    default_gridding=10,
    symmetry_analysis_flag=False,
    refinment_spacing=0,
    symmetries=[[0,0,0]],
    threshold=0.0001,
    refinment_iteration=0,
    shift_in_plane=[0,0],
    shift_in_space=[0,0,0],
    precedent_count=0
):
    r"""
    k points generator in a 2d plane
    
    Parameters
    ----------
    brillouin_primitive_vectors_3d: (3,3) |array_like| (columns: kx,ky,kz, rows: b1,b2,b3)
    chosen_plane: (,3) |array_like|  ex. [0,1,1] the plane is the b2 x b3 plane in the reciprocal space where the bi are the brillouin primitive vectors
    initial_grid_spacing: |double| spacing of the k grid before the refinment procedure
    shift_in_plane : (,2) |array_like| shift of the chosen reciprocal 2D plane with respecet to the crystal coordinates
    shift_in_space : (,3) |array_like|  shift of the chosen reciprocal 2D plane with respecet to the cartesian coordinates 
    (this allow to build a 3D k points grid, considering different shifts along the third brillouin primitive vector, if there are no symmetries along this direction to consider)
    symmetries: |list of lists| a symmetry is a list of 3 elements (the versor is the axis of rotation, while the modulus is the angle)
    refinment_spacing: |double| initial spacing given to generate the refinment, half of the preceding refinment spacing is considered at each refinment iteration
    refinment_iteration: |int| number of refinment iterations considered
    threshold: |double| therhold to recognize a symmetry
    symmetry_analysis: |boolean| local_refinment_with_symmetry_analysis or not
    Return
    -------------
    "local_refinment_with_symmetry_analysis" not considered:
        k_points_list: (1,k0*k1) |array_like| k points (kx,ky,kz,w) where w is the weight of the k point
        parallelograms : (n,4) |array_like| each row is a parallelogram, where the 4 vertices are integers, which correspond to the list positions of the given k points 
    "local_refinment_with_symmetry_analysis" considered:
        k_points_list: (1,k0*k1) |array_like| k points (kx,ky,kz,w) where w is the weight of the k point
        triangles: (n,3) |array_like| each row is a triangle, where the 3 vertices are integers, which correspond to the list positions of the given k points 
    """
    normalized_brillouin_primitive_vectors_2d = np.zeros((2, 3),dtype=float)
    ##print("ecco",precedent_count)
    if  chosen_plane==[0,0,0]:
        chosen_plane=[]
        for i in range(2):
            normalized_brillouin_primitive_vectors_2d[i] = brillouin_primitive_vectors_2d[i]/(brillouin_primitive_vectors_2d[i]@brillouin_primitive_vectors_2d[i])
            # redefining the brillouin_primitive_vectors_3d in order to take into account the input brillouin_primitive_vectors_2d
            for j in range(3):
                if (brillouin_primitive_vectors_3d[j,:]@brillouin_primitive_vectors_2d[i,:])!=0:
                    chosen_plane.append(j)
        count = 0
        for i in chosen_plane:
            brillouin_primitive_vectors_3d[i,:]=brillouin_primitive_vectors_2d[count,:]
            count +=1                    
    else:
        #saving the chosen 2d plane 
        count = 0
        for i in range(3):
            if chosen_plane[i] != 0:
                brillouin_primitive_vectors_2d[count] = brillouin_primitive_vectors_3d[i]
                normalized_brillouin_primitive_vectors_2d[count] = brillouin_primitive_vectors_2d[count]/(brillouin_primitive_vectors_2d[count]@brillouin_primitive_vectors_2d[count])
                count += 1

    #initial 2D grid dimensions
    print(brillouin_primitive_vectors_2d[1])
    k0 = int(
        (brillouin_primitive_vectors_2d[0] @ brillouin_primitive_vectors_2d[0])/ initial_grid_spacing
        )
    k1 = int(
        (brillouin_primitive_vectors_2d[1] @ brillouin_primitive_vectors_2d[1]) / initial_grid_spacing
        )
    if k0==0 or k1==0:
        k0=default_gridding
        k1=default_gridding

    print("k0 k1",k0,k1,default_gridding)
    initial_weights = 1 / (k0 * k1)
    #building the initial 2D k points grid
    k_points_grid = np.zeros((k0*k1,4),dtype=float)
    for i in range(k0):
        for j in range(k1):
            k_points_grid[i*k1+j,:3] = (float(i + shift_in_plane[0]) / k0) * (shift_in_space + brillouin_primitive_vectors_2d[0,:]) + (float(j + shift_in_plane[1]) / k1) * (shift_in_space + brillouin_primitive_vectors_2d[1,:])
            k_points_grid[i*k1+j,3] = initial_weights
            ###print(k_points_grid[i*k1+j,:3])
    if symmetry_analysis_flag == True:
        if refinment_spacing==0:
            refinment_spacing=initial_grid_spacing/2

        #applying the refinment procedure to the 2d k points grid
        #obtaining a refined list
        refined_k_points_list = []

        local_refinment_with_symmetry_analysis(
            refined_k_points_list,
            k_points_grid,
            refinment_spacing,
            refinment_iteration,
            symmetries,
            threshold,
            brillouin_primitive_vectors_3d,
            brillouin_primitive_vectors_2d,
            normalized_brillouin_primitive_vectors_2d,
            True
        )
        #transforming a list into an array-like element
        k0=int(len(refined_k_points_list)/4)
        refined_k_points_list = np.reshape(refined_k_points_list,(int(len(refined_k_points_list)/4), 4))
        #applying a triangulation to order the k points
        #the periodicity of the BZ is properly considered
        refined_k_points_list,triangles=k_points_triangulation_2d(refined_k_points_list,brillouin_primitive_vectors_2d,0)
        return refined_k_points_list,triangles
    else:
        not_refined_k_points_list = np.zeros((k0*k1,4))
        parallelograms=[]
        if np.array_equal(other_brillouin_primitive_vectors_3d,brillouin_primitive_vectors_3d):
            for i in range(0,k0):
                for j in range(0,k1):
                   # print(i,j,k0,k1)
                    not_refined_k_points_list[i*k1+j][:3]=(float(i + shift_in_plane[0]) / k0) * (shift_in_space + brillouin_primitive_vectors_2d[0]) \
                       + (float(j + shift_in_plane[1]) / k1) * (shift_in_space + brillouin_primitive_vectors_2d[1])
                    not_refined_k_points_list[i*k1+j][3]=initial_weights
                    #periodicity of the BZ
                    parallelogram=[]
                    if i<k0-1 and j<k1-1:
                        parallelogram=[[i*k1+j,0],[(i+1)*k1+j,0],[(i+1)*k1+j+1,0],[i*k1+j+1,0]]
                    elif i<k0-1 and j==k1-1:
                        parallelogram=[[i*k1+j,0],[(i+1)*k1+j,0],[(i+1)*k1+0,2],[i*k1+0,2]]
                    elif i==k0-1 and j<k1-1:
                        parallelogram=[[i*k1+j,0],[0*k1+j,1],[0*k1+j+1,1],[i*k1+j+1,0]]
                    else:
                        parallelogram=[[i*k1+j,0],[0*k1+j,1],[0*k1+0,3],[i*k1+0,2]]
                    ##print(parallelogram)
                    #for r in range(4):
                     #   parallelogram[r][0]+=precedent_count  
                    ####print(parallelogram)    
                    parallelograms.append(parallelogram)
                    ##print(parallelogram[1][0])
            parallelograms=np.reshape(parallelograms,(int(k0*k1),4,2))
        else:
            for i in range(0,k0):
                for j in range(0,k1):
                   # print(i,j,k0,k1)
                    not_refined_k_points_list[i*k1+j][:3]=(float(i + shift_in_plane[0]) / k0) * (shift_in_space + brillouin_primitive_vectors_2d[0]) \
                       + (float(j + shift_in_plane[1]) / k1) * (shift_in_space + brillouin_primitive_vectors_2d[1])
                    not_refined_k_points_list[i*k1+j][3]=initial_weights
                    parallelogram=[]
                    parallelogram=[[i*k1+j,0],[(i+1)*k1+j,0],[(i+1)*k1+j+1,0],[i*k1+j+1,0]]
                    parallelograms.append(parallelogram)
                    ##print(parallelogram[1][0])
            parallelograms=np.reshape(parallelograms,(int(k0*k1),4,2))
            print("dentro")
            print(not_refined_k_points_list)
            ### checking if the points are going over one of the borders of the other_brillouin_primitive_vectors_3d (in the input)
            not_refined_k_points_list[:,:3],indices=downfold_inside_brillouin_zone(
                not_refined_k_points_list[:,:3],
                other_brillouin_primitive_vectors_3d)
            print(np.shape(not_refined_k_points_list))
            #print(np.shape(not_refined_k_points_list))
            print(np.shape(parallelograms))
            print(np.shape(indices))
            #print(not_refined_k_points_list[0][3])
            print(parallelograms)

            for parallelogram in parallelograms:
                for vertex in parallelogram:
                    print(vertex)
                    if indices[vertex[0]][0]==3:
                        vertex[1]+=-(1+int(vertex[0][1]/k1))*k1
                        vertex[2]+=-(int(vertex[0][1]%k1)+1)-(1+int(vertex[0][1]/k1))*k1
                        vertex[3]+=-(int(vertex[0][1]%k1)+1)
                    elif indices[vertex[0]][0]==2:
                        vertex[2]+=-(int(vertex[0][1]%k1)+1)
                        vertex[3]+=-(int(vertex[0][1]%k1)+1)
                    else:
                        vertex[1]+=-(1+int(vertex[0][1]/k1))*k1
                        vertex[2]+=-(1+int(vertex[0][1]/k1))*k1     
        
        print(not_refined_k_points_list)      
        return not_refined_k_points_list,parallelograms

def check_inside_closed_shape_2d(
    eigenvectors_around_array,
    refined_k_points_list,
    brillouin_primitive_vectors_2d
):
    number_elements_border=eigenvectors_around_array.shape[0]
    number_elements=refined_k_points_list.shape[0]

    k_points_list_projections_border=np.zeros((number_elements_border,2),dtype=float)
    k_points_list_projections=np.zeros((number_elements_border,2),dtype=float)

    origin=np.zeros(3,dtype=float)

    #calculating the projections of the different k points on the primitive vectors
    for i in range(number_elements_border):
        for j in range(2):
            k_points_list_projections_border[i,j]=(eigenvectors_around_array[i,:3]-origin)@brillouin_primitive_vectors_2d[j,:]
    for i in range(number_elements):
        for j in range(2):
            k_points_list_projections[i,j]=(refined_k_points_list[i,:3]-origin)@brillouin_primitive_vectors_2d[j,:]
    
    #Point Inclusion in Polygon Test W. Randolph Franklin (WRF) 
    def pnpoly(nvert,vert,test):
        i=0
        c=1
        while i < nvert:
            for j in range(i+1,nvert-1):
                if ( ((vert[i,1]>test[1]) != (vert[j,1]>test[1])) and (test[0]<(vert[j,0]-vert[i,0])*(test[1]-vert[i,1])/(vert[j,1]-vert[i,1])+vert[i,0]) ):    
                    c = -c
        return c
    indices=[]
    for i in range(number_elements):
        if pnpoly(number_elements_border,k_points_list_projections_border,k_points_list_projections[i])<0:
            indices.append(i)
    del refined_k_points_list[indices]
    return refined_k_points_list

def dynamical_refinment_little_paths_2d(
        little_paths,
        position_little_paths_to_refine,
        number_vertices,
        all_k_points_list,
        refinment_iteration,
        symmetries,
        threshold,
        brillouin_primitive_vectors_3d,
        brillouin_primitive_vectors_2d,
        chosen_plane,
        normalized_brillouin_primitive_vectors_2d,
        epsilon
):
    r"""
    some k points of the "all k points list" are selected (the ones in the selected little paths "position_littles_paths_to_refine"), 
    and a local refinment is applied to them, in case of triangles (number_vertices=3) a refinment with symmetry analysis is applied,
    in case of parallelograms (number_vertices=4) a refinment without symmetry analysis is applied 
    points on the border or nearby the border of the BZ are properly considered

    a refinmente without symmetry analysis is done in the case of parallelograms 

    Parameters
    ---------
    little_paths: (s,number_vertices) |array_like| (v1,v2,v3...) int (v=vertex)
    all_k_points_list: (n,4) |array_like| (kx,ky,kz,w)
    positions_little_paths_to_refine: |list| (int) positions of the little paths to which the refinment procedure is applied
    number_vertices: |int| distinguishing between traingles and parallelograms

    (parameters for the refinment...)

    Returns
    ---------
    new_k_points_list: (n,4) |array_like| (kx,ky,kz,w)
    added_little_paths: (,3) |array_like| (v1,v2,v3)
    """
    ###print(all_k_points_list)
    new_all_k_points_list=all_k_points_list
    only_new_little_paths=[]
    number_little_paths=len(little_paths)
    eigenspaces_little_paths_to_refine=[[i] for i in position_little_paths_to_refine]
    flag_checking_indipendence=True
    print(position_little_paths_to_refine)
    while flag_checking_indipendence == True:
        number_eigenspaces=len(eigenspaces_little_paths_to_refine)
        number_total_eigenvectors=0
        number_total_around=0
        little_paths_around_each_eigenspace=[]
        print("eigenspaces",eigenspaces_little_paths_to_refine)
        for eigenspace in eigenspaces_little_paths_to_refine:
            print(eigenspace)
            number_eigenvectors=len(eigenspace)
            number_total_eigenvectors+=number_eigenvectors
            # considering the to-refine little paths in the selected eigenspace
            eigenvectors = little_paths[eigenspace]
            # the little paths around each eigenvector are associated to it
            little_paths_around_each_eigenvector=[]
            for i in range(number_eigenvectors):
                little_paths_around_each_eigenvector.extend([r for r in range(number_little_paths) for j in little_paths[r][:,0] if j in eigenvectors[i][:,0] and r not in eigenspace])
            little_paths_around_each_eigenvector=list(np.unique(little_paths_around_each_eigenvector))
            number_total_around+=len(little_paths_around_each_eigenvector)
            little_paths_around_each_eigenspace.append(little_paths_around_each_eigenvector)
        # checking if two eigenspaces are in reality the same eigenspace:
        # between the "little_paths_around" of one of the two eigenspaces the index of one of the eigenvectors of the other eigenspace appear
        check_degeneracy = np.zeros((number_eigenspaces, number_eigenspaces), dtype=bool)
        any_degeneracy = 0
        for i in range(number_eigenspaces-1):
            for j in range(i+1,number_eigenspaces):
                for r in range(len(eigenspaces_little_paths_to_refine[i])):
                    if eigenspaces_little_paths_to_refine[i][r] in little_paths_around_each_eigenspace[j]:
                        check_degeneracy[i,j]=True
                        any_degeneracy+=1
                        break
                    else:
                        check_degeneracy[i,j]=False
        if any_degeneracy!=0:
            #unifying the eigenspaces properly
            #after having written them in an array form to facilitate it (the unification)
            #unifying as well the "little paths around"
            eigenspaces_little_paths_to_refine_array=np.zeros((number_total_eigenvectors,2),dtype=int)
            little_paths_around_each_eigenspace_array=np.zeros((number_total_around,2),dtype=int)
            count1=0
            count2=0
            count4=0
            for eigenspace in eigenspaces_little_paths_to_refine:
                print("degeneracy checking",eigenspace)
                count3=0
                for eigenvector in eigenspace:
                    eigenspaces_little_paths_to_refine_array[count1,0]=eigenvector
                    eigenspaces_little_paths_to_refine_array[count1,1]=count2
                    count1+=1
                for around in little_paths_around_each_eigenspace[count2]:
                    little_paths_around_each_eigenspace_array[count4,0]=around
                    little_paths_around_each_eigenspace_array[count4,1]=count2
                    count4+=1
                count3+=1
                count2+=1
            count=0
            print("before degeneracy",eigenspaces_little_paths_to_refine_array)
            print(check_degeneracy)
            for i in range(number_eigenspaces-1):
                for j in range(i+1,number_eigenspaces):
                    if check_degeneracy[i][j]==True:
                        min_value=min(i,j)
                        max_value=max(i,j)
                        eigenvectors_positions=[r for r in range(number_total_eigenvectors) if eigenspaces_little_paths_to_refine_array[r,1]==max_value]
                        around_positions=[r for r in range(number_total_around) if little_paths_around_each_eigenspace_array[r,1]==max_value]
                        eigenspaces_little_paths_to_refine_array[eigenvectors_positions,1]=min_value
                        little_paths_around_each_eigenspace_array[around_positions,1]=min_value
            print("after degeneracy",eigenspaces_little_paths_to_refine_array)
            # redefining eigenspaces in order to take into account the found degeneracies
            values_eigenspaces=list(np.unique(eigenspaces_little_paths_to_refine_array[:,1]))
            eigenspaces_little_paths_to_refine=[]
            little_paths_around_each_eigenspace=[]
            for value in values_eigenspaces:
                eigenspaces_little_paths_to_refine.append([eigenspaces_little_paths_to_refine_array[r,0] for r in range(number_total_eigenvectors) if eigenspaces_little_paths_to_refine_array[r,1]==value])
                little_paths_around_each_eigenspace.append([little_paths_around_each_eigenspace_array[r,0] for r in range(number_total_around) if little_paths_around_each_eigenspace_array[r,1]==value])
            print("proper renaming",eigenspaces_little_paths_to_refine,little_paths_around_each_eigenspace)
            # eliminating in each eigenspace the presence of eigenvectors in other eigenvectors little paths around
            number_eigenspaces=len(eigenspaces_little_paths_to_refine)
            print(number_eigenspaces)
            for i in range(number_eigenspaces):
                print(i,little_paths_around_each_eigenspace[i])
                indices=[]
                count6=0
                for r in little_paths_around_each_eigenspace[i]:
                    for j in eigenspaces_little_paths_to_refine[i]:
                        if j == r:
                            indices.append(count6)
                    count6+=1
                indices.sort()
                print("indices",indices)
                if len(indices)!=0:
                    count5=0
                    for index in indices:
                        print(index)
                        del little_paths_around_each_eigenspace[i][index-count5]
                        count5+=1
                print("after erasing",little_paths_around_each_eigenspace)
            # checking if two eigenspaces have one little path around in common 
            # this in common little path is inserted into the to refine little paths and the procedure is repeated
            new_little_paths_to_refine=[]
            for i in range(number_eigenspaces-1):
                for j in range(i+1,number_eigenspaces):
                    for element in little_paths_around_each_eigenspace[i]:
                        if element in little_paths_around_each_eigenspace[j]:
                            new_little_paths_to_refine.append(element)
            if len(new_little_paths_to_refine)==0:
                flag_checking_indipendence=True
            else:
                new_little_paths_to_refine=list(np.unique(new_little_paths_to_refine))
                for s in new_little_paths_to_refine:
                    eigenspaces_little_paths_to_refine.append([s])
        else:
            flag_checking_indipendence=False
        print("finish cycle",eigenspaces_little_paths_to_refine,little_paths_around_each_eigenspace)
    print("Little paths to refine:", eigenspaces_little_paths_to_refine)
    print("Little paths around the ones to refine:", little_paths_around_each_eigenspace)
    #substituting to the little_paths_positions, the k points positions
    print("in the middle",new_all_k_points_list)
    number_eigenspaces=len(eigenspaces_little_paths_to_refine)
    eigenspaces_k_points_to_refine=[]
    eigenspaces_k_points_around=[]
    for eigenspace in eigenspaces_little_paths_to_refine:
        eigenspaces_k_points_to_refine.append(np.unique([vertex for eigenvector in eigenspace for vertex in little_paths[eigenvector]],axis=0))
        for eigenvector in eigenspace:
            print("k point paths to refine",little_paths[eigenvector])
    for eigenspace in little_paths_around_each_eigenspace:
        eigenspaces_k_points_around.append(np.unique([vertex for eigenvector in eigenspace for vertex in little_paths[eigenvector]],axis=0))    
    print("K points to refine:", np.shape(eigenspaces_k_points_to_refine))
    print(eigenspaces_k_points_to_refine)
    print("K points around the ones to refine:", np.shape(eigenspaces_k_points_around))
    print(eigenspaces_k_points_around)
    # procede to a refinement of the k points constituing the to-refine little paths
    if number_vertices==3:
        all_new_triangles=[]
        all_k_points_list_tmp=[]
        # finding the minimum distance between the to-refine k points and the border k points
        for i in range(number_eigenspaces):
            number_eigenvectors=len(eigenspaces_k_points_to_refine[i])
            eigenvectors_array=np.zeros((number_eigenvectors,3),dtype=float)
            number_eigenvectors_around=len(eigenspaces_k_points_around[i])
            eigenvectors_around_array=np.zeros((number_eigenvectors_around,3),dtype=float)
            for j in range(number_eigenvectors):
                if eigenspaces_k_points_to_refine[i][j,1]==0:
                    eigenvectors_array[j]=all_k_points_list[eigenspaces_k_points_to_refine[i][j,0]]
                elif eigenspaces_k_points_to_refine[i][j,1]==1:
                    eigenvectors_array[j]=all_k_points_list[eigenspaces_k_points_to_refine[i][j,0]]+brillouin_primitive_vectors_2d[0]
                else:
                    eigenvectors_array[j]=all_k_points_list[eigenspaces_k_points_to_refine[i][j,0]]+brillouin_primitive_vectors_2d[1]
            minimal_distance = (cdist(eigenvectors_array-eigenvectors_around_array)).min()
            refined_k_points_list=[]
            local_refinment_with_symmetry_analysis(
                refined_k_points_list,
                eigenvectors_array,
                minimal_distance,
                refinment_iteration,
                symmetries,
                threshold,
                brillouin_primitive_vectors_3d,
                brillouin_primitive_vectors_2d,
                normalized_brillouin_primitive_vectors_2d,
                False
            )
            # transforming from a list to array_like elements
            refined_k_points_list = np.reshape(refined_k_points_list,(int(len(refined_k_points_list)/4), 4))
            # check if the points are inside the border 
            refined_k_points_list = check_inside_closed_shape_2d(
                                        eigenvectors_around_array,
                                        refined_k_points_list,
                                        brillouin_primitive_vectors_2d)
            # triangulation
            refined_k_points_list,added_triangles=k_points_triangulation_2d(
                                                    refined_k_points_list,
                                                    brillouin_primitive_vectors_2d,
                                                    count)
            count+=len(refined_k_points_list)
            all_k_points_list_tmp.append(refined_k_points_list)
            all_new_triangles.append(added_triangles)
        all_k_points_list.append(all_k_points_list_tmp)
        return all_k_points_list, added_triangles
    else:
        print("dentro2")
        # here it is sufficient to find for each eigenspace the extremal k points
        # these k points are then used to draw a simil-BZ, which is refined using the grid-generation 2d methods
        precedent_count=len(all_k_points_list)
        ###print("ecco2",precedent_count)
       # print(np.shape(eigenspaces_k_points_around))
        for i in range(number_eigenspaces):
            number_eigenvectors_around=len(eigenspaces_k_points_around[i])
            #print(number_eigenvectors_around)
            eigenvectors_around_array=np.zeros((number_eigenvectors_around,4),dtype=float)
            #print(eigenspaces_k_points_around[i])
            for j in range(number_eigenvectors_around):
                print(all_k_points_list[eigenspaces_k_points_around[i][j][0]])
                if eigenspaces_k_points_around[i][j][1]==3:
                    eigenvectors_around_array[j,:3]=all_k_points_list[eigenspaces_k_points_around[i][j][0],:3]+brillouin_primitive_vectors_2d[1]+brillouin_primitive_vectors_2d[0]
                elif eigenspaces_k_points_around[i][j][1]==2:
                    eigenvectors_around_array[j,:3]=all_k_points_list[eigenspaces_k_points_around[i][j][0],:3]+brillouin_primitive_vectors_2d[1]
                elif eigenspaces_k_points_around[i][j][1]==1:
                    eigenvectors_around_array[j,:3]=all_k_points_list[eigenspaces_k_points_around[i][j][0],:3]+brillouin_primitive_vectors_2d[0]
                else:
                    eigenvectors_around_array[j]=all_k_points_list[eigenspaces_k_points_around[i][j][0]]
                eigenvectors_around_array[j,3]=all_k_points_list[eigenspaces_k_points_around[i][j][0],3]
            #print(eigenvectors_around_array)
            #calculating the projections of the different k points on the primitive vectors
            print(brillouin_primitive_vectors_2d,eigenvectors_around_array)
            k_points_list_projections_border=np.zeros((number_eigenvectors_around,2),dtype=float)
            for i in range(number_eigenvectors_around):
                for j in range(2):
                    k_points_list_projections_border[i,j]=(eigenvectors_around_array[i,:3])@brillouin_primitive_vectors_2d[j,:]
            #transforming into polar coordinates x,y -> rho,theta
            rho=list(map(lambda x,y: math.sqrt(x**2+y**2),k_points_list_projections_border[:,0],k_points_list_projections_border[:,1]))
            rho=np.reshape(rho,(number_eigenvectors_around,1))
            ij_origin=np.argmin(rho)
            print(rho)
            origin=eigenvectors_around_array[ij_origin,:3]
            print("origine:", origin)
            #defining the projections respect to the new origin
            for i in range(number_eigenvectors_around):
                for j in range(2):
                    k_points_list_projections_border[i,j]=((eigenvectors_around_array[i,:3])-origin)@brillouin_primitive_vectors_2d[j,:]
            #transforming into polar coordinates x,y -> rho,theta
            rho=list(map(lambda x,y: math.sqrt(x**2+y**2),k_points_list_projections_border[:,0],k_points_list_projections_border[:,1]))
            rho=np.reshape(rho,(number_eigenvectors_around,1))
            theta=list(map(lambda x,y: math.atan(y/(x+epsilon)),k_points_list_projections_border[:,0],k_points_list_projections_border[:,1]))
            for i in range(len(theta)):
                if theta[i]<0:
                    theta[i]=-theta[i]+np.pi/2
            theta=np.reshape(theta,(number_eigenvectors_around,1))
            #print("theta ",theta)
            #print("rho",rho)
            theta_0=np.min(theta)
            ij_a0=[i for i in range(number_eigenvectors_around) if np.isclose(theta[i],theta_0,atol=epsilon)]
            rho_0=np.max(rho[ij_a0])
            j_a0=np.min([i for i in range(number_eigenvectors_around) if np.isclose(rho_0,rho[i],atol=epsilon) and i in ij_a0])
            #i_a0=[i for i in range(number_eigenvectors_around) if np.isclose(np.min(rho[ij_a0]),rho[i])]
            theta_1=np.max(theta)
            ij_a1=[i for i in range(number_eigenvectors_around) if np.isclose(theta[i],theta_1,atol=epsilon)]
            rho_1=np.max(rho[ij_a1])
            j_a1=np.min([i for i in range(number_eigenvectors_around) if np.isclose(rho_1,rho[i],atol=epsilon) and i in ij_a1])
            #i_a1=[i for i in range(number_eigenvectors_around) if np.isclose(np.min(rho[ij_a1]),rho[i],atol=epsilon)]
            #print(theta_0,theta_1)
            #print(rho_0,rho_1)
            #print("indices: ",j_a0,j_a1)
            #print(origin,eigenvectors_around_array[j_a0,:3],eigenvectors_around_array[j_a1,:3])
            #finding the new bordening
            new_brillouin_primitive_vectors_2d=np.zeros((2,3),dtype=float)
            new_brillouin_primitive_vectors_2d[0]=eigenvectors_around_array[j_a0,:3]-origin
            new_brillouin_primitive_vectors_2d[1]=eigenvectors_around_array[j_a1,:3]-origin
            #print(new_brillouin_primitive_vectors_2d)
            new_brillouin_primitive_vectors_3d=np.zeros((3,3),dtype=float)
            new_brillouin_primitive_vectors_3d[2,:]=brillouin_primitive_vectors_3d[[i for i in range(3) if chosen_plane[i]==0],:]
            for i in range(2):
                new_brillouin_primitive_vectors_3d[i,:]=new_brillouin_primitive_vectors_2d[i,:]
            
            #finding the minimal grid spacing
            max_value=np.linalg.norm(new_brillouin_primitive_vectors_2d[0]+new_brillouin_primitive_vectors_2d[1],2)
            moduli=np.zeros(number_eigenvectors_around,dtype=float)
            for i in range(number_eigenvectors_around):
                moduli[i]=np.linalg.norm(eigenvectors_around_array[i,:3]-origin,2)
                if moduli[i]<epsilon:
                    moduli[i]=max_value
            initial_grid_spacing=np.min(moduli)/2
            #print(initial_grid_spacing)
            print("input gridding",new_brillouin_primitive_vectors_3d,
              initial_grid_spacing,
              chosen_plane,
              new_brillouin_primitive_vectors_2d,
              origin)
            
            new_not_refined_k_points_list,new_parallelograms=k_points_generator_2D(
                new_brillouin_primitive_vectors_3d,
                brillouin_primitive_vectors_3d,
                initial_grid_spacing,
                chosen_plane,
                new_brillouin_primitive_vectors_2d,
                100,
                False,
                0,
                [[0,0,0]],
                0.0,
                0,
                [0,0],
                origin,
                precedent_count
                )
            for parallelogram in parallelograms:
                for vertex in parallelogram:
                    vertex[1]+=precedent_count
           ### print(new_all_k_points_list)
           #### print(new_not_refined_k_points_list)
            precedent_count+=len(new_not_refined_k_points_list)
            new_all_k_points_list=np.append(new_all_k_points_list,new_not_refined_k_points_list,axis=0)
            only_new_little_paths.extend(new_parallelograms)

        print(np.shape(only_new_little_paths))
        ##only_new_little_paths=np.reshape(only_new_little_paths,(int(len(only_new_little_paths)/3),3))
        
        return new_all_k_points_list,only_new_little_paths

#TESTING INPUT
if __name__ == "__main__":
    import timeit
    import os
    import matplotlib
    from matplotlib.artist import Artist
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection
    import numpy as np
    ##from termcolor import cprint
    from radtools.io.internal import load_template
    from radtools.io.tb2j import load_tb2j_model
    from radtools.magnons.dispersion import MagnonDispersion
    from radtools.decorate.stats import logo
    from radtools.spinham.constants import TXT_FLAGS
    from radtools.decorate.array import print_2d_array
    from radtools.decorate.axes import plot_hlines

    brillouin_primitive_vectors_3d=np.zeros((3,3),dtype=float)
    brillouin_primitive_vectors_3d[0]=[1,0,0]
    brillouin_primitive_vectors_3d[1]=[0,1,0]
    brillouin_primitive_vectors_3d[2]=[0,0,1]
    brillouin_primitive_vectors_2d=np.zeros((2,3),dtype=float)
    chosen_plane=[1,1,0]
    symmetries=[[0,0,np.pi/2]]
    initial_grid_spacing=0.1
    refinment_iteration=0
    refinment_spacing=0.1
    threshold=0.001
    epsilon=0.000000001
    default_gridding=1000
    count=0
    shift_in_plane=[0,0]
    shift_in_space=[0,0,0]

    ###LITTLE TRIANGLES
    refined_k_points_list,triangles=k_points_generator_2D(
        brillouin_primitive_vectors_3d,
        initial_grid_spacing,
        chosen_plane,
        brillouin_primitive_vectors_2d,
        True,
        refinment_spacing,
        symmetries,
        threshold,
        refinment_iteration,
        shift_in_space,
        shift_in_space,
        count
        )
    
    print(brillouin_primitive_vectors_3d)
    print(brillouin_primitive_vectors_2d)
    number_triangles=len(triangles)
    triangle=[0]*3
    new_triangles=[]
    for i in range(number_triangles):
        indx_1=[triangles[i][r][0] for r in range(3)]
        indx_2=[triangles[i][r][1] for r in range(3)]
        count=0
        for indx in indx_1:
            triangle[count]=[refined_k_points_list[indx,s] for s in range(3)]
            if indx_2[count]!=0:
                for s in range(3):
                    if indx_2[count]==1:
                        triangle[count][s]+=brillouin_primitive_vectors_2d[0,s]
                    elif indx_2[count]==2:
                        triangle[count][s]+=brillouin_primitive_vectors_2d[1,s]
                    else:
                        triangle[count][s]+=brillouin_primitive_vectors_2d[1,s]+brillouin_primitive_vectors_2d[0,s]
            count+=1
        new_triangles.extend(triangle)
    print(new_triangles) 
    new_triangles=np.reshape(new_triangles,(number_triangles,3,3))
    new_triangles=new_triangles[:,:,:2]
    fig,ax=plt.subplots()
    patches=[]
    
    for i in range(number_triangles):
        polygon=Polygon(new_triangles[i], closed=True, fill=None, edgecolor='b')
        patches.append(polygon)
    
    p = PatchCollection(patches,cmap=matplotlib.cm.jet,alpha=0.4)
    colors = 100*np.random.rand(len(patches))
    p.set_array(np.array(colors))
    ax.add_collection(p)
    plt.show()
    fig=plt.figure()
    ax=fig.add_subplot(projection='3d')
    ax.scatter(refined_k_points_list[:,0],refined_k_points_list[:,1],refined_k_points_list[:,3])
    plt.show()

    ###LITTLE PARALLELOGRAMS
    not_refined_k_points_list,parallelograms=k_points_generator_2D(
        brillouin_primitive_vectors_3d,
        brillouin_primitive_vectors_3d,
        initial_grid_spacing,
        chosen_plane,
        brillouin_primitive_vectors_2d,
        default_gridding,
        False,
        refinment_spacing,
        symmetries,
        threshold,
        refinment_iteration,
        shift_in_plane,
        shift_in_space,
        count
        )
    ###print(not_refined_k_points_list)
    ##print(parallelograms)
    number_parallelograms=len(parallelograms)
    print(np.shape(not_refined_k_points_list))
    print(np.shape(parallelograms))
    #print(parallelograms)
    parallelogram=[0]*4
    new_parallelograms_tmp=[]
    for i in range(number_parallelograms):
        indx_1=[parallelograms[i][r][0] for r in range(4)]
        indx_2=[parallelograms[i][r][1] for r in range(4)]
        count=0
        for indx in indx_1:
            parallelogram[count]=[not_refined_k_points_list[indx,s] for s in range(3)]
            if indx_2[count]!=0:
                for s in range(3):
                    if indx_2[count]==1:
                        parallelogram[count][s]+=brillouin_primitive_vectors_2d[0,s]
                    elif indx_2[count]==2:
                        parallelogram[count][s]+=brillouin_primitive_vectors_2d[1,s]
                    else:
                        parallelogram[count][s]+=brillouin_primitive_vectors_2d[1,s]+brillouin_primitive_vectors_2d[0,s]
            count+=1
        new_parallelograms_tmp.extend(parallelogram)
    print(np.shape(new_parallelograms_tmp))
    number_parallelograms=int(len(new_parallelograms_tmp)/4)
    new_parallelograms=np.reshape(new_parallelograms_tmp,(number_parallelograms,4,3))
    print(new_parallelograms)
    new_parallelograms=new_parallelograms[:,:,:2]
    fig,ax=plt.subplots()
    patches=[]
    for i in range(number_parallelograms):
        polygon=Polygon(new_parallelograms[i], closed=True, fill=None, edgecolor='c')
        patches.append(polygon)
    
    print(new_parallelograms)
    p = PatchCollection(patches,cmap=matplotlib.cm.jet,alpha=0.4)
    colors = 100*np.random.rand(len(patches))
    p.set_array(np.array(colors))
    ax.add_collection(p)
    plt.show()
    ##fig=plt.figure()
    ##ax=fig.add_subplot(projection='3d')
    ##ax.scatter(not_refined_k_points_list[:,0],not_refined_k_points_list[:,1],not_refined_k_points_list[:,3])
    ###plt.show()

    position_little_paths_to_refine=[31,32,33]
    for i in position_little_paths_to_refine:
        print(parallelograms[i])
    number_vertices=4,
    normalized_brillouin_primitive_vectors_2d=np.zeros((2,3),dtype=float)
    for i in range(2):
        normalized_brillouin_primitive_vectors_2d[i]=brillouin_primitive_vectors_2d[i]/np.dot(brillouin_primitive_vectors_2d[i],brillouin_primitive_vectors_2d[i])
    
    #print("prima", not_refined_k_points_list)
    #print(parallelograms)
    #print(position_little_paths_to_refine,
    #    number_vertices,
    #    not_refined_k_points_list,
    #    refinment_iteration,
    #    symmetries,
    #    threshold,
    #    brillouin_primitive_vectors_3d,
    #    brillouin_primitive_vectors_2d,
    #    chosen_plane,
    #    normalized_brillouin_primitive_vectors_2d,
    #    epsilon)
    #
    not_refined_k_points_list,parallelograms=dynamical_refinment_little_paths_2d(
        parallelograms,
        position_little_paths_to_refine,
        number_vertices,
        not_refined_k_points_list,
        refinment_iteration,
        symmetries,
        threshold,
        brillouin_primitive_vectors_3d,
        brillouin_primitive_vectors_2d,
        chosen_plane,
        normalized_brillouin_primitive_vectors_2d,
        epsilon
    )  
    #print("dopo", not_refined_k_points_list)
    #print(parallelograms)
    number_parallelograms=len(parallelograms)
    #print(np.shape(not_refined_k_points_list))
    #print(np.shape(parallelograms))
    #print(parallelograms)
    parallelogram=[0]*4
    new_parallelograms_tmp=[]
    for i in range(number_parallelograms):
        indx_1=[parallelograms[i][r][0] for r in range(4)]
        indx_2=[parallelograms[i][r][1] for r in range(4)]
        count=0
        for indx in indx_1:
            parallelogram[count]=[not_refined_k_points_list[indx,s] for s in range(3)]
            if indx_2[count]!=0:
                for s in range(3):
                    if indx_2[count]==1:
                        parallelogram[count][s]+=brillouin_primitive_vectors_2d[0,s]
                    elif indx_2[count]==2:
                        parallelogram[count][s]+=brillouin_primitive_vectors_2d[1,s]
                    else:
                        parallelogram[count][s]+=brillouin_primitive_vectors_2d[1,s]+brillouin_primitive_vectors_2d[0,s]
            count+=1
        new_parallelograms_tmp.extend(parallelogram)
    print(np.shape(new_parallelograms_tmp))
    number_parallelograms=int(len(new_parallelograms_tmp)/4)
    new_parallelograms=np.reshape(new_parallelograms_tmp,(number_parallelograms,4,3))
    #print(new_parallelograms)
    new_parallelograms=new_parallelograms[:,:,:2]
    fig,ax=plt.subplots()
    patches=[]
    for i in range(number_parallelograms):
        polygon=Polygon(new_parallelograms[i], closed=True, fill=None, edgecolor='c')
        patches.append(polygon)
    
    #print(new_parallelograms)
    p = PatchCollection(patches,cmap=matplotlib.cm.jet,alpha=0.4)
    colors = 100*np.random.rand(len(patches))
    p.set_array(np.array(colors))
    ax.add_collection(p)
    plt.show()
    ##fig=plt.figure()
    ##ax=fig.add_subplot(projection='3d')
    ##ax.scatter(not_refined_k_points_list[:,0],not_refined_k_points_list[:,1],not_refined_k_points_list[:,3])
    ##plt.show()

    ##dynamical refinment (parallelograms)
    ##print(not_refined_k_points_list)
    ##print(parallelograms)
    ##indices=[0,1,2,3,4,4,4,5]
    ##subset_parallelograms=parallelograms[indices]
    ##print(subset_parallelograms)
    ##normalized_brillouin_primitive_vectors_2d=np.zeros((2,3))
    ##for i in range(2):
    ##    for r in range(3):
    ##        normalized_brillouin_primitive_vectors_2d[i,r]=brillouin_primitive_vectors_2d[i,r]/np.dot(brillouin_primitive_vectors_2d[i],brillouin_primitive_vectors_2d[i])
    ##
    ##not_refined_k_points_list, parallelograms=dynamical_refinment_little_paths_2d(
    ##    parallelograms,
    ##    indices,
    ##    4,
    ##    not_refined_k_points_list,
    ##    refinment_iteration,
    ##    symmetries,
    ##    threshold,
    ##    brillouin_primitive_vectors_3d,
    ##    brillouin_primitive_vectors_2d,
    ##    chosen_plane,
    ##    normalized_brillouin_primitive_vectors_2d
    ##)