import re
from bblconverter.export_cleaner import cleaner

out_str = []
def export_markdown(biblist, outfile):
  for bib in biblist:
    res_str = ''.join(bib[1])
    res = cleaner(res_str,'markdown')
    out_str.append(res)
  with open(outfile, mode ='w') as f:
    f.write('\n\n'.join(out_str))

