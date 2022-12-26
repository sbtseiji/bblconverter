import re

def cleaner(instr, mode):
  outstr = instr
  outstr = outstr.replace('&#58;',':')
  outstr = re.sub(r'<punct>(.)<punct>(\1)','\g<1>',outstr)
  outstr = re.sub(r'(.)</italic><punct>(\1)',r'</italic>\g<1>',outstr)
  outstr = re.sub(r'(.)</bold><punct>(\1)',r'</bold>\g<1>',outstr)
  outstr = re.sub(r"(.)('+)<punct>(\1)",r'\g<1>\g<2>',outstr)
  outstr = re.sub(r'(.)<punct>(\1)','\g<1>',outstr)
  outstr = re.sub(r'\?<punct>(.)','?',outstr)
  outstr = re.sub(r'<punct>(.)','\g<1>',outstr)

  if mode == 'tex':
    url_str = ''

    # url文字列を避難
    match_obj = re.match(r'.*<url>(.*?)</url>.*', outstr)
    if not match_obj is None:
      url_str= match_obj[1]
    
    # LaTeX 特殊文字の変換
    outstr = re.sub(r'#', r'\\#', outstr)
    outstr = re.sub(r'%', r'\\%', outstr)
    outstr = re.sub(r'~', r'\\textasciitilde', outstr)
    outstr = re.sub(r'_', r'\\_', outstr)
    outstr = re.sub(r'\^', r'\\textasciicircum', outstr)
    outstr = re.sub(r'([^\\])&', r'\g<1>\\&', outstr)

    outstr = re.sub(r'—','---',outstr)
    outstr = re.sub(r'–','--',outstr)
    outstr = re.sub(r'<dots>', r'{\\ldots}', outstr)
    outstr = re.sub(r'<italic>', r'\\textit{', outstr)
    outstr = re.sub(r'</italic>', '}', outstr)
    outstr = re.sub(r'<bold>', r'\\textbf{', outstr)
    outstr = re.sub(r'</bold>', '}', outstr)

    # url文字列を戻す
    outstr = re.sub(r'<url>.*?</url>',r'\\url{'+url_str+'}', outstr)

  elif mode == 'markdown':
    outstr = re.sub(r'—', '&mdash;', outstr)
    outstr = re.sub(r'--', '&ndash;', outstr)
    outstr = re.sub(r'<dots>', r'&hellip;', outstr)
    outstr = re.sub(r'<italic>', '*', outstr)
    outstr = re.sub(r'</italic>', '*', outstr)
    outstr = re.sub(r'<bold>', '**', outstr)
    outstr = re.sub(r'</bold>', '**', outstr)
    outstr = re.sub(r'\\&', '&', outstr)
    outstr = re.sub(r'``', '“', outstr)
    outstr = re.sub(r"''", '”', outstr)
    outstr = re.sub(r'<url>', '', outstr)
    outstr = re.sub(r'</url>', '', outstr)

  elif mode == 'docx':
    outstr = re.sub(r'--', '–', outstr)
    outstr = re.sub(r'<dots>', r'…', outstr)
    outstr = re.sub(r'\\&', '&', outstr)
    outstr = re.sub(r'``', '“', outstr)
    outstr = re.sub(r"''", '”', outstr)
    outstr = re.sub(r'<url>', '', outstr)
    outstr = re.sub(r'</url>', '', outstr)
  return outstr