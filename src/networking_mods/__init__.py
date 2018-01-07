
class Rule():
  def __init__(self):
    # Make check function when you inherent it
    self.fail_reason = None
  
  def check(self, user):
    return False

class Conjunction(Rule):
  '''
  Takes "Rule"'s and makes dynamic decisions by and/or operators.
  '''
  def __init__(self, operator, fail_reason=None, *rules):
    Rule.__init__(self)
    self.operator = operator
    self.fail_reason = fail_reason
    
    for x in rules:
      if not isinstance(x, Rule):
        raise ValueError('{} should be instances of Rule'.format(x))
    
    if not len(rules) > 1:
      raise ValueError('Needs 2 or more Rules.')
    
    self.rules = rules
    self.check = lambda user: eval(' {} '.format(self.operator).join(str(x.check(user)) for x in self.rules))

##
# Sugar
##


class Or_Conjunction(Conjunction):
  def __init__(self, fail_reason=None, *rules):
    Conjunction.__init__(self, 'or', fail_reason, *rules)


class And_Conjunction(Conjunction):
  def __init__(self, fail_reason=None, *rules):
    Conjunction.__init__(self, 'and', fail_reason, *rules)
 
