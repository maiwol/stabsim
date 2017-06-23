import sys
import d5color
import correction as cor
import qcircuit_functions as qfun
import qcircuit_wrapper as qwrap
from visualizer import browser_vis as brow

#circ = qfun.create_EC_subcircs('d5color', False, True, False, False, 5)
d5_stabs = d5color.Code.stabilizer_alt[:]
d5_stab_oct = d5_stabs[8]
flags_oct = [[1,6], [2,7]]
flags_sq = [[1,3]]
flags_list = [flags_oct] + [flags_sq for i in range(7)]
n_flags = [len(flags) for flags in flags_list]

#circ = cor.Flag_Correct.generate_one_flagged_stab(17, d5_stab_oct, flags, True, True)
#circ = cor.Flag_Correct.generate_all_flagged_stabs(d5_stabs[:8], flags_list, True,
#                                                   False, 17)
QEC_circ = cor.Flag_Correct.generate_whole_QEC_circ(5, d5_stabs, flags_list+flags_list,
                                                True, False, 17)
#brow.from_circuit(QEC_circ.gates[0].circuit_list[0], True)
QEC_circ_list = []
for log_gate in QEC_circ.gates:
    QEC_circ_list += [log_gate.circuit_list[0]]

X_stabs, X_destabs = d5color.Code.stabilizer_CHP_X[:], d5color.Code.destabilizer_CHP_X[:]
Z_stabs, Z_destabs = qfun.change_operators(X_stabs), qfun.change_operators(X_destabs)
init_state = [Z_stabs, Z_destabs]
chp_loc = './chp_extended'
QEC_flags = qwrap.QEC_with_flags(init_state, QEC_circ_list[:], chp_loc)
out_dict = QEC_flags.run_one_roundCSS(0, 'bla', n_flags)
