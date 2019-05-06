import re
import csv
import json
import requests
import argparse
import logging
from lxml import html
from requests.exceptions import MissingSchema

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(description='Retrieve parts of a webpage using XPath expressions')

parser.add_argument('--url', help='The URL to query', type=str)
parser.add_argument('--xpath', help='The XPath expression to use')
parser.add_argument('--noempty', help='Exclude empty values', action='store_true')
parser.add_argument('--filter', help='A regular expression to filter the values with. Single value mode only', type=str)
parser.add_argument('--outfile', help='The CSV file to write the results to', type=str, default='out.csv')
parser.add_argument('--config-file', help='The configuration file for multi-row output', type=str)

args = parser.parse_args()

# If we don't have rows, we need url and xpath.
if not args.config_file:
    if not args.url or not args.xpath:
        parser.error('If a config file is not supplied, --url and --xpath must be supplied')


def get_value(e):
    """
    Get the value from an element retrieved by an XPath expression.

    This may either be an HTMLElement or an attribute string.

    :param e:
        The element to get the value from.
    :return string:
        The string value from the element.
    """
    if isinstance(e, html.HtmlElement):
        return e.text_content()
    else:
        # Attributes are basically just strings. e.g. //a/@href
        return '{0}'.format(e)


if __name__ == '__main__':
    row_selector = None
    mapping = None

    if args.config_file:
        try:
            with open(args.config_file, 'r', encoding='utf8') as fh:
                config = json.load(fh)
                row_selector = config['row-selector']
                mapping = config['mapping']
        except json.JSONDecodeError as e:
            logging.error('Failed to parse config: {0}'.format(e))
            exit(1)
        except KeyError as e:
            logging.error('Error reading config value {0}'.format(e))
            exit(1)
        except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
            logging.error('Error opening file: {0}'.format(e))
            exit(1)

    try:
        if args.filter:
            # Compile the pattern here so we fail early if it's invalid
            pattern = re.compile(args.filter)
        else:
            pattern = None

        r = requests.get(args.url)
        r.encoding = 'utf8'

        if 199 < r.status_code < 400:
            f = open(args.outfile, 'w', encoding='utf8')
            content = html.fromstring(r.content)

            if row_selector:
                writer = csv.DictWriter(f, dialect='unix', fieldnames=mapping.keys())
                writer.writeheader()

                rows = content.xpath(row_selector)

                for row in rows:
                    skip = False
                    values = {}

                    for label, item_selector in mapping.items():
                        try:
                            v = get_value(row.xpath(item_selector)[0])
                        except IndexError:
                            # No value was found, so set it to an empty string.
                            v = ''

                        if args.noempty and v == '':
                            skip = True
                            break
                        else:
                            values[label] = v

                    if skip:
                        continue

                    writer.writerow(values)
            else:
                elements = content.xpath(args.xpath)
                writer = csv.writer(f, dialect='unix')

                for v in [get_value(e) for e in elements]:
                    if v is not None:
                        if args.noempty and v == '':
                            continue

                        if pattern is not None and re.search(pattern, v):
                            writer.writerow([v])
                        else:
                            writer.writerow([v])

            f.close()
        else:
            logging.warning('Returned status code {0}'.format(r.status_code))
    except MissingSchema:
        logging.error('No URL schema provided')
    except re.error as e:
        logging.error('Error compiling regular expression: {0}'.format(e))
    except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
        logging.error('Error opening file: {0}'.format(e))
    except Exception as e:
        logging.exception('Unknown exception: {0}'.format(repr(e)), exc_info=e)
