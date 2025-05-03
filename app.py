# Note: This script requires the 'streamlit' module and assumes you run it in a Streamlit-compatible environment.

try:
    import streamlit as st
    import sqlite3
    import json
except ModuleNotFoundError as e:
    raise ImportError("This script must be run in a Streamlit environment where the 'streamlit' module is available.") from e

# Load data from SQLite

def load_family_tree_from_db(root_id="P1"):
    conn = sqlite3.connect("family_tree.db")
    cursor = conn.cursor()

    def get_person(pid):
        cursor.execute("SELECT * FROM people WHERE id = ?", (pid,))
        row = cursor.fetchone()
        if not row:
            return None

        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))

        st.write(f"Loading person: {data['id']} - {data['name']}")

        node = {
            "id": data["id"],
            "name": data["name"],
            "gender": data.get("gender", "U"),
            "dob": data["dob"],
            "valavu": data["valavu"],
            "is_alive": data["alive"] == "Yes",
            "url": f"https://abc.com?id={data['id']}"
        }

        spouse_id = data.get("spouse_id")
        spouse_node = None
        if spouse_id:
            spouse_node = get_person(spouse_id)

        # Couple node if married
        if spouse_node:
            couple_node = {
                "id": f"{data['id']}_couple",
                "type": "couple",
                "husband": node if node["gender"] == "M" else spouse_node,
                "wife": spouse_node if node["gender"] == "M" else node,
                "children": []
            }
            node = couple_node

        children_str = data.get("children_ids", "")
        children = []
        for cid in children_str.split(";"):
            cid = cid.strip()
            if cid:
                child = get_person(cid)
                if child:
                    children.append(child)

        if children:
            node["children"] = children

        return node

    result = get_person(root_id)
    conn.close()
    return result

# HTML + JS for D3 Tree Rendering
def get_d3_tree_html(tree_data):
    return f"""
    <div id='tree'></div>
    <style>
        .node rect {{ stroke: #333; stroke-width: 1.5px; }}
        .node text {{ font: 12px sans-serif; pointer-events: none; }}
        .link {{ fill: none; stroke: #ccc; stroke-width: 1.5px; }}
    </style>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        const treeData = {json.dumps(tree_data)};
        console.log("Rendering treeData:", treeData);

        const width = 1200, height = 700;
        const svg = d3.select("#tree")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(50,50)");

        const treeLayout = d3.tree().size([width - 100, height - 100]);
        const root = d3.hierarchy(treeData, d => d.children);
        treeLayout(root);

        svg.selectAll('path.link')
            .data(root.links())
            .enter()
            .append('path')
            .attr('class', 'link')
            .attr('d', d3.linkVertical()
                .x(d => d.x)
                .y(d => d.y));

        const node = svg.selectAll('g.node')
            .data(root.descendants())
            .enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => 'translate(' + d.x + ',' + d.y + ')');

        node.each(function(d) {
            if (d.data.type === 'couple') {
                const g = d3.select(this);
                g.append('rect')
                    .attr('x', -70).attr('y', -40).attr('width', 140).attr('height', 30)
                    .style('fill', '#d0e1f9');
                g.append('text')
                    .attr('x', 0).attr('y', -20)
                    .attr('text-anchor', 'middle')
                    .text(d.data.husband.name);
                g.append('rect')
                    .attr('x', -70).attr('y', -10).attr('width', 140).attr('height', 30)
                    .style('fill', '#f9d0f0');
                g.append('text')
                    .attr('x', 0).attr('y', 10)
                    .attr('text-anchor', 'middle')
                    .text(d.data.wife.name);
            } else {
                const g = d3.select(this);
                g.append('rect')
                    .attr('x', -70).attr('y', -30).attr('width', 140).attr('height', 60)
                    .style('fill', d.data.gender === 'F' ? '#f9d0f0' : '#d0e1f9');
                g.append('text')
                    .attr('x', 0).attr('y', -5)
                    .attr('text-anchor', 'middle')
                    .text(d.data.name);
                g.append('text')
                    .attr('x', 0).attr('y', 15)
                    .attr('text-anchor', 'middle')
                    .text((d.data.dob || '') + ' ' + (d.data.valavu || ''));
            }
        });
    </script>
    """

# Streamlit UI
st.set_page_config(layout="wide")
st.title("Interactive Family Tree")

params = st.query_params
query_id = params.get("id", ["P1"])[0]
st.write(f"Loading tree for ID: {query_id}")
tree_data = load_family_tree_from_db(query_id)

if tree_data:
    d3_html = get_d3_tree_html(tree_data)
    st.components.v1.html(d3_html, height=750, scrolling=True)
else:
    st.warning("No data found for the given ID.")
