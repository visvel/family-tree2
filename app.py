import streamlit as st
import sqlite3
import json

# Set Streamlit config
st.set_page_config(layout="wide", page_title="Interactive Family Tree")

# Track first load using session state
if "iframe_loaded" not in st.session_state:
    st.session_state.iframe_loaded = False

# Read person ID from query param
params = st.query_params
query_id = params.get("id", None)

if not query_id:
    st.warning("No person ID provided in URL. Use ?id=<UID>")
    st.stop()

st.write(f"Loading tree for ID: {query_id}")

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

        children_str = data.get("children_ids", "")
        children = []
        for cid in children_str.split(";"):
            cid = cid.strip()
            if cid:
                child = get_person(cid)
                if child:
                    children.append(child)

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

# Load tree only on first render
if not st.session_state.iframe_loaded:
    tree_data = load_family_tree_from_db(query_id)
    if tree_data:
        st.session_state.iframe_loaded = True
        setup_html = f"""
        <script>
        localStorage.setItem('treeData', {json.dumps(tree_data)});
        </script>
        <iframe src="tree.html" width="100%" height="750" style="border:none;"></iframe>
        """
        st.components.v1.html(setup_html, height=800, scrolling=True)
    else:
        st.warning("No data found for the given ID.")
else:
    # On rerun, avoid reloading data, just show iframe
    iframe_html = """
    <iframe src="tree.html" width="100%" height="750" style="border:none;"></iframe>
    """
    st.components.v1.html(iframe_html, height=800, scrolling=True)
