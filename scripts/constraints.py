import re
from collections import defaultdict
from scripts.codesystems import CodeSystems


def parse_path(label, path_string):
  paths = [i.rpartition('.')[2] for i in path_string.split(':')]
  return '.'.join(filter(None, [label] + paths))


class Constraints:

  def __init__(self, constraints: list, label: str=''):
    self.constraints = constraints
    self.label = label
    self.codesystems = dict()
    self.uses = set()
    if constraints:
      self.c_type = constraints[0].get('type')

  def get_value_set(self) -> str:
    binding = self.constraints[0].get('bindingStrength', '')
    cp = self.constraints[0].get('path', '')
    valueset = self.constraints[0].get('valueset')
    if 'http://standardhealthrecord.org/shr/' in valueset:
      use = re.search(r'shr/(.*)/vs', valueset).group(1)
      self.uses.add('shr.{0}'.format(use))
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
    if system and abbrev and abbrev != 'TBD':
      self.codesystems[system] = abbrev
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
      if system and abbrev and abbrev != 'TBD':
        self.codesystems[system] = abbrev
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
      name = i.get('isA', {}).get('label')
      types.append(text.format(self.label, name))
    return ' or '.join(types)

  def get_card(self):
    cards = []
    i = 0
    while i < len(self.constraints):
      c0 = self.constraints[i]
      path = c0.get('path', '')
      label = parse_path(self.label, path)
      c_min = str(c0.get('min', 0))
      c_max = str(c0.get('max', '*'))
      range_vals = '{0}..{1}'.format(c_min, c_max)
      constraint_sub = ''
      if i + 1 < len(self.constraints):
        c1 = self.constraints[i + 1]
        if c1.get('type') != 'CardConstraint' and path == c1.get('path', ''):
          c1['path'] = ''
          constraint_sub = str(Constraints([c1], label))
          i += 1
      new_label = constraint_sub if constraint_sub else label
      cards.append('{0:20}{1}'.format(range_vals, new_label))
      i += 1
    return '\n'.join(cards)

  def get_includes_type(self):
    types_dict = defaultdict(list)
    for i in self.constraints:
      path = parse_path(self.label, i.get('path', ''))
      is_a = i.get('isA', {})
      c_min = str(i.get('min', 0))
      c_max = str(i.get('max', '*'))
      label = is_a.get('label', '')
      includes = 'includes {0}..{1}'.format(c_min, c_max)
      output = '{0:30}ref({1})'.format(includes, label)
      types_dict[path].append(output)
    paths = sorted(list(types_dict.keys()))
    return '\n'.join('\n'.join([i] + types_dict[i]) for i in paths)

  def __str__(self):
    type_handler = {
        'ValueSetConstraint': self.get_value_set,
        'CodeConstraint': self.get_code,
        'BooleanConstraint': self.get_boolean,
        'IncludesCodeConstraint': self.get_includes_code,
        'TypeConstraint': self.get_type,
        'CardConstraint': self.get_card,
        'IncludesTypeConstraint': self.get_includes_type
    }
    if not self.constraints:
      return ''
    elif self.c_type not in type_handler:
      print(self.c_type, 'MISSING')
      return ''
    return type_handler[self.c_type]()