import streamlit as st
import requests

st.title("My AI Aggregator")
st.write("Ask questions to the 2 models:")
user_input = st.text_input("Enter yout question:")


if st.button("Send request"):
    with st.spinner("Отримую відповіді..."):
        response = requests.post(
            "http://localhost:8000/ask",
            json={"question": user_input}
        )

        if response.status_code == 200:
            data = response.json()

            final_answer = data["final_answer"]
            total_duration = data["total_duration"]

            model1_name = data["model1"]["name"]
            model1_answer = data["model1"]["answer"]
            model1_duration = data["model1"]["duration"]

            model2_name = data["model2"]["name"]
            model2_answer = data["model2"]["answer"]
            model2_duration = data["model2"]["duration"]

            st.subheader("Final answer", divider="blue")
            st.write(final_answer)
            st.caption(f"Total duration: {total_duration}")
            
            st.subheader(f"{model1_name}", divider="violet")
            st.write(model1_answer)
            st.caption(f"Duration: {model1_duration}")
            
            st.subheader(f"{model2_name}", divider="violet")
            st.write(model2_answer)
            st.caption(f"Duration: {model2_duration}")

        else:
            st.write("Error:", response.status_code)

st.divider()
st.subheader("Requests history")

if st.button("Show last requests"):
    history_response = requests.get("http://localhost:8000/history")
    
    if history_response.status_code == 200:
        history = history_response.json()["history"]
        
        for item in history:
            with st.expander(f"{item['timestamp']} - {item['question'][:50]}..."):
                st.write(f"**Model:** {item['model']}")
                st.write(f"**Duration:** {item['duration']}")
    else:
        st.write("Error")