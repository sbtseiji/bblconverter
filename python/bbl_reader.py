import re
import ruamel
import ruamel.yaml

bbl_file_path = '../jpa-style.bbl'

# BibLaTeXの記号の置き換え
bibinitperiod = '.'
bibinitdelim =''
bibnamedelim =''
bibnamedelimi =''
bibrangedash = '--'

# YAMLのインデント
yml_indent = '  '

# YAML作成用リスト
string_list_for_creating_yml = []

# エントリ処理用のフラグ
is_entry = False
is_name = False
is_list = False

# nameラベルを表示するかどうかのフラグ
label_name = True
# listラベルを表示するかどうかのフラグ
label_list = True

# nameやiistの最初の要素かどうかのフラグ
is_first_element =False

# nameおよびlistのタイプ
name_type = ''
list_type = ''

# BibLaTeXファイルのYAML格納用変数
bbl_yml = ''

# ========== 各種変数・フラッグの初期化 ==========
def reset_flags():
  is_entry = False
  is_name = False
  is_list = False
  label_name = True
  label_list = True
  is_first_element =False
  name_type = ''
  list_type = ''

# ========== bblファイルの読み込み ==========
bbl_contents =[]
with open(bbl_file_path) as f:
  bbl_contents = f.readlines()


# ========== ファイル内容の変換処理 ==========
for line in bbl_contents:

  # エントリデータ処理中の場合
  if is_entry:
    # ========== フラグの処理 ==========
    # \endentry でエントリ終了
    if re.search(r'.*\\endentry',line):
      is_entry = False

    # \name でname処理へのフラグを立てる
    match_obj = re.search(r'\\name\{(.*?)\}',line)
    if match_obj:
      name_type = match_obj.group(1)
      if label_name:
        print(yml_indent+'name:')
        string_list_for_creating_yml.append(yml_indent+'name:')
        label_name = False
      print(yml_indent*2+name_type+':')
      is_list = False
      is_name = True
      is_first_element = True
      label_list = True

    # \list でlist処理へのフラグを立てる
    match_obj = re.search(r'\\list\{(.*?)\}',line)
    if match_obj:
      list_type = match_obj.group(1)
      if label_list:
        print(yml_indent+'list:')
        string_list_for_creating_yml.append(yml_indent+'list:')
        label_list = False
      print(yml_indent*2+list_type+':')
      string_list_for_creating_yml.append(yml_indent*2+list_type+':')
      is_list = True
      is_name = False
      is_first_element = True
      label_name = True

    # \field でnameとlistのフラグをおろす
    # かつ，fieldの内容を処理する
    match_obj = re.search(r'\\field\{(.*?)\}\{(.*?)\}',line)
    if match_obj:
      is_list = False
      is_name = False
      label_name = True
      label_list = True
      item_content = match_obj.group(2).replace('\\bibrangedash ',bibrangedash)
      print(yml_indent+match_obj.group(1)+':',item_content)
      string_list_for_creating_yml.append(yml_indent+match_obj.group(1)+': '+item_content)

    # \string でnameとlistのフラグをおろす
    if re.search(r'\\string',line):
      is_list = False
      is_name = False

    # ========== パース処理 ==========

    # name
    if is_name:
      name_part=['family','familyi','given','giveni']
      for item in name_part:
        match_obj = re.search(item+r'=\{+(.*?)\}+', line)
        if match_obj :
          item_content = match_obj.group(1).replace('\\bibinitperiod',bibinitperiod).replace('\\bibinitdelim',bibinitdelim).replace('\\bibnamedelimi',bibnamedelim).replace('\\bibnamedelim',bibnamedelimi)
          if is_first_element :
            print(yml_indent*3+'- '+item+':',item_content)
            string_list_for_creating_yml.append(yml_indent*3+'- '+item+': '+item_content)
            is_first_element = False
          else :
            print(yml_indent*4+item+':',item_content)
            string_list_for_creating_yml.append(yml_indent*4+item+': '+item_content)
      if re.search(r'\}\}\%', line):
        is_first_element = True

    # list
    if is_list:
      match_obj = re.search(r'\s*\{+(.*?)\}+\%', line)
      if match_obj :
        item_content = match_obj.group(1)
        print(yml_indent*3+'- '+item_content)
        string_list_for_creating_yml.append(yml_indent*3+'- '+item_content)


  # エントリデータ処理中以外の場合
  else:
    match_obj = re.search(r'\\entry\{',line)
    if match_obj:
      entry_type = line.split('}{')[1]
      print('- type:', entry_type)
      string_list_for_creating_yml.append('- type: '+ entry_type)
      skip_bib = 'true' if re.search(r'skipbib',line) else 'false'
      print(yml_indent+'skip: '+skip_bib)
      string_list_for_creating_yml.append(yml_indent+'skip: '+skip_bib)
      reset_flags()
      is_entry = True

# ========== リストからYAMLを作成 ==========
yaml = ruamel.yaml.YAML()
bby_yml_str = '\n'.join(string_list_for_creating_yml)
bbl_yml = yaml.load(bby_yml_str)