# Formats version based on major, minor, and patch values
def get_version(version_dict):
  major = version_dict.get('major', 0)
  minor = version_dict.get('minor', 0)
  patch = version_dict.get('patch', 0)
  return '{}.{}.{}'.format(major, minor, patch)


def get_concept(concept_dict):
  pass


class DataElement:

  def __init__(self, data_element):
    self.label = data_element.get('label', '')
    self.concepts = data_element.get('concepts', [])
    self.based_on = data_element.get('basedOn', [])
    self.description = data_element.get('description', '')
    self.children = data_element.get('children', [])


class Namespace:

  def __init__(self, namespace):
    self.label = namespace.get('label', '')
    self.description = namespace.get('description', '')
    self.version = get_version(namespace.get('grammarVersion', {}))

  def format_header(self):
    grammar = ''

  def __str__(self):
    string = 'Label: {}\nVersion: {}\nDescription: {}'
    return string.format(self.label, self.version, self.description)


class Namespaces:

  def __init__(self, namespaces):
    self.label = namespaces['label']
    self.type = namespaces['type']
    # self.version = get_version(namespaces['grammarVersion'])
    self.namespaces = namespaces['children']

  def __str__(self):
    header = 'Label: {}\nType: {}'.format(self.label, self.type)
    body = '\n\n'.join(str(Namespace(name)) for name in self.namespaces)
    return header + '\n' + body