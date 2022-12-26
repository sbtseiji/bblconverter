import re
import ruamel
import ruamel.yaml
import bblconverter.LaTexAccents as utfconverter

# BibLaTeXの記号の置き換え
BIBINITPERIOD = '.'
BIBINITDELIM =''
BIBNAMEDELIM =''
BIBNAMEDELIMI =''
BIBRANGEDASH = '--'

# colon(:)のエスケープ
CHAR_COLON = '&#58;'

# YAMLのインデント
YAML_INDENT = '  '

# YAML作成用リスト
strlist_yml = []

# ========== 各種フラッグ ==========
class BblFlags:
  def __init__(self):
    self.reset()
  def reset(self):
    self.is_entry = False
    self.is_name = False
    self.is_list = False
    self.is_first_element =False

# ========== bblファイルの読み込み ==========
def load_bbl(file_path):
  bbl_contents =[]
  with open(file_path) as f:
    bbl_contents = f.readlines()
    return bbl_contents

# ========== nameフィールドの処理 ==========
def handle_name(line, flag):
  res = []
  # フラッグの処理
  match_obj = re.search(r'\\name\{(.*?)\}',line)
  if match_obj:
    name_type = match_obj.group(1)
    res.append(YAML_INDENT+name_type+':')
    flag.is_list = False
    flag.is_name = True
    flag.is_first_element = True

  # nameフィールドの中身の処理
  if flag.is_name:
    name_part=['family','familyi','given','giveni']
    for item in name_part:
      match_obj = re.search(item+r'=\{+(.*?)\}+', line)
      if match_obj :
        item_content = match_obj.group(1).replace('\\bibinitperiod',BIBINITPERIOD).replace('\\bibinitdelim',BIBINITDELIM).replace('\\bibnamedelimi',BIBNAMEDELIMI).replace('\\bibnamedelim',BIBNAMEDELIM)
        if flag.is_first_element :
          res.append(YAML_INDENT*2+'- '+item+': '+item_content)
          flag.is_first_element = False
        else :
          res.append(YAML_INDENT*3+item+': '+item_content)
    if re.search(r'\}\}\%', line):
      flag.is_first_element = True
  return res

# ========== listフィールドの処理 ==========
def handle_list(line, flag):
  res = []
  # フラグの処理
  match_obj = re.search(r'\\list\{(.*?)\}',line)
  if match_obj:
    list_type = match_obj.group(1)
    # if flag.label_list:
    #   res.append(YAML_INDENT+'list:')
    #   flag.label_list = False
    res.append(YAML_INDENT+list_type+':')
    flag.is_list = True
    flag.is_name = False
    flag.is_first_element = True

  # nameフィールドの中身の処理
  if flag.is_list:
    match_obj = re.search(r'\s*\{+(.*?)\}+\%', line)
    if match_obj :
      item_content = match_obj.group(1)
      res.append(YAML_INDENT*2+'- '+item_content)

  return res

# ========== fieldフィールドの処理 ==========
def handle_field(line, flag):
  res = []
  match_obj = re.search(r'\\field\{(.*?)\}\{(.*?)\}',line)
  if match_obj:
    flag.is_list = False
    flag.is_name = False
    item_content = match_obj.group(2).replace('\\bibrangedash ',BIBRANGEDASH)
    res.append(YAML_INDENT+match_obj.group(1)+': '+item_content)
    return res

# ========== verbフィールドの処理 ==========
def handle_verb(line, flag, verb_type):
  res = []
  match_obj = re.search(r'\\verb\{(.*?)\}',line)
  if match_obj:
    flag.is_list = False
    flag.is_name = False
    verb_type = match_obj.group(1)
    return res, verb_type
  else:
    match_obj = re.search(r'\\verb\s+(.*?)$',line)
    if match_obj:
      res.append(YAML_INDENT+verb_type+': '+match_obj.group(1))
    return res, verb_type

# ========== stringフィールドの処理 ==========
def handle_string(line, flag):
  if re.search(r'\\string',line):
    flag.is_list = False
    flag.is_name = False
    return

# ========== エントリ外の処理 ==========
def handle_others(line, flag):
  res = []
  match_obj = re.search(r'\\entry\{',line)
  if match_obj:
    flag.reset()
    flag.is_entry = True
    match_obj = re.search(r'\\entry\{(.*?)\}',line)
    entry_key = match_obj[1]
    res.append('- entry: '+ entry_key)
    entry_type = line.split('}{')[1]
    skip_bib = 'true' if re.search(r'skipbib',line) else 'false'
    res.append('  entrytype: '+ entry_type)
    res.append(YAML_INDENT+'skip: '+skip_bib)
    return res

# ========== YAMLを作成してデータに変換 ==========
def convert_to_yaml(yml_str):
  yaml = ruamel.yaml.YAML()
  bby_yml_str = '\n'.join(yml_str)
  bbl_data = yaml.load(bby_yml_str)
  return bbl_data

# ========== bblをyamlに変換 ==========
def bbl_to_yml(bbl_contents):
  bbl_flags = BblFlags()
  converter = utfconverter.AccentConverter()
  
  verb_type = ''
  for line in bbl_contents:
    # colonを置き換え
    line = line.replace(':',CHAR_COLON)
    line = converter.decode_Tex_Accents(line, utf8_or_ascii=1)

    if bbl_flags.is_entry: # エントリ内の処理
      if re.search(r'.*\\endentry',line): # \endentry でエントリ終了
        bbl_flags.is_entry = False

      # nameの処理
      res = handle_name(line, bbl_flags)
      if res:
        strlist_yml.extend(res)

      # listの処理
      res = handle_list(line, bbl_flags)
      if res:
        strlist_yml.extend(res)

      # fieldの処理
      res = handle_field(line, bbl_flags)
      if res:
        strlist_yml.extend(res)

      # verbの処理
      res = handle_verb(line, bbl_flags, verb_type)
      verb_type = res[1]
      if res[0]:
        strlist_yml.extend(res[0])

      # stringの処理
      res = handle_string(line, bbl_flags)

    else: # エントリ外の処理
      res = handle_others(line, bbl_flags)
      if res:
        strlist_yml.extend(res)

  # YAMLデータに変換
  bbl_data = convert_to_yaml(strlist_yml)
  return bbl_data

# === 出力して確認
# yaml = ruamel.yaml.YAML()
# bbl_contents = load_bbl('../jpa-style.bbl')
# bbl_data = bbl_to_yml(bbl_contents)
# with open('../yaml/out.yml', 'w') as stream:
#     yaml.dump(bbl_data, stream=stream)




