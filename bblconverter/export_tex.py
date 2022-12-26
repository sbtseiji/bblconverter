import re
from bblconverter.export_cleaner import cleaner

out_str = []
def export_tex(biblist, bibitem, outfile):
  for bib in biblist:
    res_str = ''.join(bib[1])
    res = cleaner(res_str,'tex')
    if bibitem:
      out_str.append('\\bibitem{'+bib[0]+'} '+res)
      with open(outfile, mode ='w') as f:
        f.write('\n'.join(out_str))

    else:
      out_str.append(res)
      with open(outfile, mode ='w') as f:
        f.write('\n\n'.join(out_str))

