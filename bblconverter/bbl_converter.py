import re
import ruamel
import ruamel.yaml
import bbl_reader as bbl
from ruamel.yaml.comments import CommentedMap, CommentedSeq

COLON  = ':'
SPACE  = ' '
COMMA  = ','
PERIOD = '.'
DOT    = '.'
EMDASH = '—'
CHAR_COLON = '&#58;'
LINEBREAK = '\n'

BIBFIELDS = ['author','editor','editora','translator','translatora',
             'authortype','editortype','editoratype','translatortype',
             'translatoratype','origauthor','family','familyi',
             'given','giveni','pubstate',
             'year', 'endyear','origyear','title','subtitle',
             'journaltitle','volume','volumes','number','pages'
             'edition','doi','series','language', 'type',
             'publisher','origpublisher','urlday','urlmonth','urlyear','url']
NAMES = ['author','editor','editora','translator','translatora','origauthor']
NAMEPART = ['family','familyi','given','giveni']

# ========== ymlファイルの読み込み ==========
def load_yml(file_path):
  bib_contents =[]
  with open(file_path) as f:
    yaml = ruamel.yaml.YAML(typ='safe')
    yml_data = yaml.load(f)
    return yml_data

# ========== formatデータの展開 ==========
def expand_format(field_format,entry_data,listcount,listtotal):
  # print(field_format,entry_data)
  outstr = ''
  for item in field_format:
    if isinstance(item, str):
      if '::' in item: # 出力
        tmp = item.split('::',1)
        match tmp[0]:
          case 'value': # フィールドから値を取得
            outstr += retrieve_value(tmp[1], entry_data)
          case 'text': # テキストの出力
            outstr += print_text(tmp[1])
          case 'delim': # delimは対応する文字列に置き換え
            outstr += str(globals()[tmp[1]])
          case 'punct': # ユニット区切りの処理
            outstr += handle_punct(tmp[1])
          case 'url': # URL
            outstr += handle_url(tmp[1])
          case _:
            # print("hogehoge",tmp[0])
            pass
      elif isinstance(entry_data,list): # name リストの場合の処理
        listcount = 1
        listtotal = len(entry_data)
        name_format = field_format.get(item)
        for name_item in entry_data:
          outstr += expand_format(name_format,name_item,listcount,listtotal)
          listcount += 1
      else:
        if entry_data.get(item):
          field_data = entry_data.get(item)
          if isinstance(field_data,str):
            outstr += field_data
          else:
            outstr += expand_format(field_format,field_data,listcount,len(field_data))
    elif isinstance(item, list):
      if 'cond::' in item[0]:
        outstr += handle_cond(item, entry_data,listcount, listtotal)
    else:
      if isinstance(item, dict):
        #  print('dict',item.items())
         outstr = expand_format(dict(item.items()),entry_data,listcount,listtotal)
      else:
        print('list',item)
        outstr = expand_format(item,entry_data,listcount, listtotal)

  # outstr = str(outstr)
  return outstr


def handle_field():
  pass

# value:: の処理
def retrieve_value(value_str, entry_data):
  field_value = ''
  outstr = ''

  if '::' in value_str: # 書式設定がある場合
    field_value = entry_data.get(value_str.split('::')[0])
    if type(field_value) == CommentedSeq:
      field_value=field_value[0]
    outstr += '\\'+str(value_str.split('::')[1])+"{"
    outstr += str(field_value).strip()
    outstr += '\\'+str(value_str.split('::')[1])+"}"
  else: # 書式設定なしの場合はそのまま
    field_value = entry_data.get(value_str)
    if type(field_value) == CommentedSeq:
      field_value=field_value[0]
    outstr += str(field_value).strip()
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

def handle_url(url_str): # urlはタグで囲む
  outstr= ''

  match_obj = re.search(r"\[\"(.*?)\"\s*,\s*(.*?)\]",url_str)
  url_content = match_obj[1]
  outstr += "\\url{"+str(url_content)+"\\url}"
  return outstr

def handle_cond(cond_list, entry_data,listcount, listtotal):
  res = ''
  # 複数条件かどうかを確認
  cond_str = cond_list[0].split('::',1)[1] # 「cond::」を削除
  if "&&" in cond_str:
    multi_cond_str = cond_str.split("&&")
    res = ifthenelse(multi_cond_str[0],entry_data,listcount,listtotal) and ifthenelse(multi_cond_str[1],entry_data,listcount,listtotal)
  elif "||" in cond_str:
    multi_cond_str = cond_str.split("||")
    res = ifthenelse(multi_cond_str[0],entry_data,listcount,listtotal) or ifthenelse(multi_cond_str[1],entry_data,listcount,listtotal)
  else:
    res = ifthenelse(cond_str,entry_data,listcount,listtotal)

  if res: # 結果が真の場合は次のステップを実施して終了
    return expand_format(cond_list[1],entry_data,listcount,listtotal)
  else:
    if len(cond_list)>2 :
      return expand_format(cond_list[2],entry_data,listcount,listtotal)

# cond関数の処理
def ifthenelse(cond_str,entry_data,listcount,listtotal):
  # 文字列から条件式とパラメタを構成
  cond_function = cond_str.split('[',1)[0]

  param1=param2=''
  match_obj = re.search(r'\[(.*?)\]',cond_str)
  if match_obj:
    param1 = match_obj[1].split(',')[0]
    param2 = match_obj[1].split(',')[1]

  if param1 in locals() :
    param1 = locals()[param1]
  elif param1 in globals() :
    param1 = globals()[param1]
  else:
    if '::' in param1:
      param1 = param1.split('::')[1]
 
  if param2 in locals() :
    param2 = locals()[param2]
  elif param2 in globals() :
      param2 = globals()[param2]
  else:
    if '::' in param2:
      param2 = param2.split('::')[1]

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
      if param2 =='true' and param1 in entry_data:
        return True
      elif param2 =='false' and param1 not in entry_data:
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
    print("\\bibitem{"+item[0]+"}", bib_str)


# メインの処理

# 文献データ
# bib_contents = bbl.load_bbl('../jpa-style.bbl')
yaml = ruamel.yaml.YAML(typ='safe')
bib_data = load_yml('../yaml/test.yml')
# bib_data = bbl.bbl_to_yml(bib_contents)

# 文献リストの書式
yaml = ruamel.yaml.YAML(typ='safe')
bib_yml = load_yml('../yaml/jjpsy.yml')

# 変数を処理
bib_variables = bib_yml['constants']
for key, value in bib_variables.items():
  exec("%s = %s" % (key,value)) # keyの値を変数名，valueを変数値として処理

# ネームリストを処理
bib_names = bib_yml['names']

bib_list = [] # 最終的な変換結果を入れるためのリスト
cite_key = '' # 引用キー
# 文献ファイル全体のデータ：bib_data
# 対象の文献情報全体：entry_data
# 特定フィールドのデータ:field_data
# 特定フィールドのキー:field_key
# 文献タイプの書式情報：driver_format
# 特定フィールドの書式情報：field_format

for entry_data in bib_data:

  bib_item = None # 変換後の文献リスト項目

  if not entry_data.get('skip'): # skipしないエントリの場合のみ
    bib_item = ''

    # entryの言語を調べ，言語が指定されていればそちらのdriverを選択
    if 'language' in entry_data:
      entry_language = entry_data.get('language')[0]
      bib_driver = bib_yml['driver'].get(entry_language)
    else:
      bib_driver = bib_yml['driver'].get('other')

    # # 文献タイプ（article, book, etc.）の書式を取得
    driver_format = bib_driver.get(entry_data['entrytype'])

    if driver_format: # articleやbookなどの処理
      for field_format in driver_format: # 順番にフィールドを処理
        bib_item += expand_format(field_format, entry_data,0,0)
  print(bib_item)
  if bib_item:
    bib_list.append(bib_item)
# export_latex(bib_list)
