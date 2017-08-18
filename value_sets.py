from codesystems import CodeSystems


# Formats version based on major, minor, and patch values
def get_version(version_dict):
  major = version_dict.get('major', 0)
  minor = version_dict.get('minor', 0)
  patch = version_dict.get('patch', 0)
  return '{}.{}.{}'.format(major, minor, patch)


# Manages a single value within a value set
class Value:

  def __init__(self, value: dict):
    self.label = ''
    self.system = ''
    self.abbrev = ''
    self.code = ''
    self.display_text = ''
    self.run_handler(value)

  # Parsed the code dictionary for label, code, system, and abbreviation
  def parse_code_dict(self, code_dict: dict) -> None:
    self.label = code_dict.get('label', '')
    self.code = code_dict.get('code', '')
    self.system = code_dict.get('system', '')
    self.abbrev = CodeSystems.get(self.system)

  # Handles code type ValueSetIncludesFromCodeRule
  def handle_from_code_rule(self, value: dict) -> None:
    self.parse_code_dict(value.get('code', {}))
    text = 'Includes codes from {0}#{1} "{3}"'
    self.display_text = text.format(self.abbrev, self.code, 40, self.label)

  # Handles code type ValueSetIncludesCodeRule
  def handle_code_rule(self, value: dict) -> None:
    self.parse_code_dict(value.get('code', {}))
    length = 40 - len(self.abbrev) - 1
    text = '{0}#{1:<{2}}"{3}"'
    self.display_text = text.format(self.abbrev, self.code, length, self.label)

  # Handles code type ValueSetIncludesDescendentsRule
  def handle_descendents_rule(self, value: dict) -> None:
    self.parse_code_dict(value.get('code', {}))
    text = 'Includes codes descending from {0}#{1} "{2}"'
    self.display_text = text.format(self.abbrev, self.code, self.label)

  # Handles code type ValueSetIncludesFromCodeSystemRule
  def handle_from_code_system_rule(self, value: dict) -> None:
    self.label = value.get('label', '')
    self.system = value.get('system', '')
    self.abbrev = CodeSystems.get(self.system)
    self.display_text = "Includes codes from {0}".format(self.abbrev)

  # Identifies and runs the handler based on the type
  def run_handler(self, value: dict) -> None:
    type_handler = {
        'ValueSetIncludesFromCodeRule': self.handle_from_code_rule,
        'ValueSetIncludesCodeRule': self.handle_code_rule,
        'ValueSetIncludesDescendentsRule': self.handle_descendents_rule,
        'ValueSetIncludesFromCodeSystemRule': self.handle_from_code_system_rule
    }
    type_handler[value['type']](value)

  # Sets string representation to be display text
  def __str__(self):
    return self.display_text


# Manages all values for a given value set
class ValueSet:

  def __init__(self, value_set: dict):
    self.label = value_set.get('label', '')
    self.namespace = value_set.get('namespace', '')
    self.version = get_version(value_set.get('grammarVersion', {}))
    self.description = value_set.get('description', '')
    self.codesystems = dict()
    self.concepts = self.build_concepts(value_set.get('concepts', []))
    self.children = self.build_children(value_set.get('children', []))

  # Makes each child into a Value structure and aggregates codesystems
  def build_children(self, children: list) -> list:
    value_children = []
    for child in children:
      value = Value(child)
      value_children.append(value)
      if len(value.system) and len(value.abbrev):
        self.codesystems[value.system] = value.abbrev
    return value_children

  # Build a list of codesystems used in the child values
  def build_codesystems(self) -> list:
    systems = []
    text = '{0:20}{1} = {2}'
    for c in self.codesystems:
      abbrev = self.codesystems[c]
      if len(abbrev) > 0 and abbrev != 'TBD':
        systems.append(text.format('CodeSystem:', abbrev, c))
    return systems

  # Build a list of concepts
  def build_concepts(self, concepts: list) -> list:
    cs = []
    for concept in concepts:
      code = concept.get('code', '')
      system = concept.get('system', '')
      abbrev = CodeSystems.get(system)
      if len(system) and len(abbrev):
        self.codesystems[system] = abbrev
      cs.append('{0:{3}}{1}#{2}'.format('Concept:', abbrev, code, 40))
    return cs

  # Build description string
  def build_description(self) -> str:
    if len(self.description) == 0:
      return ''
    else:
      return '{0:{2}}{1}'.format('Description:', self.description, 40)

  # Return the string representation of a value set
  def __str__(self):
    header = '{0:{2}}{1}'.format('ValueSet:', self.label, 40)
    concepts = '\n'.join(self.concepts)
    description = self.build_description()
    values = '\n'.join(str(c) for c in self.children)
    output = [header, concepts, description, values]
    return '\n'.join(filter(None, output))


# Manages all valuesets for a given namespace
class ValueSetNamespace:

  def __init__(self, vs: ValueSet):
    self.namespace = vs.namespace
    self.version = vs.version
    self.value_sets = [str(vs)]
    self.code_system_set = set(vs.build_codesystems())

  # Add a valueset with the same namespace
  def add(self, vs: ValueSet) -> None:
    self.value_sets.append(str(vs))
    self.code_system_set.update(vs.build_codesystems())

  # Build the header
  def build_header(self) -> str:
    grammar = '{0:20}ValueSet {1}'.format('Grammar:', self.version)
    namespace = '{0:20}{1}'.format('Namespace:', self.namespace)
    return '\n'.join([grammar, namespace])

  # Build the code systems with abbreviations and urls
  def build_codesystems(self) -> str:
    return '\n'.join(self.code_system_set)

  # String representation of valuesets within a namespace
  def __str__(self):
    header = self.build_header()
    code_systems = self.build_codesystems()
    value_sets = '\n\n'.join(self.value_sets)
    output = [header, code_systems, value_sets]
    return '\n\n'.join(filter(None, output))


# Manages all namespace valuesets
class ValueSets:

  def __init__(self, value_sets: dict):
    self.value_sets = dict()
    self.parse_children(value_sets.get('children', []))
    for i in self.value_sets:
      name = i.replace('.', '_')
      with open('./out/%s_vs.txt' % name, 'w') as outfile:
        outfile.write(str(self.value_sets[i]))

  # Parses children and joins children with the same namespace
  def parse_children(self, children: list) -> None:
    for child in children:
      vs = ValueSet(child)
      if vs.namespace in self.value_sets:
        self.value_sets[vs.namespace].add(vs)
      else:
        self.value_sets[vs.namespace] = ValueSetNamespace(vs)
