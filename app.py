import streamlit as st
import json
import requests
from generate import GenerateEmail
import pandas

# --- CONFIG ---
st.set_page_config(page_title="AI Email Editor", page_icon="📧", layout="wide")

# 3 tabs
edit_email_tab, generate_tab, analysis_tab = st.tabs(["Edit emails", "Generate", "View Analysis"])

with edit_email_tab:
    # --- UI HEADER ---
    st.title("📧 AI Email Editing Tool")
    st.write("Select an email record by ID and use AI to refine it.")

    selected_dataset_edit = st.selectbox("Select Dataset", options=["lengthen.jsonl", "shorten.jsonl", "tone.jsonl"], key="dataset_edit")
    dataset_path_edit = "datasets/" + selected_dataset_edit
    emails = []
    with open(dataset_path_edit, "r") as fh:     
        for line in fh:
            emails.append(json.loads(line))
    if not emails:
        st.warning("No emails found in your JSONL file.")
        st.stop()

    selected_model_edit = st.selectbox("Select Model", options=["gpt-4o-mini", "gpt-4.1"], index=0, key="model_edit")

    # --- ID NAVIGATION BAR ---
    email_ids = [email.get('id') for email in emails]
    selected_id = st.selectbox("📂 Select Email ID", options=email_ids, index=0)

    # Find the selected email
    selected_email = None
    for email in emails:
        if email.get("id") == selected_id:
            selected_email = email
            break

    if not selected_email:
        st.error(f"No email found with ID {selected_id}.")
        st.stop()

    # --- DISPLAY SELECTED EMAIL ---
    st.markdown(f"### ✉️ Email ID: `{selected_id}`")
    st.markdown(f"**From:** {selected_email.get('sender', '(unknown)')}")
    st.markdown(f"**Subject:** {selected_email.get('subject', '(no subject)')}")

    email_text = st.text_area("Email Content", value=selected_email.get("content", ""), height=250, key=f"email_text_{selected_id}")

    if "email_data" not in st.session_state:
        st.session_state.email_data = {}

    email_key = f"email_{selected_id}"
    edited_email_key = f"edited_email_{selected_id}"

    if email_key not in st.session_state.email_data:
        st.session_state.email_data[email_key] = {
            "edited_email": "",
            "faithfulness_rating": {"rating": 0, "reasoning": ""},
            "user_instruction": "",
            "completeness_rating": {"rating": 0, "reasoning": ""}
        }
    selected_email_data = st.session_state.email_data[email_key]

    if edited_email_key not in st.session_state:
        st.session_state[edited_email_key] = selected_email_data["edited_email"]

    generator = GenerateEmail(model=selected_model_edit)

    # Display buttons
    column1, column2, column3 = st.columns(3)
    with column1:
        if st.button("Elaborate", key=f"lengthen_{selected_id}"):
            selected_email_data["user_instruction"] = "lengthen"
            edited = generator.generate("lengthen", email_text)
            selected_email_data["edited_email"] = edited
            st.session_state[f"edited_email_{selected_id}"] = edited

            selected_email_data["faithfulness_rating"] = generator.judge_faithfulness(email_text, selected_email_data["edited_email"])
            selected_email_data["completeness_rating"] = generator.judge_completeness(selected_email_data["user_instruction"], email_text, selected_email_data["edited_email"])

            st.session_state.email_data[email_key] = selected_email_data
            # st.rerun()
    with column2:
        if st.button("Shorten", key=f"shorten_{selected_id}"):
            selected_email_data["user_instruction"] = "shorten"
            edited = generator.generate("shorten", email_text)
            selected_email_data["edited_email"] = edited
            st.session_state[f"edited_email_{selected_id}"] = edited

            selected_email_data["faithfulness_rating"] = generator.judge_faithfulness(email_text, selected_email_data["edited_email"])
            selected_email_data["completeness_rating"] = generator.judge_completeness(selected_email_data["user_instruction"], email_text, selected_email_data["edited_email"])

            st.session_state.email_data[email_key] = selected_email_data
            # st.rerun()
    with column3:
        selected_tone = st.selectbox("Change Tone", ("Select a Tone", "Friendly", "Sympathetic", "Professional"), key=f"change_tone_{selected_id}")
        if selected_tone != "Select a Tone":
                selected_email_data["user_instruction"] = f"change_tone_{selected_tone.lower()}"
                edited = generator.generate(f"change_tone", email_text, tone=selected_tone.lower())
                selected_email_data["edited_email"] = edited
                st.session_state[f"edited_email_{selected_id}"] = edited

                selected_email_data["faithfulness_rating"] = generator.judge_faithfulness(email_text, selected_email_data["edited_email"])
                selected_email_data["completeness_rating"] = generator.judge_completeness(selected_email_data["user_instruction"], email_text, selected_email_data["edited_email"])

                st.session_state.email_data[email_key] = selected_email_data


    edited_email = st.text_area("Edited Email", height=250, key=f"edited_email_{selected_id}")
    # value=st.session_state.get(f"edited_email_{selected_id}", "")

    selected_email_data = st.session_state.email_data[email_key]

    st.text_area(
        "Scores of Evaluation", 
        value=(
            f"Faithfulness\n"
            f"Rating: {selected_email_data['faithfulness_rating'].get('rating', 0)}\n"
            f"Reasoning: {selected_email_data['faithfulness_rating'].get('reasoning', '')}\n\n"
            f"Completeness\n"
            f"Rating: {selected_email_data['completeness_rating'].get('rating', 0)}\n"
            f"Reasoning: {selected_email_data['completeness_rating'].get('reasoning', '')}"
        ),
        height=250
    )

with generate_tab:
    st.title("Generate")
    st.write("Run a model on all emails in a dataset")

    selected_dataset_gen = st.selectbox("Select Dataset", options=["lengthen.jsonl", "shorten.jsonl", "tone.jsonl"], key="dataset_gen")
    dataset_path_gen = "datasets/" + selected_dataset_gen
    emails_gen = []
    with open(dataset_path_gen, "r") as fh:     
        for line in fh:
            emails_gen.append(json.loads(line))
    if not emails_gen:
        st.warning("No emails found in your JSONL file.")
        st.stop()

    selected_model_gen = st.selectbox("Select Model", options=["gpt-4o-mini", "gpt-4.1"], index=0, key="model_gen")

    if st.button("Generate"):
        # st.write(f"Processing all {len(emails_gen)} email records in {selected_dataset_gen}")

        apply_action = ""
        if selected_dataset_gen == "lengthen.jsonl":
            apply_action = "lengthen"
        elif selected_dataset_gen == "shorten.jsonl":
            apply_action = "shorten"
        elif selected_dataset_gen == "tone.jsonl":
            apply_action = "change_tone"
            tones = ["friendly", "sympathetic", "professional"]
        
        generator = GenerateEmail(model=selected_model_gen)
        
        # Progress bar
        progress_bar = st.progress(0, text=f"Processed 0/{len(emails_gen)} email records")

        results = []
        faithfulness_scores = []
        completeness_scores = []
        for index, email in enumerate(emails_gen):
            email_text_gen = email.get("content", "")
            if apply_action == "change_tone":
                for select_tone in tones:
                    user_instruction_gen = f"change_tone_{select_tone}"
                    edited_gen = generator.generate("change_tone", email_text_gen, tone=select_tone)

                    faithfulness_gen = generator.judge_faithfulness(email_text_gen, edited_gen)
                    completeness_gen = generator.judge_completeness(user_instruction_gen, email_text_gen, edited_gen)
                    faithfulness_scores.append(faithfulness_gen.get('rating', 0))
                    completeness_scores.append(completeness_gen.get('rating', 0))

                    results.append({
                        "id": f"{email.get('id')}_{select_tone}", 
                        "original_email": email_text_gen,
                        "edited_email": edited_gen,
                        "faithfulness": faithfulness_gen,
                        "completeness": completeness_gen, 
                        "user_instruction": user_instruction_gen
                    })

            else:
                user_instruction_gen = apply_action
                edited_gen = generator.generate(user_instruction_gen, email_text_gen)

                faithfulness_gen = generator.judge_faithfulness(email_text_gen, edited_gen)
                completeness_gen = generator.judge_completeness(user_instruction_gen, email_text_gen, edited_gen)

                faithfulness_scores.append(faithfulness_gen.get('rating', 0))
                completeness_scores.append(completeness_gen.get('rating', 0))

                results.append({
                    "id": email.get("id"), 
                    "original_email": email_text_gen,
                    "edited_email": edited_gen,
                    "faithfulness": faithfulness_gen,
                    "completeness": completeness_gen, 
                    "user_instruction": user_instruction_gen
                })
            # Update progress bar
            progress_bar.progress((index + 1)/len(emails_gen), text=f"Processed {index + 1}/{len(emails_gen)} emails")  

        st.write(f"Finished processing {len(emails_gen)} email records in {selected_dataset_gen}!")

        st.markdown("---")
        st.subheader("Average Scores of Evaluation (0-3 Scale)")

        avg_faithfulness_score = sum(faithfulness_scores)/len(faithfulness_scores) if len(faithfulness_scores) > 0 else 0
        avg_completeness_score = sum(completeness_scores)/len(completeness_scores) if len(completeness_scores) > 0 else 0
        
        faithfulness_col, completeness_col = st.columns(2)
        with faithfulness_col:
            st.metric(label="Faithfulness", value=f"{avg_faithfulness_score:.2f}")
        with completeness_col:
            st.metric(label="Completeness", value=f"{avg_completeness_score:.2f}")

        st.markdown("---")
        st.subheader("Individual Model Responses and Scores")
        for i, res in enumerate(results):
            # st.markdown("---")
            st.markdown(f"Email ID: {res['id']}")
            
            # Display original and edited emails
            original_col, edited_col, scores_col = st.columns(3)
            with original_col:
                st.text_area("Original Email", value=res['original_email'], height=200, key=f"original_{res['id']}_{i}")
            with edited_col:
                st.text_area("Edited Email", value=res['edited_email'], height=200, key=f"edited_{res['id']}_{i}")
            with scores_col:
                st.text_area(
                    "Scores of Evaluation", 
                    value=(
                        f"Faithfulness\n"
                        f"Rating: {res['faithfulness'].get('rating', 0)}\n"
                        f"Reasoning: {res['faithfulness'].get('reasoning', '')}\n\n"
                        f"Completeness\n"
                        f"Rating: {res['completeness'].get('rating', 0)}\n"
                        f"Reasoning: {res['completeness'].get('reasoning', '')}"
                    ),
                    height=200
                )

with analysis_tab:
    st.title("Model Comparison")
    st.write("Compare the performance of models, GPT-4o mini and GPT-4.1, on an action.")

    selected_instruction = st.selectbox("Select User Instruction", options=["Lengthen", "Shorten", "Change Tone"], key="selected_instruction")
    if selected_instruction == "Lengthen":
        selected_dataset_scores = "lengthen.jsonl"
    elif selected_instruction == "Shorten":
        selected_dataset_scores = "shorten.jsonl"
    elif selected_instruction == "Change Tone":
        selected_dataset_scores = "tone.jsonl"
        tones = ["friendly", "sympathetic", "professional"]
    dataset_path_scores = "datasets/" + selected_dataset_scores

    emails_scores = []
    with open(dataset_path_scores, "r") as fh:     
        for line in fh:
            emails_scores.append(json.loads(line))
    if not emails_scores:
        st.warning("No emails found in your JSONL file.")
        st.stop()

    if st.button("Compare"):
        # st.write(f"Processing all {len(emails_scores)} email records in {selected_dataset_scores}")

        combined_results = {}
        for model_name in ["gpt-4o-mini", "gpt-4.1"]:
            # st.write(f"Running {model_name}")
            generator = GenerateEmail(model=model_name)

            # Progress bar for each model
            progress_bar = st.progress(0, text=f"Processed 0/{len(emails_scores)} emails using {model_name}")

            model_results = []
            faithfulness_scores = []
            completeness_scores = []
            for i, email in enumerate(emails_scores):
                email_text = email.get("content", "")
                if selected_instruction == "Change Tone":
                    for select_tone in tones:
                        user_instruction = f"change_tone_{select_tone}"
                        edited = generator.generate("change_tone", email_text, tone=select_tone)

                        faithfulness = generator.judge_faithfulness(email_text, edited)
                        completeness = generator.judge_completeness(user_instruction, email_text, edited)
                        faithfulness_scores.append(faithfulness.get('rating', 0))
                        completeness_scores.append(completeness.get('rating', 0))

                        model_results.append({
                            "id": f"{email.get('id')}_{select_tone}", 
                            "original_email": email_text,
                            "edited_email": edited,
                            "faithfulness": faithfulness,
                            "completeness": completeness, 
                            "user_instruction": user_instruction,
                            "model": model_name
                        })
                
                else:
                    edited = generator.generate(selected_instruction.lower(), email_text)

                    faithfulness = generator.judge_faithfulness(email_text, edited)
                    completeness = generator.judge_completeness(selected_instruction.lower(), email_text, edited)
                    faithfulness_scores.append(faithfulness.get('rating', 0))
                    completeness_scores.append(completeness.get('rating', 0))

                    model_results.append({
                        "id": f"{email.get('id')}", 
                        "original_email": email_text,
                        "edited_email": edited,
                        "faithfulness": faithfulness,
                        "completeness": completeness, 
                        "user_instruction": selected_instruction.lower(),
                        "model": model_name
                    })
                
                if model_name == "gpt-4o-mini":
                    progress_bar.progress((i + 1)/len(emails_scores), text=f"Processed {i + 1}/{len(emails_scores)} emails using GPT-4o mini")
                else:
                     progress_bar.progress((i + 1)/len(emails_scores), text=f"Processed {i + 1}/{len(emails_scores)} emails using GPT-4.1")

            avg_faithfulness = sum(faithfulness_scores)/len(faithfulness_scores) if len(faithfulness_scores) > 0 else 0
            avg_completeness = sum(completeness_scores)/len(completeness_scores) if len(completeness_scores) > 0 else 0
            
            combined_results[model_name] = {"results": model_results, "faithfulness": avg_faithfulness, "completeness": avg_completeness}
            # st.subheader(f"{model_name}")
            # st.write(f"\tAverage Faithfulness: {avg_faithfulness:.2f}")
            # st.write(f"\tAverage Completeness: {avg_completeness:.2f}")
        
        st.markdown("---")
        st.subheader("Model Scores")
        scores_table = {
            "Model": ["GPT-4o mini", "GPT-4.1"],
            "Faithfulness": [f"{combined_results['gpt-4o-mini']['faithfulness']:.2f}", f"{combined_results['gpt-4.1']['faithfulness']:.2f}"],
            "Completeness": [f"{combined_results['gpt-4o-mini']['completeness']:.2f}", f"{combined_results['gpt-4.1']['completeness']:.2f}"],
        }
        st.table(scores_table)

        st.markdown("---")
        st.subheader("Comparison Chart")
        comparison_data = pandas.DataFrame({
            "Model": ["GPT-4o mini", "GPT-4.1", None, "GPT-4o mini", "GPT-4.1"],
            "Metric": ["Faithfulness (GPT-4o mini)","Faithfulness (GPT-4.1)", "", "Completeness (GPT-4o mini)", "Completeness (GPT-4.1)"],
            "Score": [combined_results['gpt-4o-mini']['faithfulness'], combined_results['gpt-4.1']['faithfulness'], 0, combined_results['gpt-4o-mini']['completeness'], combined_results['gpt-4.1']['completeness']]
        })
        st.bar_chart(data=comparison_data[comparison_data["Model"].notna()], x="Metric", y="Score", color="Model", x_label="Score (0-3)", y_label="Metric", horizontal=True, sort=False, height=400)

        
        