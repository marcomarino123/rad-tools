from math import cos, pi, sin

from radtools.crystal.lattice import Lattice
from radtools.routines import toradians
from radtools.crystal.constants import BRAVAIS_LATTICE_VARIATIONS

from radtools.crystal.bravais_lattice.constructor import (
    CUB,
    FCC,
    BCC,
    TET,
    BCT,
    ORC,
    ORCF,
    ORCI,
    ORCC,
    HEX,
    RHL,
    MCL,
    MCLC,
    TRI,
)

__all__ = [
    "lattice_example",
]


def lattice_example(
    lattice_name: str = None,
):
    r"""
    Return an example of the lattice.

    Parameters
    ----------
    lattice_name : str, optional
        Name of the lattice to be returned.
        For available names see documentation of each Bravais lattice class.
        Lowercased before usage.

    Returns
    -------
    lattice : Lattice or list
        :py:class:`.Lattice` class is returned.
        If no math found a list with available examples is returned.
    """

    if (
        not isinstance(lattice_name, str)
        or lattice_name not in BRAVAIS_LATTICE_VARIATIONS
    ):
        message = (
            f"There is no {lattice_name} Bravais lattice. Available examples are:\n"
        )
        for name in BRAVAIS_LATTICE_VARIATIONS:
            message += f"  * {name}\n"
        raise ValueError(message)

    lattice_name = lattice_name.lower()

    if lattice_name == "cub":
        return CUB(pi)
    elif lattice_name == "fcc":
        return FCC(pi)
    elif lattice_name == "bcc":
        return BCC(pi)
    elif lattice_name == "tet":
        return TET(pi, 1.5 * pi)
    elif lattice_name in ["bct1", "bct"]:
        return BCT(1.5 * pi, pi)
    elif lattice_name == "bct2":
        return BCT(pi, 1.5 * pi)
    elif lattice_name == "orc":
        return ORC(pi, 1.5 * pi, 2 * pi)
    elif lattice_name in ["orcf1", "orcf"]:
        return ORCF(0.7 * pi, 5 / 4 * pi, 5 / 3 * pi)
    elif lattice_name == "orcf2":
        return ORCF(1.2 * pi, 5 / 4 * pi, 5 / 3 * pi)
    elif lattice_name == "orcf3":
        return ORCF(pi, 5 / 4 * pi, 5 / 3 * pi)
    elif lattice_name == "orci":
        return ORCI(pi, 1.3 * pi, 1.7 * pi)
    elif lattice_name == "orcc":
        return ORCC(pi, 1.3 * pi, 1.7 * pi)
    elif lattice_name == "hex":
        return HEX(pi, 2 * pi)
    elif lattice_name in ["rhl1", "rhl"]:
        # If alpha = 60 it is effectively FCC!
        return RHL(pi, 70)
    elif lattice_name == "rhl2":
        return RHL(pi, 110)
    elif lattice_name == "mcl":
        return MCL(pi, 1.3 * pi, 1.6 * pi, alpha=75)
    elif lattice_name in ["mclc1", "mclc"]:
        return MCLC(pi, 1.4 * pi, 1.7 * pi, 80)
    elif lattice_name == "mclc2":
        return MCLC(1.4 * pi * sin(75 * toradians), 1.4 * pi, 1.7 * pi, 75)
    elif lattice_name == "mclc3":
        b = pi
        x = 1.1
        alpha = 78
        ralpha = alpha * toradians
        c = b * (x**2) / (x**2 - 1) * cos(ralpha) * 1.8
        a = x * b * sin(ralpha)
        return MCLC(a, b, c, alpha)
    elif lattice_name == "mclc4":
        b = pi
        x = 1.2
        alpha = 65
        ralpha = alpha * toradians
        c = b * (x**2) / (x**2 - 1) * cos(ralpha)
        a = x * b * sin(ralpha)
        return MCLC(a, b, c, alpha)
    elif lattice_name == "mclc5":
        b = pi
        x = 1.4
        alpha = 53
        ralpha = alpha * toradians
        c = b * (x**2) / (x**2 - 1) * cos(ralpha) * 0.9
        a = x * b * sin(ralpha)
        return MCLC(a, b, c, alpha)
    elif lattice_name in ["tri1a", "tri1", "tri", "tria"]:
        return TRI(1, 1.5, 2, 120, 110, 100, reciprocal=True)
    elif lattice_name in ["tri2a", "tri2"]:
        return TRI(1, 1.5, 2, 120, 110, 90, reciprocal=True)
    elif lattice_name in ["tri1b", "trib"]:
        return TRI(1, 1.5, 2, 60, 70, 80, reciprocal=True)
    elif lattice_name == "tri2b":
        return TRI(1, 1.5, 2, 60, 70, 90, reciprocal=True)
