from collections import defaultdict

from scripts.codesystems import CodeSystems


# Formats version based on major, minor, and patch values
def get_version(version_dict):
  major = version_dict.get('major', 0)
  minor = version_dict.get('minor', 0)
  patch = version_dict.get('patch', 0)
  # return '{}.{}.{}'.format(major, minor, patch)
  return '{}.{}'.format(major, minor)


# Parse Constraint for data elements and values
def get_constraint(constraints: list, label: str) -> str:
  if not constraints:
    return ''
  c_type = constraints[0].get('type')
  if c_type == 'ValueSetConstraint':
    binding = constraints[0].get('bindingStrength', '')
    ext = ' if covered' if binding == 'EXTENSIBLE' else ''
    pre = ' should be' if binding == 'PREFERRED' else ''
    valueset = constraints[0].get('valueset')
    if 'http://standardhealthrecord.org/shr/' in valueset:
      valueset = valueset.rpartition('/')[2]
    elif 'urn:tbd' in valueset:
      valueset = 'TBD "{0}"'.format(valueset.rpartition(':')[2])
    return '{0}{3} from {1}{2}'.format(label, valueset, ext, pre)
  elif c_type == 'CodeConstraint':
    code = constraints[0].get('code')
    system = code.get('system')
    abbrev = CodeSystems.get(system)
    display = code.get('display', '')
    text = '{0}#{1} "{2}"' if display else '{0}#{1}'
    source = text.format(abbrev, code.get('code'), display)
    conj = ' with units ' if label == 'Quantity' else ' is '
    return '{0}{1}{2}'.format(label, conj, source)
  elif c_type == 'BooleanConstraint':
    value = str(constraints[0].get('value')).lower()
    return '{0} is {1}'.format(label, value)
  elif c_type == 'IncludesCodeConstraint':
    includes = []
    for i in constraints:
      code = i.get('code')
      system = code.get('system')
      abbrev = CodeSystems.get(system)
      display = code.get('display', '')
      text = '{0}#{1} "{2}"' if display else '{0}#{1}'
      source = text.format(abbrev, code.get('code'), display)
      includes.append(source)
    return '{0} includes {1}'.format(label, ' includes '.join(includes))
  elif c_type == 'TypeConstraint':
    types = []
    for i in constraints:
      name = i.get('isA', {}).get('_name')
      types.append('{0} is type {1}'.format(label, name))
    return ' or '.join(types)
  # TODO Add functionality to card constraint when done
  elif c_type == 'CardConstraint':
    print('ADD CARDCONSTRAINT')
  else:
    print(c_type, 'MISSING')
    return 'NONE'


class IdentifiableValue:

  def __init__(self, value: dict, is_ref=False):
    self.is_ref = is_ref
    self.no_range = 'min' not in value and 'max' not in value
    self.min = str(value.get('min', 0))
    self.max = str(value.get('max', '*'))
    identifier = value.get('identifier', {})
    self.label = identifier.get('label', '')
    self.namespace = identifier.get('namespace', '')
    self.constraint = get_constraint(value.get('constraints', []), self.label)

  def __str__(self):
    text = '{0:20}ref({1})' if self.is_ref else '{0:20}{1}'
    if self.constraint:
      if self.no_range:
        return self.constraint.rjust(len(self.constraint) + 30)
      else:
        range_vals = '{0}..{1}'.format(self.min, self.max)
        return text.format(range_vals, self.constraint)
    else:
      range_vals = '{0}..{1}'.format(self.min, self.max)
      return text.format(range_vals, self.label)


class ChildTBD:

  def __init__(self, value: dict):
    self.text = value.get('text', '')
    self.no_range = 'min' not in value and 'max' not in value
    self.min = str(value.get('min', 0))
    self.max = str(value.get('max', '*'))

  def __str__(self):
    if self.no_range:
      return '{0:20}{1}'.format('', self.text)
    else:
      range_vals = '{0}..{1}'.format(self.min, self.max)
      return '{0:20}TBD "{1}"'.format(range_vals, self.text)


class ChoiceValue:

  def __init__(self, value: dict):
    self.no_range = 'min' not in value and 'max' not in value
    self.min = str(value.get('min', 0))
    self.max = str(value.get('max', '*'))
    self.elements = defaultdict(list)
    self.values = self.build_values(value.get('value', []))

  def build_values(self, vs: list) -> list:
    values = []
    for value in vs:
      label = value.get('identifier', {}).get('label', '')
      namespace = value.get('identifier', {}).get('namespace', '')
      v_type = value.get('type')
      if v_type == 'RefValue':
        values.append('ref({0})'.format(label))
        self.elements[namespace].append(label)
      elif v_type == 'TBD':
        values.append('TBD "{0}'.format(value.get('text', '')))
      else:
        self.elements[namespace].append(label)
        values.append(label)
    return values

  def __str__(self):
    values = ' or '.join(filter(None, self.values))
    if self.no_range:
      return '{0:20}{1}'.format('', values)
    else:
      range_vals = '{0}..{1}'.format(self.min, self.max)
      return '{0:20}{1}'.format(range_vals, values)


class DataElement:

  def __init__(self, data_element: dict, namespace: str):
    self.is_defined = False
    self.namespace = namespace
    self.label = data_element.get('label', '')
    self.codesystems = dict()
    self.uses = set()
    self.concepts = self.build_concepts(data_element.get('concepts', []))
    self.based_on = data_element.get('basedOn', [])
    self.description = data_element.get('description', '')
    self.is_entry = data_element.get('isEntry', False)
    self.is_abstract = data_element.get('isAbstract', False)
    self.value = self.build_value(data_element.get('value', {}))
    self.children = data_element.get('children', [])
    self.properties = []
    self.definitions = []

  # Update definitions on whether to define a data element
  def update_definitions(self, elements: dict, label: str) -> None:
    data_element = elements[label]
    if not data_element.is_defined:
      data_element.is_defined = True
      self.definitions.append(data_element.label)

  # Parse children for each sub element, pass in all data elements
  # MUST BE RUN BEFORE STR OF DATA ELEMENT IS USED
  def parse_children(self, elements: dict) -> None:
    for child in self.children:
      c_type = child.get('type')
      if c_type == 'IdentifiableValue':
        iv = IdentifiableValue(child)
        self.properties.append(str(iv))
        if iv.constraint:
          for c in child.get('constraints', []):
            if c.get('type', '') == 'TypeConstraint':
              name = c.get('isA', {}).get('_name', '')
              namespace = c.get('isA', {}).get('_namespace', '')
              if name and namespace == self.namespace:
                self.update_definitions(elements, name)
        if iv.namespace == self.namespace:
          self.update_definitions(elements, iv.label)
        else:
          self.uses.add(iv.namespace)
      elif c_type == 'TBD':
        tbd = ChildTBD(child)
        self.properties.append(str(tbd))
      elif c_type == 'ChoiceValue':
        cv = ChoiceValue(child)
        for namespace in cv.elements:
          if namespace == self.namespace:
            for label in cv.elements[namespace]:
              self.update_definitions(elements, label)
          else:
            self.uses.add(namespace)
        self.properties.append(str(cv))
      elif c_type == 'RefValue':
        ivr = IdentifiableValue(child, is_ref=True)
        self.properties.append(str(ivr))
        if ivr.namespace == self.namespace:
          self.update_definitions(elements, ivr.label)
        else:
          self.uses.add(ivr.namespace)
      # TODO Update when fixed
      elif c_type == 'Incomplete':
        print('INCOMPLETE', c_type, child.get('label', ''), self.namespace)
      else:
        print('STATUS', c_type, child.get('label'), self.namespace)

  # Build concept list
  def build_concepts(self, concepts: list) -> list:
    cs = []
    for concept in concepts:
      code = concept.get('code', '')
      system = concept.get('system', '')
      abbrev = CodeSystems.get(system)
      if len(system) and len(abbrev):
        self.codesystems[system] = abbrev
      cs.append('{0}#{1}'.format(abbrev, code))
    return '{0:20}{1}'.format('Concept:', ', '.join(cs) if cs else 'TBD')

  # Builds the children of a data element
  def build_definitions(self, elements: dict) -> str:
    all_definitions = []
    for label in self.definitions:
      data_element_str = elements[label].to_string(elements)
      lines = data_element_str.split('\n')
      definition = '\n'.join(l.rjust(len(l) + 10) for l in lines)
      all_definitions.append(definition)
    return '\n\n'.join(all_definitions)

  # Builds line for data elements based on others
  def build_based_on(self) -> str:
    values = []
    for i in self.based_on:
      values.append('{0:20}{1}'.format('Based on:', i.get('label', '')))
    return '\n'.join(values)

  def build_description(self) -> str:
    if self.description:
      return '{0:20}"{1}"'.format('Description:', self.description)
    return ''

  #  Builds value line
  def build_value(self, value: dict) -> str:
    label = value.get('identifier', {}).get('label', '')
    namespace = value.get('identifier', {}).get('namespace', '')
    if namespace:
      self.uses.add(namespace)
    constraint = get_constraint(value.get('constraints', []), label)
    if value.get('type') == 'ChoiceValue':
      vs = value.get('value', [])
      values = []
      for value in vs:
        identifier = value.get('identifier', {})
        label = value.get('identifier', {}).get('label', '')
        # Find dependencies in the value
        namespace = identifier.get('namespace', '')
        if namespace:
          self.uses.add(namespace)
        # Get display value for each child
        if value.get('type') == 'RefValue':
          values.append('ref({0})'.format(label))
        elif value.get('type') == 'TBD':
          values.append('TBD "{0}"'.format(value.get('text', '')))
        else:
          values.append(label)
      return '{0:20}{1}'.format('Value:', ' or '.join(filter(None, values)))
    elif label and not constraint:
      return '{0:20}{1}'.format('Value:', label)
    elif label and constraint:
      vs = value.get('constraints')[0].get('valueset', '')
      system = value.get('constraints')[0].get('code', {}).get('system', '')
      abbrev = CodeSystems.get(vs) if vs else CodeSystems.get(system)
      if abbrev and vs:
        self.codesystems[vs] = abbrev
      elif abbrev and system:
        self.codesystems[system] = abbrev
      return '{0:20}{1}'.format('Value:', constraint)
    return ''

  # Converts data element to string
  def to_string(self, elements: dict) -> str:
    title_text = 'EntryElement:' if self.is_entry else 'Element:'
    title = '{0:20}{1}'.format(title_text, self.label)
    concept = self.concepts
    based_on = self.build_based_on()
    description = self.build_description()
    # TODO finish value
    value = self.value
    properties = '\n'.join(self.properties)
    definitions = self.build_definitions(elements)
    output = [title, based_on, concept, description, value, properties]
    output_def = (filter(None, ['\n'.join(filter(None, output)), definitions]))
    return '\n\n'.join(output_def)


class Namespace:

  def __init__(self, namespace):
    self.label = namespace.get('label', '')
    self.description = namespace.get('description', '')
    self.version = get_version(namespace.get('grammarVersion', {}))
    self.uses = set()
    self.data_elements = dict()
    self.child_to_parent = defaultdict(list)
    self.populate_master_lists(namespace.get('children', []))
    self.base_elements = self.get_base_elements()

  #  Builds codesystems by looking through all the elements
  def build_codesystems(self) -> str:
    cs_dict = dict()
    for i in self.data_elements:
      cs_dict.update(self.data_elements[i].codesystems)
    output = []
    for i in cs_dict:
      output.append('{0:20}{1} = {2}'.format('CodeSystem:', cs_dict[i], i))
    return '\n'.join(output)

  # Generates the headers for the namespace
  def build_header(self) -> str:
    grammar = '{0:20}DataElement {1}'.format('Grammar:', self.version)
    namespace = '{0:20}{1}'.format('Namespace:', self.label)
    description = '{0:20}"{1}"'.format('Description:', self.description)
    uses = '{0:20}{1}'.format('Uses:', ', '.join(self.uses))
    output = [grammar, namespace, description, uses]
    return '\n'.join(filter(None, output))

  # Generates the data elements and returns a string
  def build_body(self) -> str:
    elems = []
    for i in self.base_elements:
      elems.append(self.data_elements[i].to_string(self.data_elements))
    return '\n\n\n'.join(elems)

  # Identifies all data elements and identifiable values
  def populate_master_lists(self, children: list, parent: str=None) -> None:
    for child in children:
      nested_children = []
      label = ''
      labels = []

      child_type = child.get('type', '')
      constraints = child.get('constraints', [])
      if child_type == 'DataElement':
        label = child.get('label', '')
        self.data_elements[label] = DataElement(child, self.label)
        nested_children = child.get('children', [])

        # TODO Figure out data elements within children
        # LOOK AT ENCOUNTER
        # child_value_type = child.get('value', {}).get('type', '')
        # cvn = child.get('value', {}).get('identifier', {}).get('namespace', '')
        # if child_value_type == 'IdentifiableValue' and cvn == self.label:
        #   print(child.get('value').get('label'))
        #   self.populate_master_lists([child.get('value', {})], label)
      elif child_type == 'IdentifiableValue':
        if len(constraints) and constraints[0].get('type') == 'TypeConstraint':
          for i in constraints:
            labels.append(i.get('isA', {}).get('_name', ''))
        else:
          label = child.get('identifier', {}).get('label', '')
      elif child_type == 'ChoiceValue':
        for c in child.get('value', []):
          labels.append(c.get('identifier', {}).get('label', ''))

      if labels and parent is not None:
        for label in (filter(None, labels)):
          self.child_to_parent[label].append(parent)
      if label and parent is not None:
        self.child_to_parent[label].append(parent)

      if label and nested_children:
        self.populate_master_lists(nested_children, label)

  # Returns base elements parses children for future use
  def get_base_elements(self) -> list:
    base_elems = []
    for i in self.data_elements:
      element = self.data_elements[i]
      if len(self.child_to_parent[element.label]) == 0:
        # Prevents elements from being defined in other data elements
        element.is_defined = True
        base_elems.append(element.label)
      # Prepares children so they aren't defined in multiple places
      element.parse_children(self.data_elements)
      self.uses.update(element.uses)
    return base_elems

  def __str__(self):
    header = self.build_header()
    codesystems = self.build_codesystems()
    body = self.build_body()
    return '\n\n'.join(filter(None, [header, codesystems, body]))


class Namespaces:

  def __init__(self, namespaces):
    self.label = namespaces.get('label', '')
    self.type = namespaces.get('type', '')
    self.namespaces = dict()
    self.parse_namespaces(namespaces.get('children', []))

  def parse_namespaces(self, namespaces: list) -> list:
    for name in namespaces:
      try:
        n = Namespace(name)
      except Exception as e:
        print('PARSE_ERROR', name['label'], e)
        continue
      self.namespaces[n.label] = n