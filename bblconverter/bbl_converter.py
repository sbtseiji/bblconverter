import copy
import re
import ruamel
import ruamel.yaml
import bbl_reader as bbl
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from collections import namedtuple

COLON  = ':'
SPACE  = ' '
COMMA  = ','
PERIOD = '.'
DOT    = '.'
DOTS   = '...'
EMDASH = '—'
CHAR_COLON = '&#58;'
LINEBREAK = '\n'


# ========== bibエントリクラス ==========
class BibEntry:
  def __init__(self):
    self.reset()
  def reset(self):
    self.listcount = 0
    self.listtotal = 1
    self.entry_data = ''
    self.related_entry = ''
    self.isrelated = False

# ========== ymlファイルの読み込み ==========
def load_yml(file_path):
  bib_contents =[]
  with open(file_path) as f:
    yaml = ruamel.yaml.YAML(typ='safe')
    yml_data = yaml.load(f)
    return yml_data


# ========== dict to named tuple ==========
def convert(dictionary):
    for key, value in dictionary.items():
            if isinstance(value, dict):
                dictionary[key] = convert(value) 
    return namedtuple('GenericDict', dictionary.keys())(**dictionary)

def parse_name_list(field_key, field_yaml, bib_entry):
  left_item = []
  current_item = []
  res_item = []
  bibitem_data = []
  # nameリストの処理
  if field_key in bib_names:
    bibitem_data = copy.deepcopy(bib_entry.entry_data.get(field_key))
    # print("bibitem_data", bibitem_data)
  elif field_key.replace('related:','') in bib_names and bib_entry.related_entry:
    field_key = field_key.replace('related:','')
    bibitem_data = copy.deepcopy(bib_entry.related_entry.get(field_key))
    # print("bibitem_data", bibitem_data)

  if not bibitem_data is None:

    bib_entry.listtotal = len(bibitem_data)

    for i in range(1, bib_entry.listtotal+1):
      bib_entry.listcount = i

      current_item = copy.deepcopy(parse_yaml(field_yaml,bib_entry))
      # print("current_name_format", current_item)
      if current_item:
        current_item = flatten_list(current_item)
        res_item.append(copy.deepcopy(current_item))
      # print("resulted_name_format", res_item)

    return res_item

def flatten_list(nested_list):
    # フラットなリストとフリンジを用意
    flat_list = []
    fringe = [nested_list]

    while len(fringe) > 0:
        node = fringe.pop(0)
        # ノードがリストであれば子要素をフリンジに追加
        # リストでなければそのままフラットリストに追加
        if isinstance(node, list):
            fringe = node + fringe
        else:
            flat_list.append(node)

    return flat_list

# 無駄に入れ子になっているリストを解消
def peelout_list(nested_list):
  while isinstance(nested_list,list) and len(nested_list)==1:
    nested_list = nested_list[0]
  return nested_list

def parse_yaml(item_yaml, bib_entry):
  left_item = copy.deepcopy(item_yaml)
  # print('item_yaml: ', item_yaml)
  # 1要素のみでネストになっているリストを展開
  left_item = peelout_list(left_item)

  # 文字列なら終了
  if isinstance(left_item, str):
    return left_item

  # リストの場合
  elif isinstance(left_item,list):
    # 最初の項目に条件文があるなら条件文の処理
    if "cond::" in left_item[0]:
      # print('left_item', left_item, bib_entry)
      left_item = conditional(left_item, bib_entry)
      res = parse_yaml(left_item,  bib_entry)
      if res:
        return res
    # そうでなければ2要素目以降についてyamlを展開    
    else: 
      res=[]
      res1 = parse_yaml(left_item.pop(0),bib_entry)
      res2 = parse_yaml(left_item, bib_entry)
      if res1:
        # print("res1: ", res1)
        res.append(res1)
      if res2:
        # print("res2: ", res2)
        if isinstance(res2,list) and len(res2)>1:
          res.extend(res2)
        else:
          res.append(res2)
      if res:
        return res
  # dictの場合，キーと値を設定して終了
  elif isinstance(left_item,dict):
    dict_key = list(left_item.keys())[0]
    dict_value = left_item.get(dict_key)

    # name list の場合
    if dict_key.replace('related:','') in bib_names:
      # print("dict_key",dict_key, bib_entry)
      dict_value = parse_name_list(dict_key, dict_value, bib_entry)

    else:
      dict_value = parse_yaml(dict_value, bib_entry)
      dict_value = flatten_list(dict_value)
    if dict_value:
      # 1要素のみでネストになっているリストを展開
      dict_value = peelout_list(dict_value)
      # print('dict value: ', dict_value)
      return {dict_key: dict_value}

def parse_formatter(formatter):
  res=''
  # print("formatter: ", formatter)
  # リストの場合
  if isinstance(formatter,list) and len(formatter)>0:
    # 最初の項目に条件文があるなら条件文の処理
    res_list=[]
    res1 = parse_formatter(formatter.pop(0))
    res2 = parse_formatter(formatter)
    if res1:
      res_list.append(res1)
      # print('res_list.append(res1)' , res_list)
    if res2:
      if isinstance(res2,list) and len(res2)>1:
        res_list.extend(res2)
      else:
        res_list.append(res2)
      # print('res_list.append(res2)' , res_list)
    return res_list

  if isinstance(formatter, dict):
    field_key = list(formatter.keys())[0]
    field_value = copy.deepcopy(formatter.get(field_key))
    # print('key: ', field_key, 'value:', field_value)

    if not field_value is None and field_value != [None]:
      # res = [field_key, field_value]
      res = {field_key: field_value}

  if isinstance(formatter, str):
    # res = ['TEXT', formatter]
    res = {'TEXT': formatter}

  return res


# ========== formatデータの展開 ==========
def format_field_data(field_format, bib_entry): 
  # print("format: ", field_format,bib_entry)

  if field_format is None:
    return

  if 'related:' in field_format:
    field_format = field_format.replace('related:','')

  (cont_type, cont_value) = field_format.split('::',1)
  match cont_type:
    case 'value': # フィールドから値を取得
      return retrieve_value(cont_value, bib_entry)
    case 'text': # テキストの出力
      return print_text(cont_value)
    case 'italic': # テキストの出力
      return handle_italic(cont_value)
    case 'bold': # テキストの出力
      return handle_bold(cont_value)
    case 'delim': # delimは対応する文字列に置き換え
      return str(globals()[cont_value])
    case 'punct': # ユニット区切りの処理
      return handle_punct(cont_value)
    case 'url': # URLの処理
      return handle_url(cont_value, bib_entry)
    case _:
      # print("hogehoge",tmp[0])
      return

def field_render(formatter, entry_data):

  is_related = False
  res_str = ''
  # print('========== レンダリング ==========')
  
  field_key = list(formatter.keys())[0]
  field_format = formatter.get(field_key)
  # print('field key: ', field_key, field_format, entry_data.entry_data.get(field_key))

  if field_key == 'TEXT':
    return format_field_data(field_format, entry_data)

  # relatedフィールドなら，文献情報はrelated_entry
  if "related:" in field_key:
    entry_data = copy.deepcopy(entry_data.related_entry)
    if not entry_data:
      return
    field_key = field_key.replace('related:','')
  else:
    entry_data = copy.deepcopy(entry_data.entry_data)

  # name listの場合はname_listのみに限定して処理
  if field_key in bib_names:
    name_data = entry_data.get(field_key)
    name_size = len(name_data)
    # print("name_data", name_data)

    if name_size == 1:
      for name_item in field_format:
        # print("name_item" , name_item, name_data[0])
        res_str += format_field_data(name_item, name_data[0])
    else:
      for i in range(name_size):
        for name_item in field_format[i]:
          res_str += format_field_data(name_item, name_data[i])
          # print("res_str" , res_str)
    res_str = res_str.strip()
    return res_str

  else:
    if isinstance(field_format,str):
       res_str += format_field_data(field_format, entry_data) 
    else:
      for field_item in field_format:
        res_str += format_field_data(field_item, entry_data) 
  return res_str

# value:: の処理
def retrieve_value(field_key, entry_data):
  outstr = ''
  field_value = ''

  # if '::' in field_key: # 書式設定がある場合
  #   (field_key, field_style) = field_key.split('::',1)
  #   field_value = copy.deepcopy(entry_data.get(field_key))
  #   if isinstance(field_value, list):
  #     field_value=copy.deepcopy(field_value[0])
  #   outstr += '\\'+str(field_style)+"{"
  #   outstr += str(field_value)
  #   outstr += '\\'+str(field_style)+"}"
  # else: # 書式設定なしの場合はそのまま
  field_value = copy.deepcopy(entry_data.get(field_key))
  if isinstance(field_value, list):
    field_value=copy.deepcopy(field_value[0])
  if not field_value is None:
    outstr += str(field_value)
  return outstr

# text:: の処理
def print_text(text_str):
  text_value = ''
  text_style = ''
  outstr = ''
  if '::' in text_str:
    text_value = text_str.split('::')[0].strip()
    text_style = text_str.split('::')[1]
    outstr += '\\'+text_style+"{"
    outstr += str(text_value.replace('\"',''))
    outstr += '\\'+text_style+"}"
  
  else: # 書式設定なしの場合はそのまま
    outstr += str(text_str.strip().replace('\"',''))
  return outstr

def handle_italic(italic):
  if italic == 'true':
    return "\\italic{"
  else:
    return "\\italic}"

def handle_bold(bold):
  if bold == 'true':
    return "\\bold{"
  else:
    return "\\bold}"

def handle_punct(punct_str):
  punct_char = punct_str.strip('\"')
  # print('punct:', punct_char)
  # outstr = punct_str.rstrip(punct_char) # 同じマークが連続しないようにする
  # if punct_char =="　": # 全角スペースの場合は空白を削除
  #   outstr = punct_str.rstrip()
  # if punct_str == punct_str.rstrip('?'): # 末尾が?でないならマークを追加
  #   outstr += punct_char
  return "\\punct\\"+punct_char      

def handle_url(url, bib_entry): # urlはタグで囲む
  url_string = ''
  if url == 'true':
    return "\\url{"
  else:
    return "\\url}"

  # match_obj = re.search(r'\[(.*?)\]',url_str)
  # if match_obj:
  #   match_str = match_obj.group(1)
  #   match_list = match_str.split(',')
  #   url_string = match_list[0].strip('"')+ format_field_data(match_list[1], bib_entry)

  # return "\\url{"+str(url_string)+"\\url}"


def conditional(cond_list, bib_entry):
  # print("cond_list: ",cond_list)
  res = ''
  # 複数条件かどうかを確認
  while isinstance(cond_list,list) and len(cond_list)==1:
    cond_list = cond_list[0]

  cond_str = cond_list[0].split('::',1)[1] # 「cond::」を削除

  if "&&" in cond_str:
    multi_cond_str = cond_str.split("&&")
    res = ifthenelse(multi_cond_str[0],bib_entry) and ifthenelse(multi_cond_str[1],bib_entry)
  elif "||" in cond_str:
    multi_cond_str = cond_str.split("||")
    res = ifthenelse(multi_cond_str[0],bib_entry) or ifthenelse(multi_cond_str[1],bib_entry)
  elif "^^" in cond_str:
    multi_cond_str = cond_str.split("^^")
    if ifthenelse(multi_cond_str[0],bib_entry) != ifthenelse(multi_cond_str[1],bib_entry):
      res = True
    else:
      res = False
  else:
    res = ifthenelse(cond_str,bib_entry)
 
  if res: # 結果が真の場合は次のステップを実施して終了
    # print("true: ", cond_list[1])
    return copy.deepcopy(cond_list[1])
  else:
    if len(cond_list)>2 :
      # print("false: ", cond_list[2])
      return copy.deepcopy(cond_list[2])
    else:
      # print("false")
      return

# cond関数の処理
def ifthenelse(cond_str,bib_entry):
  # 文字列から条件式とパラメタを構成
  cond_function = cond_str.split('[',1)[0]
  listcount = bib_entry.listcount
  listtotal = bib_entry.listtotal

  param1_related = False
  param2_related = False

  param1=param2=''
  match_obj = re.search(r'\[(.*?)\]',cond_str)
  if match_obj:
    param1 = match_obj[1].split(',')[0]
    param2 = match_obj[1].split(',')[1]

  # print("param1", param1, "param2", param2, bib_entry.related_entry)
  if "related:" in param1 :
    param1_related = True
    param1 = param1.replace('related:','')

  if param1 in locals() :
    param1 = locals()[param1]
  elif param1 in globals() :
    param1 = globals()[param1]
  else:
    if 'field::' in param1:
      param1 = param1.replace('field::','')
    elif 'value::' in param1:
      if param1_related:
        param1 = bib_entry.related_entry.get(param1.replace('value::',''))
      else:
        param1 = bib_entry.entry_data.get(param1.replace('value::',''))
      if not param1:
        return False
    elif 'total::' in param1:
      if param1_related:
        bibentry_data = bib_entry.related_entry.get(param1.replace('total::',''))
      else:
        bibentry_data = bib_entry.entry_data.get(param1.replace('total::',''))

      if isinstance(bibentry_data, list):
        param1 = len(bibentry_data)
      else:
        param1 = 0

 
  if "related:" in param2 :
    param2_related = True
    param2 = param2.replace('related:','')

  if param2 in locals() :
    param2 = locals()[param2]
  elif param2 in globals() :
      param2 = globals()[param2]
  else:
    if 'field::' in param2:
      param2 = param2.split('::',1)[1]
    elif 'value::' in param2:
      if param2_related:
        param2 = format_field_data(param2, bib_entry.related_entry)
      else:
        param2 = format_field_data(param2, bib_entry.entry_data)
      if not param2:
        return False
    elif 'total::' in param2:
      if param2_related:
        bibentry_data = bib_entry.related_entry.get(param2.replace('total::',''))
      else:
        bibentry_data = bib_entry.entry_data.get(param2.replace('total::',''))

      if isinstance(bibentry_data, list):
        param2 = len(bibentry_data)
      else:
        param2 = 0

  match cond_function:
    case 'ifequal':
      return True if str(param1).strip()==str(param2).strip() else False
    case 'ifunequal':
      return True if str(param1).strip()!=str(param2).strip() else False
    case 'ifgreater':
      return True if int(param1)>int(param2) else False
    case 'ifgreatereq':
      return True if int(param1)>=int(param2) else False
    case 'ifless':
      return True if int(param1)<int(param2) else False
    case 'iflesseq':
      return True if int(param1)<=int(param2) else False
    case 'ifdef':
      if param1_related:
        if param2 =='true' and (param1 in bib_entry.related_entry):
          return True
        elif param2 =='false' and (param1 not in bib_entry.related_entry):
          return True
        else:
          return False
      else:
        if param2 =='true' and param1 in bib_entry.entry_data:
          return True
        elif param2 =='false' and (param1 not in bib_entry.entry_data):
          return True
        else:
          return False


# LaTeXのbibitemとして出力
def export_latex(biblist):
  for item in biblist:
    bib_str = item[1]
    bib_str = bib_str.replace("\\italic{","\\textit{")
    bib_str = bib_str.replace("\\italic}","}")
    bib_str = bib_str.replace("\\bold{","\\textbf{")
    bib_str = bib_str.replace("\\bold}","}")
    bib_str = bib_str.replace("\\url}","}")
    bib_str = bib_str.replace(EMDASH,"---")
    bib_str = bib_str.replace(CHAR_COLON,":")

    bib_str = bib_str.replace('&',"\&")

    print("\\bibitem{"+item[0]+"}", bib_str)


# メインの処理

# 文献データ
# bib_contents = bbl.load_bbl('../jpa-style.bbl')
yaml = ruamel.yaml.YAML(typ='safe')
bib_data = load_yml('../yaml/test.yml')
# bib_data = bbl.bbl_to_yml(bib_contents)

# 文献リストの書式
yaml = ruamel.yaml.YAML(typ='safe')
bib_yml_raw = load_yml('../yaml/jjpsy.yml')
# tp = convert(bib_yml_raw)

# 変数を処理
bib_variables = bib_yml_raw['constants']
for key, value in bib_variables.items():
  exec("%s = %s" % (key,value)) # keyの値を変数名，valueを変数値として処理

# ネームリストを処理
bib_names = bib_yml_raw['names']

bib_list = [] # 最終的な変換結果を入れるためのリスト

for entry_data in bib_data:
  bib_yml = copy.deepcopy(bib_yml_raw)
  bib_item = ['',[]] # 変換後の文献リスト項目
  # print(bib_item)
  if not entry_data.get('skip'): # skipしないエントリの場合のみ
    bib_item[0] = entry_data.get('entry')

    # print("###### start entry ",bib_item[0], "########")

    bib_entry = BibEntry() # エントリクラスの作成
    bib_entry.entry_data = copy.deepcopy(entry_data)

    if 'related' in bib_entry.entry_data: # relatedがある場合はそれを取得
      related_entry_id = entry_data.get('related')
      bib_entry.related_entry = [x for x in bib_data if x['entry'] == related_entry_id][0]

    # entryの言語を調べ，言語が指定されていればそちらのdriverを選択
    if 'language' in entry_data:
      entry_language = entry_data.get('language')[0]
      bib_driver = bib_yml['driver'].get(entry_language)
    else:
      bib_driver = bib_yml['driver'].get('other')

    # 文献タイプ（article, book, etc.）の書式を取得
    driver_yaml = copy.deepcopy(bib_driver.get(bib_entry.entry_data['entrytype']))

    if driver_yaml: 

      # print("###### start entry ########")
      # print(driver_yaml)
      field_key = '' # フィールドキー
      field_list = [] # フィールドキーとformatterを入れるためのリスト

      # yamlリストを1項目ずつ順番に処理
      for field_yaml in driver_yaml: # 順番にフィールドを処理
        formatter = parse_yaml(field_yaml, bib_entry)
        # print("formatter: ", formatter)
        if formatter:
          res = parse_formatter(formatter)
          res = peelout_list(res)
          if isinstance(res, list) and len(res)>2:
            field_list.extend(copy.deepcopy(res))
          elif res:
            field_list.append(copy.deepcopy(res))
          
      # print('field_list, ', field_list)

#     ========== レンダリング ==========
      for list_item in field_list:
        res_str = ""
        list_item = peelout_list(list_item)
        # print('list_item: ',list_item)
        # print(bib_item)
        if len(list_item) > 0:
          if isinstance(list_item,list) and len(list_item) > 1:
            for item in list_item:
              item = peelout_list(item)
              res_str += field_render(item,bib_entry)
          else:
            res_str = field_render(list_item,bib_entry)

          if res_str:
            bib_item[1].append(res_str)

#     if bib_item:
    bib_list.append(bib_item)
  print(bib_item)
# print(bib_list)
# export_latex(bib_list)
