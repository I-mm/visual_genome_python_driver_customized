
import json
import requests
from os.path import dirname, realpath, join
from visual_genome.models import (Image, Object, Attribute, Relationship,
                                  Region, Graph, QA, QAObject, Synset)

requests.adapters.DEFAULT_RETRIES = 5

def get_data_dir():
    """
    Get the local directory where the Visual Genome data is locally stored.
    """
    data_dir = join(dirname(realpath('__file__')), 'data')
    return data_dir


def retrieve_data(request):
    """
    Helper Method used to get all data from request string.
    """
    url = 'http://visualgenome.org'
    try:
        s = requests.session()
        s.keep_alive = False
        data_1 = s.get(url + request)
        # data_1 = requests.get(url + request)
    except:
        print 'Not Found'
        return {'detail': 'Not found.'}
    data = data_1.json()

    # connection = httplib.HTTPSConnection("visualgenome.org", '443')
    # connection.request("GET", request)
    # response = connection.getresponse()
    # jsonString = response.read()
    # data = json.loads(json_string)
    return data


def parse_synset(canon):
    """
    Helper to Extract Synset from canon object.
    """
    if len(canon) == 0:
        return None
    return Synset(canon[0]['synset_name'], canon[0]['synset_definition'])


def parse_graph(data, image):
    """
    Helper to parse a Graph object from API data.
    """
    objects = []
    object_map = {}
    relationships = []
    attributes = []
    # Create the Objects
    for obj in data['bounding_boxes']:
        names = []
        synsets = []
        for bbx_obj in obj['boxed_objects']:
            names.append(bbx_obj['name'])
            synsets.append(parse_synset(bbx_obj['object_canon']))
            object_ = Object(obj['id'], obj['x'], obj['y'], obj[
                             'width'], obj['height'], names, synsets)
            object_map[obj['id']] = object_
        objects.append(object_)
    # Create the Relationships
    for rel in data['relationships']:
        relationships.append(Relationship(rel['id'],
                                          object_map[rel['subject']],
                                          rel['predicate'],
                                          object_map[rel['object']],
                                          parse_synset(
                                          rel['relationship_canon'])))
    # Create the Attributes
    for atr in data['attributes']:
        attributes.append(Attribute(atr['id'], object_map[atr['subject']],
                                    atr['attribute'],
                                    parse_synset(atr['attribute_canon'])))
    return Graph(image, objects, relationships, attributes)


def parse_image_data(data):
    """
    Helper to parse the image data for one image.
    """
    img_id = data['id'] if 'id' in data else data['image_id']
    url = data['url']
    width = data['width']
    height = data['height']
    coco_id = data['coco_id']
    flickr_id = data['flickr_id']
    image = Image(img_id, url, width, height, coco_id, flickr_id)
    return image

def parse_objects(data, image):
    """
    Helper to parse the obejct data for one Object. => objects
    Objects.
      id         int
      x          int
      y          int
      width      int
      height     int
      names      string array
      synsets    Synset array
      image      image object
    """
    objects = []
    for info in data:
        objects.append(parse_object(info, image))
    return objects

def parse_object(info, image):
    """
    Helper to parse the obejct data for one Object.
    Objects.
      id         int
      x          int
      y          int
      width      int
      height     int
      names      string array
      synsets    Synset array
      image      image object
    """
    if 'names' in info:
        return Object(info['object_id'], info['x'], info['y'], info['w'], info['h'], info['names'], info['synsets'], image)
    else:
        return Object(info['object_id'], info['x'], info['y'], info['w'], info['h'], info['name'], info['synsets'], image)



def parse_relationships(data, image):
    """
    Relationships. Ex, 'man - jumping over - fire hydrant'.
        subject    int
        predicate  string
        object     int
        rel_canon  Synset
    """
    #     def __init__(self, id, subject, predicate, object, synset):

    relationships = []
    for info in data:
        relationships.append(Relationship(info['relationship_id'], parse_object(info['subject'], image), info['predicate'], parse_object(info['object'], image), info['synsets'], image))
    return relationships

def parse_attributes(data, image):

    #
    # def __init__(self, id, subject, attribute, synset):
    #     self.id = id
    #     self.subject = subject
    #     self.attribute = attribute
    #     self.synset = synset
    attributes = []
    for info in data:
        attributes.append(parse_attribute(info, image))
    return attributes

def parse_attribute(info, image):
    if 'attributes' in info:
        return Attribute(info['object_id'], parse_object(info, image), info['attributes'], info['synsets'])
    else:
        return Attribute(info['object_id'], parse_object(info, image), [], info['synsets'])




def parse_region_descriptions(data, image):
    """
    Helper to parse region descriptions.
    """
    if len(data) == 0:
        return []

    regions = []
    if 'region_id' in data[0]:
        region_id_key = 'region_id'
    else:
        region_id_key = 'id'
    for info in data:
        regions.append(Region(info[region_id_key], image, info['phrase'],
                              info['x'], info['y'], info['width'],
                              info['height']))
    return regions


def parse_QA(data, image_map):
    """
    Helper to parse a list of question answers.
    """
    qas = []
    for info in data:
        qos = []
        aos = []
        if 'question_objects' in info:
            for qo in info['question_objects']:
                synset = Synset(qo['synset_name'], qo['synset_definition'])
                qos.append(QAObject(qo['entity_idx_start'], qo[
                           'entity_idx_end'], qo['entity_name'], synset))
        if 'answer_objects' in info:
            for ao in info['answer_objects']:
                synset = Synset(ao['synset_name'], ao['synset_definition'])
                aos.append(QAObject(ao['entity_idx_start'], ao[
                           'entity_idx_end'], ao['entity_name'], synset))
        qas.append(QA(info['qa_id'], image_map[info['image_id']],
                      info['question'], info['answer'], qos, aos))
    return qas
