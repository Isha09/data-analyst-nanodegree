import string
import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = "austin_sample.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
default_tag_type = 'regular'

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

#Function to add speed unit when missing
def add_speed_unit(speed):
    unit = speed.split(' ')
    if unit[-1] == 'mph':
        return speed
    else:
        return speed + " mph"

#Function to update street names, phone, direction, state, speed before loading to csv files
def clean_data(element, elem_child):
    tag_data = {}
    tag_data['id'] = element.attrib['id']
    if LOWER_COLON.search(elem_child.attrib['k'].lower()):
        tag_data['type'] = elem_child.attrib['k'].split(':',1)[0]
        tag_data['key'] = elem_child.attrib['k'].split(':',1)[1]
        tag_data['value'] = elem_child.attrib['v']
    else:
        tag_data['key'] = elem_child.attrib['k']
        tag_data['value'] = elem_child.attrib['v']
        tag_data['type'] = default_tag_type
    
    #update street names
    if is_street_name(elem_child):
        tag_data['value'] = update_street_name(elem_child.attrib['v'])
     
    #change format of phone number
    if is_phone(elem_child):
        tag_data['value'] = update_phone(elem_child.attrib['v'])
        
    #Update TX, tx , Texas etc to common state code
    if (elem_child.attrib['k'] == "addr:state"):
        tag_data['value'] = 'TX'
        
    #update directions    
    if ((elem_child.attrib['k'] == "tiger:name_direction_suffix") | (elem_child.attrib['k'] == "tiger:name_direction_prefix")):
        tag_data['value'] = elem_child.attrib['v']
        if 'N' in tag_data['value']:
            tag_data['value'] = tag_data['value'].replace('N','North')
        if 'E' in tag_data['value']:
            tag_data['value'] = tag_data['value'].replace('E','East')
        if 'W' in tag_data['value']:
            tag_data['value'] = tag_data['value'].replace('W','West')
        if 'S' in tag_data['value']:
            tag_data['value'] = tag_data['value'].replace('S','South')
            
    #update speed units            
    if(elem_child.attrib['k'] == "maxspeed"):
        tag_data['value'] = add_speed_unit(elem_child.attrib['v'])
            
    return tag_data
    


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    # YOUR CODE HERE
    if element.tag == 'node':
        for attrib in element.attrib:
            if attrib in NODE_FIELDS:
                node_attribs[attrib] = element.attrib[attrib]
                
        for child in element.iter():
            if child.tag == 'tag':
                if problem_chars.search(child.attrib['k']):
                    continue
                else:
                    new_data = clean_data(element, child)
                    if new_data:
                        tags.append(new_data)
        return {'node': node_attribs, 'node_tags': tags}
        
    elif element.tag == 'way':
        for attrib in element.attrib:
            if attrib in WAY_FIELDS:
                way_attribs[attrib] = element.attrib[attrib]
                
        position = 0
        for child in element.iter():   
            if child.tag == 'tag':
                if problem_chars.search(child.attrib['k']):
                    continue
                else:
                    new_data = clean_data(element, child)
                    if new_data:
                        tags.append(new_data)
            elif child.tag == 'nd':
                way_node = {}
                way_node['id'] = element.attrib['id']
                way_node['node_id'] = child.attrib['ref']
                way_node['position'] = position
                position += 1
                way_nodes.append(way_node)
                
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)