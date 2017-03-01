import sys
import circuit as c
import chper_extended as chper
import chper_wrapper as wrapper
from visualizer import browser_vis as brow
import qcircuit_functions as qfun
import copy


init_stabs = ['+ZZIIII', '+IZZIII', '+XXXIII', '+IIIZII', '+IIIIZI', '+IIIIIZ']
init_destabs = ['+XIIIII', '+IIXIII', '+IZIIII', '+IIIXII', '+IIIIXI', '+IIIIIX']
init_state = (init_stabs, init_destabs)

circ1 = c.Circuit()
circ1.add_gate_at([4], 'H')
circ1.add_gate_at([4,5], 'CX')
circ1.add_gate_at([6], 'PrepareXPlus')
circ1.add_gate_at([6,1], 'CX')
circ1.add_gate_at([6,2], 'CX')
circ1.add_gate_at([6], 'MeasureX')
circ1.to_ancilla([6])

circ_chp1 = chper.Chper(circ1, 6, 1, init_stabs[:], init_destabs[:], [], [], 'None', False)

circ_chp_output1 = circ_chp1.run('./chp_extended')
#print circ_chp_output
dic1 = copy.deepcopy(circ_chp_output1[0])
stabs1 = copy.deepcopy(circ_chp_output1[1])
destabs1 = copy.deepcopy(circ_chp_output1[2])

print dic1
print stabs1
#print destabs1
#sys.exit(0)

#stabs1 = ['+XXXIII', '+IXXIII', '+IIIIXX', '+IZZIII', '+IIIZII', '+IIIIZZ']
#destabs1 = ['+ZIIIII', '+ZZIIII', '+IIIIZI', '+IIXIII', '+IIIXII', '+IIIIIX']

circ2 = c.Circuit()
circ2.add_gate_at([6], 'PrepareXPlus')
circ2.add_gate_at([6,3], 'CX')
circ2.add_gate_at([6,0], 'CX')
circ2.add_gate_at([6], 'MeasureX')
circ2.to_ancilla([6])

circ_chp2 = chper.Chper(circ2, 6, 1, stabs1[:], destabs1[:], [], [], 'None', False)

circ_chp_output2 = circ_chp2.run('./chp_extended')
dic2 = copy.deepcopy(circ_chp_output2[0])
stabs2 = copy.deepcopy(circ_chp_output2[1])
destabs2 = copy.deepcopy(circ_chp_output2[2])

print dic2
print stabs2
#print destabs2
