#function to calculate number of times a tag has appeared

import xml.etree.cElementTree as ET
import pprint

def count_tags(filename):
    tree = ET.parse(filename)
    d = dict()
    for elem in tree.iter():
        if elem.tag in d:
            d[elem.tag] += 1
        else:
            d[elem.tag] = 1
    return d