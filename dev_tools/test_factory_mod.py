import sys
sys.path.append('../src')
import logic_interpreter

# Testing your logic.
print '\n'.join(logic_interpreter.LogicInterpreter().generate(
  "http://proxy-daily.com{/%Y/%m/%d-%m-%Y}-proxy-list-{range(0,5)}/"
))