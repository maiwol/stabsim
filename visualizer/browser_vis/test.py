import circuit
c = circuit.Circuit()
c.load_from_file('default.txt')

for m in c.read():
	print ''
	for q in m:
		print q

import main
