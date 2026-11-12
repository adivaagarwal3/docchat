# docchat

docchat is a command-line chatbot that answers questions about the files in the current folder. The model calls `ls`, `cat`, `grep`, and `calculate` tools to inspect the files before answering.

## Webpage

```
$ cd test_projects/webpage
$ chat
chat> /ls .
Kuchipudi.jpg
README.md
bharatnatyam.html
bharatnatyam.jpeg
index.html
indian_dances.jpeg
kuchipudi.html
style.css
submission.toml
chat> What is this webpage about?
(reply pending: Groq API key not yet configured)
```

From the webpage project I learned how to build a multi-page site with HTML and style it with CSS.

## Markdown compiler

```
$ cd test_projects/markdown_compiler
$ chat
chat> /ls .
README.md
example
markdown_compiler
pyproject.toml
requirements.txt
chat> What markdown features does this compiler support?
(reply pending: Groq API key not yet configured)
```

From the Markdown compiler I learned how to use regular expressions and doctests to turn Markdown into HTML.

## eBay scraper

```
$ cd test_projects/ebay_scraper
$ chat
chat> /ls .
README.md
drill press.csv
drill press.json
ebay-dl.py
garden tools.csv
garden tools.json
mechanical keyboard.csv
mechanical keyboard.json
submission.toml
chat> What data does this scraper collect from eBay?
(reply pending: Groq API key not yet configured)
```

From the eBay scraper I learned how to download web pages and extract structured data from HTML.
