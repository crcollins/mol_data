import os


methods = ["b3lyp", "cam", "m06hf"]
indo_methods = ["indo_" + x for x in ["default"] + methods]

OPTSETS = ["noopt"] + [os.path.join("opt", x) for x in methods]
STRUCTSETS = ['O', 'N', "rot", "4", "8"]
CALCSETS = methods + indo_methods
PROPS = ["homo", "lumo", "excitation"]


def input_check(prop=None, optsets=None, structsets=None, calcsets=None):
    if prop not in PROPS:
        return ValueError("Invalid property: %s" % prop)
    if not all(x in OPTSETS for x in optsets):
        return ValueError("Invalid optsets: %s" % (optsets, ))
    if not all(x in STRUCTSETS for x in structsets):
        return ValueError("Invalid structsets: %s" % (structsets, ))
    if not all(x in CALCSETS for x in calcsets):
        return ValueError("Invalid calcsets: %s" % (calcsets, ))
