import sys
import ruamel
import ruamel.yaml
import LaTexAccents as utfconverter

with open("../yaml/jjpsy.yml") as f:
  yaml = ruamel.yaml.YAML(typ='safe')
  yml_data = yaml.load(f)
  yaml.dump(yml_data, sys.stdout)