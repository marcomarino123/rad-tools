r"""
Collection of small routines and constants, 
which are used across the whole package.

It's purpose is to serve as an "other" folder.
"""

import sys
from math import asin, cos, pi, sin, sqrt

from matplotlib.colors import LinearSegmentedColormap, to_rgb

from scipy.spatial.transform import Rotation

from typing import Iterable

from radtools.crystal.constants import ABS_TOL_ANGLE, ABS_TOL, REL_TOL
from radtools.constants import todegrees, toradians

import numpy as np
from termcolor import cprint, colored

__all__ = [
    "print_2d_array",
    "compare_numerically",
    "volume",
    "angle",
    "parallelepiped_check",
    "absolute_to_relative",
    "span_orthonormal_set",
    "plot_horizontal_lines",
    "plot_vertical_lines",
    "custom_cmap",
    "winwait",
]


def atom_mark_to_latex(mark):
    r"""
    Latexifier for atom marks.

    Cr12 -> Cr\ :sub:`12`\.

    Parameters
    ----------
    mark : str
        Mark of atom.

    Returns
    -------
    new_mark : str
        Latex version of the mark.
    """
    numbers = "0123456789"
    new_mark = "$"
    insert_underline = False
    for symbol in mark:
        if symbol in numbers and not insert_underline:
            insert_underline = True
            new_mark += "_{"
        new_mark += symbol
    new_mark += "}$"
    return new_mark


def rot_angle(x, y, dummy=False):
    r"""
    Rotational angle from 2D vector.

    Mathematically positive => counterclockwise.
    From [0 to 360)

    Parameters
    ----------
    x : float or int
        x coordinate of a vector.
    y : float or int
        y coordinate of a vector.
    """
    # rot_cos = x / (x ** 2 + y ** 2) ** 0.5
    # rot_angle = m.acos(rot_cos) / m.pi * 180
    try:
        sin = abs(y) / sqrt(x**2 + y**2)
    except ZeroDivisionError:
        raise ValueError("Angle is ill defined (x = y = 0).")
    if x > 0:
        if y > 0:
            return asin(sin) / pi * 180
        elif y == 0:
            return 0
        elif y < 0:
            if not dummy:
                return -asin(sin) / pi * 180
            return 360 - asin(sin) / pi * 180
    elif x == 0:
        if y > 0:
            return 90
        elif y == 0:
            raise ValueError("Angle is ill defined (x = y = 0).")
        elif y < 0:
            if not dummy:
                return 90
            return 270
    elif x < 0:
        if y > 0:
            if not dummy:
                return -asin(sin) / pi * 180
            return 180 - asin(sin) / pi * 180
        elif y == 0:
            if not dummy:
                return 0
            return 180
        elif y < 0:
            if not dummy:
                return asin(sin) / pi * 180
            return 180 + asin(sin) / pi * 180


def absolute_to_relative(cell, absolute):
    r"""
    Compute relative coordinates with respect to the unit cell.

    Parameters
    ----------
    cell : (3, 3) |array_like|_
        Lattice vectors.
    absolute : (3,) |array_like|_
        Absolute coordinates.

    Returns
    -------
    relative : (3,) :numpy:`ndarray`
        Relative coordinates.
    """

    # Three vectors of the cell
    v1 = np.array(cell[0], dtype=float)
    v2 = np.array(cell[1], dtype=float)
    v3 = np.array(cell[2], dtype=float)

    v = np.array(absolute, dtype=float)
    if (v == np.zeros(3)).all():
        return np.zeros(3)

    # Compose system of linear equations
    B = np.array([np.dot(v1, v), np.dot(v2, v), np.dot(v3, v)])
    A = np.array(
        [
            [np.dot(v1, v1), np.dot(v1, v2), np.dot(v1, v3)],
            [np.dot(v2, v1), np.dot(v2, v2), np.dot(v2, v3)],
            [np.dot(v3, v1), np.dot(v3, v2), np.dot(v3, v3)],
        ]
    )

    # Solve and return
    return np.linalg.solve(A, B)


def volume(*args):
    r"""
    Computes volume.

    .. versionadded:: 0.7

    Three type of arguments are expected:

    * One argument.
        Matrix ``cell``.
        Volume is computed as:

        .. math::
            V = v_1 \cdot (v_2 \times v_3)
    * Three arguments.
        Vectors ``v1``, ``v2``, ``v3``.
        Volume is computed as:

        .. math::
            V = v_1 \cdot (v_2 \times v_3)
    * Six arguments.
        Parameters ``a``, ``b``, ``c``, ``alpha``, ``beta``, ``gamma``.
        Volume is computed as:

        .. math::
            V = abc\sqrt{1+2\cos(\alpha)\cos(\beta)\cos(\gamma)-\cos^2(\alpha)-\cos^2(\beta)-\cos^2(\gamma)}

    Parameters
    ----------
    v1 : (3,) |array_like|_
        First vector.
    v2 : (3,) |array_like|_
        Second vector.
    v3 : (3,) |array_like|_
        Third vector.
    cell : (3,3) |array_like|_
        Cell matrix, rows are interpreted as vectors.
    a : float, default 1
        Length of the :math:`v_1` vector.
    b : float, default 1
        Length of the :math:`v_2` vector.
    c : float, default 1
        Length of the :math:`v_3` vector.
    alpha : float, default 90
        Angle between vectors :math:`v_2` and :math:`v_3`. In degrees.
    beta : float, default 90
        Angle between vectors :math:`v_1` and :math:`v_3`. In degrees.
    gamma : float, default 90
        Angle between vectors :math:`v_1` and :math:`v_2`. In degrees.

    Returns
    -------
    volume : float
        Volume of corresponding region in space.
    """

    if len(args) == 1:
        cell = np.array(args[0])
    elif len(args) == 3:
        cell = np.array(args)
    elif len(args) == 6:
        a, b, c, alpha, beta, gamma = args
        alpha = alpha * toradians
        beta = beta * toradians
        gamma = gamma * toradians
        sq_root = (
            1
            + 2 * cos(alpha) * cos(beta) * cos(gamma)
            - cos(alpha) ** 2
            - cos(beta) ** 2
            - cos(gamma) ** 2
        )
        return abs(a * b * c * sqrt(sq_root))
    else:
        raise ValueError(
            "Unable to identify input. "
            + "Supported: one (3,3) array_like, or three (3,) array_like, or 6 floats."
        )

    return abs(np.linalg.det(cell))


def winwait():
    r"""
    Add "Press Enter to continue" behaviour to Windows.

    Its a hotfix for Window`s terminal behaviour.
    """
    if sys.platform == "win32":
        cprint("Press Enter to continue", "green")
        input()


def print_2d_array(
    array, fmt=".2f", highlight=False, print_result=True, borders=True, shift=0
):
    r"""
    Print 1D and 2D arrays in the terminal.

    .. versionadded:: 0.7

    .. versionchanged:: 0.7.11 Renamed from ``print_2D_array``

    Parameters
    ----------
    array : (N,) or (N, M) |array_like|_
        Array to be printed.
    fmt : str
        Format string.
    highlight : bool, default False
        Whether to highlight positive and negative values.
        Only works for real-valued arrays.

        .. versionchanged:: 0.7.11 Renamed from ``posneg``

    print_result : bool, default True
        Whether to print the result or return it as a string.
    borders : bool, default True
        Whether to print borders around the array.

        .. versionadded:: 0.7.11

    shift : int, default 0
        Shifts the array to the right by ``shift`` columns.

        .. versionadded:: 0.7.11

    Returns
    -------
    string : str
        String representation of the array.
        Returned only if ``print_result`` is False.
    """

    array = np.array(array)
    if (len(array.shape) == 1 and array.shape[0] != 0) or (
        len(array.shape) == 2 and array.shape[1] != 0
    ):
        # Convert 1D array to 2D array
        if len(array.shape) == 1:
            array = np.array([array])

        # Array dimensions
        N = len(array)
        M = len(array[0])

        # Find the longest number, used for string formatting
        n = max(
            len(f"{np.amax(array.real):{fmt}}"), len(f"{np.amin(array.real):{fmt}}")
        )
        n = max(
            n, len(f"{np.amax(array.imag):{fmt}}"), len(f"{np.amin(array.imag):{fmt}}")
        )

        # Check if input fmt exceeds the longest number
        try:
            n = max(n, int(fmt.split(".")[0]))
        except ValueError:
            pass

        fmt = f"{n}.{fmt.split('.')[1]}"

        def print_number(number, fmt, highlight=False, condition=None):
            if condition is None:
                condition = number
            string = ""
            # Highlight positive and negative values with colours
            if highlight:
                if condition > 0:
                    string += colored(f"{number:{fmt}}", "red", attrs=["bold"])
                elif condition < 0:
                    string += colored(f"{number:{fmt}}", "blue", attrs=["bold"])
                else:
                    string += colored(f"{number:{fmt}}", "green", attrs=["bold"])
            # Print without colours
            else:
                string += f"{number:{fmt}}"
            return string

        def print_complex(number, fmt, highlight):
            string = ""
            if number.real != 0:
                string += print_number(number.real, fmt, highlight)
            else:
                string += " " * len(print_number(number.real, fmt))

            if number.imag > 0:
                sign = "+"
            else:
                sign = "-"

            if number.imag != 0:
                string += f" {sign} i"
                string += print_number(
                    abs(number.imag), f"<{fmt}", highlight, condition=number.imag
                )
            else:
                string += " " * (
                    len(print_number(abs(number.imag), fmt, condition=number.imag)) + 4
                )
            return string

        def print_border(symbol_start, symbol_middle, symbol_end, n):
            string = symbol_start
            for j in range(0, M):
                # If at least one complex value is present in the column
                if np.iscomplex(array[:, j]).any():
                    string += f"{(2*n + 6)*'─'}"
                else:
                    string += f"{(n + 2)*'─'}"
                if j == M - 1:
                    string += symbol_end + "\n"
                else:
                    string += symbol_middle
            return string

        string = ""
        for i in range(0, N):
            substring = " " * shift
            if borders:
                substring += "│"

            for j in range(0, M):
                # Print complex values
                if np.iscomplex(array[:, j]).any():
                    # Print complex part if it is non-zero
                    substring += " " + print_complex(array[i][j], fmt, highlight)
                # Print real values
                else:
                    # Highlight positive and negative values with colours
                    substring += " " + print_number(array[i][j].real, fmt, highlight)
                if borders:
                    substring += " │"
            if i != N - 1 or borders:
                substring += "\n"

            if borders:
                # Header of the table
                if i == 0:
                    symbol_start = "┌"
                    symbol_middle = "┬"
                    symbol_end = "┐"
                    substring = (
                        " " * shift
                        + print_border(symbol_start, symbol_middle, symbol_end, n)
                        + substring
                    )

                # Footer of the table
                if i == N - 1:
                    symbol_start = "└"
                    symbol_middle = "┴"
                    symbol_end = "┘"
                    substring += (
                        " " * shift
                        + print_border(symbol_start, symbol_middle, symbol_end, n)[:-1]
                    )
                # Middle of the table
                else:
                    symbol_start = "├"
                    symbol_middle = "┼"
                    symbol_end = "┤"
                    substring += " " * shift + print_border(
                        symbol_start, symbol_middle, symbol_end, n
                    )

            string += substring
        if print_result:
            print(string)
        else:
            return string
    else:
        if print_result:
            print(None)
        else:
            return None


def angle(v1, v2, radians=False):
    r"""
    Angle between two vectors.

    .. versionadded:: 0.7

    .. math::

        \alpha = \dfrac{(\vec{v_1} \cdot \vec{v_2})}{\vert\vec{v_1}\vert\cdot\vert\vec{v_2}\vert}

    Parameters
    ----------
    v1 : (3,) |array_like|_
        First vector.
    v2 : (3,) |array_like|_
        Second vector.
    radians : bool, default False
        Whether to return value in radians. Return value in degrees by default.

    Returns
    -------
    angle: float
        Angle in degrees or radians (see ``radians``).

    Raises
    ------
    ValueError
        If one of the vectors is zero vector (or both). Norm is compare against
        :numpy:`finfo`\ (float).eps.
    """

    # Normalize vectors
    v1_norm = np.linalg.norm(v1)
    v2_norm = np.linalg.norm(v2)
    if abs(v1_norm) <= np.finfo(float).eps or abs(v2_norm) <= np.finfo(float).eps:
        raise ValueError("Angle is ill defined (zero vector).")

    v1 = np.array(v1) / v1_norm
    v2 = np.array(v2) / v2_norm

    alpha = np.arccos(np.clip(np.dot(v1, v2), -1.0, 1.0))
    if radians:
        return alpha
    return alpha * todegrees


def span_orthonormal_set(vec):
    r"""
    Span orthonormal set of vectors.

    Parameters
    ----------
    vec : (3,) |array_like|_
        Vector, which serves as :math:`e_3`

    Returns
    -------
    e1 : (3,) :numpy:`ndarray`
    e2 : (3,) :numpy:`ndarray`
    e3 : (3,) :numpy:`ndarray`
    """

    vec = np.array(vec) / np.linalg.norm(vec)

    if np.allclose(vec, [0, 0, 1]):
        return (
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
        )

    if np.allclose(vec, [0, 0, -1]):
        return (
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, -1.0, 0.0]),
            np.array([0.0, 0.0, -1.0]),
        )

    z_dir = [0, 0, 1]
    n = (
        np.cross(vec, z_dir)
        / np.linalg.norm(np.cross(vec, z_dir))
        * np.arccos(np.dot(vec, z_dir) / np.linalg.norm(vec))
    )
    rotation_matrix = Rotation.from_rotvec(n).as_matrix()

    return rotation_matrix


def plot_horizontal_lines(ax, positions):
    r"""
    Plot horizontal lines.

    Parameters
    ----------
    ax : :matplotlib:`axes`
        Axes to plot on.
    positions : list
        List of y positions.
    """

    if not isinstance(positions, Iterable):
        positions = [positions]

    ax.hlines(
        positions,
        0,
        1,
        transform=ax.get_yaxis_transform(),
        color="grey",
        linewidths=0.5,
        linestyles="dashed",
    )


def plot_vertical_lines(ax, positions):
    r"""
    Plot vertical lines.

    Parameters
    ----------
    ax : :matplotlib:`axes`
        Axes to plot on.
    positions : list
        List of x positions.
    """

    if not isinstance(positions, Iterable):
        positions = [positions]

    ax.vlines(
        positions,
        0,
        1,
        transform=ax.get_xaxis_transform(),
        color="grey",
        linewidths=0.5,
        linestyles="dashed",
    )


def custom_cmap(start_color, finish_color):
    r"""
    Prepare custom colormap. From one color to the other.

    Parameters
    ----------
    start_color : Color
        Start color.
    finish_color : Color
        Finish color.
    """

    r1, g1, b1 = to_rgb(start_color)

    r2, g2, b2 = to_rgb(finish_color)

    cdict = {
        "red": ((0, r1, r1), (1, r2, r2)),
        "green": ((0, g1, g1), (1, g2, g2)),
        "blue": ((0, b1, b1), (1, b2, b2)),
    }

    return LinearSegmentedColormap("custom_cmap", cdict, N=256)


def compare_numerically(x, condition, y, eps=None, rtol=REL_TOL, atol=ABS_TOL):
    r"""
    Compare two numbers numerically.

    Parameters
    ----------
    x : float
        First number.
    condition : str
        Condition to compare with. One of "<", ">", "<=", ">=", "==", "!=".
    y : float
        Second number.
    eps : float, optional
        Tolerance. Used for the comparison if provided. If ``None``, the computed as:

        .. code-block:: python

            eps = atol + rtol * y

    rtol : float, default 1e-04
        Relative tolerance.
    atol : float, default 1e-08
        Absolute tolerance.

    Returns
    -------
    result: bool
        Whether the condition is satisfied.
    """

    if eps is None:
        eps = atol + rtol * y

    if condition == "<":
        return x < y - eps
    if condition == ">":
        return y < x - eps
    if condition == "<=":
        return not y < x - eps
    if condition == ">=":
        return not x < y - eps
    if condition == "==":
        return not (x < y - eps or y < x - eps)
    if condition == "!=":
        return x < y - eps or y < x - eps


def parallelepiped_check(a, b, c, alpha, beta, gamma, raise_error=False):
    r"""
    Check if parallelepiped is valid.

    Parameters
    ----------
    a : float
        Length of the :math:`v_1` vector.
    b : float
        Length of the :math:`v_2` vector.
    c : float
        Length of the :math:`v_3` vector.
    alpha : float
        Angle between vectors :math:`v_2` and :math:`v_3`. In degrees.
    beta : float
        Angle between vectors :math:`v_1` and :math:`v_3`. In degrees.
    gamma : float
        Angle between vectors :math:`v_1` and :math:`v_2`. In degrees.
    raise_error : bool, default False
        Whether to raise error if parameters could not form a parallelepiped.

    Returns
    -------
    result: bool
        Whether the parameters could from a parallelepiped.

    Raises
    ------
    ValueError
        If parameters could not form a parallelepiped.
        Only raised if ``raise_error`` is ``True`` (it is ``False`` by default).
    """

    result = (
        compare_numerically(a, ">", 0.0, ABS_TOL)
        and compare_numerically(b, ">", 0.0, ABS_TOL)
        and compare_numerically(c, ">", 0.0, ABS_TOL)
        and compare_numerically(alpha, "<", 180.0, ABS_TOL_ANGLE)
        and compare_numerically(beta, "<", 180.0, ABS_TOL_ANGLE)
        and compare_numerically(gamma, "<", 180.0, ABS_TOL_ANGLE)
        and compare_numerically(alpha, ">", 0.0, ABS_TOL_ANGLE)
        and compare_numerically(beta, ">", 0.0, ABS_TOL_ANGLE)
        and compare_numerically(gamma, ">", 0.0, ABS_TOL_ANGLE)
        and compare_numerically(gamma, "<", alpha + beta, ABS_TOL_ANGLE)
        and compare_numerically(alpha + beta, "<", 360.0 - gamma, ABS_TOL_ANGLE)
        and compare_numerically(beta, "<", alpha + gamma, ABS_TOL_ANGLE)
        and compare_numerically(alpha + gamma, "<", 360.0 - beta, ABS_TOL_ANGLE)
        and compare_numerically(alpha, "<", beta + gamma, ABS_TOL_ANGLE)
        and compare_numerically(beta + gamma, "<", 360.0 - alpha, ABS_TOL_ANGLE)
    )

    if not result and raise_error:
        message = "Parameters could not form a parallelepiped:\n"
        message += f"a = {a}"
        if not compare_numerically(a, ">", 0.0, ABS_TOL):
            message += f" (a <= 0 with numerical tolerance: {ABS_TOL})"
        message += "\n"
        message += f"b = {b}"
        if not compare_numerically(b, ">", 0.0, ABS_TOL):
            message += f" (b <= 0 with numerical tolerance: {ABS_TOL})"
        message += "\n"
        message += f"c = {c}"
        if not compare_numerically(c, ">", 0.0, ABS_TOL):
            message += f" (c <= 0 with numerical tolerance: {ABS_TOL})"
        message += "\n"
        message += f"alpha = {alpha}\n"
        if not compare_numerically(alpha, "<", 180.0, ABS_TOL_ANGLE):
            message += f"  (alpha >= 180 with numerical tolerance: {ABS_TOL_ANGLE})\n"
        if not compare_numerically(alpha, ">", 0.0, ABS_TOL_ANGLE):
            message += f"  (alpha <= 0 with numerical tolerance: {ABS_TOL_ANGLE})\n"
        message += f"beta = {beta}\n"
        if not compare_numerically(beta, "<", 180.0, ABS_TOL_ANGLE):
            message += f"  (beta >= 180 with numerical tolerance: {ABS_TOL_ANGLE})\n"
        if not compare_numerically(beta, ">", 0.0, ABS_TOL_ANGLE):
            message += f"  (beta <= 0 with numerical tolerance: {ABS_TOL_ANGLE})\n"
        message += f"gamma = {gamma}\n"
        if not compare_numerically(gamma, "<", 180.0, ABS_TOL_ANGLE):
            message += f"  (gamma >= 180 with numerical tolerance: {ABS_TOL_ANGLE})\n"
        if not compare_numerically(gamma, ">", 0.0, ABS_TOL_ANGLE):
            message += f"  (gamma <= 0 with numerical tolerance: {ABS_TOL_ANGLE})\n"
        if not compare_numerically(gamma, "<", alpha + beta, ABS_TOL_ANGLE):
            message += f"Inequality gamma < alpha + beta is not satisfied with numerical tolerance: {ABS_TOL_ANGLE}\n"
        if not compare_numerically(alpha + beta, "<", 360.0 - gamma, ABS_TOL_ANGLE):
            message += f"Inequality alpha + beta < 360 - gamma is not satisfied with numerical tolerance: {ABS_TOL_ANGLE}\n"
        if not compare_numerically(beta, "<", alpha + gamma, ABS_TOL_ANGLE):
            message += f"Inequality beta < alpha + gamma is not satisfied with numerical tolerance: {ABS_TOL_ANGLE}\n"
        if not compare_numerically(alpha + gamma, "<", 360.0 - beta, ABS_TOL_ANGLE):
            message += f"Inequality alpha + gamma < 360 - beta is not satisfied with numerical tolerance: {ABS_TOL_ANGLE}\n"
        if not compare_numerically(alpha, "<", beta + gamma, ABS_TOL_ANGLE):
            message += f"Inequality alpha < beta + gamma is not satisfied with numerical tolerance: {ABS_TOL_ANGLE}\n"
        if not compare_numerically(beta + gamma, "<", 360.0 - alpha, ABS_TOL_ANGLE):
            message += f"Inequality beta + gamma < 360 - alpha is not satisfied with numerical tolerance: {ABS_TOL_ANGLE}\n"
        raise ValueError(message)

    return result