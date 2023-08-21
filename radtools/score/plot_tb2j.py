from argparse import ArgumentParser
from math import asin, pi, sqrt
import os

import numpy as np
from matplotlib import pyplot as plt
from termcolor import cprint

from radtools.constants import TODEGREES
from radtools.io.internal import read_template
from radtools.io.tb2j import read_tb2j_model


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
            return asin(sin) * TODEGREES
        elif y == 0:
            return 0
        elif y < 0:
            if not dummy:
                return -asin(sin) * TODEGREES
            return 360 - asin(sin) * TODEGREES
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
                return -asin(sin) * TODEGREES
            return 180 - asin(sin) * TODEGREES
        elif y == 0:
            if not dummy:
                return 0
            return 180
        elif y < 0:
            if not dummy:
                return asin(sin) * TODEGREES
            return 180 + asin(sin) * TODEGREES


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


def manager(
    input_filename,
    output_name="exchange",
    what_to_plot="iso",
    draw_cells=False,
    min_distance=None,
    max_distance=None,
    distance=None,
    template_file=None,
    R_vector=None,
    scale_atoms=1,
    scale_data=1,
    title=None,
    form_model=False,
    verbose=False,
):
    r"""
    :ref:`rad-plot-tb2j` script.

    Full documentation on the behaviour is available in the
    :ref:`User Guide <rad-plot-tb2j>`.
    Parameters of the function directly
    correspond to the arguments of the script.
    """

    head, _ = os.path.split(input_filename)
    out_head, out_tail = os.path.split(output_name)
    if len(out_head) == 0:
        out_head = head
    if len(out_tail) == 0:
        out_tail = "exchange"

    output_name = os.path.join(out_head, out_tail)

    # Create the output directory if it does not exist
    if out_head != "":
        os.makedirs(out_head, exist_ok=True)

    # Check input parameters for consistency
    if form_model and template_file is None:
        raise ValueError("--form-model option requires a template file.")

    if distance is not None:
        min_distance = distance
        max_distance = distance

    # Translate sequence of numbers to R vectors
    if R_vector is not None:
        R_vector = np.array(R_vector[: len(R_vector) // 3 * 3], dtype=int).reshape(
            (len(R_vector) // 3, 3)
        )
        R_vector = list(map(tuple, R_vector.tolist()))

    # Read the model
    model = read_tb2j_model(input_filename, quiet=not verbose)

    # Force symmetry of the template
    if template_file is not None:
        template = read_template(template_file)
    else:
        template = None
    if form_model:
        model.form_model(template=template)

    # Filter the model
    model.filter(
        min_distance=min_distance,
        max_distance=max_distance,
        R_vector=R_vector,
        template=template,
    )

    dummy = True
    ha = "center"
    x_min, y_min, z_min, x_max, y_max, z_max = model.space_dimensions
    X = max(abs(x_min), abs(x_max))
    Y = max(abs(y_min), abs(y_max))
    if X == 0 and Y == 0:
        X = Y = 1
    linewidth = 1
    fontsize = 11
    if what_to_plot == "all":
        wtps = ["iso", "distance", "dmi"]
    else:
        wtps = [what_to_plot]
    for wtp in wtps:
        if X < Y:
            fig = plt.figure(figsize=(6.4 * X / Y, 4.8))
        else:
            fig = plt.figure(figsize=(6.4, 4.8 * Y / X))
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
        ax.set_aspect("equal")
        ax.set_xlabel("x, Angstroms")
        ax.set_ylabel("y, Angstroms")

        for atom1, atom2, R, J in model:
            dis = model.get_distance(atom1, atom2, R)
            x1, y1, z1 = model.get_atom_coordinates(atom1, relative=False)
            x2, y2, z2 = model.get_atom_coordinates(atom2, R, relative=False)
            xm = (x1 + x2) / 2
            ym = (y1 + y2) / 2
            zm = (z1 + z2) / 2

            ax.scatter(x1, y1, s=100 * fig.dpi / 72.0, c="white")
            ax.scatter(x2, y2, s=100 * fig.dpi / 72.0, c="white")

            ax.text(
                x2,
                y2,
                atom_mark_to_latex(atom2.name),
                va="center",
                ha="center",
                fontsize=1.5 * fontsize * scale_atoms,
            )
            ax.text(
                x1,
                y1,
                atom_mark_to_latex(atom1.name),
                va="center",
                ha="center",
                fontsize=1.5 * fontsize * scale_atoms,
                color="#A04F4D",
            )
            if wtp == "iso":
                ax.text(
                    xm,
                    ym,
                    str(round(J.iso, 4)),
                    va="bottom",
                    ha=ha,
                    rotation_mode="anchor",
                    rotation=rot_angle(x2 - x1, y2 - y1, dummy=dummy),
                    fontsize=fontsize * scale_data,
                )
            elif wtp == "distance":
                ax.text(
                    xm,
                    ym,
                    str(round(dis, 4)),
                    va="bottom",
                    ha=ha,
                    rotation_mode="anchor",
                    rotation=rot_angle(x2 - x1, y2 - y1, dummy=dummy),
                    fontsize=fontsize * scale_data,
                )
            elif wtp == "dmi":
                ax.text(
                    xm,
                    ym,
                    str(round(sqrt(np.sum(J.dmi**2)), 4)),
                    va="bottom",
                    ha=ha,
                    rotation_mode="anchor",
                    rotation=rot_angle(x2 - x1, y2 - y1, dummy=dummy),
                    fontsize=fontsize * scale_data,
                )

        xlims = (ax.get_xlim()[0] - 0.5, ax.get_xlim()[1] + 0.5)
        ylims = (ax.get_ylim()[0] - 0.5, ax.get_ylim()[1] + 0.5)

        if draw_cells:
            cells = model.cell_list
            a_x, a_y, a_z = tuple(model.cell[0])
            b_x, b_y, b_z = tuple(model.cell[1])
            Rx_min = 0
            Rx_max = 0
            Ry_min = 0
            Ry_max = 0
            Rz_min = 0
            Rz_max = 0
            for Rx, Ry, Rz in cells:
                Rx_min = min(Rx, Rx_min)
                Rx_max = max(Rx, Rx_max)
                Ry_min = min(Ry, Ry_min)
                Ry_max = max(Ry, Ry_max)
                Rz_min = min(Rz, Rz_min)
                Rz_max = max(Rz, Rz_max)

            for i in range(Rx_min, Rx_max + 2):
                for j in range(Ry_min, Ry_max + 2):
                    for k in range(Rz_min, Rz_max + 2):
                        ax.plot(
                            [Rx_min * a_x + j * b_x, (Rx_max + 1) * a_x + j * b_x],
                            [Rx_min * a_y + j * b_y, (Rx_max + 1) * a_y + j * b_y],
                            linewidth=linewidth,
                            color="#DFDFDF",
                        )
                        ax.plot(
                            [i * a_x + Ry_min * b_x, i * a_x + (Ry_max + 1) * b_x],
                            [i * a_y + Ry_min * b_y, i * a_y + (Ry_max + 1) * b_y],
                            linewidth=linewidth,
                            color="#DFDFDF",
                        )
            ax.plot(
                np.array([0, a_x, a_x + b_x, b_x, 0]),
                np.array([0, a_y, a_y + b_y, b_y, 0]),
                linewidth=linewidth,
                color="#CA7371",
            )

        ax.set_xlim(*xlims)
        ax.set_ylim(*ylims)

        if title is not None:
            ax.set_title(title, fontsize=1.5 * fontsize)

        png_path = f"{output_name}.{wtp}.png"
        plt.savefig(png_path, dpi=400, bbox_inches="tight")
        cprint(f"2D plot with {wtp} is in {os.path.abspath(png_path)}", "blue")


def create_parser():
    parser = ArgumentParser(description="Script for visualization of TB2J results")

    parser.add_argument(
        "-if",
        "--input-filename",
        metavar="filename",
        type=str,
        required=True,
        help="Relative or absolute path to the 'exchange.out' file,"
        + "including the name and extension of the file itself.",
    )
    parser.add_argument(
        "-on",
        "--output-name",
        metavar="filename",
        type=str,
        default="exchange",
        help="Seedname for the output files.",
    )
    parser.add_argument(
        "-wtp",
        "--what-to-plot",
        metavar="value",
        type=str,
        choices=["all", "iso", "distance", "dmi"],
        default="all",
        help="Type of data for display.",
    )
    parser.add_argument(
        "-dc",
        "--draw-cells",
        action="store_true",
        default=False,
        help="Whether to draw the cells.",
    )
    parser.add_argument(
        "-R",
        "--R-vector",
        metavar="R1a R1b R1c",
        type=int,
        nargs="*",
        default=None,
        help="R vectors for filtering the model.",
    )
    parser.add_argument(
        "-maxd",
        "--max-distance",
        metavar="distance",
        type=float,
        default=None,
        help="(<=) Maximum distance.",
    )
    parser.add_argument(
        "-mind",
        "--min-distance",
        metavar="distance",
        type=float,
        default=None,
        help="(>=) Minimum distance.",
    )
    parser.add_argument(
        "-d",
        "--distance",
        metavar="distance",
        type=float,
        default=None,
        help="(=) Exact distance.",
    )
    parser.add_argument(
        "-tf",
        "--template-file",
        metavar="filename",
        type=str,
        default=None,
        help="Relative or absolute path to the template file, "
        + "including the name and extension of the file.",
    )
    parser.add_argument(
        "-sa",
        "--scale-atoms",
        metavar="factor",
        default=1,
        type=float,
        help="Scale for the size of atom marks.",
    )
    parser.add_argument(
        "-sd",
        "--scale-data",
        metavar="factor",
        default=1,
        type=float,
        help="Scale for the size of data text.",
    )
    parser.add_argument(
        "-t",
        "--title",
        metavar="title",
        default=None,
        type=str,
        help="Title for the plots.",
    )
    parser.add_argument(
        "-fm",
        "--form-model",
        default=False,
        action="store_true",
        help="Force the Exchange model to have the symmetry of the template.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Verbose output, propagates to the called methods.",
    )

    return parser
