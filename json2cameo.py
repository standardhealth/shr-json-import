import json
import os
import sys

from namespace import Namespaces
from value_sets import ValueSets


def read_json_file(filename):
  with open(filename, 'r') as json_file:
    data = json.load(json_file)
  return data


def main(args):
  data = read_json_file(args[0])
  os.makedirs('out/', exist_ok=True)
  n = Namespaces(data['children'][0])
  v = ValueSets(data['children'][1])


if __name__ == '__main__':
  main(sys.argv[1:])