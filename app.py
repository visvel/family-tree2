import streamlit as st
import json

# ... your load_family_tree_from_db function remains unchanged ...

st.set_page_config(layout="wide")
st.title("Interactive Family Tree")

query_id = st.query_params.get("id", "P1")
tree_data = load_family_tree_from_db(query_id)

if tree_data:
    # Save JSON to localStorage via script
    setup_script = f"""
    <script>
    localStorage.setItem('treeData', {json.dumps(tree_data)});
    </script>
    """
    st.components.v1.html(setup_script + '<iframe src="tree.html" width="100%" height="800"></iframe>', height=850)
else:
    st.warning("No data found for the given ID.")
