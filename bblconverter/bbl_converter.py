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


# 対象の文献情報全体：entry_data
# 特定フィールドのデータ:field_data
# 特定フィールドのキー:field_key
# 文献タイプの書式情報：driver_format
# 特定フィールドの書式情報：field_format

# ========== ymlファイルの読み込み ==========
def load_yml(file_path):
  bib_contents =[]
  with open(file_path) as f:
    yaml = ruamel.yaml.YAML(typ='safe')
    yml_data = yaml.load(f)
    return yml_data

# ========== dictデータの展開 ==========
def expand_format(bib_format,bib_data,out,listcount,listtotal):
  outstr = out
  tmp = []
  for item in bib_format:
    if isinstance(item, str):
      tmp = item.split('::',1)
      match tmp[0]:
        case 'value':
          if '::' in tmp[1]: # 書式設定がある場合
            field_value = bib_data.get(tmp[1].split('::')[0])
            if type(field_value) == CommentedSeq:
              field_value=field_value[0]
            outstr += '\\'+str(tmp[1].split('::')[1])+"{"
            outstr += str(field_value).strip()
            outstr += '\\'+str(tmp[1].split('::')[1])+"}"
          else: # 書式設定なしの場合はそのまま
            field_value = bib_data.get(tmp[1])
            if type(field_value) == CommentedSeq:
              field_value=field_value[0]
            outstr += str(field_value).strip()
        case 'text': # textの内容はそのまま
          outstr += str(tmp[1].replace('\"',''))
        case 'delim': # delimは対応する文字列に置き換え
          outstr += str(globals()[tmp[1]])
        case 'punct': # 
          punct_char =tmp[1].replace('\"','')
          outstr = outstr.rstrip(punct_char) # 同じマークが連続しないようにする
          if punct_char =="　": # 全角スペースの場合は空白を削除
            outstr = outstr.rstrip()
          if outstr == outstr.rstrip('?'): # 末尾が?でないならマークを追加
            outstr += punct_char
        case 'url': # urlの場合はタグで囲む
          match_obj = re.search(r"\[\"(.*?)\"\s*,\s*(.*?)\]",tmp[1])
          url_content = expand_format([match_obj[2]],bib_data,match_obj[1],listcount,listtotal)
          outstr += "\\url{"+str(url_content[0])+"\\url}"
        case 'cond':
          # 複数条件かどうかを確認
          cond_list=[]

          if "&&" in tmp[1]:
            cond_list = tmp[1].split("&&")
            res = handle_cond(cond_list[0],bib_data) and handle_cond(cond_list[1],bib_data)
          elif "||" in tmp[1]:
            cond_list = tmp[1].split("||")
            res = handle_cond(cond_list[0],bib_data) or handle_cond(cond_list[1],bib_data)
          else:
            res = handle_cond(tmp[1],bib_data)
          if res: # 結果が真の場合は次のステップを実施して終了
            res = expand_format(bib_format[1],bib_data,outstr,listcount,listtotal)
            outstr = res[0]
            break
          else:
            if len(bib_format)>2 :
              res = expand_format(bib_format[2],bib_data,outstr,listcount,listtotal)
              outstr = res[0]
            break
        case 'count':
          listcount += int(tmp[1])
        case _:
          pass
    else:
      if isinstance(item, dict):
        res = expand_format(list(item.items()),bib_data,outstr,listcount,listtotal)
        outstr = res[0]
      else:
        res = expand_format(item,bib_data,outstr,listcount,listtotal)
        outstr = res[0]

  # outstr = str(outstr)
  return [outstr, listcount]

# cond関数の処理
def handle_cond(cond_str,bib_data):
  # 文字列から条件式とパラメタを構成
  cond_function = cond_str.split('[',1)[0]

  param1=param2=''
  match_obj = re.search(r'\[(.*?)\]',cond_str)
  if match_obj:
    param1 = match_obj[1].split(',')[0]
    param2 = match_obj[1].split(',')[1]

  if param1 in globals() :
    param1 = globals()[param1]
  else:
    if '::' in param1:
      param1 = param1.split('::')[1]
  if param2 in globals() :
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
      if param2 =='true' and param1 in bibentry:
        return True
      elif param2 =='false' and param1 not in bibentry:
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
bib_contents = bbl.load_bbl('../jpa-style.bbl')
bib_data = bbl.bbl_to_yml(bib_contents)

# 文献リストの書式
yaml = ruamel.yaml.YAML(typ='safe')
bib_format = load_yml('../yaml/jjpsy.yml')

# 変数を処理
bib_variables = bib_format['constants']
for key, value in bib_variables.items():
  exec("%s = %s" % (key,value)) # keyの値を変数名，valueを変数値として処理

listcount = 0
listtotal = 0

bib_list = [] # 最終的な変換結果を入れるためのリスト
cite_key = '' # 引用キー

for bibentry in bib_data:

  # 条件文なら条件文の処理
  # テキストなら出力
  # フィールドデータならキーで値を取得して処理
  def begin_with_cond(bib_format,bib_data,out,listcount,listtotal): # 最初に条件文がある場合の処理
    res = expand_format(field.get(item),bibentry,res_str,listcount,listtotal)
    return res

  # cite_key = bibentry.get('language')[0]
  # bibentryの言語を調べ，言語が指定されていればそちらのフォーマットを選択
  if not bibentry.get('skip'): # skipしないエントリの場合のみ
    if 'language' in bibentry:
      biblanguage = bibentry.get('language')[0]
      bib_driver = bib_format['driver'].get(biblanguage)
    else:
      bib_driver = bib_format['driver'].get('other')


    # # 文献タイプ（article, book, etc.）の定義
    format_def = bib_driver.get(bibentry['entrytype'])
    formatted_list =[] # yamlの変換結果を入れるためのリスト

    if format_def:
      for field in format_def:
        if not isinstance(field,dict): # 条件式や文字列などの場合
          print(field)
          if field.startswith('cond::'): # 条件式の場合
            res = handle_cond(field.split('::')[1],bibentry)
            print(res)
          else: # 文字列の場合
            pass
        else:
          for item in field:
            res_str = ''
            if isinstance(bibentry.get(item),list):
              listcount = 1
              listtotal = len(bibentry.get(item))

              for listitem in bibentry.get(item):
                res = expand_format(field.get(item),listitem,res_str,listcount,listtotal)
                res_str = res[0]
                listcount = res[1]

            else:
              listcount = 1
              res = expand_format(field.get(item),bibentry,res_str,listcount,listtotal)
              res_str = res[0]
            
          formatted_list.append(res_str)


    res_entry = "".join(formatted_list)
    if res_entry:
      bib_list.append([bibentry.get('entry'), res_entry])

export_latex(bib_list)
