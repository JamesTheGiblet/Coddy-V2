# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\generated_ui.py

import streamlit as st
from models.user_profile_model import UserProfileModel

st.title('📝 Input for UserProfileModel')

with st.form(key='data_form'):
    username_input = st.text_input('Username')
    full_name_input = st.text_input('Full Name')
    age_input = st.number_input('Age', step=1)
    is_active_input = st.checkbox('Is Active')
    join_date_input = st.date_input('Join Date')
    submit_button = st.form_submit_button(label='Submit')

if submit_button:
    try:
        instance = UserProfileModel(username=username_input, full_name=full_name_input, age=age_input, is_active=is_active_input, join_date=join_date_input)
        st.success('Instance created successfully!')
        import json
        if hasattr(instance, 'json'):
            st.json(json.loads(instance.json()))
        else:
            st.json(instance.__dict__)
    except Exception as e:
        st.error(f'Error creating instance: {e}')
