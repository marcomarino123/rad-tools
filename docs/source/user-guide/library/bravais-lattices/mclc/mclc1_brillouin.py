import radtools as rad

l = rad.lattice_example("MCLC1")
backend = rad.PlotlyBackend()
backend.plot(l, kind="brillouin-kpath")
# Save an image:
backend.save("mclc1_brillouin.png")
# Interactive plot:
backend.show()
