import xml.etree.cElementTree as ET
import pprint
import re

#function to check for certain patterns in tag key values
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    if element.tag == "tag":
        ln = lower.search(element.attrib['k'])
        lcn = lower_colon.search(element.attrib['k'])
        pcn = problemchars.search(element.attrib['k'])
        if(ln):
            keys['lower'] += 1
        elif(lcn):
            keys['lower_colon'] += 1
        elif(pcn):
            keys['problemchars'] += 1
        else:
            keys['other'] += 1
    return keys

def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys