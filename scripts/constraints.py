from scripts.codesystems import CodeSystems


class Constraints:

  def __init__(self, constraints: list, label: str):
    self.constraints = constraints
    self.label = label
    if constraints:
      self.c_type = constraints[0].get('type')

  def get_value_set(self) -> str:
    binding = self.constraints[0].get('bindingStrength', '')
    cp = self.constraints[0].get('path', '')
    valueset = self.constraints[0].get('valueset')
    if 'http://standardhealthrecord.org/shr/' in valueset:
      valueset = valueset.rpartition('/')[2]
    elif 'urn:tbd' in valueset:
      valueset = 'TBD "{0}"'.format(valueset.rpartition(':')[2])

    path = ' {0}.{1}'.format(self.label, cp.rpartition('.')[2]) if cp else ''

    if binding == 'EXTENSIBLE':
      return '{0}{2} from {1} if covered'.format(self.label, valueset, path)
    elif binding == 'PREFERRED':
      return '{0}{2} should be from {1}'.format(self.label, valueset, path)
    elif binding == 'EXAMPLE':
      return '{0}{2} could be from {1}'.format(self.label, valueset, path)
    else:
      return '{0}{2} from {1}'.format(self.label, valueset, path)

  def get_code(self):
    code = self.constraints[0].get('code')
    system = code.get('system')
    abbrev = CodeSystems.get(system)
    display = code.get('display', '')
    text = '{0}#{1} "{2}"' if display else '{0}#{1}'
    source = text.format(abbrev, code.get('code'), display)
    conj = ' with units ' if self.label == 'Quantity' else ' is '
    return '{0}{1}{2}'.format(self.label, conj, source)

  def get_boolean(self):
    value = str(self.constraints[0].get('value')).lower()
    return '{0} is {1}'.format(self.label, value)

  def get_includes_code(self):
    includes = []
    for i in self.constraints:
      code = i.get('code')
      system = code.get('system')
      abbrev = CodeSystems.get(system)
      display = code.get('display', '')
      text = '{0}#{1} "{2}"' if display else '{0}#{1}'
      source = text.format(abbrev, code.get('code'), display)
      includes.append(source)
    return '{0} includes {1}'.format(self.label, ' includes '.join(includes))

  def get_type(self):
    types = []
    for i in self.constraints:
      isVal = i.get('onValue', False)
      text = '{0} value is type {1}' if isVal else '{0} is type {1}'
      name = i.get('isA', {}).get('_name')
      types.append(text.format(self.label, name))
    return ' or '.join(types)

  def get_card(self):
    print('ADD CARDCONSTRAINT')
    return ''

  def __str__(self):
    type_handler = {
        'ValueSetConstraint': self.get_value_set,
        'CodeConstraint': self.get_code,
        'BooleanConstraint': self.get_boolean,
        'IncludesCodeConstraint': self.get_includes_code,
        'TypeConstraint': self.get_type,
        'CardConstraint': self.get_card,
    }
    if not self.constraints:
      return ''
    elif self.c_type not in type_handler:
      print(self.c_type, 'MISSING')
      return ''
    return type_handler[self.c_type]()