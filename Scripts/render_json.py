import pyglet
if "." in __name__:  # filed is called by a script outside of Scripts
    from .read_json import get_dict
    from .write_json import insert_edges, insert_rails
    from .abstract_geometry import approx_bezier
else:
    from read_json import get_dict
    from write_json import insert_edges, insert_rails
    from abstract_geometry import approx_bezier

"""
multiplied_coordinates():
    'miltiplier' is a float coefficient used to zoom/unzoom displayed vertices, so
    that they fit the display. The final px length of a vertice is computed as its
    length in meters (from JSON) times this multiplier. Function also returns
    processed simple graph dictionary
    Uses: read_json.get_dict()

    Input: pythonised json graph data - "Vertices" and "Edges"(dict),
           window resolution (int,int),
           padding (int,int)
    OPTIONAL: multiplier (float OR False)

    Output: multiplier (float), reduced vertice dict: {"A" : [3, 6], "B" : [10, 5], ...}
"""
def multiplied_coordinates(json_dict, window_res, padding, multiplier = False):  # TODO: subtract unused x and y pixels
    vertices = json_dict["Vertices"]  # if (lowest-left point is [200, 60], set it to [0, 0], subtract 200 from every x and 60 from all y)
    edges = json_dict["Edges"]
    # Get measurements needed for full-network viewport (how much do we un-zoom?)
    max_x, max_y = 0, 0
    min_x, min_y = 0, 0
    coordinates = {}  # reduced vertice dict: {"A" : [3, 6], "B" : [10, 5], ...}
    for label, point in vertices.items():
        x,y = point["Coordinates"]
        coordinates[label] = x, y
        if isinstance(x, list):  # complex rail vertice with line as "Coordinates"
            xy1, xy2 = x, y
            x = xy1[0] if xy1[0] > xy2[0] else xy2[0]  # assigning the larger x
            y = xy1[1] if xy1[1] > xy2[1] else xy2[1]  # assigning the larger y

        max_x = x if max_x < x else max_x
        max_y = y if max_y < y else max_y
        min_x = x if min_x > x else min_x
        min_y = y if min_y > y else min_y
    # Now, acount for non-intersection parts of the edge (they might be further out)
    # Yes, Beziér control points are checked as regular ones. I'm not happy either
    complex_edges = [r for r in edges if "Shape" in r.keys()]
    for edge in complex_edges:
        for shape in edge["Shape"]:
            if isinstance(shape[0], list):  # bezier
                if isinstance(shape[-1], dict):
                    shape = shape[:-1]  # Chop off offset dict before interpolating
                actual_points = approx_bezier(shape, [], step=0.125)  # bezier reduced to 8 points
                for xy in actual_points:
                    max_x = xy[0] if max_x < xy[0] else max_x
                    max_y = xy[1] if max_y < xy[1] else max_y
                    min_x = x if min_x > x else min_x
                    min_y = y if min_y > y else min_y
            else:
                max_x = shape[0] if max_x < shape[0] else max_x
                max_y = shape[1] if max_y < shape[1] else max_y
                min_x = x if min_x > x else min_x
                min_y = y if min_y > y else min_y
    x_ratio = (window_res[0] - (padding[0]*2)) / max_x
    y_ratio = (window_res[1] - (padding[1]*2) - 80) / max_y  # subtract 80px for window head
    if not multiplier:
        multiplier = x_ratio if x_ratio < y_ratio else y_ratio
    return multiplier, coordinates  # float, dict

"""
graph_lines():
    Converts a JSON road network graph into a set of pyglet vertices.
    Uses: read_json.get_dict()
          approx_bezier()  # note: both before and after zooming

    Input: json file path (str) OR ready JSON dictionary (dict),
           rgb tri-tuplet
    OPTIONAL: window resolution (int,int),
              padding (int,int),
              multiplier (float OR False)
              bezier step (float)
              drive right (bool)

    Output: array of pyglet indexed vertex lists
"""
def graph_lines(data_source, float_rgb, window_res=(1920, 1080), padding=(150, 150), multiplier=False, step=0.005, drive_right = True, half_gauge = 2.1):
    # set values to adjust viewport (fit all the edges into the window)
    if isinstance(data_source, str):
        json_dict = get_dict(data_source)
    else:
        json_dict = data_source
    vertices = json_dict["Vertices"]
    if "Edges" not in json_dict:  # Deduce edges, if necessary
        insert_edges(data_source)
        print("...insertion commanded by render_json.graph_lines().")
        json_dict = get_dict(data_source)
    edges = json_dict["Edges"]
    (r,g,b) = float_rgb   # rgb for edge color in floats

    complex_vertices = []  # vertices with list coordinates
    for key, vertice in vertices.items():
        if isinstance(vertice["Coordinates"][0], list):
            complex_vertices.append(key)

    multiplier, coordinates = multiplied_coordinates(json_dict, window_res, padding, multiplier)
    # bulid indexed vertice list:
    graph_vertices = []
    for edge in edges:
        (vert_a, vert_b) = edge["Vertices"]

        complex_verts = []  # Checking for complex rail vertices
        if vert_a in complex_vertices or vert_b in complex_vertices:  # vertice is a line! (complex vertices)
            if vert_a in complex_vertices:
                complex_verts.append(vert_a)
            if vert_b in complex_vertices:
                complex_verts.append(vert_b)
            for complex_vert in complex_verts:  # Might run twice - from 1 complex vertice to another
                (vert_x1, vert_y1) = coordinates[complex_vert][0]
                (vert_x2, vert_y2) = coordinates[complex_vert][1]
                vert_x1 = float(vert_x1 * multiplier + padding[0])  # resolution adjustments
                vert_x2 = float(vert_x2 * multiplier + padding[0])
                vert_y1 = float(vert_y1 * multiplier + padding[1])
                vert_y2 = float(vert_y2 * multiplier + padding[1])
                vertex = pyglet.graphics.vertex_list_indexed(2, [0,1],
                    ("v3f", [vert_x1,vert_y1,0, vert_x2,vert_y2,0]),
                    ("c3f", [r,g,b, r,g,b])
                )
                if vertex not in graph_vertices:
                    graph_vertices.append(vertex)  # appending the vertice itself as a line
            # complex vertice's xys are ordered in direction (from write_json), as well as Edges:
            if len(complex_verts) == 2:  # worst edge case - from complex vertice to complex vertice
                if edge["Vertices"].index(complex_verts[0]) == 0:  # going FROM complex vertice (vert_a)
                    (x1,y1) = coordinates[complex_verts[0]][1]
                    (x2,y2) = coordinates[complex_verts[1]][0]
                else:  # going TO complex vertice (vert_b)
                    (x1,y1) = coordinates[complex_verts[1]][1]
                    (x2,y2) = coordinates[complex_verts[0]][0]
            else:
                if edge["Vertices"].index(complex_verts[0]) == 0:  # going FROM complex vertice (vert_a)
                    (x1,y1) = coordinates[complex_verts[0]][1]
                    (x2,y2) = coordinates[vert_b]
                else:  # going TO complex vertice (vert_b)
                    (x1,y1) = coordinates[vert_a]
                    (x2,y2) = coordinates[complex_verts[0]][0]
        else:  # vertice is just a point
            (x1,y1) = coordinates[vert_a]
            (x2,y2) = coordinates[vert_b]
        x1 = float(x1 * multiplier + padding[0])  # resolution adjustments
        x2 = float(x2 * multiplier + padding[0])
        y1 = float(y1 * multiplier + padding[1])
        y2 = float(y2 * multiplier + padding[1])

        # convert graph edges to a list of pyglet vertexes
        if "Shape" in edge.keys():  # multiple corners and Beziér curves
            previous_corner = (x1, y1)
            for unscaled_corner in edge["Shape"]:
                if isinstance(unscaled_corner[0], list):  # Bezier curve
                    if isinstance(unscaled_corner[-1], dict):  # curve has defined Offsets dict
                        offsets = unscaled_corner.pop()["Offsets"]
                        points = approx_bezier(unscaled_corner, [], step, offsets)
                    else:
                        points = approx_bezier(unscaled_corner, [], step)

                    x1 =  float(points[0][0] * multiplier + padding[0])
                    y1 =  float(points[0][1] * multiplier + padding[0])
                    first_corner = (x1, y1)
                    for point in points[1:]:
                        x1, y1 = first_corner
                        x2 = float(point[0] * multiplier + padding[0])
                        y2 = float(point[1] * multiplier + padding[1])
                        first_corner = (x2, y2)
                        vertex = pyglet.graphics.vertex_list_indexed(2, [0,1],
                            ("v3f", [x1,y1,0, x2,y2,0]),
                            ("c3f", [r,g,b, r,g,b])
                        )
                        graph_vertices.append(vertex)
                    previous_corner = (x2, y2)  # rewrite old (x1, y1), that was just the first control point
                elif edge["Shape"].index(unscaled_corner) != 0:  # skip 1st iteration
                    x1, y1 = previous_corner
                    x2 = float(unscaled_corner[0] * multiplier + padding[0])
                    y2 = float(unscaled_corner[1] * multiplier + padding[1])
                    previous_corner = (x2, y2)
                    vertex = pyglet.graphics.vertex_list_indexed(2, [0,1],
                        ("v3f", [x1,y1,0, x2,y2,0]),
                        ("c3f", [r,g,b, r,g,b])
                    )
                    graph_vertices.append(vertex)
        else:  # direct A->B line
            vertex = pyglet.graphics.vertex_list_indexed(2, [0,1],
                ("v3f", [x1,y1,0, x2,y2,0]),
                ("c3f", [r,g,b, r,g,b])
            )
            graph_vertices.append(vertex)
    return graph_vertices

# SAFE TESTS:
#print(graph_vertices("../Data/capital.json", [100.0,100.0,100.0]))
#points = approx_bezier([[270,130],[310,130],[310,100]], 0.1)
#print(points)

"""
rails_lines():
    Converts a JSON road network graph (including "Vertices", "Edges", and "Rails")
    into a set of pyglet vertices. Deduces parts of JSON (using write_json's functions),
    if necessary. Since 'Rails' obey conventional structure, just a wrapper around
    render_graph.graph_lines()
    Uses: read_json.get_dict()
          write_json.insert_edges(), write_json.insert_rails()

    Input: json file path (str) OR ready JSON dictionary (dict),
           rgb tri-tuplet
    OPTIONAL: window resolution (int,int),
              padding (int,int),
              half_gauge (float),
              drive_right (bool)
              multiplier (float OR False)

    Output: array of pyglet indexed vertex lists, possibly rewritten JSON
"""
def rails_lines(data_source, float_rgb, resolution=(1920, 1080), padding=(150, 150), multiplier=False, half_gauge=2.1, step=0.005, drive_right=True, copy=True):
    # input deduction and testing
    assert len(float_rgb) == 3 and all(isinstance(x, (int, float)) for x in float_rgb), "rgb invalid ~ render_json.rails_lines()"
    if isinstance(data_source, str):
        json_dict = get_dict(data_source)
        if "Edges" not in json_dict:  # Deduce edges, if necessary
            insert_edges(data_source)
            print("...insertion commanded by render_json.graph_lines().")
            json_dict = get_dict(data_source)
        if "Rails" not in json_dict:
            insert_rails(data_source, half_gauge, drive_right, copy)
            print("...insertion commanded by render_json.rails_lines().")
            json_dict = get_dict(data_source)
    else:
        json_dict = data_source
    assert isinstance(json_dict, dict), "data corrupt (failed loading json_dict) ~ render_json.rails_lines()"

    rails = json_dict["Rails"]
    return graph_lines(rails, float_rgb, window_res=resolution, padding=padding, drive_right=drive_right, step=step, multiplier=multiplier, half_gauge=half_gauge)
