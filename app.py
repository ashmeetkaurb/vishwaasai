
import streamlit as st
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import traceback
from html import escape as html_escape
import base64

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

st.set_page_config(page_title="VishwasAI", layout="wide")

local_css("style.css")

# --- prompt given ---
MASTER_PROMPT = """
You are VishwasAI, an expert in deconstructing misinformation, propaganda, and logical fallacies. 
Your task is to analyze a given text and identify manipulative techniques. Be thorough and identify every single manipulative technique you can find in the text.

You must return your analysis as a single, valid JSON object. Do not add any text before or after the JSON object.

The JSON object must have a single key: "findings".
The value of "findings" should be a list of JSON objects.
Each object in the list represents a manipulative phrase you found and must have three keys:
1.  "technique": A string naming the technique (e.g., "Appeal to Fear", "Ad Hominem Attack", "Bandwagon Fallacy", "Loaded Language").
2.  "phrase": The exact, verbatim string from the text that uses this technique.
3.  "explanation": A concise, one-sentence explanation of why this phrase is manipulative and how it works, written for a non-expert.
If you find no manipulative techniques, return a JSON object with an empty list: {{"findings": []}}.

Analyze the following text:
---
{text_input}
---
"""

def analyze_text(text_to_analyze, model):
    try:
        prompt = MASTER_PROMPT.format(text_input=text_to_analyze)
        response = model.generate_content(prompt)
        json_str = response.text.strip().replace("```json", "").replace("```", "").strip()
        analysis_result = json.loads(json_str)
        return analysis_result
    except Exception as e:
        traceback.print_exc()
        return {"error": f"Internal error occurred...check terminal "}

# --- disp. func ---
def display_findings_list(findings):
    st.subheader("Analysis Results", divider="blue")

    if not findings:
        st.success("No manipulative techniques were detected in this text.")
        return

    st.info(f"Found {len(findings)} potential manipulative technique(s):")

    # 2-col layout
    col1, col2 = st.columns(2)
    
    for i, finding in enumerate(findings):
        if i % 2 == 0:
            with col1:
                display_card(finding)
        else:
            with col2:
                display_card(finding)

def display_card(finding):
    """Helper function to display a single finding in a card format."""
    technique = finding.get("technique", "N/A")
    phrase = finding.get("phrase", "N/A")
    explanation = finding.get("explanation", "N/A")

    with st.container(border=True):
        st.markdown(f"##### 🔺 **{technique}**")

        st.markdown(f"> *{phrase}*")
        
        st.markdown(f"**Explanation:** {explanation}")
st.title("VishwasAI: Propaganda Deconstructor")

if not api_key:
    st.error("API Key NOT FOUND!!!")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        'gemini-1.5-flash-latest',
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
except Exception as e:
    st.error(f"Error configuring the Google API. Details: {e}")
    st.stop()

st.markdown("Paste a suspicious message (like a WhatsApp forward) below to see how it might be trying to manipulate you.")

# --- ex.s ---
EXAMPLE_TEXTS = (
    "URGENT NEWS!! EVERYONE IS SAYING doctors are LYING about the new X-flu! They just want to sell you their expensive, useless drugs. A brave scientist, who was fired for telling the truth, revealed that a simple mix of ginger and lemon is the REAL cure. Don't be a sheep! Protect your family from the big pharma conspiracy. You must act now before it's too late and they silence this message! Forward this to every group you are in!",
    "Official Government Alert! As per the new 'Digital India Education Initiative', all students from Class 10 to B.A. are eligible for a FREE laptop. Over 50,000 students have already received their laptops. This is a once-in-a-lifetime opportunity to secure your future. Registration closes TONIGHT at 11 PM! You MUST forward this to 10 WhatsApp groups to activate your application link. Don't let your friends get ahead of you! Click the official link to apply now: bit.ly/gov-laptop-free-apply"
)

if 'example_index' not in st.session_state:
    st.session_state.example_index = 0

def load_next_example():
    current_index = st.session_state.example_index
    st.session_state.text_input = EXAMPLE_TEXTS[current_index]
    st.session_state.example_index = (current_index + 1) % len(EXAMPLE_TEXTS)

#---button---

CUSTOM_BUTTON_CSS = """
<style>
    [data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button {
        background-color: #28a745;
        color: white;
        border-radius: 5px;
        border: none;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button:hover {
        background-color: #218838;
        color: white;
        border: none;
    }
</style>
"""
st.markdown(CUSTOM_BUTTON_CSS, unsafe_allow_html=True)


col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Enter text to analyze")
    text_input = st.text_area("Paste text here...", height=300, key="text_input")
    analyze_button = st.button("Analyze Text", type="primary")

with col2:
    st.subheader("Or try an example")
    st.button("Load an example", on_click=load_next_example)


if analyze_button and text_input:
    with st.spinner("AI is analyzing the text..."):
        analysis_result = analyze_text(text_input, model)
    if "error" in analysis_result:
        st.error(analysis_result["error"])
    elif "findings" in analysis_result and analysis_result["findings"]:
        findings = analysis_result["findings"]
        display_findings_list(findings)
    else:
        st.success("No manipulative techniques were detected in this text.")
        st.markdown("### Original Text:")
        st.markdown(f"> {text_input}")

st.markdown("---")
st.caption("Built for Google hackathon.")
