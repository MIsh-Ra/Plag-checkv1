# we_go_crawlin

Crawls LNMIIT DSpace institutional repository and downloads all PDFs.

## Setup
pip install -r requirements.txt

## Run
python3 crawler.py

# or if no tmux
nohup python3 crawler.py > crawler.log 2>&1 &

## Check progress
tail -f crawler.log