#! /usr/local/bin/python3
from argparse import ArgumentParser
from os.path import join
from os import makedirs
from math import sqrt

import numpy as np

from rad_tools.tb2j_tools.file_logic import ExchangeModelTB2J
from rad_tools.tb2j_tools.template_logic import ExchangeTemplate
from rad_tools.routines import  OK, RESET


def main(filename, out_dir, out_name, template):

    model = ExchangeModelTB2J(filename)
    template = ExchangeTemplate(template)
    with open(join(out_dir, out_name), "w") as out_file:
        for name in template.names:
            J_iso = 0
            J_aniso = np.zeros((3, 3), dtype=float)
            DMI = np.zeros(3, dtype=float)
            abs_DMI = 0
            for bond in template.names[name]:
                atom1 = bond[0]
                atom2 = bond[1]
                R = bond[2]
                J_iso += model.bonds[atom1][atom2][R].iso
                J_aniso += model.bonds[atom1][atom2][R].aniso
                DMI += model.bonds[atom1][atom2][R].dmi
                abs_DMI += sqrt(model.bonds[atom1][atom2][R].dmi[0]**2 +
                                model.bonds[atom1][atom2][R].dmi[1]**2 +
                                model.bonds[atom1][atom2][R].dmi[2]**2)
            J_iso /= len(template.names[name])
            J_aniso /= len(template.names[name])
            DMI /= len(template.names[name])
            abs_DMI /= len(template.names[name])
            out_file.write(f"""
{name}
    Isotropic: {round(J_iso, 4)}
    Anisotropic: 
    {J_aniso}
    DMI: {round(DMI[0], 4)} {round(DMI[1], 4)} {round(DMI[2], 4)}
    |DMI|: {round(abs_DMI, 4)}
    |DMI/J| {round(abs(abs_DMI/J_iso), 4)}

""")


if __name__ == '__main__':
    parser = ArgumentParser(description="Script for refractoring of TB2J results",
                            epilog="""
                            See the docs: 
                            https://rad-tools.adrybakov.com/en/latest/user_guide/tb2j_refractor.html
                            """)

    parser.add_argument("-f", "--file",
                        type=str,
                        required=True,
                        help="""
                        Relative or absulute path to the *exchange.out* file,
                        including the name and extention of the file itself.
                        """
                        )
    parser.add_argument("-op", "--output-dir",
                        type=str,
                        default='.',
                        help="""
                        Relative or absolute path to the folder for saving outputs.

    If the folder does not exist then it is created from the specified path.
    The creation is applied recursevly to the path, starting from the right
    until the existing folder is reached.
                        """
                        )
    parser.add_argument("-on", "--output-name",
                        type=str,
                        default='exchange_refr',
                        help="""
                        Seedname for the output files.

    Output files will have the following name structure:
    output-name
                        """
                        )
    parser.add_argument("-t", "--template",
                        type=str,
                        default=None,
                        help="""
                        Relative or absolute path to the template file, 
                        including the name and extention of the file.
                        """)

    args = parser.parse_args()

    makedirs(args.output_dir)

    main(filename=args.file,
         out_dir=args.output_dir,
         out_name=args.output_name,
         template=args.template)