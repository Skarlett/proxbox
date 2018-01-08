
class Rule():
  def __init__(self):
    # Make check function when you inherent it
    self.fail_reason = None
    self.log_hook_true= None
    self.log_hook_false= None
  
  def _check(self, user):
    return False
  
  def check(self, user):
    if self._check(user):
      self.log_hook_true() if self.log_hook_true else None
      return True
    else:
      self.log_hook_false() if self.log_hook_false else None
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
    self._check = lambda user: eval(' {} '.format(self.operator).join(str(x.check(user)) for x in self.rules))

##
# Sugar
##


class Or_Conjunction(Conjunction):
  def __init__(self, fail_reason=None, *rules):
    Conjunction.__init__(self, 'or', fail_reason, *rules)


class And_Conjunction(Conjunction):
  def __init__(self, fail_reason=None, *rules):
    Conjunction.__init__(self, 'and', fail_reason, *rules)
 
