from pathlib import Path
from graph_generator import graph

import networkx as nx
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash
from dash.dependencies import Input, Output, State
import re
import csv
from SecretColors import Palette
from copy import deepcopy

app = dash.Dash(__name__, external_stylesheets=[
                dbc.themes.CYBORG, "https://use.fontawesome.com/releases/v5.7.0/css/all.css"])
app.config.suppress_callback_exceptions = True
app.scripts.config.serve_locally=True
server = app.server
def get_list(file):
    with open(file, 'r') as f:
        reader = csv.reader(f)
        result = list(reader)[0]
        return result


CURRENT_PATH = Path(__file__).parent
filenames = ['names.csv', 'links.csv', 'codes.csv']
files = [ Path.joinpath(CURRENT_PATH, f) for f in filenames]

#recover data from csv files
[NAMES, LINKS, CODES] = [get_list(f)
                         for f in files]
infos = graph.INFO_DICT


radioitems = dbc.FormGroup(
    [
        dbc.RadioItems(
            id='radio_items',
            options=[
                {'label': 'What you can take after taking this course', 'value': 'course'},
                {'label': 'Prerequisites that you need for this course', 'value': 'prerequisites'},
                {'label': 'Overview by subject', 'value': 'overview'},
            ],
            value='course',
            style={
                'fontSize': '20px',
                'color': 'white'
            }
        ),
        html.Hr()
    ]
)

message_display = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader("Error"),
                dbc.ModalBody(id='message_body'),
            ],
            id="message",
        )]
)

message_display1 = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader("Oops!"),
                dbc.ModalBody(id='message_body1'),
            ],
            id="message1",
        )]
)

message_display2 = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader("Sorry..."),
                dbc.ModalBody(id='message_body2'),
            ],
            id="message2",
        )]
)


dropdown_item_options = [{'label': n, 'value': c}
                         for (n, c) in zip(NAMES, CODES)]

subjects_dropdown_menu = dbc.FormGroup(
    [
        dbc.Label('See all courses of this subject!\nYou can type to search.', id='dropdown_label', style={
            'color': 'white'}),
        dcc.Dropdown(
            id='subject_input',
            options=dropdown_item_options,
            value="COMP",
        )
    ]
)

subjects_dropdown_fade = dbc.Fade(
    subjects_dropdown_menu,
    id='subject_fade',
    is_in=True,
)


course_input_box = dbc.FormGroup(
    [
        dbc.Label('Course Name', style={'color': 'white'}),
        dbc.InputGroup([
            dbc.Input(
                id='course_input',
                type='text',
                placeholder='e.g. COMP 202',
                value='comp 302',
            ),
            dbc.InputGroupAddon(
                dbc.Button(
                    'GO',
                    id='submit_button',
                    color='warning',
                    outline=True,
                ),
                addon_type='append',
            )
        ]
        ),
    ]
)

course_input_fade = dbc.Fade(
    course_input_box,
    id='course_fade',
    is_in=True,
    appear=True
)

# Stylesheets for Cytoscape graphs
overview_stylesheet = [
    {
        # Group selectors
        'selector': 'node',
        'style': {
            'width': '30px',
            'height': '30px',
            'background-color': '#f5a44e',
            # 'background-color': '#FF7216',
            'background-opacity': 1,
            'label': 'data(label)',
            'color': '#001345',
            'text-halign': 'center',
            'text-valign': 'center',
            'text-wrap': 'wrap',
            'font-size': '10px',
            'font-family': ['Lucida Console', 'Courier', 'monospace'],
            'font-weight':'light',
        }
    },
    {
        'selector': 'edge',
        'style': {
            'line-color': '#f6da83',
            'width': 1,
            'curve-style': 'bezier',
            'target-arrow-color': '#f6da83',
            'target-arrow-shape': 'triangle',
        }
    },
]


def get_color_coded_style_sheet(max_depth=1):
    output = deepcopy(overview_stylesheet)

    class_selector_template = {
        'selector': '.depth_0',  # Depth of nodes that shall apply this color selector.
        'style': {
            'background-color': '#000000',  # Color in Hex
            'line-color': '#000000'
        }
    }

    color_palette = Palette("material")
    first_color_hex = color_palette.green()
    second_color_hex = color_palette.purple()

    # Generate a random list of gradient colors in Hex
    colors = color_palette.color_between(first_color_hex, second_color_hex, max_depth + 1)

    # colors = color_palette.random(max_depth + 2)

    for depth in range(max_depth + 1):
        class_selector = deepcopy(class_selector_template)
        class_selector['selector'] = '.depth_' + str(depth)
        class_selector['style']['background-color'] = colors[depth]
        class_selector['style']['line-color'] = colors[depth]
        output.append(class_selector)

    return output


course_path_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'width':'50px',
            'height':'50px',
            'background-color': '#f5a44e',
            # 'background-color': '#FF7216',
            'background-opacity':1,
            'label': 'data(label)',
            'color': '#001345',
            'text-halign': 'center',
            'text-valign': 'center',
            'text-wrap':'wrap',
            'font-size':'17px',
            'font-family': ['Lucida Console', 'Courier', 'monospace'],
            'font-weight':'light',
        }
    },
    {
        'selector': 'edge',
        'style': {
            'line-color': '#f6da83',
            'width': 1.1,
            'curve-style': 'bezier',
            'target-arrow-color': '#f6da83',
            'target-arrow-shape': 'triangle',
        }
    },
]

minimap_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'width': '42px',
            'height': '42px',
            'background-color': '#f5a44e',
            # 'background-color': '#FF7216',
            'background-opacity': 1,
            'label': 'data(label)',
            'color': '#001345',
            'text-halign': 'center',
            'text-valign': 'center',
            'text-wrap': 'wrap',
            'font-size': '14px',
            'font-family': ['Lucida Console', 'Courier', 'monospace'],
            # 'font-weight':'light',
        }
    },
    {
        'selector': 'edge',
        'style': {
            'line-color': '#f6da83',
            'width': 1.1,
            'curve-style': 'bezier',
            'target-arrow-color': '#f6da83',
            'target-arrow-shape': 'triangle',
        }
    },
]


overview_graph = cyto.Cytoscape(
    id='overview_graph',
    # layout={'name':'concentric', 'mindNodeSpacing':15, 'spacingFactor':0.25, 'equidistant':True},
    layout={'name':'circle'},
    style={
        'width': '100%', 
        'height': '650px',
        },
    maxZoom=1.5,
    stylesheet=get_color_coded_style_sheet(),
    elements=graph.big_picture('comp')
)


def get_course_path_graph(show_prerequisite=False):
    elements = \
        graph.get_elements(graph.learning_path('comp 302', graph.dfs_tree, show_prerequisite), include_depth=True)

    course_path_graph=cyto.Cytoscape(
        id='course_path_graph',
        layout={'name':'cose'},
        style={
            'width': '100%',
            'height': '650px',
        },
        zoom= 1.2,
        minZoom= 0.3,
        maxZoom= 1.5,
        stylesheet=get_color_coded_style_sheet(5),
        elements=elements
    )
    return course_path_graph

mini_map = cyto.Cytoscape(
    id='mini_map',
    layout={'name': 'concentric', 'equidistant': False,
            'mindNodeSpacing': 10, 'spacingFactor': 1.1},
    style={
        'width': '100%',
        'height': '250px',
    },
    zoom=1.2,
    minZoom=0.5,
    maxZoom=1.5,
    stylesheet=minimap_stylesheet,
    elements=graph.get_elements(graph.learning_path('comp 202', graph.bfs_tree))
)

guide_content=dcc.Markdown(
    """
    * "Overview" shows all courses from the subject you search
    * "Path by course" shows which courses you can take after the course you search
    * You can zoom in/out and drag nodes to change their positions inside the graph
    ---
    * Path mode:
        * "Filters": Filter out subjects you want to ignore
        * "Layout": Change the layout of nodes in the graph
    * Overview mode:
        * The mini-map(only available in overview mode) on the left corner shows which courses are JUST after the one you click
    ---
    For bugs/enhancements:
    * Create an issue on GitHub (preferred)
    * Write me an email by clicking my name (please describe the problem clearly)
    """
)


starlink = html.A(" Star", href="https://github.com/Deerhound579/mcgill-course-map",
                  target='_blank', style={'color': 'black'}, id='star')
issueslink = html.A(" Issues", href="https://github.com/Deerhound579/mcgill-course-map/issues",
                    target='_blank', style={'color': 'black'}, id='issues')

minimap_content = [
    dbc.CardHeader(html.A('COMP 202 Foundations of Programming (3 credits)', id='minimap_header',
                          href='https://www.mcgill.ca/study/2019-2020/courses/comp-202', style={'color': 'white'}, target='_blank'),
                          ),
    dbc.CardBody(
        [
            mini_map
        ]
    ),
]

external_icon = html.I(className="fas fa-external-link-alt", style={})
course_info = html.A("COMP 302 Programming Languages and Paradigms (3 credits)")
course_info_panel=[
    dbc.CardHeader(html.A([external_icon, course_info],target='_blank', id='course_info_title', href='https://www.mcgill.ca/study/2019-2020/courses/comp-302', style={'color': 'white'})),
    dbc.CardBody("Fall 2018, Winter 2019", id='course_info_body')
]

# filter_dropdown = dcc.Dropdown(
#     options=[
#         {"label": "COMP", "value": 'COMP'},
#         {"label": "ECSE", "value": 'ECSE'},
#     ],
#     multi=True,
#     value=[],
#     id='filter_list',
# )

filter_body = dbc.CardBody(
    dcc.Dropdown(
        options=[
            {"label": "COMP", "value": 'COMP'},
            {"label": "ECSE", "value": 'ECSE'},
        ],
        multi=True,
        value=[],
        id='filter_list'
    )
)

layout_body=dbc.CardBody(
    dcc.Dropdown(
        id='layout_dropdown',
        value='cose',
        clearable=False,
        options=[
            {'label': name.capitalize(), 'value': name}
            for name in ['grid', 'random', 'circle', 'cose', 'concentric']
        ]
    )
)

filters_layouts = dbc.Card(
    [
        dbc.CardHeader([
            dbc.Tabs(
                [
                    dbc.Tab(filter_body, label="Filters", tab_id="filter_tab"),
                    dbc.Tab(layout_body, label="Layout", tab_id="layout_tab"),
                ],
                id="card_tabs",
                active_tab="filter_tab",
                card=True,
                style={'color': '#FF8800'},
            )
            ],
            id='filter_header'),
    ],
    color='warning',
    outline=True
)

filters_fade_card = dbc.Fade(
    filters_layouts,
    id='filters_fade',
    is_in=False,
    appear=True
)

# tooltips

startip=dbc.Tooltip('Like it? Star it!',target='star')
issuetip = dbc.Tooltip('Bugs? Enhancements?', target='issues')

navbar = dbc.NavbarSimple(
    children=[
        startip, issuetip,
        message_display,
        message_display1,
        message_display2,
        dbc.NavLink("© 2019 Sixian Li", href="mailto:lisixian579@gmail.com", style={
                    'color': 'black'}),
        dbc.NavLink([html.I(className='fab fa-github'), starlink],
                    style={'color': 'black'}),
        dbc.NavLink([html.I(className='fas fa-bug'), issueslink],
                    style={'color': 'black'}),
        dbc.DropdownMenu(
            right=True,
            nav=True,
            in_navbar=True,
            label="Guide",
            children=[
                dbc.DropdownMenuItem(guide_content)
            ],
            style={'color': 'black'},
        ),
    ],
    brand="McGill Course Map",
    color="warning",
    sticky="top",
)

body = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Hr(),
                        radioitems,
                        html.Div(children=[course_input_fade], id='display_current_mode'),
                        dbc.Card(id='left_corner_display', color="warning", outline=True),
                        html.Hr(),
                        # course_input_fade,
                        filters_fade_card,
                        html.Div(children=[], id='filter_test')
                    ],
                    md=4,
                ),
                dbc.Col(
                    [
                        html.Div(id='graph_container'),
                    ],
                    md=8
                ),
            ]
        )
    ],
    className="md-12",
)

app.title = 'McGill Course Map'
app.layout = html.Div([navbar, body])
error_message = "Please double check.\nIf you're sure it exists, or you've found an invalid course, create an issue on GitHub or contact me by email(click my name on the navigation bar)."


# !callbacks
@app.callback(
    [
        Output('display_current_mode', 'children'),
        Output('subject_fade', 'is_in'),
        Output('course_fade', 'is_in'),
        Output('graph_container', 'children'),
        Output('left_corner_display', 'children'),
        Output('filters_fade', 'is_in')
    ],
    [
        Input('radio_items', 'value'),
    ],
)
def choose_mode(current_type):
    #cur_subject, cur_course
    if current_type == 'overview':
        return subjects_dropdown_fade, True, False, overview_graph, minimap_content, False
    elif current_type == 'course':
        return course_input_fade, False, True, get_course_path_graph(show_prerequisite=False), course_info_panel, True
    else: # current_type == "prerequisites"
        return course_input_fade, False, True, get_course_path_graph(show_prerequisite=True), course_info_panel, True


@app.callback(
    Output('overview_graph', 'elements'),
    [
        Input('subject_input', 'value')
    ]
)
def update_overview(subject):
    return graph.big_picture(subject)


@app.callback(
    [
        Output('course_path_graph', 'elements'),
        Output('message', 'is_open'),
        Output('message_body', 'children'),
        Output('filter_list', 'options'),
    ],
    [
        Input('submit_button', 'n_clicks'), # user clicks 'GO'
        Input('course_input', 'n_submit'),   # user presss 'Enter'
        Input('filter_list', 'value'),
        Input('radio_items', 'value') # Bind the radio button for view modes
    ],
    [
        State('course_input', 'value'),
        # State('course_path_graph', 'elements'),
        State('filter_list', 'options')
    ]
)
def update_course(n, sub, filters, view_mode, course, cur_options):
    ctx = dash.callback_context
    if ctx.triggered:
        latest_trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        try:
            new_graph = graph.learning_path(course, graph.dfs_tree, view_mode == "prerequisites")
            if latest_trigger_id == 'filter_list': # If filter value changes, we change the current graph without recalculating subjects
                return graph.get_elements(new_graph, set(filters)), False, '', cur_options
            
            new_subjects = graph.subjects_in_graph(new_graph)
            options_list = [{'label': sub, 'value': sub} for sub in new_subjects]

            return graph.get_elements(new_graph), False, ' ', options_list
        except Exception as e:
            return [], True, f"There's no course called {course}. "+error_message, cur_options


@app.callback(
    [
        Output('mini_map', 'elements'),
        Output('minimap_header', 'children'),
        Output('minimap_header', 'href'),
        Output('message1', 'is_open'),
        Output('message_body1', 'children')
    ],
    [
        Input('overview_graph', 'tapNode')
    ],
    [
        State('mini_map', 'elements'),
        State('minimap_header', 'children'),
        State('minimap_header', 'href')
    ]
)
def update_minimap(node, current_elements, cur_header, cur_href):
    current_course = node['data']['id']
    try:
        return graph.get_elements(graph.learning_path(current_course, graph.bfs_tree)), infos[current_course]['name'], infos[current_course]['link'], False, ''
    except Exception as e:
        return current_elements, cur_header, cur_href, True, repr(e)+f"There's no course called {current_course}. "+error_message

@app.callback(
    [
        Output('course_info_title', 'children'),
        Output('course_info_title', 'href'),
        Output('course_info_body', 'children'),
        Output('message2', 'is_open'),
        Output('message_body2', 'children')
    ],
    [
        Input('course_path_graph', 'tapNode')
    ],
    [
        State('course_info_title', 'children'),
        State('course_info_title', 'href'),
        State('course_info_body', 'children'),
    ]
)
def update_course_info_panel(node, cur_title, cur_href, cur_term):
    current_course = node['data']['id']
    try:
        return [external_icon, infos[current_course]['name']], infos[current_course]['link'], infos[current_course]['term'], False, ' '
    except Exception as e:
        return cur_title, cur_href, cur_term, True, f"There's no course called {current_course}. "+error_message

@app.callback(
    Output('course_path_graph', 'layout'),
    [
        Input('layout_dropdown', 'value')
    ]
)
def update_layout(cur_lay):
    return {'name':cur_lay}

if __name__ == '__main__':
    app.run_server(debug=True)
