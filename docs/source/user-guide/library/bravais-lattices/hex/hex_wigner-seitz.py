import radtools as rad

l = rad.lattice_example("HEX")
backend = rad.PlotlyBackend()
backend.plot(l, kind="wigner-seitz")
# Save an image:
backend.save("hex_wigner-seitz.png")
# Interactive plot:
backend.show()
