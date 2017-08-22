import json
import os
import sys

from namespace import Namespaces
from value_sets import ValueSets


def read_json_file(filename):
  with open(filename, 'r') as json_file:
    return json.load(json_file)


class JsonToCameo:

  def __init__(self, json_data: dict=None, filename: str='',
               output: str='out/'):
    self.error_checking(json_data, filename)
    os.makedirs(output, exist_ok=True)
    self.output = output
    n, v = self.get_data(json_data, filename)
    self.namespaces = Namespaces(n)
    self.value_sets = ValueSets(v)

  # Does some basic checking to on the input data
  def error_checking(self, d: dict, f: str) -> None:
    if d is None and not f:
      raise Exception('Missing input data')
    elif d is not None and f:
      raise Exception('Can\'t use both data sources')
    elif d is not None and not isinstance(d, dict):
      raise Exception('json_data must be of type dict')
    elif f and not isinstance(f, str):
      raise Exception('filename must be of type str')
    elif f and f.rpartition('.')[2] != 'json':
      raise Exception('file must end in .json')

  # Get the namespaces and valuesets dictionaries
  def get_data(self, json_data: dict, filename: str) -> dict:
    if json_data is not None:
      data = json_data
    else:
      data = read_json_file(filename)
    namespaces = None
    valuesets = None
    for i in data.get('children', []):
      if i.get('type') == 'Namespaces':
        namespaces = i
      elif i.get('type') == 'ValueSets':
        valuesets = i
    if namespaces is None or valuesets is None:
      raise Exception('Missing Namespaces or ValueSets')
    return namespaces, valuesets

  # Writes the valuesets to files
  def vs_to_file(self) -> None:
    value_sets = self.value_sets.value_sets
    for i in value_sets:
      name = i.replace('.', '_')
      with open('{0}{1}_vs.txt'.format(self.output, name), 'w') as outfile:
        outfile.write(str(value_sets[i]))

  # Writes the namespaces to file
  def ns_to_file(self) -> None:
    namespaces = self.namespaces.namespaces
    for i in namespaces:
      name = i.replace('.', '_')
      with open('{0}{1}.txt'.format(self.output, name), 'w') as outfile:
        outfile.write(str(namespaces[i]))

  # Write all output files
  def all_files(self) -> None:
    self.vs_to_file()
    self.ns_to_file()


def main(args):
  j2c = JsonToCameo(filename=args[0])
  j2c.all_files()


if __name__ == '__main__':
  main(sys.argv[1:])