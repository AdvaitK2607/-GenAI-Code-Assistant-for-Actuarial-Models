import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os

# --- Configuration ---
# Load environment variables from a .env file
load_dotenv()

# --- Page Setup ---
st.set_page_config(
    page_title="GenAI Studio",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for a professional look ---
def load_css():
    st.markdown("""
    <style>
        /* Main app styling */
        .stApp {
            background-color: #1E1E1E;
            color: #E0E0E0;
        }

        /* Sidebar styling */
        .st-emotion-cache-16txtl3 {
            background-color: #252526;
            border-right: 1px solid #333333;
        }
        
        /* Input widgets */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: #2A2D31;
            color: #E0E0E0;
            border: 1px solid #3E3E3E;
            border-radius: 8px;
        }

        /* Buttons */
        .stButton>button {
            background-color: #007ACC;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            transition: background-color 0.3s, transform 0.1s;
        }
        .stButton>button:hover {
            background-color: #005A9E;
            transform: scale(1.02);
        }
        .stButton>button:active {
            transform: scale(0.98);
        }

        /* Expander/Accordion styling */
        .st-expander {
            background-color: #2A2D31;
            border: 1px solid #3E3E3E;
            border-radius: 8px;
        }
        .st-expander header {
            color: #00A3FF;
            font-weight: bold;
        }

        /* Code block styling */
        .stCodeBlock {
            border: 1px solid #3E3E3E;
            border-radius: 8px;
            background-color: #1E1E1E !important;
        }
        
        pre code {
            white-space: pre-wrap !important;
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #2A2D31;
            font-weight: bold;
        }
                
        /* Custom card for metrics */
        .metric-card {
            background-color: #2A2D31;
            border: 1px solid #3E3E3E;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .metric-card h3 {
            margin-top: 0;
            color: #00A3FF;
        }

    </style>
    """, unsafe_allow_html=True)

load_css()

# --- Session State Initialization ---
def init_session_state():
    defaults = {
        "gemini_model": None,
        "chat_history": [],
        "generated_code": "",
        "code_language": "python",
        "code_explanation": None,
        "complexity_analysis": None,
        "unit_tests": None,
        "dockerfile": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# --- Gemini API Call Function ---
def generate_from_gemini(model, prompt):
    """
    Makes a call to the Gemini API with error handling.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
        st.error("Please check your API key, model configuration, and API rate limits.")
        return None

# --- Sidebar UI ---
with st.sidebar:
    st.title("⚙️ Configuration")
    st.markdown("---")

    # Model Selection
    st.selectbox(
        "Select Gemini Model",
        ("gemini-2.5-pro", "gemini-2.5-flash", "gemini-pro-latest", "gemini-flash-latest"),
        key="model_selection",
        index=0
    )
    
    st.markdown("---")
    st.header("💡 Project Info")
    st.info(
        "This is an advanced GenAI Code Assistant. "
        "It can generate, explain, analyze, and even test code. "
        "Built to showcase modern AI capabilities in a professional UI."
    )


# --- Main App UI ---
st.title("🚀 GenAI Code Studio")
st.write("Your personal AI-powered assistant for generating, analyzing, and perfecting code.")

# Check if API key is configured from .env and initialize the model
if not st.session_state.get("gemini_model"):
    api_key_env = os.getenv("GEMINI_API_KEY")
    if not api_key_env:
        st.error("🚨 GEMINI_API_KEY not found in .env file. Please create a .env file and add your API key to continue.")
        st.stop()
    else:
        try:
            genai.configure(api_key=api_key_env)
            st.session_state["gemini_model"] = genai.GenerativeModel(st.session_state.model_selection)
        except Exception as e:
            st.error(f"Failed to configure API from environment variables: {e}")
            st.stop()


# --- Prompt Input Area ---
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        user_prompt = st.text_area(
            "Enter your code request (e.g., 'Python function for quicksort')",
            height=150,
            key="user_prompt",
            placeholder="Describe the code you want to generate..."
        )
    with col2:
         st.write("") # Spacer
         st.write("") # Spacer
         generate_button = st.button("Generate Code", use_container_width=True, type="primary")


# --- Main Logic ---
if generate_button and user_prompt:
    # Reset previous analysis results
    st.session_state["code_explanation"] = None
    st.session_state["complexity_analysis"] = None
    st.session_state["unit_tests"] = None
    st.session_state["dockerfile"] = None
    
    # Ensure model is selected and available
    if st.session_state.model_selection != st.session_state.gemini_model.model_name:
        st.session_state.gemini_model = genai.GenerativeModel(st.session_state.model_selection)
    
    model = st.session_state.gemini_model

    with st.spinner("🧠 AI is thinking... Generating code..."):
        # 1. Generate the Code
        code_prompt = f"Write clean, correct, and well-commented code for the following request. Provide only the code, without any explanation or markdown formatting.\n\nRequest: {user_prompt}"
        generated_code = generate_from_gemini(model, code_prompt)
        
        if generated_code:
            st.session_state["generated_code"] = generated_code
            
            # 2. Detect Language
            lang_prompt = f"Detect the programming language of this code. Respond with a single word (e.g., Python, JavaScript, Java).\n\nCode:\n```\n{generated_code}\n```"
            detected_language = generate_from_gemini(model, lang_prompt)
            if detected_language:
                st.session_state["code_language"] = detected_language.strip().lower()

            # Add to history
            st.session_state.chat_history.append({"prompt": user_prompt, "code": generated_code})
        else:
            st.session_state["generated_code"] = "" # Clear previous code if generation fails

# --- Display Results ---
if st.session_state["generated_code"]:
    code = st.session_state["generated_code"]
    lang = st.session_state["code_language"]

    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Generated Code", 
        "🔍 Code Explanation", 
        "📊 Complexity Analysis", 
        "✅ Unit Test Generation", 
        "🐳 Dockerfile Generation"
    ])

    with tab1:
        st.subheader("Generated Code")
        st.code(code, language=lang, line_numbers=True)
        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            st.download_button(
                label="Download Code",
                data=code,
                file_name=f"generated_code.{lang}",
                mime=f"text/{lang}",
                use_container_width=True
            )

    with tab2:
        st.subheader("Line-by-Line Explanation")
        if not st.session_state.get("code_explanation"):
            with st.spinner("Generating explanation..."):
                explanation_prompt = f"Explain the following {lang} code line by line in a clear, concise manner. Use markdown for formatting.\n\nCode:\n```\n{code}\n```"
                explanation = generate_from_gemini(st.session_state["gemini_model"], explanation_prompt)
                st.session_state["code_explanation"] = explanation or "Could not generate explanation."
        st.markdown(st.session_state["code_explanation"])
                
    with tab3:
        st.subheader("Algorithmic Complexity (Big O)")
        if not st.session_state.get("complexity_analysis"):
            with st.spinner("Analyzing complexity..."):
                complexity_prompt = f"Analyze the time and space complexity of the following {lang} code. Provide the Big O notation and a brief justification.\n\nCode:\n```\n{code}\n```"
                complexity = generate_from_gemini(st.session_state["gemini_model"], complexity_prompt)
                st.session_state["complexity_analysis"] = complexity or "Could not analyze complexity."
        st.markdown(st.session_state["complexity_analysis"])

    with tab4:
        st.subheader("Unit Tests")
        if not st.session_state.get("unit_tests"):
            with st.spinner("Generating unit tests..."):
                test_prompt = f"Generate unit tests for the following {lang} code. Use a common testing framework for the language (e.g., pytest for Python, Jest for JavaScript, JUnit for Java).\n\nCode:\n```\n{code}\n```"
                tests = generate_from_gemini(st.session_state["gemini_model"], test_prompt)
                st.session_state["unit_tests"] = tests or "Could not generate unit tests."
        st.code(st.session_state["unit_tests"], language=lang, line_numbers=True)
    
    with tab5:
        st.subheader("Dockerfile")
        if not st.session_state.get("dockerfile"):
            with st.spinner("Generating Dockerfile..."):
                docker_prompt = f"Generate a basic, production-ready Dockerfile for this {lang} code snippet. Assume standard dependencies for the language if not specified.\n\nCode:\n```\n{code}\n```"
                dockerfile = generate_from_gemini(st.session_state["gemini_model"], docker_prompt)
                st.session_state["dockerfile"] = dockerfile or "Could not generate Dockerfile."
        st.code(st.session_state["dockerfile"], language='dockerfile', line_numbers=True)

