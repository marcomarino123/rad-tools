import radtools as rad

l = rad.lattice_example("RHL2")
backend = rad.PlotlyBackend()
backend.plot(l, kind="wigner-seitz")
# Save an image:
backend.save("rhl2_wigner-seitz.png")
# Interactive plot:
backend.show()
