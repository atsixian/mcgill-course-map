import networkx as nx
import jsonlines
import warnings
import re
from pathlib import Path
from functools import partial

warnings.filterwarnings("ignore")

currentdir = Path(__file__).parent
targetpath = currentdir.parent.joinpath('course_data')
files = targetpath.iterdir()

all_courses = currentdir.joinpath('all_courses.jl')


def replace_symbol(lst):
        return [s.replace('-', '\n') for s in lst]


def generate_values(f, key, course_list):

    result = []
    
    # If there's no prereq, return None because we want a 1-1 pair between names and prereqs
    temp = [ f(c.get(key, [])) for c in course_list ]

    if key=='name': # If it's for full names, we don't do anything, just take out the data
        return temp

    # prereqs are lists, so I use this to identify prereqs
    if temp and isinstance(temp[0], list): 
        for l in temp:
            result.append(replace_symbol(l))
    else:
        result = replace_symbol(temp)
    return result

def generate_graph(subject):

    # Get the last part of the link because the prefix is the same
    # For example, we extract "comp-250" from "https://mcgill.ca/study/2019-2020/courses/comp-250",
    # And we replace "-" with "\n" so that we can fit the string inside a node in the final graph(to have a clearer display)
    course_codes = generate_values(lambda x: Path(x).stem, 'link', subject)
    course_names = generate_values(lambda x: x, 'name', subject)

    nodes = [ (code, {'fullname': course_name}) for (code, course_name) in zip(course_codes, course_names) ]

    # Replace spaces '-' in preq course names with "\n" because 
    preqs = generate_values(lambda x: x, 'prereq', subject)

    # Create edges
    edges = []

    for c, plist in zip(course_codes, preqs):
        if plist: # if there's any prereq, create an edge 
            [edges.append((c, p)) for p in plist]

    # Create the complete graph
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    G = G.reverse()
    return G, course_codes


# Create a graph for every subject, store them in a dictionary
GRAPH_DICT = {}

# A dictionary for all courses, format like 
# {
#   'comp202':{'fullname': 'foundations...', 'term': 'xxx', 'link': xxx,}, 
#   'math223': {...(same)}
# }
INFO_DICT = {}

for f in files:
    with jsonlines.open(f) as reader:
        course_info = list(reader.iter(type=dict))
        key = Path(f).stem
        GRAPH_DICT[key], codes = generate_graph(course_info)
        for d in course_info:
            # del d['subject']
            d.pop('prereq', None)
        for (code, otherinfo) in zip(codes, course_info):
            INFO_DICT[code] = otherinfo

with jsonlines.open(all_courses) as reader:
    course_info = list(reader.iter(type=dict))
    BIG_GRAPH = generate_graph(course_info)[0]

def split_course_name(course):
    code_pattern = re.compile('[a-z]{3}\w{1}', re.IGNORECASE)
    num_pattern = re.compile('\d{3}\w*')
    code = code_pattern.search(course)
    number = num_pattern.search(course)
    if code == None or number == None:
       raise ValueError(
           'Invalid input, please follow "subject number" pattern like "COMP 202"(lowercase also works).')
    code = code.group(0)
    number = number.group(0)
    return code, number


def get_graph(graph_type, key):
    if graph_type == 'course':
        key = split_course_name(key)[0]
    try:
        G = GRAPH_DICT[key.upper()]
    except KeyError as e:
        raise KeyError(f"There's no subject called {key}.") from e
    else:
        return G


def get_elements(G, filters=None, include_depth=True):
    max_depth = 0
    def in_filter(key):
        return INFO_DICT[key]['subject'] not in filters

    nodes = G.nodes()
    edges = G.edges()

    # Filter out courses that are from subjects in filters
    # ! Why use != None instead of 
    # if filters:
    # ! Because set(), the empty set will be evaluated to False, but we still want to filter items
    if filters != None:
        nodes = list(filter(in_filter, nodes))
        edges = G.edges(nodes)

    if not include_depth:
        ns = [
            {
                'data': {'id': name, 'label': name}
            } for name in nodes
        ]
    else:
        depth_dictionary, max_depth = calculate_depth(G)
        ns = [
            {
                'data': {'id': name, 'label': name},
                'classes': 'depth_' + str(depth_dictionary[name])
            } for name in nodes
        ]

    es = [
        {
            'data': {'source': src, 'target': tar}
        } for (src, tar) in edges
    ]

    return ns+es

# This function shall return a tuple:
# First element: a dictionary from nodes to depths
# Second element: an integer that gives the maximum depth in this graph.
def calculate_depth(graph):
    nodes = graph.nodes()
    depth_dictionary = dict()
    max_depth = 0

    # Start by assuming that all nodes are leaves. Hence the initial depth of zero.
    for node in nodes:
        depth_dictionary[node] = 0

    # Step one: find all the leaves in this graph.
    # We call a node a "leaf" if and only if that node has no prerequisite.
    # Assuming that NetworkX keeps an adjacency matrix of the edges, the time complexity of this step shall be O(N + E).
    leaves = list(filter(lambda node: len(list(graph.predecessors(node))) == 0, nodes))

    # Step two: For each leaf, perform a BFS and assign depth to each node.
    # Update the depth of a node if the current depth is greater than the previous one.
    # The time complexity of this step shall be O(L * N), where L is the number of leaves and N is the number of nodes.
    for leaf in leaves:
        # To make depth calculations easier, keep track of the parent of each node.
        # Consider using a queue for (potentially) better performance.
        # Elements of this list are tuples in the form (node, child_node).
        nodes_to_visit = list()
        for child in graph.successors(leaf):
            nodes_to_visit.append((leaf, child))

        # Assumption: this graph is acyclic (i.e., it does not contain any cycle.)
        # If the program gets into an infinite loop here, talk to your school's administration.
        while len(nodes_to_visit) > 0:
            current_node, node_to_visit = nodes_to_visit.pop(0)

            depth_dictionary[node_to_visit] = \
                max([depth_dictionary[current_node] + 1, depth_dictionary[node_to_visit]])

            for child in graph.successors(node_to_visit):
                nodes_to_visit.append((node_to_visit, child))

            max_depth = max(max_depth, depth_dictionary[current_node] + 1)

    return depth_dictionary, max_depth


# Define a partial bfs with depth_limit=1, so we can reuse the learning_path function
bfs_tree = partial(nx.bfs_tree, G=BIG_GRAPH, depth_limit=1)
dfs_tree = partial(nx.dfs_tree, G=BIG_GRAPH)


# def learning_path(course, search_method, filters=None):
#     code, number = split_course_name(course)
#     try:
#         path = search_method(source=code.lower() + '\n' + number)
        
#         return get_elements(path, filters)
#     except KeyError as e:
#         raise KeyError(
#             f"There's no course called {course}.") from e

def learning_path(course, search_method, show_prerequisites=False):
    code, number = split_course_name(course)
    try:
        if not show_prerequisites:
            path = search_method(source=code.lower() + '\n' + number)
            return path
        else:
            return get_prerequisite_graph(code.lower() + '\n' + number)
    except KeyError as e:
        raise KeyError(
            f"There's no course called {course}.") from e

def big_picture(subject):
    thegraph = get_graph('overview', subject)
    return get_elements(thegraph)

def subjects_in_graph(G):
    subjects = set()
    for node in G.nodes:
        subjects.add(INFO_DICT[node]['subject'])
    return subjects


def get_prerequisite_graph(query_course_code):
    dependency_graph = nx.DiGraph()

    dependency_graph.add_node(query_course_code)

    prerequisites = list()

    # A list of tuples in the form (course, prerequisite_of_the_course).
    prerequisites_to_visit = list()
    for prerequisite in list(BIG_GRAPH.predecessors(query_course_code)):
        prerequisites_to_visit.append((query_course_code, prerequisite))

    while len(prerequisites_to_visit) > 0:
        required_course, prerequisite = prerequisites_to_visit.pop(-1)
        if prerequisite not in prerequisites:
            prerequisites.append(prerequisite)

            if not dependency_graph.has_node(prerequisite):
                dependency_graph.add_node(prerequisite)

            # Add an edge from the prerequisite to a course that leads to the query.
            for super_prerequisite in list(BIG_GRAPH.predecessors(prerequisite)):
                prerequisites_to_visit.append((prerequisite, super_prerequisite))

        # We are looking at a dependency graph, not a dependency tree.
        # Hence, we shall add the dependency edge even if the more basic course was already on the graph.
        dependency_graph.add_edge(prerequisite, required_course)

    return dependency_graph
