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

# ========== bibエントリクラス ==========
class BibEntry:
  def __init__(self):
    self.reset()
  def reset(self):
    self.listcount = 0
    self.listtotal = 1
    self.entry_data = ''

# ========== ymlファイルの読み込み ==========
def load_yml(file_path):
  bib_contents =[]
  with open(file_path) as f:
    yaml = ruamel.yaml.YAML(typ='safe')
    yml_data = yaml.load(f)
    return yml_data

# ========== formatデータの展開 ==========
def format_field_data(field_format, bib_entry): 
  # print(field_format,bib_entry)

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
    case 'url': # URL
      return handle_url(cont_value)
    case _:
      # print("hogehoge",tmp[0])
      return

# value:: の処理
def retrieve_value(field_key, entry_data):
  outstr = ''
  field_value = ''

  if '::' in field_key: # 書式設定がある場合
    (field_key, field_style) = field_key.split('::',1)
    field_value = entry_data.get(field_key)
    if isinstance(field_value, list):
      field_value=field_value[0]
    outstr += '\\'+str(field_style)+"{"
    outstr += str(field_value).strip()
    outstr += '\\'+str(field_style)+"}"
  else: # 書式設定なしの場合はそのまま
    field_value = entry_data.get(field_key)
    if isinstance(field_value, list):
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

def handle_cond(cond_list, bib_entry):
  res = ''
  # 複数条件かどうかを確認
  cond_str = cond_list[0].split('::',1)[1] # 「cond::」を削除
  # print('条件式', cond_str)

  if "&&" in cond_str:
    multi_cond_str = cond_str.split("&&")
    res = ifthenelse(multi_cond_str[0],bib_entry) and ifthenelse(multi_cond_str[1],bib_entry)
  elif "||" in cond_str:
    multi_cond_str = cond_str.split("||")
    res = ifthenelse(multi_cond_str[0],bib_entry) or ifthenelse(multi_cond_str[1],bib_entry)
  else:
    res = ifthenelse(cond_str,bib_entry)
 
  if res: # 結果が真の場合は次のステップを実施して終了
    # print('true:', cond_list[1])
    return expand_format(cond_list[1],bib_entry)
  else:
    # print('False')
    if len(cond_list)>2 :
      return expand_format(cond_list[2],bib_entry)

def conditional(cond_list, bib_entry):
  # print("cond_list: ",cond_list)
  res = ''
  # 複数条件かどうかを確認
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
    return cond_list[1]
  else:
    if len(cond_list)>2 :
      # print("false: ", cond_list[2])
      return cond_list[2]


# cond関数の処理
def ifthenelse(cond_str,bib_entry):
  # 文字列から条件式とパラメタを構成
  cond_function = cond_str.split('[',1)[0]

  listcount = bib_entry.listcount
  listtotal = bib_entry.listtotal

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
      if param2 =='true' and param1 in bib_entry.entry_data:
        return True
      elif param2 =='false' and param1 not in bib_entry.entry_data:
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

for entry_data in bib_data:
  bib_item = ['',''] # 変換後の文献リスト項目

  if not entry_data.get('skip'): # skipしないエントリの場合のみ
    bib_item[0] = entry_data.get('entry')

    bib_entry = BibEntry() # エントリクラスの作成
    bib_entry.field_data = entry_data
    bib_entry.entry_data = entry_data

    # entryの言語を調べ，言語が指定されていればそちらのdriverを選択
    if 'language' in entry_data:
      entry_language = entry_data.get('language')[0]
      bib_driver = bib_yml['driver'].get(entry_language)
    else:
      bib_driver = bib_yml['driver'].get('other')

    # 文献タイプ（article, book, etc.）の書式を取得
    driver_format = bib_driver.get(bib_entry.entry_data['entrytype'])
    # print('bib_driver: ', driver_format)

    if driver_format: # articleやbookなどの処理
      for field_format in driver_format: # 順番にフィールドを処理
        field_key = '' # フィールドキー
        formatter = [] # フィールド内容のフォーマット

        while isinstance(field_format,list): # 条件分岐を処理
          field_format = conditional(field_format,bib_entry)
        
        if field_format:
          field_key = list(field_format.keys())[0] # フィールドを取得
          field_format = field_format.get(field_key) # そのフィールドの書式を設定
          
          if field_key in NAMES: # nameリストの処理
            if bib_entry.entry_data.get(field_key):
              bib_entry.listtotal = len(bib_entry.entry_data.get(field_key))
              for i in range(1,bib_entry.listtotal+1):
                bib_entry.listcount = i
                for format_item in field_format:
                  while isinstance(format_item, list) and "cond::" in format_item[0]:
                    format_item = conditional(format_item, bib_entry)
                  formatter.append(format_item)
          else:
            for format_item in field_format:
              while isinstance(format_item, list) and "cond::" in format_item[0]:
                format_item = conditional(format_item, bib_entry)
              if format_item:
                formatter.append(format_item)

          if formatter:
          # 取り出したキーとフォーマットで文献項目を作成
            if field_key in NAMES: # nameフィールドの場合
              name_list = bib_entry.entry_data.get(field_key)
              for i in range(len(name_list)):
                format_list = formatter[i]
                name_data = name_list[i]
                for i in format_list:
                  bib_item[1] += format_field_data(i, name_data)
            else:
              if isinstance(formatter[0],list): # フォーマットが入れ子リストになっている場合は展開
                formatter = sum(formatter,[])
              for i in formatter:
                bib_item[1] += format_field_data(i, bib_entry.entry_data)

    print(bib_item)




#     print(bib_item)
#   if bib_item:
#     bib_list.append(bib_item)
# export_latex(bib_list)
