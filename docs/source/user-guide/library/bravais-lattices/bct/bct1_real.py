import radtools as rad

l = rad.lattice_example("BCT1")
backend = rad.PlotlyBackend()
backend.plot(l, kind="primitive", label="primitive")
backend.plot(l, kind="conventional", label="conventional", color="black")
# Save an image:
backend.save("bct1_real.png")
# Interactive plot:
backend.show()
