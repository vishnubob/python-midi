import midi
import pprint
x = midi.FileReader()
p = midi.read('a.mid')
print(p)
input()
midi.write('aa.mid', p)
p = midi.read('aa.mid')
print(p)
input()
#midi.write('aaa.mid', p)
#p = midi.read('aaa.mid')

