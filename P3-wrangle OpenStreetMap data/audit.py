import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
PHONENUM = re.compile(r'\+1\s\d{3}\-\d{3}\-\d{4}')


expected = ["street", "avenue", "boulevard", "drive", "court", "place", "expressway", "lane", "road", "way", "bend", 
            "branch", "trail", "parkway", "commons", "circle", "cove", "plaza", "loop", "park", "path", "pass","highway",
            "east", "west", "north", "south", "terrace", "crossing","ridge", "trace", "hollow", "view", "walk", "vista"]

#mapping of street abbreviation
st_mapping = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Rd.": "Road",
            "Ln": "Lane",
            "Dr.":"Drive",
            "Dr" : "Drive",
            "Cv" : "Cove",
            "Rd" : "Road",
            "Tr" : "Trail",
            "Ps" : "Pass",
            "Ct" : "Court",
            "Pl" : "Place",
            "Trl" : "Trail",
            "Cir" : "Circle",
            "Blvd" : "Boulevard"
            }

#function to audit street names
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)    
    if m:
        street_type = m.group()
        if str(street_type[0]).isdigit():
            return
        if street_type.lower() not in expected:
            street_types[street_type].add(street_name)
            
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit_street(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

#function to update street names
def update_street_name(name):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type in st_mapping.keys():
            new_name = re.sub(street_type_re, st_mapping[street_type], name)
            return new_name
        else:
            return name

#functions to audit phone numbers
def is_phone(elem):
    return ((elem.attrib['k'] == "phone") | (elem.attrib['k'] == "contact:phone"))


def isvalid_ph(phone_number):
    m = PHONENUM.match(phone_number)
    if m is None:
        return phone_number
    else:
        pass
       
        

def audit_phone(osmfile):
    osm_file = open(osmfile, "r")
    postcode_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_phone(tag):
                    if isvalid_ph(tag.attrib['v']):
                        print tag.attrib['v']          
    osm_file.close()
    
    
#function to format phone numbers as '+1 999-999-9999' 
def update_phone(phone_num):
    m = PHONENUM.match(phone_num)
    
    if m is None:
        #remove brackets
        if "(" in phone_num or ")" in phone_num:
            phone_num = re.sub("[()]", "", phone_num)
        #remove hyphen
        if "-" in phone_num:
            phone_num = re.sub("-", "", phone_num)
        #remove all spaces
        if " " in phone_num:
            phone_num = re.sub(" ", "", phone_num)
        #format phone 
        if re.match(r'\+1\d{10}', phone_num) is not None:
            phone_num = phone_num[:2] + " " + phone_num[2:5] + "-" + phone_num[5:8] + "-" + phone_num[8:]
        # add '+' and format phone number
        elif re.match(r'\d{11}', phone_num) is not None:
            phone_num = "+" + phone_num[:1] + " " + phone_num[1:4] + "-" + phone_num[4:7] + "-" + phone_num[7:]
        #add country code and format phone number
        elif re.match(r'\d{10}', phone_num) is not None:
            phone_num = "+1" + " " + phone_num[:3] + "-" + phone_num[3:6] + "-" + phone_num[6:]
        #checking if number of digits are less than 10
        elif sum(d.isdigit() for d in phone_num) < 10:
            return None
        
    return phone_num

#function to audit direction
def is_direction(elem):
    return ((elem.attrib['k'] == "tiger:name_direction_prefix") | (elem.attrib['k'] == "tiger:name_direction_suffix"))

def audit_direction(osmfile):
    osm_file = open(osmfile, "r")
    postcode_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_direction(tag):
                    print tag.attrib['v']
                                  
    osm_file.close()

#function to audit postcodes
def is_post_code(elem):
    return ((elem.attrib['k'] == "tiger:zip_left") | (elem.attrib['k'] == "tiger:zip_right") | (elem.attrib['k'] == "addr:postcode"))

def audit_postcode(osmfile):
    osm_file = open(osmfile, "r")
    postcode_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_post_code(tag):
                    #checking if zipcode is of 5 digit
                    if ((len(tag.attrib['v']) == 5) & (tag.attrib['v'].isdigit())):
                        continue
                    else:
                        print tag.attrib['v']             
    osm_file.close()