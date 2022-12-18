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


# ========== フォーマットyamlの処理 ==========
def process_format_yaml(field_key, field_yaml, bib_entry):
  left_item = []
  current_item = []
  res_item = []

  if (field_key in bib_names) or ("related::" in field_key and field_key.replace('related::','') in bib_names): # nameリストの処理
    if field_key in bib_names:
      bibitem_data = copy.deepcopy(bib_entry.entry_data.get(field_key))
    elif field_key.replace('related::','') in bib_names:
      field_key = field_key.replace('related::','')
      bibitem_data = copy.deepcopy(bib_entry.related_entry.get(field_key))


    if bibitem_data:
      bib_entry.listtotal = len(bibitem_data)

      for i in range(1, bib_entry.listtotal+1):
        bib_entry.listcount = i

        left_item = copy.deepcopy(field_yaml)

        current_item =[]
        current_item = parse_yaml(left_item,bib_entry)

        if current_item:
          res_item.append(current_item)

  else:
    left_item = copy.deepcopy(field_yaml)

    current_item =[]
    current_item = parse_yaml(left_item,bib_entry)

    res_item.append(current_item)
  return res_item


def handle_name_list(field_key, field_yaml, bib_entry):
  left_item = []
  current_item = []
  res_item = []
  bibitem_data = []
  # nameリストの処理
  if field_key in bib_names:
    bibitem_data = copy.deepcopy(bib_entry.entry_data.get(field_key))
  elif field_key.replace('related::','') in bib_names and bib_entry.related_entry:
    field_key = field_key.replace('related::','')
    bibitem_data = copy.deepcopy(bib_entry.related_entry.get(field_key))

  if not bibitem_data is None:

    bib_entry.listtotal = len(bibitem_data)

    for i in range(1, bib_entry.listtotal+1):
      bib_entry.listcount = i
      left_item = copy.deepcopy(field_yaml)
      current_item =[]
      current_item = parse_yaml(left_item,bib_entry)
      if current_item:
        current_item = flatten_list(current_item)
        res_item.append(copy.deepcopy(current_item))
      # print('for loop', i, res_item)

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

def parse_yaml(item_yaml, bib_entry):
  left_item = copy.deepcopy(item_yaml)

  # 1要素のみでネストになっているリストを展開
  while isinstance(left_item,list) and len(left_item)==1:
    left_item = left_item[0]

  # 文字列なら終了
  if isinstance(left_item, str):
    return left_item

  # リストの場合
  elif isinstance(left_item,list):
    # 最初の項目に条件文があるなら条件文の処理
    if "cond::" in left_item[0]:
      left_item = conditional(left_item, bib_entry)
      res = parse_yaml(left_item,  bib_entry)
      if res:
        return res
    # そうでなければ2要素目以降についてyamlを展開    
    else: 
      res=[]
      res1 = parse_yaml(left_item.pop(0),bib_entry)
      res2 = parse_yaml(left_item, bib_entry)
      if res1 and res2:
        return [res1, res2]
      elif res1:
        return res1
      elif res2:
        return res2
      else:
        return
  # dictの場合，キーと値を設定して終了
  elif isinstance(left_item,dict):
    dict_key = list(left_item.keys())[0]
    dict_value = left_item.get(dict_key)

    # name list の場合
    if dict_key in bib_names:
      dict_value = handle_name_list(dict_key, dict_value, bib_entry)

    else:
      dict_value = parse_yaml(dict_value, bib_entry)
      dict_value = flatten_list(dict_value)
    if dict_value:
      return {dict_key: dict_value}


# ========== formatデータの展開 ==========
def format_field_data(field_format, bib_entry): 
  # print("format", field_format,bib_entry)

  if field_format is None:
    return

  (cont_type, cont_value) = field_format.split('::',1)
  match cont_type:
    case 'value': # フィールドから値を取得
      return retrieve_value(cont_value, bib_entry)
    case 'text': # テキストの出力
      return print_text(cont_value)
    case 'delim': # delimは対応する文字列に置き換え
      return str(globals()[cont_value])
    case 'punct': # ユニット区切りの処理
      return handle_punct(cont_value)
    case 'url': # URLの処理
      return handle_url(cont_value, bib_entry)
    case _:
      # print("hogehoge",tmp[0])
      return

# value:: の処理
def retrieve_value(field_key, entry_data):
  outstr = ''
  field_value = ''

  if '::' in field_key: # 書式設定がある場合
    (field_key, field_style) = field_key.split('::',1)
    field_value = copy.deepcopy(entry_data.get(field_key))
    if isinstance(field_value, list):
      field_value=copy.deepcopy(field_value[0])
    outstr += '\\'+str(field_style)+"{"
    outstr += str(field_value)
    outstr += '\\'+str(field_style)+"}"
  else: # 書式設定なしの場合はそのまま
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

def handle_punct(punct_str):
  outstr = ''

  punct_char = punct_str.replace('\"','')
  outstr = outstr.rstrip(punct_char) # 同じマークが連続しないようにする
  if punct_char =="　": # 全角スペースの場合は空白を削除
    outstr = outstr.rstrip()
  if outstr == outstr.rstrip('?'): # 末尾が?でないならマークを追加
    outstr += punct_char
  return outstr            

def handle_url(url_str, bib_entry): # urlはタグで囲む
  url_string = ''

  match_obj = re.search(r'\[(.*?)\]',url_str)
  if match_obj:
    match_str = match_obj.group(1)
    match_list = match_str.split(',')
    url_string = match_list[0].strip('"')+ format_field_data(match_list[1], bib_entry)

  return "\\url{"+str(url_string)+"\\url}"


def conditional(cond_list, bib_entry):
  # print("cond_list: ",cond_list)
  res = ''
  # 複数条件かどうかを確認
  # print("cond list: ", cond_list)
  while isinstance(cond_list,list) and len(cond_list)==1:
    print("cond list: ", cond_list)
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

  if "related::" in param1 :
    param1_related = True
    param1 = param1.replace('related::','')

  # print("param1", param1, param2)

  if param1 in locals() :
    param1 = locals()[param1]
  elif param1 in globals() :
    param1 = globals()[param1]
  else:
    if 'field::' in param1:
      param1 = param1.split('::',1)[1]
    elif 'value::' in param1:
      if param1_related:
        param1 = format_field_data(param1, bib_entry.related_entry)
      else:
        param1 = format_field_data(param1, bib_entry.entry_data)
      # print(param1)
      if not param1:
        return False
 
  if "related::" in param2 :
    param2_related = True
    param2 = param2.replace('related::','')

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
  # print("conditional: ", cond_str, "param1: ",param1, "param2: ",param2)

  match cond_function:
    case 'ifequal':
      return True if str(param1)==str(param2) else False
    case 'ifunequal':
      return True if str(param1)!=str(param2) else False
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
        if param2 =='true' and param1 in bib_entry.related_entry:
          return True
        elif param2 =='false' and param1 not in bib_entry.related_entry:
          return True
        else:
          return False
      else:
        # print("****", param1, param2, bib_entry.entry_data)
        if param2 =='true' and param1 in bib_entry.entry_data:
          # print('true')
          return True
        elif param2 =='false' and (param1 not in bib_entry.entry_data):
          # print('true')
          return True
        else:
          # print('false')
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
  bib_item = ['',''] # 変換後の文献リスト項目
  if not entry_data.get('skip'): # skipしないエントリの場合のみ
    bib_item[0] = entry_data.get('entry')

    print("###### start entry ",bib_item[0], "########")

    bib_entry = BibEntry() # エントリクラスの作成
    bib_entry.entry_data = copy.deepcopy(entry_data)

    if 'relatedtype' in entry_data: # relatedがある場合はそれを取得
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

      print("###### start entry ########")
      # print(driver_yaml)
      field_key = '' # フィールドキー
      field_list = [] # フィールドキーとformatterを入れるためのリスト

      # yamlリストを1項目ずつ順番に処理
      for field_yaml in driver_yaml: # 順番にフィールドを処理
        print("###### start field ########")

        res = parse_yaml(field_yaml, bib_entry)

        if res:
          if isinstance(res, dict):
            field_key = list(res.keys())[0]
            field_value = res.get(field_key)

            if not field_value is None and field_value != [None]:
              field_list.append([field_key, field_value]) 

          if isinstance(res, str):
            field_list.append(['TEXT', res])

          while isinstance(res, list) and len(res)>0:
            tmp = res.pop(0)

            while isinstance(res,list) and len(res)==1:
              res = res[0]

            if isinstance(tmp, dict):
              field_key = list(tmp.keys())[0]
              field_value = tmp.get(field_key)

              if not field_value is None and field_value != [None]:
                field_list.append([field_key, field_value]) 
            elif isinstance(tmp, str):
              if tmp:
                field_list.append(['TEXT', tmp])
          
      print('field_list, ', field_list)



#     ========== レンダリング ==========
      for list_item in field_list:
        # print('list_item',list_item)
        if len(list_item[1]) > 0:
          is_related = False

          res_str = ''
          print('========== レンダリング ==========')
          # print('field_key',list_item[0], 'list_item: ', list_item[1])

          if list_item[0]=='TEXT':
            res_str += format_field_data(list_item[1], bib_entry)

          if isinstance(list_item[1],list):
            formatter_list = list_item[1]

            if 'related::' in list_item[0]:
              is_related = True
              list_item[0] = list_item[0].replace('related::','')

            if list_item[0] in bib_names:
              if is_related and bib_entry.related_entry:
                name_data = bib_entry.related_entry.get(list_item[0])
              else:
                name_data = bib_entry.entry_data.get(list_item[0])
              
              name_size = len(name_data)
              # print("name size", name_size, formatter_list)

              if name_size == 1 and isinstance(formatter_list[0],str):
                for item in formatter_list:
                  # print("name parts: ",item)
                  res_str += format_field_data(item, name_data[0])
              else:
                for i in range(name_size):
                  for item in formatter_list[i]:
                    # print("name parts: ",item)
                    res_str += format_field_data(item, name_data[i])
              res_str = res_str.strip()

            elif isinstance(formatter_list, list):
              while formatter_list:
                formatter = formatter_list.pop(0)

                if isinstance(formatter, list):
                  for item in formatter:
                    if is_related:
                      res_str += format_field_data(item, bib_entry.related_entry)
                    else:
                      res_str += format_field_data(item, bib_entry.entry_data)

                elif formatter:
                  if is_related and bib_entry.related_entry:
                    res_str += format_field_data(formatter, bib_entry.related_entry)
                  else:
                    res_str += format_field_data(formatter, bib_entry.entry_data)
                
            else:
              if is_related:
                res_str += format_field_data(field_list[1], bib_entry.related_entry)
              else:
                res_str += format_field_data(field_list[1], bib_entry.entry_data)

          bib_item[1] += res_str

    print(bib_item)
#     if bib_item:
#       bib_list.append(bib_item)
# export_latex(bib_list)
