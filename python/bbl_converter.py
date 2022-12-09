import re
import ruamel
import ruamel.yaml
import bbl_reader as bbl

# ========== ymlファイルの読み込み ==========
def load_yml(file_path):
  bbl_contents =[]
  with open(file_path) as f:
    yaml = ruamel.yaml.YAML()
    yml_data = yaml.load(f)
    return yml_data

# ========== dictデータの展開 ==========
def expand_format(obj,out):
  tmp = []
  print(obj)
  for item in obj:
    if isinstance(item, list) or isinstance(item, dict) :
      expand_dict(item,res)
    tmp = item.split('//')
    match tmp[0]:
      case 'value':
        print(tmp[1])


# メインの処理

# 文献データ
bbl_contents = bbl.load_bbl('../jpa-style.bbl')
bbl_data = bbl.bbl_to_yml(bbl_contents)

# 文献リストの書式
yaml = ruamel.yaml.YAML()
bbl_formatter = load_yml('../yaml/jjpsy.yml')

i = 0
for bibentry in bbl_data:
  # 文献タイプ（article, book, etc.）の定義
  format_def = bbl_formatter['type'].get(bibentry['type'])

  formatter =[] # yamlをさらに加工してここに入れるためのリスト
  if format_def:
    # 文献項目（author, year, etc.）の書式
    field_format = bbl_formatter['format'].get(bibentry['type'])
    # print('a',field_format)
    # print(bibentry)
    for item in format_def:
      print(bibentry.get(item))
      # print(field_format.get(item)) # フィールドの書式を取得
      formatter.extend(['format',item])
    # print(formatter)
    expand_format(field_format,'')
    # for field in formatter:
      # print(field)
  # for key, value in bibentry.items():
  #   print(key, value)