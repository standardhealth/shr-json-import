import json


# Initiate class to singleton, only one instance
def singleton(cls):
  return cls()


# Manages codesystem abbreviation and generates new ones if they don't exist
@singleton
class CodeSystems:
  BANNED = ['urn:oid', 'standardhealthrecord']

  def __init__(self):
    with open('./config/codesystems.json', 'r') as code_file:
      self.codesystems = json.load(code_file)
    self.abbrev_set = set(self.codesystems[i] for i in self.codesystems)
    # Initialize defualt abbreviation to 'AAA' in bytes
    self.next_abbreviation = [65, 65, 65]

  # Returns abbreviation for existing codesystem or new one
  def get(self, codesystem: str) -> str:
    if codesystem is None:
      return ''
    elif any(b in codesystem for b in self.BANNED):
      return ''
    elif codesystem in self.codesystems:
      return self.codesystems[codesystem]
    else:
      abbrev = self.get_next_abbreviation()
      self.update_codesystems(codesystem, abbrev)
      return abbrev

  def update_codesystems(self, codesystem: str, abbrev: str) -> None:
    self.codesystems[codesystem] = abbrev
    self.abbrev_set.add(abbrev)

  # Return next default abbreviation, checks to make sure it doesn't exist
  def get_next_abbreviation(self):
    next_abbrev = bytes(self.next_abbreviation).decode('utf-8')
    while next_abbrev in self.codesystems:
      self.update_abbreviation()
      next_abbrev = bytes(self.next_abbreviation).decode('utf-8')
    else:
      self.update_abbreviation()
      self.abbrev_set.add(next_abbrev)
    return next_abbrev

  # Updates default abbreviation byte array
  def update_abbreviation(self) -> None:
    array = self.next_abbreviation
    if array[1] == 90 and array[2] == 90:
      array[0] += 1
      array[1] = 65
      array[2] = 65
    elif array[2] == 90:
      array[1] += 1
      array[2] = 65
    else:
      array[2] += 1


# Main function to run some basic tests on functionality
def main():
  print(CodeSystems.get("http://example.com"))
  print(CodeSystems.get("http://www.dsm5.org/"))
  print(CodeSystems.get("http://shr.com"))
  print(CodeSystems.get("http://www.meddra.org"))
  print(CodeSystems.get("http://example1.com"))


if __name__ == '__main__':
  main()