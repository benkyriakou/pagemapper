# pagemapper

A simple script to map values from HTML pages to a CSV.

It has two basic modes - single value mode, which pulls the text of all elements matching an XPath selector into a spreadsheet, and row mode which pulls rows of values from each element matching the row selector in the config file according to a mapping.

In single value mode, you can do something like this:

```bash
python3 pagemapper.py --url="https://theguardian.com" --xpath="//h1"
```

This will pull the values of all `<h1>` elements into a CSV file.

In row mode, you can pull more complicated data. See the results of:

```bash
python3 pagemapper.py --url="https://theguardian.com" --config="sample-config.json" --noempty
```

This pulls the title and URL of all article teasers into a CSV.

To get set up, run:

```bash
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

To see other options for the script, run `python pagemapper.py -h`.
