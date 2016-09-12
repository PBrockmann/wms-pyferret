import pyferret
import pyferretWMS

def ferret_init(id):
    '''Slippy map'''
    initdict = { "numargs": 1,
                 "descript": "Command to create slippy map",
		 "argnames": ("cmd",),
		 "argtypes": (pyferret.STRING_ONEVAL,) }
    return initdict

def ferret_compute(id, result, result_bad_flag, inputs, input_bad_flags):
    cmd = inputs[0]
    print cmd
    pyferretWMS.slippyMap(cmd)
