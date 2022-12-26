[English](README.md)・[日本語](README.j.md)

# bblconverter

> A tool to convert BibLaTeX bbl files to plain LaTeX, markdown, or docx files. 



## How to install

```
pip install git+https://github.com/sbtseiji/bblconverter
```

## Usage

```
bblconverter --infile [your bbl file or yaml bib file] --outfile [destination file path] --yaml [bib formatter yaml] --bibitem
```

### Options
<dl>
  <dt ><code>-i INFILE, --infile INFILE</code></dt>
  <dd>The file path of the input file. Either .bbl or .yml</dd>
  <dt ><code>-o OUTFILE, --outfile OUTFILE</code></dt>
  <dd>File path of the output file. Either .tex, .md, or .docx. The extension of the output file name determines the destination format. If no output file is specified, the conversion result is output to a file with the same name as the input file and a .tex extension.</dd>
  <dt ><code>-y YAML, --yaml YAML</code></dt>
  <dd>File path of the bibliography formatter YAML.</dd>
  <dt ><code>-b, --bibitem</code></dt>
  <dd>Switch whether the bibliography should be in bibitem format when the output format is LaTeX. If this option is set, the bibliography items are output as bibitems. Otherwise, they are output as plain LaTeX strings.</dd>
</dl>

## Bibliography formatter YAML

bblconverter creates a bibliography list from a bbl or yaml bibfile using a bibliography formatter created in YAML format. The bibliography formatter YAML file contains sections for `constants`, `names`, and `driver`. 

The `constants` section contains constants to be used when creating the bibliography list, such as the maximum number of author names to be displayed. Each constant is defined in dictionary format as shown below. If there is no constant to be used, no definition is required.

```
constants:
  maxnames: 20
```

The `names` key contains a list of fields in BibLaTeX's names list, such as `author`, `editor`, and so on. The `driver` describes the format of each bibliography type, such as `article`, `book`.

The bibliography type in `driver` must have the same name as the bibliography type used by BibLaTeX. The format of each bibliography type is described as a list consisting of the elements "`field name: field format`".

### Formatter basics

The `field name` must be the same as the field name used in BibLaTeX.

In `field format`, the following commands can be used in list form to indicate how the field contents should be rendered.

<dl>
  <dt ><code>value::FIELDNAME</code></dt>
  <dd>Retrieves and displays the contents of the field.</dd>
  <dt ><code>text::"STRING"</code></dt>
  <dd>Displays a string.</dd>
  <dt ><code>delim::DELIMITER</code></dt>
  <dd>The delimiters that can be used are <code>COLON</code> (:), <code>SPACE</code> (&nbsp;), <code>COMMA</code> (,), <code>PERIOD</code> (.), <code>DOT</code> (.), <code>DOTS</code> (&hellip;), <code>EMDASH</code> (&mdash;), <code>NDASH</code> (&ndash;), <code>LINEBREAK</code> (\n). </dd>
  <dt ><code>punct::"PUNCTUATION"</code></dt>
  <dd>Symbols specified as punctuation marks are processed so that they do not overlap if the same symbol immediately precedes them. For example, if you specified <code>punct::"."</code> immediately after the <code>value::title</code>, the title "my first paper" will appear as "my first paper." in the bibliography, and the title "my second paper." will also appear as "my second paper.", not "my second paper.."</dd>
</dl>

The minimal YAML file sample will look something like this.

```
names:
  - author
  - editor

driver:
  article:
    - author:
      - value::family
      - text::", "
      - value::giveni
    - year: value::year
    - title: value::title
    - journaltitle: value::journaltitle
    - volume: value::volume
    - pages: value::pages

  book:
    - editor:
      - value::family
      - text::", "
      - value::giveni
    - year: value::year
    - booktitle: value::booktitle
    - publisher: value::publisher
```

As an example of a more complex formatter, attached to the yaml folder is the bibliography format for *The Japanese Journal of Psychology*.

### Conditional

YAML formatter can also perform basic conditional branching. Condition clauses are indicated by keys beginning with `cond::` and are used in the following format: 

```
  - - cond::CONDITIONAL
    - formats when conditional is true
    - formats when conditional is false
```

The condition clauses available in Formatter are:

<dl>
  <dt ><code>cond::ifequal[VALUE1,VALUE2]</code></dt>
  <dd>Check if values 1 and 2 are the same.</dd>
  <dt ><code>cond::ifgreater[VALUE1,VALUE2]</code></dt>
  <dd>Check if value 1 is greater than value 2.</dd>
  <dt ><code>cond::ifgreatereq[VALUE1,VALUE2]</code></dt>
  <dd>Check if value 1 is greater than or equals to value 2.</dd>
  <dt ><code>cond::ifless[VALUE1,VALUE2]</code></dt>
  <dd>Check if value 1 is smaller than value 2.</dd>
  <dt ><code>cond::iflesseq[VALUE1,VALUE2]</code></dt>
  <dd>Check if value 1 is smaller than or equals to value 2.</dd>
  <dt ><code>cond::ifdef[field::FIELDNAME,true]</code></dt>
  <dd>Check if field <code>FIELDNAME</code> is defined.</dd>
  <dt ><code>cond::ifdef[field::FIELDNAME,false]</code></dt>
  <dd>Check if field <code>FIELDNAME</code> is undefined.</dd>
</dl>

You can also combine two conditional clauses using `&&`, `||`, or `^^`.

<dl>
  <dt ><code>&&</code>&nbsp;&nbsp;logical conjunction</dt>
  <dd>(Example) <code>cond::ifgreater[listcount,2]&&ifless[listcount,5]</code>(listcount is greater than 2 and smaller than 5)</dd>
  <dt ><code>||</code>&nbsp;&nbsp;logical disjunction</dt>
  <dd>(Example) <code>cond::ifgreater[listcount,2]||ifless[listcount,5]</code>(listcount is greater than 2 or smaller than 5)</dd>
  <dt ><code>^^</code>&nbsp;&nbsp;exclusive disjunction</dt>
  <dd>(Example) <code>cond::ifgreater[listtotal,2]^^ifdef[field::title,false]</code>(either listtotal is greater than 2 or field <code>title</code> is not defined, not both.)</dd>
</dl>

You can also use the variables `listcount` and `listtotal` in the condition clause. The variable `listcount` is the position of the author currently being processed, and `listtotal` is the total number of author names listed in the entry.

