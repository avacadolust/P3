
# coding: utf-8

# ### Process Data
# ### Look at sample data

# In[1]:

import xml.etree.ElementTree as ET  # Use cElementTree or lxml if too slow

OSM_FILE = "leeds.osm"  # Replace this with your osm file
SAMPLE_FILE = "sample.osm"

k = 10 # Parameter: take every k-th top level element

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag

    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


with open(SAMPLE_FILE, 'wb') as output:
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write('<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write('</osm>')


# * explore common tags provided by users
# * explore essoteric "ways" if any exist
# * explore incomplete street names and fix
# * source known postal codes for leeds city area
# * common amenities
# * expletives and swearwords
# 

# In[155]:

get_ipython().magic('pdb')


# In[2]:

import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
from collections import defaultdict


# ### Audit Street Names
# 
# Street names did not tend to be abbreviated. Some misspellings were fixed.

# In[12]:

osmfile = 'leeds.osm'

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

mapping = { "St": "Street",
            "St.": "Street",
           "Rd.": "Road",
           "Ave": "Avenue",
           "Ave.": "Avenue",
           "Avenueue": "Avenue"
            }
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
addr = re.compile(r'addr:')
doubled_colon = re.compile(r':')

def update_name(name, mapping):
    for incorrect_value, correct in mapping.items():
        if re.search(incorrect_value, name):
            name = re.sub(incorrect_value, correct, name, count=1)
            return name

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

def test():
    st_types = audit(osmfile)
    #print pprint.pprint(st_types.keys())
    better_names = {}
    for st_type, ways in st_types.iteritems():
            for name in ways:
                better_name = update_name(name, mapping)
                if better_name:
                    better_names[name]=[better_name]
    print len(better_names)
    return better_names
    

test()


# ### Audit postcodes
# 
# Postcodes beginning 'BD have not been makred incorrect as there are s few from Bradford city, the neighbouring city to the the West.
# 
# Postcodes have been audited againstr a list retrieved from here.
# 
# http://www.postcodearea.co.uk/postaltowns/leeds/
# 
# The remnaining postcodes sampled were found in this database, but marked as inactive. I chose to keep them for lack of a better replacement. The first portion eg. 'LS10' can still be used.

# In[13]:

import csv

OSMFILE = "leeds.osm"
postcode_pattern = re.compile(r'LS')
postcode_pattern_lower = re.compile(r'ls')

def get_standard_postcodes(postcode_csv):
    postcode_list=[]
    with open(postcode_csv, 'r') as f:
        read = csv.reader(f)
        f.next()
        for postcode in read:
            postcode_list.append(postcode[0])
        print "postcode list 0",postcode_list[0]
    return postcode_list

def is_postcode_element(elem):
    return (elem.attrib['k'] == "addr:postcode")

def is_bradford(elem):
    return re.match(r'BD',elem)

def audit_postcodes(osm_file, postcode_csv):
    number_of_postcodes = 0
    lower_case_postcodes = 0
    postcode_list = get_standard_postcodes(postcode_csv)
    print 'postcode list =',len(postcode_list), '\n'
    osm_file = open(OSMFILE, "r")
    non_standard_postcodes = set()
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_postcode_element(tag):
                    number_of_postcodes +=1

                    if tag.attrib['v'] not in postcode_list:
                        if not is_bradford(tag.attrib['v']):
                            non_standard_postcodes.add(tag.attrib['v'])
                    if re.match(postcode_pattern_lower, tag.attrib['v']):
                        lower_case_postcodes +=1
    print 'lower_case_postcodes=',lower_case_postcodes, "number of postcodes=", number_of_postcodes
    return non_standard_postcodes, lower_case_postcodes
    
audit_postcodes(OSMFILE, 'ls_postcodes.csv')


# ### Create JSON File

# In[31]:

import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
from collections import defaultdict

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
addr = re.compile(r'addr:')
doubled_colon = re.compile(r':')
naptan = re.compile(re.compile(r'naptan'))

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
POS = ['lon','lat']

def yes_is_true(x):
    if x =="yes" or x=='Yes' or x=='YES':
        return True
    elif x=="no" or x=="No" or x=="NO"
        return False
    else:
        return x

def shape_element(element):

    node = defaultdict(dict)

    if element.tag == "node" or element.tag == "way" :


        node['type']=element.tag
        node['pos']=[0,0]
        node['node_refs']=[]
        # YOUR CODE HERE            
        for key, value in element.attrib.items():
            if key in CREATED:
                node['created'][key] = value
            elif key in POS:
                #print '\n', key, 'true'
                if key == 'lat':
                    node['pos'][0]=float(value)
                elif key == 'lon':
                    node['pos'][1]=float(value)
        for child in element.iter():
            #print child.tag, child.attrib
# put all child entries into respective dictionaries
            if child.tag=='tag':
                
                if re.match(addr,child.attrib['k']) and len(re.findall(doubled_colon,child.attrib['k']))<2:
                    node['address']
                    node['address'][re.sub(addr,'',child.attrib['k'])] = yes_is_true(child.attrib['v'])
                else:
                    if re.match(naptan, child.attrib['k']):
                        node['naptan:']
                        node['naptan:'][re.sub(naptan, '',child.attrib['k'])]=yes_is_true(child.attrib['v'])


                    else:    
                        node[child.attrib['k']] = yes_is_true(child.attrib['v'])
                
            if child.tag=='nd':
                node['node_refs'].append(child.attrib['ref'])
                

        if node['pos']==[0,0]:
            del node['pos']

        if node['k']=={}:
            del node['k']
        if node['v']=={}:
            del node['v']
        node = dict(node)

        if node['node_refs']==[]:
            del node['node_refs']        
        return node
    else:
        return None


def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        count =0
        for _, element in ET.iterparse(file_in):
            #print element.tag, element.attrib
            
            count +=1
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")

    return data

def test():
    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.
    data = process_map('leeds.osm', False)
    pprint.pprint(data[-1])

test()

