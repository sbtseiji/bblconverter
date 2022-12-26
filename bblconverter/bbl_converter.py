from bbl_reader import load_bbl
from bbl_reader import bbl_to_yml
from bbl_parser import bib_formatter
from export_tex import export_tex
from export_markdown import export_markdown
from export_docx import export_docx
import bbl_parser
import argparse
import ruamel.yaml
import gettext
import os
import sys

def load_yml(file_path):
  bib_contents =[]
  with open(file_path) as f:
    yaml = ruamel.yaml.YAML(typ='safe')
    yml_data = yaml.load(f)
    return yml_data

def init_translation():
    # 翻訳ファイルを配置するディレクトリ
    path_to_locale_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '../locale'
        )
    )

    # 翻訳用クラスの設定
    translater = gettext.translation(
        'messages',                   # domain: 辞書ファイルの名前
        localedir=path_to_locale_dir, # 辞書ファイル配置ディレクトリ
        languages=['ja_JP'],          # 翻訳に使用する言語
        fallback=True                 # .moファイルが見つからなかった時は未翻訳の文字列を出力
    )

    # Pythonの組み込みグローバル領域に_という関数を束縛する
    translater.install()


def main():
  parser =  argparse.ArgumentParser(
            prog='bblconverter', # プログラム名
            usage='bblconverter --infile inputfile --yaml format yaml --outfile outputfile --bibitem false', # プログラムの利用方法
            description='The bibliographic information in the .bbl or .yml file specified by --infile is converted into a bibliographic list according to the format specified by --yaml, and export it as a latex, markdown, or docx file.', # 引数のヘルプの前に表示
            add_help=True, 
            )
  parser.add_argument('-i', '--infile',default='', type= str, help = 'File path of the input file. Either .bbl or .yml')
  parser.add_argument('-o', '--outfile',default='', type= str, help = 'File path of the output file. Either .tex, .md, or .docx')
  parser.add_argument('-y', '--yaml',default='', type= str, help = 'File path of the bibliography style yaml file.')
  parser.add_argument('-b', '--bibitem',default=False, action= 'store_true', help = 'Switch whether the bibliography should be in bibitem format when the output format is .tex.')

  args = parser.parse_args()
  yaml = ruamel.yaml.YAML()
  biblist =[]
  bbl_yaml =''
  format_yaml = ''
  out_path = args.outfile
  out_format = 'tex'
  bibitem_mode = args.bibitem

  ## 文献データの読み込み
  if args.infile.endswith('.bbl'):
    bbl_data = load_bbl(args.infile)
    bbl_yaml = bbl_to_yml(bbl_data)
  elif args.infile.endswith('.yml') or args.infile.endswith('.yaml'):
    yaml = ruamel.yaml.YAML()
    bbl_yaml = load_yml(args.infile)
  else:
    print(_('Bibliography data must be in bbl or YAML format.'))
    sys.exit()

  ## YAMLフォーマットの読み込み
  if args.yaml.endswith('.yml') or args.yaml.endswith('.yaml'):
    format_yaml = load_yml(args.yaml)
  elif args.yaml =='':
    print(_('The Bibliography list format YAML is not specified.'))
    sys.exit()
  else:
    print(_('The Bibliography list format must be in YAML format.'))
    sys.exit()

  ## 文献リストの作成
  biblist = bbl_parser.bib_formatter(bbl_yaml, format_yaml)

  ## 出力先の設定
  if args.outfile.endswith('.tex'):
    export_tex(biblist, bibitem_mode, out_path)
  elif args.outfile.endswith('.md'):
    export_markdown(biblist,out_path)
  elif args.outfile.endswith('.docx'):
    export_docx(biblist,out_path)
  elif args.outfile =='':
    in_path = args.infile.replace('.bbl','').replace('.yml','').replace('.yaml','')
    out_path = in_path+'.tex'
    export_tex(biblist, bibitem_mode, out_path)
  else:
    print(_('The destination file must be .tex, .md, or .docx format.'))
    sys.exit()

if __name__ == '__main__':
  init_translation()
  main()