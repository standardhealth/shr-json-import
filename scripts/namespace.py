from collections import defaultdict

from scripts.codesystems import CodeSystems
from scripts.constraints import Constraints


# Formats version based on major, minor, and patch values
def get_version(version_dict):
  major = version_dict.get('major', 0)
  minor = version_dict.get('minor', 0)
  patch = version_dict.get('patch', 0)
  # return '{}.{}.{}'.format(major, minor, patch)
  return '{}.{}'.format(major, minor)


class IdentifiableValue:

  def __init__(self, value: dict, is_ref=False):
    self.is_ref = is_ref
    self.no_range = 'min' not in value and 'max' not in value
    self.min = str(value.get('min', 0))
    self.max = str(value.get('max', '*'))
    identifier = value.get('identifier', {})
    self.label = identifier.get('label', '')
    self.namespace = identifier.get('namespace', '')
    constraint = Constraints(value.get('constraints', []), self.label)
    self.constraint = str(constraint)
    self.codesystems = constraint.codesystems
    self.uses = constraint.uses

  def to_string_value(self) -> str:
    if not self.label:
      return ''
    if self.min == '1' and self.max == '1':
      range_vals = ''
    else:
      range_vals = '{0}..{1} '.format(self.min, self.max)
    text = '{0:20}{2}ref({1})' if self.is_ref else '{0:20}{2}{1}'
    if self.constraint:
      return text.format('Value:', self.constraint, range_vals)
    else:
      return text.format('Value:', self.label, range_vals)

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
    self.codesystems = dict()
    self.uses = set()

  def to_string_value(self) -> str:
    if self.text:
      return '{0:20}TBD "{1}"'.format('Value:', self.text)
    return ''

  def __str__(self):
    if self.no_range:
      return '{0:20}{1}'.format('', self.text)
    else:
      range_vals = '{0}..{1}'.format(self.min, self.max)
      return '{0:20}TBD "{1}"'.format(range_vals, self.text)


class Incomplete:

  def __init__(self, value: dict):
    self.text = value.get('text', '')
    self.raw_paths = value.get('rawPath', [])
    self.constraints = value.get('constraints', [])
    constraint = Constraints(self.constraints, raw_paths=self.raw_paths)
    self.labels = str(constraint)
    self.codesystems = constraint.codesystems
    self.uses = constraint.uses

  def item_to_string(self, card: dict, label: str) -> str:
    no_range = 'min' not in card and 'max' not in card
    c_min = str(card.get('min', 0))
    c_max = str(card.get('max', '*'))
    if no_range:
      return '{0:20}{1}'.format('', label)
    else:
      range_vals = '{0}..{1}'.format(c_min, c_max)
      return '{0:20}{1}'.format(range_vals, label)

  def __str__(self):
    items = []
    labels = self.labels.split('\n')
    for i, c in enumerate(self.constraints):
      items.append(self.item_to_string(c, labels[i]))
    return '\n'.join(items)


class ChoiceValue:

  def __init__(self, value: dict):
    self.no_range = 'min' not in value and 'max' not in value
    self.min = str(value.get('min', 0))
    self.max = str(value.get('max', '*'))
    self.elements = defaultdict(list)
    self.namespaces = set()
    self.codesystems = dict()
    self.uses = set()
    self.values = self.build_values(value.get('value', []))

  def build_values(self, vs: list) -> list:
    values = []
    for value in vs:
      label = value.get('identifier', {}).get('label', '')
      namespace = value.get('identifier', {}).get('namespace', '')
      if namespace:
        self.namespaces.add(namespace)
      v_type = value.get('type')
      c = Constraints(value.get('constraints', []), label)
      constraint = str(c)
      self.codesystems.update(c.codesystems)
      self.uses.update(c.uses)
      if constraint:
        values.append(constraint)
      elif v_type == 'RefValue':
        values.append('ref({0})'.format(label))
        self.elements[namespace].append(label)
      elif v_type == 'TBD':
        values.append('TBD "{0}"'.format(value.get('text', '')))
      else:
        self.elements[namespace].append(label)
        values.append(label)
    return values

  def to_string_value(self):
    values = ' or '.join(filter(None, self.values))
    if not values:
      return ''
    elif not self.no_range:
      vals = '{0}..{1} ({2})'.format(self.min, self.max, values)
    return '{0:20}{1}'.format('Value:', vals), self.namespaces

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
    self.based_on = self.build_based_on(data_element.get('basedOn', []))
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
        new_child = IdentifiableValue(child)
        self.properties.append(str(new_child))
        if new_child.constraint:
          for c in child.get('constraints', []):
            if c.get('type', '') == 'TypeConstraint':
              name = c.get('isA', {}).get('_name', '')
              namespace = c.get('isA', {}).get('_namespace', '')
              if name and namespace == self.namespace:
                self.update_definitions(elements, name)
        if new_child.namespace == self.namespace:
          self.update_definitions(elements, new_child.label)
        else:
          self.uses.add(new_child.namespace)
      elif c_type == 'TBD':
        new_child = ChildTBD(child)
        self.properties.append(str(new_child))
      elif c_type == 'ChoiceValue':
        new_child = ChoiceValue(child)
        for namespace in new_child.elements:
          if namespace == self.namespace:
            for label in new_child.elements[namespace]:
              self.update_definitions(elements, label)
          else:
            self.uses.add(namespace)
        self.properties.append(str(new_child))
      elif c_type == 'RefValue':
        new_child = IdentifiableValue(child, is_ref=True)
        self.properties.append(str(new_child))
        if new_child.namespace == self.namespace:
          self.update_definitions(elements, new_child.label)
        else:
          self.uses.add(new_child.namespace)
      # TODO Update when fixed
      elif c_type == 'Incomplete':
        new_child = Incomplete(child)
        self.properties.append(str(new_child))
      else:
        print('STATUS', c_type, child.get('label'), self.namespace)
      self.codesystems.update(new_child.codesystems)
      self.uses.update(new_child.uses)

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
  def build_based_on(self, based_on: list) -> str:
    values = []
    for i in based_on:
      text = '{0:20}TBD "{1}"' if i.get('type') == 'TBD' else '{0:20}{1}'
      values.append(text.format('Based on:', i.get('label', '')))
      namespace = i.get('namespace', '')
      if namespace and namespace != self.namespace:
        self.uses.add(namespace)
    return '\n'.join(values)

  def build_description(self) -> str:
    if self.description:
      return '{0:20}"{1}"'.format('Description:', self.description)
    return ''

  #  Builds value line
  def build_value(self, value: dict) -> str:
    if not value:
      return ''
    label = value.get('identifier', {}).get('label', '')
    namespace = value.get('identifier', {}).get('namespace', '')
    if namespace:
      self.uses.add(namespace)
    constraint = Constraints(value.get('constraints', []), label)
    constraint_string = str(constraint)
    self.codesystems.update(constraint.codesystems)
    self.uses.update(constraint.uses)
    v_type = value.get('type')
    if v_type == 'ChoiceValue':
      cv = ChoiceValue(value)
      output, namespaces = cv.to_string_value()
      for i in namespaces:
        self.uses.add(i)
      return output
    elif v_type == 'IdentifiableValue':
      return IdentifiableValue(value).to_string_value()
    elif v_type == 'RefValue':
      return IdentifiableValue(value, is_ref=True).to_string_value()
    elif v_type == 'TBD':
      return ChildTBD(value).to_string_value()
    else:
      if constraint:
        return '{0:20}{1}'.format('Value:', constraint)
      elif label:
        return '{0:20}{1}'.format('Value:', label)
      else:
        return ''

  # Converts data element to string
  def to_string(self, elements: dict) -> str:
    title_text = 'EntryElement:' if self.is_entry else 'Element:'
    title = '{0:20}{1}'.format(title_text, self.label)
    concept = self.concepts
    based_on = self.based_on
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
    if self.description:
      description = '{0:20}"{1}"'.format('Description:', self.description)
    else:
      description = ''
    if self.uses:
      uses = '{0:20}{1}'.format('Uses:', ', '.join(self.uses))
    else:
      uses = ''
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
      elif child_type == 'IdentifiableValue' or child_type == 'RefValue':
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
    for i in ['primitive', self.label]:
      if i in self.uses:
        self.uses.remove(i)
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