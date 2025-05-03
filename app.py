import streamlit as st
import sqlite3
import json

def load_family_tree_from_db(root_id):
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

        # First, load children
        children_str = data.get("children_ids", "")
        children = []
        for cid in children_str.split(";"):
            cid = cid.strip()
            if cid:
                child = get_person(cid)
                if child:
                    children.append(child)

        # Then, check for spouse and create couple node if married
        spouse_id = data.get("spouse_id")
        spouse_node = None
        if spouse_id:
            spouse_node = get_person(spouse_id)

        if spouse_node:
            couple_node = {
                "id": f"{data['id']}_couple",
                "type": "couple",
                "husband": node if node["gender"] == "M" else spouse_node,
                "wife": spouse_node if node["gender"] == "M" else node,
                "children": children
            }
            return couple_node
        else:
            if children:
                node["children"] = children
            return node

    result = get_person(root_id)
    conn.close()
    return result

# ✅ Setup Streamlit app
st.set_page_config(layout="wide", page_title="Interactive Family Tree")

# ✅ Get query param
params = st.query_params
query_id = params.get("id", "P1")
st.write(f"Loading tree for ID: {query_id}")

# ✅ Load tree data
tree_data = load_family_tree_from_db(query_id)

if tree_data:
    setup_script = f"""
    <script>
    localStorage.setItem('treeData', {json.dumps(tree_data)});
    </script>
    <iframe src="tree.html" width="100%" height="750" style="border:none;"></iframe>
    """
    st.components.v1.html(setup_script, height=800, scrolling=True)
else:
    st.warning("No data found for the given ID.")
