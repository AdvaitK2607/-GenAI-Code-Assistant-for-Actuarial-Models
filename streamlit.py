import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import tempfile
import base64

# --- Configuration ---
# Load environment variables from a .env file
load_dotenv()

# --- Page Setup ---
st.set_page_config(
    page_title="GenAI Analysis Studio",
    page_icon="🔍",
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
        
        .file-uploader {
            border: 2px dashed #4ECDC4;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin: 10px 0;
        }

    </style>
    """, unsafe_allow_html=True)

load_css()

# --- Session State Initialization ---
def init_session_state():
    defaults = {
        "gemini_model": None,
        "chat_history": [],
        "generated_content": "",
        "code_language": "python",
        "uploaded_files": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Gemini API Call Functions ---
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

def process_uploaded_file(uploaded_file):
    """Process uploaded files and return appropriate content for Gemini"""
    file_content = None
    
    # Check file type
    if uploaded_file.type.startswith('image/'):
        # Image processing disabled temporarily
        file_content = f"Image file: {uploaded_file.name} (Image processing temporarily disabled)"
    elif uploaded_file.type in ['text/plain', 'application/pdf']:
        # Read text content
        file_content = uploaded_file.read()
        if uploaded_file.type == 'text/plain':
            try:
                file_content = file_content.decode('utf-8')
            except:
                file_content = str(file_content)
    elif uploaded_file.type == 'text/csv':
        file_content = uploaded_file.read().decode('utf-8')
    
    return file_content

# --- Available Models ---
AVAILABLE_MODELS = [
    "gemini-2.5-flash-preview-09-2025",
    "gemini-2.5-flash-lite-preview-09-2025", 
    "gemini-2.5-flash-image-preview",
    "gemini-2.5-flash-image",
    "gemini-2.5-flash-lite",
    "gemini-pro-latest",
    "gemini-flash-lite-latest",
    "gemini-robotics-er-1.5-preview",
    "gemini-2.5-computer-use-preview-10-2025"
]

# --- Sidebar UI ---
with st.sidebar:
    st.title("⚙️ Configuration")
    st.markdown("---")

    # Model Selection with available models
    st.selectbox(
        "Select Gemini Model",
        AVAILABLE_MODELS,
        key="model_selection",
        index=0,
        help="Choose the appropriate model for your analysis needs"
    )
    
    # Model descriptions
    with st.expander("ℹ️ Model Info", expanded=False):
        st.markdown("""
        **Recommended Models:**
        - **gemini-2.5-flash-preview-09-2025**: Balanced performance
        - **gemini-2.5-flash-image-preview**: Best for image analysis
        - **gemini-pro-latest**: General purpose
        - **gemini-2.5-flash-lite**: Fast and efficient
        """)
    
    st.markdown("---")

    # --- CHAT HISTORY ---
    st.header("📜 Analysis History")
    if not st.session_state.chat_history:
        st.info("Your previous analyses will appear here.")
    else:
        def load_history_item(item_index):
            history_item = st.session_state.chat_history[item_index]
            st.session_state["generated_content"] = history_item["content"]
            st.session_state["code_language"] = history_item.get("language", "python")

        for i, item in enumerate(reversed(st.session_state.chat_history)):
            with st.expander(f"#{len(st.session_state.chat_history) - i}: {item['prompt'][:40]}"):
                st.code(item['content'][:200] + "..." if len(item['content']) > 200 else item['content'], 
                       language=item.get('language', 'plaintext'))
                st.button(
                    "Reload Result",
                    key=f"history_{i}",
                    on_click=load_history_item,
                    args=(len(st.session_state.chat_history) - 1 - i,)
                )
    
    st.markdown("---")
    st.header("💡 Project Info")
    st.info(
        "**GenAI Analysis Studio** - Advanced AI assistant for analyzing prompts and documents. "
        "Upload files or enter text for comprehensive analysis."
    )

# --- Main App UI ---
st.title("🔍 GenAI Analysis Studio")
st.markdown("Your personal AI-powered assistant for **analyzing prompts, documents, and generating insights**.")

# Check if API key is configured
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

# --- Simplified Input Area ---
with st.container():
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_prompt = st.text_area(
            "Enter your prompt or question:",
            height=120,
            key="user_prompt",
            placeholder="Describe what you want to analyze... (e.g., 'Explain this code', 'Analyze this document', 'Help me understand this concept')",
            help="The AI will analyze your prompt and any uploaded files to provide comprehensive insights."
        )
        
        # File Upload Section
        st.subheader("📎 Upload Files (Optional)")
        uploaded_files = st.file_uploader(
            "Upload PDFs, text documents, or CSV files",
            type=['pdf', 'txt', 'csv'],
            accept_multiple_files=True,
            help="The AI will read and analyze uploaded files along with your prompt"
        )
        
        if uploaded_files:
            st.session_state.uploaded_files = uploaded_files
            for file in uploaded_files:
                st.success(f"✅ {file.name} ({file.type})")
        else:
            st.session_state.uploaded_files = []
    
    with col2:
        st.write("") # Spacer
        st.write("") # Spacer
        evaluate_button = st.button("🔍 Evaluate", use_container_width=True, type="primary")
        
        # Quick actions
        st.markdown("---")
        st.subheader("⚡ Quick Actions")
        if st.button("Clear All", use_container_width=True):
            st.session_state.uploaded_files = []
            st.session_state.generated_content = ""
            st.rerun()

# --- Main Logic ---
if evaluate_button and user_prompt:
    # Ensure model is selected and available
    current_model_name = st.session_state.model_selection
    if not st.session_state.get("gemini_model") or st.session_state.gemini_model.model_name != current_model_name:
        try:
            st.session_state["gemini_model"] = genai.GenerativeModel(current_model_name)
        except Exception as e:
            st.error(f"Failed to initialize model {current_model_name}: {e}")
            st.stop()
    
    model = st.session_state.gemini_model

    with st.spinner("🔍 AI is analyzing your request..."):
        # Process uploaded files
        file_contents = []
        
        if st.session_state.uploaded_files:
            for uploaded_file in st.session_state.uploaded_files:
                content = process_uploaded_file(uploaded_file)
                if content:
                    file_contents.append(f"File: {uploaded_file.name}\nContent: {content}")
        
        # Build analysis prompt
        base_prompt = f"""
        Analyze the following request and provide a comprehensive response. 
        Consider the context, provide insights, explanations, and any relevant information.
        
        USER REQUEST: {user_prompt}
        """
        
        # Add file context if files were uploaded
        if file_contents:
            files_context = "\n\n".join(file_contents)
            base_prompt = f"{base_prompt}\n\nADDITIONAL CONTEXT FROM UPLOADED FILES:\n{files_context}"
        
        # Add analysis instructions
        analysis_prompt = f"""
        {base_prompt}
        
        Please provide a comprehensive analysis that includes:
        1. Key insights and main points
        2. Detailed explanations where needed
        3. Any relevant examples or analogies
        4. Practical implications or applications
        5. Clear structure with appropriate headings
        
        Format your response using clear markdown formatting for better readability.
        """
        
        # Generate analysis
        generated_content = generate_from_gemini(model, analysis_prompt)
        
        if generated_content:
            st.session_state["generated_content"] = generated_content
            
            # Detect if content contains code
            lang_prompt = f"Does this content contain programming code? Respond with 'yes' or 'no' only.\n\nContent:\n{generated_content[:1000]}"
            has_code = generate_from_gemini(model, lang_prompt)
            if has_code and "yes" in has_code.lower():
                lang_detect_prompt = f"Detect the main programming language in this content. Respond with a single word.\n\nContent:\n{generated_content[:1000]}"
                detected_language = generate_from_gemini(model, lang_detect_prompt)
                if detected_language:
                    st.session_state["code_language"] = detected_language.strip().lower()

            # Add to history
            st.session_state.chat_history.append({
                "prompt": user_prompt, 
                "content": generated_content,
                "language": st.session_state.get("code_language", "plaintext"),
                "files": [f.name for f in st.session_state.uploaded_files],
                "model": current_model_name
            })
        else:
            st.session_state["generated_content"] = ""

# --- Display Results ---
if st.session_state["generated_content"]:
    content = st.session_state["generated_content"]
    lang = st.session_state["code_language"]

    # Create tabs for different views
    tab1, tab2 = st.tabs(["📋 Analysis Results", "📊 Detailed View"])

    with tab1:
        st.subheader("Analysis Results")
        
        # Display uploaded files info
        if st.session_state.uploaded_files:
            with st.expander("📎 Uploaded Files", expanded=False):
                for file in st.session_state.uploaded_files:
                    st.write(f"• {file.name} ({file.type})")
        
        # Display content with appropriate formatting
        st.markdown(content)
        
        # Download button
        st.download_button(
            label="Download Analysis",
            data=content,
            file_name="analysis_results.md",
            mime="text/markdown",
            use_container_width=True
        )

    with tab2:
        st.subheader("Detailed Analysis")
        
        # Show which model was used
        if st.session_state.chat_history:
            latest_analysis = st.session_state.chat_history[-1]
            st.info(f"**Model used:** {latest_analysis.get('model', 'Unknown')}")
        
        # Additional analysis options
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Summary", use_container_width=True):
                with st.spinner("Generating summary..."):
                    # Get the current model
                    current_model = st.session_state.gemini_model
                    summary_prompt = f"Create a concise summary of the following analysis. Focus on key points and main conclusions.\n\nAnalysis:\n{content}"
                    summary = generate_from_gemini(current_model, summary_prompt)
                    if summary:
                        st.markdown("### 📝 Summary")
                        st.markdown(summary)
        
        with col2:
            if st.button("Extract Key Points", use_container_width=True):
                with st.spinner("Extracting key points..."):
                    # Get the current model
                    current_model = st.session_state.gemini_model
                    keypoints_prompt = f"Extract the key points and main findings from this analysis. Present them as a bulleted list.\n\nAnalysis:\n{content}"
                    keypoints = generate_from_gemini(current_model, keypoints_prompt)
                    if keypoints:
                        st.markdown("### 🔑 Key Points")
                        st.markdown(keypoints)
        
        # Show raw content with syntax highlighting if it contains code
        st.markdown("### 📄 Full Analysis Content")
        if "```" in content:
            st.markdown(content)
        else:
            st.code(content, language=lang if lang != "plaintext" else None, line_numbers=True)

# --- Footer ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "GenAI Analysis Studio • Powered by Google Gemini"
    "</div>",
    unsafe_allow_html=True
)
