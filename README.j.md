[English](README.md)・[日本語](README.j.md)

# bblconverter

> BibLaTeX bblファイルをLaTeX, markdown, docxファイルに変換


## インストール方法

```
pip install git+https://github.com/sbtseiji/bblconverter
```

## 使用方法

```
bblconverter --infile [文献データファイル bblまたはyaml] --outfile [出力先ファイルパス] --yaml [フォーマッターYAML] --bibitem
```

### Options
<dl>
  <dt ><code>-i INFILE, --infile INFILE</code></dt>
  <dd>入力ファイルのファイルパス（<code>.bbl</code>または<code>.yml</code>）。</dd>
  <dt ><code>-o OUTFILE, --outfile OUTFILE</code></dt>
  <dd>出力ファイルのファイルパス（<code>.tex</code>、<code>.md</code>、<code>.docx</code>のいずれか）。出力ファイル名の拡張子によって、変換先の形式が決まります。出力ファイルを指定しない場合、変換結果は入力ファイルと同名で拡張子が.texのファイルに出力されます。</dd>
  <dt ><code>-y YAML, --yaml YAML</code></dt>
  <dd>文献リスト・フォーマッタYAMLのファイルパス。</dd>
  <dt ><code>-b, --bibitem</code></dt>
  <dd>出力形式がLaTeXの場合、書誌事項をbibitem形式で出力するかどうかを切り替えます。このオプションを設定すると、書誌項目はbibitemとして出力されます。指定なしの場合は、プレーンなLaTeX文字列として出力されます。</dd>
</dl>

## 文献リスト・フォーマッタYAML

bblconverterは、YAML形式で作成されたフォーマッタを使って、bblまたはyamlの文献ファイルから文献リストを作成します。フォーマッタのYAMLファイルには、`constants`, `names`, `driver`のセクションが含まれます。

`constants`セクションには、表示する著者名の最大数など、文献リストを作成する際に使用する定数を記載します。各定数は次のように辞書形式で定義してください。使用する定数がない場合は、このセクションは必要ありません。

```
constants:
  maxnames: 20
```

`names` キーには、`author`、`editor` など、BibLaTeXの名前リストに含まれるフィールドをリスト形式で記載します。`driver`には、`article`や`book`など、各文献タイプのフォーマットを記述します。

`driver`の書誌タイプは、BibLaTeXで使用する書誌タイプと同じ名前でなくてはなりません。各書誌タイプのフォーマットは、「`フィールド名: フィールド書式`」という要素で構成されたリストとして記述します。

### フォーマッタの基本

`フィールド名`は、BibLaTeXで使用されているフィールド名と同じでなければなりません。

`フィールド書式`では、以下のコマンドをリスト形式で使用し、フィールドの内容がどのように表示されるべきかを指定します。

<dl>
  <dt ><code>value::フィールド名</code></dt>
  <dd>フィールドの内容を取得し、表示します。</dd>
  <dt ><code>text::"文字列"</code></dt>
  <dd>文字列を表示します。</dd>
  <dt ><code>delim::区切り文字</code></dt>
  <dd>使用できる区切り文字は、<code>COLON</code> (:), <code>SPACE</code> (&nbsp;), <code>COMMA</code> (,), <code>PERIOD</code> (. ), <code>DOT</code> (.), <code>DOTS</code> (&hellip;), <code>EMDASH</code> (&mdash;), <code>NDASH</code> (&ndash;), <code>LINEBREAK</code> (\n)です。</dd>
  <dt ><code>punct::"句読点"</code></dt>
  <dd>句読点として指定された記号は、直前に同じ記号がある場合、重複しないように処理されます。たとえば<code>value::title</code>の後に<code>punct::"."</code>を指定した場合、「my first paper」というタイトルは文献リストでは「my first paper.」と表示され、「my second paper.」というタイトルの場合も、「my second paper..」ではなく「my second paper.」と表示されます。</dd>
</dl>

最小限のYAMLファイルのサンプルは次のようになります。

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

より複雑なフォーマッタの例として、yamlフォルダには日本心理学会の『心理学研究』用の文献リストフォーマットを添付してあります。

### 条件分岐

条件節は`cond::`で始まるキーで示され、以下の形式で使用します。

```
  - - cond::条件節
    - 真の場合の処理
    - 偽の場合の処理
```

フォーマッタでは次の条件節を使用できます。

<dl>
  <dt ><code>cond::ifequal[値1,値2]</code></dt>
  <dd>値1と値2が同じかどうかを確かめます。</dd>
  <dt ><code>cond::ifgreater[値1,値2]</code></dt>
  <dd>値1が値2より大きいかどうかを確かめます。</dd>
  <dt ><code>cond::ifgreatereq[値1,値2]</code></dt>
  <dd>値1が値2以上であるかどうかを確かめます。</dd>
  <dt ><code>cond::ifless[値1,値2]</code></dt>
  <dd>値1が値2より小さいかどうかを確かめます。</dd>
  <dt ><code>cond::iflesseq[値1,値2]</code></dt>
  <dd>値1が値2以下であるかどうかを確かめます。</dd>
  <dt ><code>cond::ifdef[field::フィールド名,true]</code></dt>
  <dd><code>フィールド名</code>の値が定義されているかどうかを確かめます。</dd>
  <dt ><code>cond::ifdef[field::フィールド名,false]</code></dt>
  <dd>フィールド名</code>の値が未定義かどうかを確かめます。</dd>
</dl>

また、`&&`、`||`、`^^`を使って、2つの条件節を組み合わせることもできます。

<dl>
  <dt ><code>&&</code>&nbsp;&nbsp;論理積</dt>
  <dd>(例) <code>cond::ifgreater[listcount,2]&&ifless[listcount,5]</code>(listcountが2より大，かつ，5より小)</dd>
  <dt ><code>||</code>&nbsp;&nbsp;論理和</dt>
  <dd>(例) <code>cond::ifgreater[listcount,2]||ifless[listcount,5]</code>(listcountが2より大，または，5より小)</dd>
  <dt ><code>^^</code>&nbsp;&nbsp;排他的論理和</dt>
  <dd>(例) <code>cond::ifgreater[listtotal,2]^^ifdef[field::title,false]</code>(listtotalが2より大，<code>title</code>フィールドが未定義のいずれか一方のみが真)</dd>
</dl>

なお、条件節では、`listcount`変数と`listtotal`変数を使用することもできます。`listcount`は現在処理中の著者の位置（何番目の著者か）を示し、`listtotal`はそのエントリに含まれる著者名の総数を示します。
