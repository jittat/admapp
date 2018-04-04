def extract_line(line):
    """
    >>> extract_line("* hello world")
    ('hello world', 1)
    >>> extract_line("** this  is a ** test!!")
    ('this  is a ** test!!', 2)
    """
    depth = 0
    l = len(line)
    while (depth < l) and (line[depth] == '*'):
        depth += 1
    return (line[depth+1:], depth)


def parse_header(header):
    """
    >>> parse_header("* a\\n* b\\n* c")
    [['a', []], ['b', []], ['c', []]]
    >>> parse_header("* a\\n** b\\n* c")
    [['a', [['b', []]]], ['c', []]]
    >>> parse_header("* a\\n** b\\n** c\\n*** d\\n* e")
    [['a', [['b', []], ['c', [['d', []]]]]], ['e', []]]
    """
    nodes = []
    current_nodes = []
    for line in header.split("\n"):
        title,depth = extract_line(line.strip())
        if depth == 0:
            continue
        this_node = [title,[]]
        if depth == 1:
            nodes.append(this_node)
            current_nodes = [this_node]
        else:
            current_nodes[depth-2][1].append(this_node)
            current_nodes = current_nodes[:depth-1]
            current_nodes.append(this_node)

    return nodes


def traverse(node, depth, rows=None):
    title = node[0]
    children = node[1]

    if len(children) == 0:
        leaf_count = 1
        is_leaf = True
    else:
        leaf_count = 0
        for child in children:
            leaf_count += traverse(child, depth+1, rows)
        is_leaf = False

    if rows != None:
        if depth not in rows:
            rows[depth] = []

        rows[depth].append((title, leaf_count, is_leaf))
        
    return leaf_count
    

def table_header(header, prefix_columns=None, postfix_columns=None, tr_class=None):
    nodes = parse_header(header)
    rows = {}

    for n in nodes:
        traverse(n,0,rows)
    output = []
    row_count = len(rows)
    for r in range(row_count):
        if tr_class == None:
            output.append('<tr>')
        else:
            output.append('<tr class="' + tr_class + '">')
        if (r == 0) and (prefix_columns):
            for c in prefix_columns:
                output.append('<th rowspan="' + str(row_count) + '">' +
                              c + '</th>')
            
        for title, span, is_leaf in rows[r]:
            if is_leaf: 
                rowspan = row_count - r
                output.append('<th rowspan="' + str(rowspan) + '">' + title + '</th>')
            else:
                output.append('<th colspan="' + str(span) + '">' + title + '</th>')

        if (r == 0) and (postfix_columns):
            for c in postfix_columns:
                output.append('<th rowspan="' + str(row_count) + '">' +
                              c + '</th>')
            
        output.append('</tr>')
    return "\n".join(output)


def table_header_as_list_template(header):
    if header == '':
        return ''
    
    nodes = parse_header(header)
    param_count = [0]
    
    def build(node):
        title = node[0]
        children = node[1]

        if len(children) == 0:
            param_count[0] += 1
            return '<li>%s: {%d}</li>' % (title, param_count[0]-1)
        else:
            children_strs = [build(child) for child in children]
            return (('<li>%s\n<ul>\n' % (title,)) +
                    '\n'.join(children_strs) +
                    '\n</ul></li>')

    output = [build(node) for node in nodes]
    return "<ul>" + "\n".join(output) + "</ul>"


def table_header_column_count(header):
    nodes = parse_header(header)
    return sum([traverse(n,0) for n in nodes])
