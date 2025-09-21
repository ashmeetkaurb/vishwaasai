
import streamlit as st
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import traceback
from html import escape as html_escape

# --- SETUP ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

st.set_page_config(page_title="VishwasAI", page_icon="🔎", layout="wide")

# --- THE MASTER PROMPT ---
MASTER_PROMPT = """
You are VishwasAI, an expert in deconstructing misinformation, propaganda, and logical fallacies. 
Your task is to analyze a given text and identify manipulative techniques.
You must return your analysis as a single, valid JSON object. Do not add any text before or after the JSON object.

The JSON object must have a single key: "findings".
The value of "findings" should be a list of JSON objects.
Each object in the list represents a manipulative phrase you found and must have three keys:
1.  "technique": A string naming the technique (e.g., "Appeal to Fear", "Ad Hominem Attack", "Bandwagon Fallacy", "Loaded Language").
2.  "phrase": The exact, verbatim string from the text that uses this technique.
3.  "explanation": A concise, one-sentence explanation of why this phrase is manipulative and how it works, written for a non-expert.
If you find no manipulative techniques, return a JSON object with an empty list: {"findings": []}.

Analyze the following text:
---
{text_input}
---
"""

# --- BACKEND FUNCTION ---
def analyze_text(text_to_analyze, model):
    try:
        prompt = MASTER_PROMPT.format(text_input=text_to_analyze)
        response = model.generate_content(prompt)
        json_str = response.text.strip().replace("```json", "").replace("```", "").strip()
        analysis_result = json.loads(json_str)
        return analysis_result
    except Exception as e:
        print("\n" + "="*50)
        print("!!! A CRITICAL ERROR WAS CAUGHT !!!")
        traceback.print_exc()
        print("="*50 + "\n")
        return {"error": f"An internal error occurred. Check the terminal for the full traceback."}

# --- HELPER FUNCTION FOR DISPLAY ---
def display_highlighted_text(original_text, findings):
    highlighted_text = original_text
    sorted_findings = sorted(findings, key=lambda x: len(x.get("phrase", "")), reverse=True)
    for finding in sorted_findings:
        phrase = finding.get("phrase")
        technique = finding.get("technique")
        explanation = finding.get("explanation")
        if phrase and phrase in highlighted_text:
            safe_phrase = html_escape(phrase)
            highlight_html = f'<span style="background-color: #FFCCCB; padding: 2px 5px; border-radius: 5px;" title="{technique}: {explanation}">{safe_phrase}</span>'
            highlighted_text = highlighted_text.replace(safe_phrase, highlight_html, 1)

    st.markdown(f"### Analysis Result:")
    st.markdown(highlighted_text, unsafe_allow_html=True)


# --- MAIN APP LOGIC ---
st.title("VishwasAI: The Propaganda Deconstructor")

if not api_key:
    st.error("API Key NOT FOUND! Please create a .env file with your GOOGLE_API_KEY.")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        'gemini-1.5-pro-latest',
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
except Exception as e:
    st.error(f"Error configuring the Google AI API. Details: {e}")
    st.stop()

st.markdown("Paste a suspicious message (like a WhatsApp forward) below to see how it might be trying to manipulate you.")
EXAMPLE_TEXT = "URGENT NEWS!! EVERYONE IS SAYING doctors are LYING about the new X-flu! They just want to sell you their expensive, useless drugs. A brave scientist, who was fired for telling the truth, revealed that a simple mix of ginger and lemon is the REAL cure. Don't be a sheep! Protect your family from the big pharma conspiracy. You must act now before it's too late and they silence this message! Forward this to every group you are in!"

def load_example():
    st.session_state.text_input = EXAMPLE_TEXT

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("Enter Text to Analyze")
    text_input = st.text_area("Paste text here...", height=250, key="text_input")
    analyze_button = st.button("Analyze Text", type="primary")
with col2:
    st.subheader("Or Try an Example")
    st.button("Load Example", on_click=load_example)

if analyze_button and text_input:
    with st.spinner("AI is analyzing the text..."):
        analysis_result = analyze_text(text_input, model)
    if "error" in analysis_result:
        st.error(analysis_result["error"])
    elif "findings" in analysis_result and analysis_result["findings"]:
        findings = analysis_result["findings"]
        display_highlighted_text(text_input, findings)
    else:
        st.success("No manipulative techniques were detected in this text.")
st.markdown("---")
st.caption("Built for the Google Cloud hackathon.")
