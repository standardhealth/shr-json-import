import json
import sys

from namespace import Namespaces
from value_sets import ValueSets


def read_json_file(filename):
  with open(filename, 'r') as json_file:
    data = json.load(json_file)
  return data


def main(args):
  data = read_json_file(args[0])
  for i in data['children']:
    print(i['label'])
    # for j in i['children']:
    #   print(j['label'])

  actor = data['children'][0]['children'][0]
  # with open('sample1.json', 'w') as json_file:
  #   params = {"indent": 3, "separators": (',', ' : ')}
  #   json.dump(actor, json_file, **params)

  n = Namespaces(data['children'][0])
  # print(n)
  v = ValueSets(data['children'][1])
  print(v)


if __name__ == '__main__':
  main(sys.argv[1:])