import streamlit as st
import sqlite3
import json

st.set_page_config(layout="wide", page_title="Interactive Family Tree")

# Get query param
params = st.query_params
query_id = params.get("id", None)

st.write("🟡 Debug: Query params received:", params)

if not query_id:
    st.error("❌ No person ID provided in URL. Use ?id=<UID>")
    st.stop()

st.write(f"🔵 Loading tree for ID: {query_id}")

def load_family_tree_from_db(root_id):
    conn = sqlite3.connect("family_tree.db")
    cursor = conn.cursor()

    def get_person(pid):
        st.write(f"🟣 Fetching person with ID: {pid}")
        cursor.execute("SELECT * FROM people WHERE id = ?", (pid,))
        row = cursor.fetchone()
        if not row:
            st.warning(f"⚠️ No data found for ID: {pid}")
            return None

        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))

        st.write(f"✅ Loaded: {data['id']} - {data['name']}")

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
        if children_str:
            st.write(f"📦 {data['name']} has children: {children_str}")
        for cid in children_str.split(";"):
            cid = cid.strip()
            if cid:
                child = get_person(cid)
                if child:
                    children.append(child)

        spouse_id = data.get("spouse_id")
        spouse_node = None
        if spouse_id:
            st.write(f"💍 {data['name']} has spouse ID: {spouse_id}")
            spouse_node = get_person(spouse_id)

        if spouse_node:
            st.write(f"🔗 Creating couple node for: {data['name']} + {spouse_node['name']}")
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

tree_data = load_family_tree_from_db(query_id)

if tree_data:
    st.write("🧩 Tree structure loaded. Injecting tree.html iframe...")
    iframe_html = f"""
    <script>
      localStorage.setItem('treeData', {json.dumps(tree_data)});
      console.log("📦 treeData injected into localStorage");
    </script>
    <iframe src="/static/tree.html" width="100%" height="750" style="border:none;"
            onload="console.log('✅ iframe loaded');"></iframe>
    """
    st.components.v1.html(iframe_html, height=800, scrolling=True)
else:
    st.error("❌ No valid family tree could be loaded for the given ID.")
