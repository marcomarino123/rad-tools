r"""
RAD-tools
"""

__version__ = "0.8.0"
__doclink__ = "rad-tools.org"
__git_hash__ = "d15ca7442fc1f016be199c47590a6502c47673ce"
__release_date__ = "21 August 2023"

from . import (
    constants,
    crystal,
    decorate,
    dos,
    exceptions,
    geometry,
    io,
    magnons,
    numerical,
    score,
    spinham,
)
from .constants import *
from .crystal import *
from .decorate import *
from .dos import *
from .geometry import *
from .io import *
from .magnons import *
from .numerical import *
from .score import *
from .spinham import *

__all__ = ["__version__", "__doclink__", "__git_hash__", "__release_date__"]
__all__.extend(crystal.__all__)
__all__.extend(decorate.__all__)
__all__.extend(dos.__all__)
__all__.extend(spinham.__all__)
__all__.extend(io.__all__)
__all__.extend(magnons.__all__)
__all__.extend(score.__all__)
__all__.extend(constants.__all__)
__all__.extend(geometry.__all__)
__all__.extend(numerical.__all__)
