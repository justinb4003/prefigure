import lxml.etree as ET
import numpy as np
import math
import utilities as util
import math_utilities as math_util
import user_namespace as un
import arrow

# Process a line XML element into an SVG line element
def line(element, diagram, parent, outline_status):
    if outline_status == 'finish_outline':
        finish_outline(element, diagram, parent)
        return

    endpts = element.get('endpoints', None)
    if endpts is None:
        p1 = un.valid_eval(element.get('p1'))
        p2 = un.valid_eval(element.get('p2'))
    else:
        p1, p2 = un.valid_eval(endpts
                               )
    endpoint_offsets = None
    if element.get('infinite', 'no') == 'yes':
        p1, p2 = infinite_line(p1, p2, diagram)
        if p1 is None:  # the line doesn't hit the bounding box
            return
    else:
        endpoint_offsets = element.get('endpoint-offsets', None)
        if endpoint_offsets is not None:
            endpoint_offsets = un.valid_eval(endpoint_offsets)

    line = mk_line(p1, p2, diagram, element.get('id', None), 
                   endpoint_offsets=endpoint_offsets)
    util.set_attr(element, 'stroke', 'black')
    util.set_attr(element, 'thickness', '2')
    util.add_attr(line, util.get_1d_attr(element))
    line.set('type', 'line')

    arrows = int(element.get('arrows', '0'))
    if arrows > 0:
        arrow.add_arrowhead_to_path(diagram, 'marker-end', line)
    if arrows > 1:
        arrow.add_arrowhead_to_path(diagram, 'marker-start', line)
    util.cliptobbox(line, element, diagram)

    if outline_status == 'add_outline':
        diagram.add_outline(element, line, parent)
        return

    if element.get('outline', 'no') == 'yes' or diagram.output_format() == 'tactile':
        diagram.add_outline(element, line, parent)
        finish_outline(element, diagram, parent)
    else:
        parent.append(line)

def finish_outline(element, diagram, parent):
    diagram.finish_outline(element,
                           element.get('stroke'),
                           element.get('thickness'),
                           element.get('fill', 'none'),
                           parent)

# We'll be adding lines in other places so we'll use this more widely
def mk_line(p0, p1, diagram, id = None, endpoint_offsets = None, user_coords = True):
    line = ET.Element('line')
    diagram.add_id(line, id)
    if user_coords:
        p0 = diagram.transform(p0)
        p1 = diagram.transform(p1)
    if endpoint_offsets is not None:
        if len(endpoint_offsets.shape) == 1:
            u = math_util.normalize(p1-p0)
            p0 = p0 + endpoint_offsets[0] * u
            p1 = p1 + endpoint_offsets[1] * u
        else:
            p0[0] += endpoint_offsets[0][0]
            p0[1] -= endpoint_offsets[0][1]
            p1[0] += endpoint_offsets[1][0]
            p1[1] -= endpoint_offsets[1][1]

    line.set('x1', util.float2str(p0[0]))
    line.set('y1', util.float2str(p0[1]))
    line.set('x2', util.float2str(p1[0]))
    line.set('y2', util.float2str(p1[1]))
    return line

# if a line is "infinite," find the points where it intersects the bounding box
def infinite_line(p0, p1, diagram, slope = None):
    ctm, bbox = diagram.ctm_stack[-1]
    p0 = np.array(p0)
    p1 = np.array(p1)
    if slope is not None:
        p = p0
        v = np.array([1, slope])
    else:
        p = p0
        v = p1 - p0
    t_max = math.inf
    t_min = -math.inf
    if v[0] != 0:
        t0 = (bbox[0]-p[0])/v[0]
        t1 = (bbox[2]-p[0])/v[0]
        if t0 > t1:
            t0, t1 = t1, t0
        t_max = min(t1, t_max)
        t_min = max(t0, t_min)
    if v[1] != 0:
        t0 = (bbox[1]-p[1])/v[1]
        t1 = (bbox[3]-p[1])/v[1]
        if t0 > t1:
            t0, t1 = t1, t0
        t_max = min(t1, t_max)
        t_min = max(t0, t_min)
    if t_min > t_max:
        return None, None
    return [p + t * v for t in [t_min, t_max]]
