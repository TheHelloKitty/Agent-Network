# Example snippet using Streamlit for a local agent command center dashboard
import streamlit as st
import json

st.title("Toku Fleet Command Center")

try:
    with open("fleet_status_report.json", "r") as f:
        data = json.load(f)
        
        for agent in data["agents"]:
            col1, col2 = st.columns([1, 4])
            with col1:
                # Displays the agent's face image if available
                st.image(f"assets/avatars/{agent['name'].lower()}_avatar.png", width=80)
            with col2:
                st.subheader(agent["name"])
                st.write(f"**Tier:** {agent['tier']}")
                st.write(f"**Directive:** {agent['directive']}")
                st.text(agent["description"])
            st.divider()
except FileNotFoundError:
    st.warning("Run your agent.py script first to generate the fleet status report.")
