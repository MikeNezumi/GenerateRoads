import json
import pyglet
if "." in __name__:  # filed is called by a script outside of Scripts
    from .abstract_geometry import get_k
else:
    from abstract_geometry import get_k

"""
get_dict():
    Loads all data of a JSON file, or only its specified TOP LEVEL object/s.
    Returns corresponding pythonic arrays and dictionaries

    Input: a .json file
    Output: array/dictionary of arrays/dictionaries
"""
def get_dict(file_path, objects = None):  # string, array of strings (json object names)
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            if objects == None:
                json_data = json.load(json_file)
            else:
                json_data = []
                raw_data = json.load(json_file)
                for object_name in objects:
                    json_data.append(raw_data[object_name])

        json_file.close()
        return json_data

    except Exception as e:
        print(e)
        return False

"""
sort_points():
    Sorts a list of letter-indexed (or letter-number-mixed) points, eg. "Neighbours"
    Uses bubble sort, since list is already supposed to be sorted almost perfectly
    NOTE: a-z order changes the order of num postfixes, too (C12, C8, B5, B3, ...)

    Input: array of strings, az_order (bool)
    Output: (sorted) array of strings
"""
def sort_points(labels, az_order = True):
    assert any(labels.count(label) > 1 for label in labels) == False, "Duplicate entries! ~ read_json.sort_points()"
    # letters are sorted as numbers, alphabet is a 26-system
    # (A = 0, D = 3, Z = 25, AC = 28 ...)
    ciphers = set([str(num) for num in range(10)])  # chars of numbers 0 - 10
    labels_dict = {}  # label : computed weight

    for label in labels:
        key = ""
        postfix = []
        weight = 0  # "AACD2" will be converted into 1 134 002
        label = list(label)
        reversed_label = label[::-1]
        for glyph in reversed_label:  # strip number postix from label
            if glyph in ciphers:
                weight += int(glyph) * (10 ** reversed_label.index(glyph))
                postfix.append(str(label.pop()))

        for i in range(len(label)):
            letter_value = (ord(label[-(i+1)]) - 65)  # A = 0, Z = 25, starting from back
            letter_order = 26 ** i  # 26-base system
            weight += letter_value * letter_order * 1000  # BD87 = 14 087
        labels_dict[weight] = key.join(label + postfix[::-1])  # unique names -> unique weights

    sorted_keys = sorted(labels_dict, reverse = not az_order)
    sorted_labels = {key : labels_dict[key] for key in sorted_keys}
    return list(sorted_labels.values())

"""
order_neighbours():
    Checks a list of vertices neighbour to an intersection vertice to graph's Edges,
    puts them by their coordinates in a clockwise/counter-clockwise order
    Uses: abstract_geometry.get_k()
    Contains: clockwise_half()

    Input: label of the intersection (str), pythonised Vertices (dict), clockwise (bool)
    Output: sorted array of strings
"""
def order_neighbours(intersection_label, vertices, clockwise = True):

    assert intersection_label in vertices.keys(), "Vertice not in given vertices ~ read_json.order_neighbours()"
    # clockwise_half():
    #   Orders tuples of points' coordinates clockwise
    #   around control_xy(clockwise => descending slope). VERTICAL POINTS FORBIDDEN!
    #
    #   Input: control_xy, points (list of xy lists), clockwise (bool)
    #   Output:  (list of xy lists)
    def clockwise_half(control_xy, points):
        # InsertSort neighbours by foci radia k, descending
        k_dict = {tuple(p) : get_k(control_xy, p) for p in points}  # format: {xy: k}, created for efficiency in InsertSort
        for point_index in range(1, len(points)):
            point = points[point_index]
            scan_index = point_index - 1
            # move all points with smaller k right by 1
            while scan_index >= 0 and k_dict[tuple(point)] > k_dict[tuple(points[scan_index])]:
                points[scan_index+1] = points[scan_index]
                scan_index -= 1
            points[scan_index+1] = point

        return points

    # order_neighbours begins:
    left_points = []  # points more on the left than intersection_label
    right_points = []
    left_vertical = False
    right_vertical = False
    # isolate only neighbour vertices, format: {(x, y) : label}
    neighbours = {tuple(v["Coordinates"]) : label for label, v in vertices.items() if intersection_label in v["Neighbours"]}
    if len(neighbours) <= 2:
        return list(neighbours.values())  # 1 or 2 neighbours, no clockwise/counter-clockwise distinction, return right away

    xy = vertices[intersection_label]["Coordinates"]
    # generate dict of neighbours' xy (omit ordering vertice)}:
    points = [list(key) for key in neighbours.keys() if key != xy]
    # divide points to left and right of ordering vertice:
    for point in points:
        if point[0] == xy[0]:
            if point[1] > xy[1]:  # point directly above is the most clockwise point of left half
                left_vertical = point
            else:
                right_vertical = point  # point directly below is the most clockwise point of right half
            continue

        elif point[0] > xy[0]:
            right_points.append(point)
        else:
            left_points.append(point)

    # get halves' points (with added vertica points, if these exist)
    left_keys = clockwise_half(xy, left_points) + [left_vertical] if left_vertical else clockwise_half(xy, left_points)
    right_keys = clockwise_half(xy, right_points) + [right_vertical] if right_vertical else clockwise_half(xy, right_points)
    keys = left_keys + right_keys
    ordered_neighbours = [neighbours[tuple(key)] for key in keys]
    return ordered_neighbours if clockwise else ordered_neighbours[::-1]

# SAFE, NON-RE-WRITING TESTS:
#vertices = {
#    "A": {"Coordinates": [60, 60], "Neighbours": ["B", "C", "D", "E", "F"]},
#    "B": {"Coordinates": [0, 0], "Neighbours": ["A"]},
#    "C": {"Coordinates": [100, 10], "Neighbours": ["A"]},
#    "D": {"Coordinates": [100, 110], "Neighbours": ["A"]},
#    "E": {"Coordinates": [0, 90], "Neighbours": ["A"]},
#    "F": {"Coordinates": [10, 50], "Neighbours": ["A"]}
#}
#neighbours = order_neighbours("A", vertices, True)
#neighbours = order_neighbours("A", *get_dict("../Data/roads_test.json", ["Vertices"]))

#print(*get_dict("../Data/capital.json", ["Vertices"]))
