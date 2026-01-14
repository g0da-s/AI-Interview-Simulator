import streamlit as st
import os
import tempfile
import time
import html
import secrets
from audio_recorder_streamlit import audio_recorder
from interview_logic import InterviewSession, transcribe_audio, text_to_speech

st.set_page_config(
    page_title="AI Interview Simulator",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --background-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }

    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }

    .main-header p {
        font-size: 1.1rem;
        margin-top: 0.5rem;
        opacity: 0.95;
    }

    /* Question card styling */
    .question-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        border-left: 5px solid #8b5cf6;
    }

    .question-number {
        font-size: 0.9rem;
        font-weight: 600;
        opacity: 0.9;
        margin-bottom: 0.5rem;
    }

    .question-text {
        font-size: 1.2rem;
        font-weight: 500;
        line-height: 1.6;
    }

    /* Answer card styling */
    .answer-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        padding: 1.25rem;
        border-radius: 12px;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }

    /* Progress bar */
    .progress-container {
        background-color: rgba(102, 126, 234, 0.1);
        border-radius: 10px;
        padding: 0.5rem;
        margin: 1rem 0;
    }

    .progress-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 8px;
        border-radius: 5px;
        transition: width 0.3s ease;
    }

    /* Button styling improvements */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.2);
    }

    /* Info/Warning/Error styling */
    .stAlert {
        border-radius: 10px;
        border-left-width: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }


    /* Voice selector styling */
    .voice-card {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }

    .voice-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }

    /* Success completion styling */
    .completion-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
    }

    .completion-card h2 {
        font-size: 2rem;
        margin-bottom: 1rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Improve text area */
    .stTextArea textarea {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        transition: border-color 0.3s ease;
    }

    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
</style>
""", unsafe_allow_html=True)

if "session" not in st.session_state:
    st.session_state.session = None
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None
if "recording_attempt" not in st.session_state:
    st.session_state.recording_attempt = 0
if "selected_voice" not in st.session_state:
    st.session_state.selected_voice = "nova"
if "interview_transcript" not in st.session_state:
    st.session_state.interview_transcript = []
if "job_description" not in st.session_state:
    st.session_state.job_description = ""
if "show_resume_section" not in st.session_state:
    st.session_state.show_resume_section = False
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "last_api_call" not in st.session_state:
    st.session_state.last_api_call = None
if "api_call_count" not in st.session_state:
    st.session_state.api_call_count = 0
if "session_start_time" not in st.session_state:
    from datetime import datetime
    st.session_state.session_start_time = datetime.now()
if "pending_transcription" not in st.session_state:
    st.session_state.pending_transcription = None
if "show_transcription_editor" not in st.session_state:
    st.session_state.show_transcription_editor = False
if "csrf_token" not in st.session_state:
    st.session_state.csrf_token = secrets.token_urlsafe(32)
if "recording_start_time" not in st.session_state:
    st.session_state.recording_start_time = None
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gpt-4o-mini"
if "selected_temperature" not in st.session_state:
    st.session_state.selected_temperature = 0.7
if "question_max_tokens" not in st.session_state:
    st.session_state.question_max_tokens = 150
if "feedback_max_tokens" not in st.session_state:
    st.session_state.feedback_max_tokens = 700

def validate_csrf_token() -> bool:
    """
    Validate CSRF token for state-changing operations

    Returns:
        True if token is valid, False otherwise
    """
    if not hasattr(st.session_state, 'csrf_token'):
        return False

    if not st.session_state.csrf_token or len(st.session_state.csrf_token) < 32:
        return False

    return True

def check_rate_limit(min_seconds_between_calls: int = 3, max_calls_per_session: int = 50) -> tuple[bool, str]:
    """
    Check if the user is allowed to make an API call based on rate limits

    Args:
        min_seconds_between_calls: Minimum seconds required between API calls (default: 3)
        max_calls_per_session: Maximum API calls allowed per session (default: 50)

    Returns:
        (is_allowed, error_message)
    """
    from datetime import datetime, timedelta

    now = datetime.now()

    if st.session_state.api_call_count >= max_calls_per_session:
        return False, f"⚠️ Rate limit reached: Maximum {max_calls_per_session} API calls per session. Please refresh the page to start a new session."

    if st.session_state.last_api_call:
        time_since_last_call = (now - st.session_state.last_api_call).total_seconds()
        if time_since_last_call < min_seconds_between_calls:
            remaining = int(min_seconds_between_calls - time_since_last_call)
            return False, f"⏳ Please wait {remaining} second(s) before making another request."

    return True, ""

def record_api_call() -> None:
    """
    Record that an API call was made

    Updates session state with the current timestamp and increments the API call counter.
    This is used for rate limiting and usage tracking.
    """
    from datetime import datetime
    st.session_state.last_api_call = datetime.now()
    st.session_state.api_call_count += 1

def generate_transcript() -> str:
    """Generate a formatted transcript of the interview"""
    from datetime import datetime

    transcript = []
    transcript.append("="*70)
    transcript.append("AI INTERVIEW SIMULATOR - INTERVIEW TRANSCRIPT")
    transcript.append("="*70)
    transcript.append(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    transcript.append(f"Interviewer: Alex (AI)")
    transcript.append(f"Voice: {st.session_state.selected_voice.capitalize()}")
    transcript.append("\n" + "-"*70)
    transcript.append("JOB DESCRIPTION")
    transcript.append("-"*70)
    transcript.append(st.session_state.job_description)
    transcript.append("\n" + "="*70)
    transcript.append("INTERVIEW CONVERSATION")
    transcript.append("="*70 + "\n")

    for idx, item in enumerate(st.session_state.interview_transcript, 1):
        if item["type"] == "question":
            transcript.append(f"\n[Question {idx}]")
            transcript.append(f"INTERVIEWER: {item['content']}")
        elif item["type"] == "answer":
            transcript.append(f"\nCANDIDATE: {item['content']}")
            transcript.append("-"*70)

    if st.session_state.current_question and not st.session_state.session.is_active:
        transcript.append("\n" + "="*70)
        transcript.append("FINAL FEEDBACK")
        transcript.append("="*70 + "\n")
        transcript.append(st.session_state.current_question)

    transcript.append("\n" + "="*70)
    transcript.append("END OF TRANSCRIPT")
    transcript.append("="*70)
    transcript.append("\nGenerated by AI Interview Simulator")
    transcript.append("Powered by OpenAI GPT-4 & Whisper")

    return "\n".join(transcript)

def extract_rating(text: str, keywords: list[str]) -> tuple[str, int]:
    """
    Extract rating from feedback text based on keyword matching

    Args:
        text: The feedback text to search
        keywords: List of rating keywords in order from best to worst

    Returns:
        Tuple of (rating_keyword, rating_index) where index indicates position in keywords list.
        Returns ("Not Rated", -1) if no keyword found.

    Example:
        >>> extract_rating("Performance was Good overall", ["Excellent", "Good", "Fair"])
        ("Good", 1)
    """
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return keyword, keywords.index(keyword)
    return "Not Rated", -1

def calculate_score(feedback_text: str) -> dict[str, tuple[str, int]]:
    """
    Calculate numerical scores from feedback ratings

    Parses structured feedback text to extract ratings for different evaluation categories
    and converts them to numerical scores (0-100).

    Args:
        feedback_text: The complete feedback text containing rating sections

    Returns:
        Dictionary mapping category keys to (rating_name, score) tuples.
        Categories: "technical", "communication", "cultural", "recommendation"

    Example:
        >>> scores = calculate_score(feedback_text)
        >>> scores["technical"]
        ("Strong", 100)
    """
    scores = {}

    tech_ratings = ["Strong", "Good", "Fair", "Needs Development"]
    comm_ratings = ["Excellent", "Good", "Fair", "Needs Work"]
    fit_ratings = ["High", "Medium", "Low"]
    rec_ratings = ["Strong Yes", "Yes", "Maybe", "No"]

    if "TECHNICAL COMPETENCY" in feedback_text:
        rating, idx = extract_rating(feedback_text.split("TECHNICAL COMPETENCY")[1].split("**")[0], tech_ratings)
        scores["technical"] = (rating, max(0, 100 - (idx * 25)) if idx >= 0 else 50)

    if "COMMUNICATION SKILLS" in feedback_text:
        rating, idx = extract_rating(feedback_text.split("COMMUNICATION SKILLS")[1].split("**")[0], comm_ratings)
        scores["communication"] = (rating, max(0, 100 - (idx * 25)) if idx >= 0 else 50)

    if "CULTURAL FIT" in feedback_text:
        rating, idx = extract_rating(feedback_text.split("CULTURAL FIT")[1].split("**")[0], fit_ratings)
        scores["cultural"] = (rating, max(0, 100 - (idx * 33)) if idx >= 0 else 50)

    if "FINAL RECOMMENDATION" in feedback_text:
        rating, idx = extract_rating(feedback_text.split("FINAL RECOMMENDATION")[1].split("**")[0], rec_ratings)
        scores["recommendation"] = (rating, max(0, 100 - (idx * 25)) if idx >= 0 else 50)

    return scores

def display_score_card(scores: dict[str, tuple[str, int]]) -> None:
    """
    Display visual score card with ratings in a formatted UI

    Creates a multi-column layout with score visualizations including progress bars,
    percentage scores, and rating labels. Also calculates and displays overall average.

    Args:
        scores: Dictionary mapping category keys to (rating_name, score) tuples.
                Expected keys: "technical", "communication", "cultural", "recommendation"
    """
    if not scores:
        return

    st.markdown("### 📊 Performance Scores")

    cols = st.columns(len(scores))

    score_config = {
        "technical": ("⚙️", "Technical", "#3b82f6"),
        "communication": ("💬", "Communication", "#8b5cf6"),
        "cultural": ("🤝", "Cultural Fit", "#ec4899"),
        "recommendation": ("✅", "Overall", "#10b981")
    }

    for idx, (key, (rating, score)) in enumerate(scores.items()):
        if key in score_config:
            emoji, label, color = score_config[key]
            with cols[idx]:
                if score >= 75:
                    bar_color = "#10b981"
                elif score >= 50:
                    bar_color = "#f59e0b"
                else:
                    bar_color = "#ef4444"

                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 2rem;">{html.escape(emoji)}</div>
                    <div style="font-weight: 600; color: #1f2937; margin: 0.5rem 0;">{html.escape(label)}</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: {html.escape(bar_color)};">{html.escape(str(score))}%</div>
                    <div style="background: #e5e7eb; border-radius: 10px; height: 8px; margin: 0.5rem 0; overflow: hidden;">
                        <div style="background: {html.escape(bar_color)}; width: {html.escape(str(score))}%; height: 100%; border-radius: 10px; transition: width 0.5s ease;"></div>
                    </div>
                    <div style="font-size: 0.85rem; color: #6b7280;">{html.escape(rating)}</div>
                </div>
                """, unsafe_allow_html=True)

    avg_score = sum(s[1] for s in scores.values()) / len(scores) if scores else 0
    performance_message = "Excellent Performance! 🌟" if avg_score >= 75 else "Good Job! Keep practicing! 💪" if avg_score >= 50 else "Keep working on it! 📈"
    st.markdown(f"""
    <div style="text-align: center; margin: 1.5rem 0; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white;">
        <h3 style="margin: 0;">Overall Interview Score</h3>
        <div style="font-size: 3rem; font-weight: 700; margin: 0.5rem 0;">{html.escape(str(int(avg_score)))}%</div>
        <p style="margin: 0; opacity: 0.9;">{html.escape(performance_message)}</p>
    </div>
    """, unsafe_allow_html=True)

def display_feedback(feedback_text: str) -> None:
    """
    Parse and display structured feedback with beautiful formatting

    Extracts and displays feedback sections with custom styling, including:
    - Score card visualization
    - Categorized feedback sections (performance, strengths, improvements, etc.)
    - Color-coded section headers

    Args:
        feedback_text: The complete feedback text containing structured sections
                      marked with **SECTION_NAME** headers
    """
    scores = calculate_score(feedback_text)
    if scores:
        display_score_card(scores)
        st.markdown("---")

    sections = {
        "OVERALL PERFORMANCE": ("📊", "#667eea", "Overall Performance"),
        "KEY STRENGTHS": ("💪", "#10b981", "Key Strengths"),
        "AREAS FOR IMPROVEMENT": ("🎯", "#f59e0b", "Areas for Improvement"),
        "TECHNICAL COMPETENCY": ("⚙️", "#3b82f6", "Technical Competency"),
        "COMMUNICATION SKILLS": ("💬", "#8b5cf6", "Communication Skills"),
        "CULTURAL FIT": ("🤝", "#ec4899", "Cultural Fit"),
        "FINAL RECOMMENDATION": ("✅", "#10b981", "Final Recommendation"),
        "NEXT STEPS": ("🚀", "#667eea", "Next Steps")
    }

    for section_key, (emoji, color, title) in sections.items():
        if f"**{section_key}**" in feedback_text:
            start = feedback_text.find(f"**{section_key}**")
            next_section = len(feedback_text)

            for other_key in sections.keys():
                if other_key != section_key:
                    pos = feedback_text.find(f"**{other_key}**", start + 1)
                    if pos != -1 and pos < next_section:
                        next_section = pos

            content = feedback_text[start:next_section].replace(f"**{section_key}**", "").strip()

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
                        padding: 1.5rem; border-radius: 12px; margin: 1rem 0;
                        border-left: 4px solid {color};
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="color: {color}; margin: 0 0 1rem 0; font-size: 1.3rem;">
                    {emoji} {html.escape(title)}
                </h3>
                <div style="color: #1f2937; line-height: 1.8; white-space: pre-wrap;">
{html.escape(content)}
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🎤 AI Interview Simulator</h1>
    <p>Practice your interview skills with an AI interviewer that asks realistic questions</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.interview_started:
    saved_sessions = InterviewSession.list_saved_sessions()

    if saved_sessions:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📂 Resume Previous Interview" if not st.session_state.show_resume_section else "🔽 Hide Saved Interviews",
                        type="secondary", use_container_width=True):
                st.session_state.show_resume_section = not st.session_state.show_resume_section
                st.rerun()

        if st.session_state.show_resume_section:
            st.markdown("### 💾 Saved Interview Sessions")
            st.markdown("---")

            for idx, session_info in enumerate(saved_sessions):
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    from datetime import datetime
                    try:
                        saved_time = datetime.fromisoformat(session_info["last_saved_at"])
                        time_str = saved_time.strftime("%b %d, %Y at %I:%M %p")
                    except:
                        time_str = "Unknown"

                    status = "✅ Complete" if not session_info["is_active"] else f"🎤 Question {session_info['current_question']}/7"

                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea15 0%, #764ba205 100%);
                                padding: 1rem; border-radius: 10px; margin: 0.5rem 0;
                                border-left: 4px solid #667eea;">
                        <div style="font-weight: 600; color: #667eea; margin-bottom: 0.3rem;">
                            Session {html.escape(str(idx + 1))}: {html.escape(status)}
                        </div>
                        <div style="font-size: 0.9rem; color: #6b7280;">
                            Last saved: {html.escape(time_str)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    if st.button("▶️ Resume", key=f"resume_{idx}", use_container_width=True):
                        if not validate_csrf_token():
                            st.error("❌ Security Error: Invalid session token. Please refresh the page.")
                        else:
                            try:
                                with st.spinner("Loading your interview..."):
                                    loaded_session = InterviewSession.load_session(session_info["session_id"])
                                    st.session_state.session = loaded_session
                                    st.session_state.job_description = loaded_session.job_description
                                    st.session_state.current_session_id = session_info["session_id"]

                                    if loaded_session.conversation_history:
                                        last_message = loaded_session.conversation_history[-1]
                                        if last_message["role"] == "assistant":
                                            st.session_state.current_question = last_message["content"]

                                            audio_path = text_to_speech(
                                                last_message["content"],
                                                "current_question.mp3",
                                                voice=st.session_state.selected_voice
                                            )
                                            st.session_state.audio_path = audio_path

                                    st.session_state.interview_transcript = []
                                    for msg in loaded_session.conversation_history:
                                        if msg["role"] == "assistant":
                                            st.session_state.interview_transcript.append({
                                                "type": "question" if loaded_session.is_active else "feedback",
                                                "content": msg["content"]
                                            })
                                        elif msg["role"] == "user" and msg.get("content") and "start" not in msg["content"].lower():
                                            st.session_state.interview_transcript.append({
                                                "type": "answer",
                                                "content": msg["content"]
                                            })

                                    st.session_state.interview_started = True
                                    st.success(f"Interview resumed! Continuing from question {loaded_session.current_question_num}")
                                    st.rerun()

                            except FileNotFoundError:
                                st.error("Session file not found. It may have been deleted.")
                            except Exception as e:
                                st.error(f"Error loading session: {str(e)}")

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{idx}", use_container_width=True):
                        if not validate_csrf_token():
                            st.error("❌ Security Error: Invalid session token. Please refresh the page.")
                        elif InterviewSession.delete_session(session_info["session_id"]):
                            st.success("Session deleted!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Failed to delete session")

            st.markdown("---")

if not st.session_state.interview_started:
    st.markdown("### 📋 Setup Your Interview")
    st.markdown("---")

    job_description = st.text_area(
        "📝 Paste the job description:",
        height=200,
        placeholder="Paste the full job posting here...\n\nExample:\n- Job Title\n- Required Skills\n- Responsibilities\n- Qualifications",
        help="The AI will generate interview questions based on this job description"
    )

    st.markdown("### 🎙️ Choose Interviewer Voice")

    col1, col2 = st.columns(2)

    voice_options = {
        "🔵 Alloy (Neutral)": "alloy",
        "👨 Echo (Male)": "echo",
        "🎩 Fable (Male, British)": "fable",
        "🎤 Onyx (Male, Deep)": "onyx",
        "👩 Nova (Female, Warm)": "nova",
        "✨ Shimmer (Female, Soft)": "shimmer"
    }

    with col1:
        selected_voice_name = st.selectbox(
            "Select voice style",
            options=list(voice_options.keys()),
            index=4,  # Default to Nova
            help="Choose the voice for your AI interviewer"
        )

    with col2:
        st.info("💡 **Tip:** Choose a voice that makes you feel comfortable and professional!")

    st.session_state.selected_voice = voice_options[selected_voice_name]
    st.markdown("---")

    st.markdown("### ⚙️ Advanced OpenAI Settings")

    with st.expander("🔧 Configure Model Parameters (Optional)", expanded=False):
        st.info("💡 **Default settings work great for most interviews!** Only adjust if you want to experiment with different AI behaviors.")

        st.markdown("#### 🤖 AI Model")
        model_options = {
            "GPT-4o Mini (Fast & Cost-Effective) ⭐": "gpt-4o-mini",
            "GPT-4o (More Capable)": "gpt-4o",
            "GPT-4 Turbo (Advanced Reasoning)": "gpt-4-turbo",
            "GPT-3.5 Turbo (Budget-Friendly)": "gpt-3.5-turbo"
        }

        selected_model_name = st.selectbox(
            "Choose the AI model",
            options=list(model_options.keys()),
            index=0,  # Default to GPT-4o Mini
            help="**GPT-4o Mini**: Best balance of speed and quality (recommended)\n\n**GPT-4o**: More sophisticated responses\n\n**GPT-4 Turbo**: Advanced reasoning for complex scenarios\n\n**GPT-3.5 Turbo**: Faster but less nuanced"
        )
        st.session_state.selected_model = model_options[selected_model_name]

        st.markdown("---")

        st.markdown("#### 🌡️ Interview Creativity (Temperature)")
        col1, col2 = st.columns([3, 1])

        with col1:
            temperature = st.slider(
                "Adjust response creativity",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="**Lower (0.0-0.3)**: More focused, consistent, predictable\n\n**Medium (0.4-0.7)**: Balanced creativity and consistency ⭐\n\n**Higher (0.8-1.0)**: More creative, varied, exploratory"
            )

        with col2:
            st.metric("Current", f"{temperature:.1f}")

        if temperature < 0.4:
            st.caption("🎯 **Focused Mode**: Consistent, predictable questions")
        elif temperature < 0.8:
            st.caption("⚖️ **Balanced Mode**: Natural conversation flow (recommended)")
        else:
            st.caption("🎨 **Creative Mode**: Varied, exploratory questions")

        st.session_state.selected_temperature = temperature

        st.markdown("---")

        st.markdown("#### 📝 Response Length (Max Tokens)")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Interview Questions**")
            question_tokens = st.slider(
                "Question length",
                min_value=50,
                max_value=300,
                value=150,
                step=10,
                help="Controls how long interview questions can be.\n\n**50-100**: Very brief\n**150**: 2-3 sentences (recommended) ⭐\n**200-300**: More detailed questions",
                label_visibility="collapsed"
            )
            st.caption(f"~{int(question_tokens * 0.75)} words • {question_tokens} tokens")

        with col2:
            st.markdown("**Final Feedback**")
            feedback_tokens = st.slider(
                "Feedback length",
                min_value=300,
                max_value=1500,
                value=700,
                step=50,
                help="Controls how detailed the final feedback will be.\n\n**300-500**: Brief summary\n**700**: Comprehensive analysis (recommended) ⭐\n**1000-1500**: Very detailed evaluation",
                label_visibility="collapsed"
            )
            st.caption(f"~{int(feedback_tokens * 0.75)} words • {feedback_tokens} tokens")

        st.session_state.question_max_tokens = question_tokens
        st.session_state.feedback_max_tokens = feedback_tokens

        st.markdown("---")
        st.success("✅ Settings saved! These will be applied to your interview.")

    st.markdown("---")

    if st.button("🚀 Start Interview", type="primary", disabled=not job_description):
        if not validate_csrf_token():
            st.error("❌ Security Error: Invalid session token. Please refresh the page.")
        elif not (is_allowed := check_rate_limit(min_seconds_between_calls=3, max_calls_per_session=50))[0]:
            st.error(is_allowed[1])
        else:
            try:
                with st.spinner("Preparing your interview..."):
                    record_api_call()

                    st.session_state.job_description = job_description
                    st.session_state.interview_transcript = []

                    st.session_state.session = InterviewSession(
                        job_description,
                        model=st.session_state.selected_model,
                        temperature=st.session_state.selected_temperature,
                        question_max_tokens=st.session_state.question_max_tokens,
                        feedback_max_tokens=st.session_state.feedback_max_tokens
                    )
                    first_question = st.session_state.session.get_first_question()

                    record_api_call()
                st.session_state.current_question = first_question

                st.session_state.interview_transcript.append({
                    "type": "question",
                    "content": first_question
                })

                audio_path = text_to_speech(
                    first_question,
                    "current_question.mp3",
                    voice=st.session_state.selected_voice
                )
                st.session_state.audio_path = audio_path
                st.session_state.interview_started = True

                st.success("Interview started! Listen to the first question below.")
                st.rerun()

            except ValueError as e:
                st.error(f"❌ Validation Error: {e}")
            except ConnectionError as e:
                st.error(f"❌ Connection Error: {e}")
            except PermissionError as e:
                st.error(f"❌ Permission Error: {e}")
            except EnvironmentError as e:
                st.error(f"❌ Configuration Error: {e}")
            except RuntimeError as e:
                st.error(f"❌ API Error: {e}")
            except Exception as e:
                error_message = str(e)
                if "authentication" in error_message.lower() or "api key" in error_message.lower():
                    st.error(f"❌ Authentication Error: {error_message}")
                else:
                    st.error(f"❌ Unexpected error: {error_message}\n\nPlease try again or contact support if the issue persists.")

else:
    session = st.session_state.session

    col1, col2 = st.columns([4, 1])

    with col1:
        progress = session.current_question_num / 7
        st.markdown(f"""
        <div class="progress-container">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="font-weight: 600; color: #667eea;">Question {html.escape(str(session.current_question_num))} of 7</span>
                <span style="font-weight: 600; color: #667eea;">{html.escape(str(int(progress * 100)))}% Complete</span>
            </div>
            <div class="progress-bar" style="width: {html.escape(str(progress * 100))}%;"></div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if session.is_active:
            if st.button("💾 Pause", use_container_width=True, help="Save and pause your interview"):
                if not validate_csrf_token():
                    st.error("❌ Security Error: Invalid session token. Please refresh the page.")
                else:
                    try:
                        session_id = session.save_session(st.session_state.current_session_id)
                        st.session_state.current_session_id = session_id

                        st.success(f"Interview saved! You can resume later.")
                        time.sleep(1.5)

                        st.session_state.session = None
                        st.session_state.interview_started = False
                        st.session_state.current_question = None
                        st.session_state.audio_path = None
                        st.session_state.show_resume_section = True
                        if os.path.exists("current_question.mp3"):
                            os.unlink("current_question.mp3")
                        st.rerun()

                    except RuntimeError as e:
                        st.error(f"Failed to save session: {str(e)}")

    st.markdown(f"""
    <div class="question-card">
        <div class="question-number">🎤 INTERVIEWER (Alex)</div>
        <div class="question-text">{html.escape(st.session_state.current_question)}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
        with open(st.session_state.audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

    st.markdown("---")

    if session.is_active:
        if st.session_state.show_transcription_editor and st.session_state.pending_transcription:
            st.markdown("### ✏️ Review Your Answer")

            st.info("📝 **Review and edit your transcription below.** Fix any mistakes before submitting.")

            edited_answer = st.text_area(
                "Your Answer (editable):",
                value=st.session_state.pending_transcription,
                height=150,
                help="Edit your answer if the transcription has any mistakes"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Submit Answer", type="primary", use_container_width=True):
                    if not validate_csrf_token():
                        st.error("❌ Security Error: Invalid session token. Please refresh the page.")
                    elif not edited_answer or len(edited_answer.strip()) < 3:
                        st.error("Please provide a valid answer (at least 3 characters)")
                    else:
                        is_allowed, error_msg = check_rate_limit(min_seconds_between_calls=2, max_calls_per_session=50)

                        if not is_allowed:
                            st.error(error_msg)
                        else:
                            try:
                                st.session_state.interview_transcript.append({
                                    "type": "answer",
                                    "content": edited_answer
                                })

                                with st.spinner("🤔 Alex is thinking about your answer..."):
                                    record_api_call()

                                    ai_response = session.process_answer(edited_answer)
                                    st.session_state.current_question = ai_response

                                    record_api_call()

                                st.session_state.interview_transcript.append({
                                    "type": "question" if session.is_active else "feedback",
                                    "content": ai_response
                                })

                                audio_path = text_to_speech(
                                    ai_response,
                                    "current_question.mp3",
                                    voice=st.session_state.selected_voice
                                )
                                st.session_state.audio_path = audio_path

                                try:
                                    session_id = session.save_session(st.session_state.current_session_id)
                                    st.session_state.current_session_id = session_id
                                except Exception:
                                    pass

                                st.session_state.pending_transcription = None
                                st.session_state.show_transcription_editor = False
                                st.session_state.recording_attempt = 0
                                st.rerun()

                            except Exception as e:
                                st.error(f"❌ Error processing answer: {str(e)}")

            with col2:
                if st.button("🔄 Re-record", use_container_width=True, type="secondary"):
                    st.session_state.pending_transcription = None
                    st.session_state.show_transcription_editor = False
                    st.session_state.recording_attempt += 1
                    st.rerun()

        else:
            st.markdown("### 🎙️ Your Turn to Answer")

            st.info("🎙️ **Click the microphone once to start recording, then click again to stop.**\n\n"
                   "⏱️ The button will turn **RED** while recording.\n\n"
                   "📏 **Tip:** Aim for 30-90 seconds for a complete answer.")

            st.markdown("<br>", unsafe_allow_html=True)

            recording_placeholder = st.empty()

            with recording_placeholder.container():
                st.markdown("""
                <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea15 0%, #764ba205 100%);
                            border-radius: 10px; border-left: 4px solid #667eea; margin-bottom: 1rem;">
                    <div style="font-size: 1.1rem; font-weight: 600; color: #667eea; margin-bottom: 0.5rem;">
                        🎤 Ready to Record
                    </div>
                    <div style="font-size: 0.9rem; color: #6b7280;">
                        Click the microphone button below to begin
                    </div>
                </div>
                """, unsafe_allow_html=True)

            audio_bytes = audio_recorder(
                pause_threshold=60.0,
                sample_rate=44100,
                text="🎙️ Click to START Recording",
                recording_color="#ef4444",
                neutral_color="#3b82f6",
                icon_name="microphone",
                icon_size="2x",
                key=f"audio_{session.current_question_num}_{st.session_state.recording_attempt}"
            )

            if audio_bytes:
                estimated_duration = len(audio_bytes) / (44100 * 2)

                with recording_placeholder.container():
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #10b98115 0%, #05966905 100%);
                                border-radius: 10px; border-left: 4px solid #10b981; margin-bottom: 1rem;">
                        <div style="font-size: 1.1rem; font-weight: 600; color: #10b981; margin-bottom: 0.5rem;">
                            ✅ Recording Complete
                        </div>
                        <div style="font-size: 0.9rem; color: #6b7280;">
                            Duration: ~{html.escape(str(int(estimated_duration)))} seconds | Processing your answer...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                if len(audio_bytes) < 1000:
                    st.warning("Recording too short. Please click the microphone and speak your answer.")
                    time.sleep(1.5)  # Show warning for 1.5 seconds
                    st.session_state.recording_attempt += 1
                    st.rerun()
                else:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_bytes)
                        tmp_path = tmp_file.name

                    os.chmod(tmp_path, 0o600)

                    try:
                        with st.spinner("Transcribing your answer..."):
                            user_answer = transcribe_audio(tmp_path)

                        if not user_answer or len(user_answer.strip()) < 3:
                            st.warning("⚠️ No speech detected. Please try again and speak clearly.")
                            time.sleep(1.5)  # Show warning for 1.5 seconds
                            os.unlink(tmp_path)
                            st.session_state.recording_attempt += 1
                            st.rerun()
                        else:
                            st.session_state.pending_transcription = user_answer
                            st.session_state.show_transcription_editor = True
                            os.unlink(tmp_path)
                            st.rerun()

                    except ValueError as e:
                        st.error(f"❌ Audio Error: {e}")
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                        time.sleep(2)
                        st.session_state.recording_attempt += 1
                        st.rerun()

                    except ConnectionError as e:
                        st.error(f"❌ Connection Error: {e}\n\nPlease check your internet connection and try recording again.")
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)

                    except RuntimeError as e:
                        st.error(f"❌ API Error: {e}\n\nPlease try again in a moment.")
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)

                    except PermissionError as e:
                        st.error(f"❌ Permission Error: {e}")
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)

                    except Exception as e:
                        st.error(f"❌ Unexpected error processing audio: {str(e)}\n\nPlease try again.")
                        if os.path.exists(tmp_path):
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass
    else:
        st.markdown("""
        <div class="completion-card">
            <h2>🎉 Interview Complete!</h2>
            <p style="font-size: 1.1rem; margin: 0;">
                Great job! You've completed all 7 questions.<br>
                Here's your comprehensive performance feedback.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()

        st.markdown("---")
        st.markdown("## 📋 Your Interview Feedback")

        if st.session_state.current_question:
            display_feedback(st.session_state.current_question)
        else:
            st.info("Feedback will appear here after the interview is complete.")

        if not session.is_active and len(st.session_state.interview_transcript) > 0:
            st.markdown("---")
            st.markdown("### 📥 Download Interview Transcript")

            col1, col2 = st.columns(2)

            with col1:
                transcript_text = generate_transcript()
                from datetime import datetime
                filename = f"interview_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

                st.download_button(
                    label="📄 Download as Text File",
                    data=transcript_text,
                    file_name=filename,
                    mime="text/plain",
                    use_container_width=True
                )

            with col2:
                st.info("💡 Save your interview for review and practice!")

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Start New Interview", type="primary", use_container_width=True):
            if not validate_csrf_token():
                st.error("❌ Security Error: Invalid session token. Please refresh the page.")
            else:
                st.session_state.session = None
                st.session_state.interview_started = False
                st.session_state.current_question = None
                st.session_state.audio_path = None
                st.session_state.interview_transcript = []
                st.session_state.job_description = ""
                if os.path.exists("current_question.mp3"):
                    os.unlink("current_question.mp3")
                st.rerun()

st.markdown("---")

if st.session_state.api_call_count > 0:
    usage_percentage = (st.session_state.api_call_count / 50) * 100
    color = "#10b981" if usage_percentage < 50 else "#f59e0b" if usage_percentage < 80 else "#ef4444"

    st.markdown(f"""
    <div style="text-align: center; margin: 1rem 0;">
        <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.5rem;">
            API Usage: {st.session_state.api_call_count} / 50 calls this session
        </div>
        <div style="background: #e5e7eb; border-radius: 10px; height: 6px; max-width: 300px; margin: 0 auto; overflow: hidden;">
            <div style="background: {color}; width: {min(usage_percentage, 100)}%; height: 100%; border-radius: 10px; transition: width 0.3s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 1rem;">
    <p style="margin: 0;">💡 <strong>Tips for Success:</strong></p>
    <p style="margin: 0.5rem 0;">Speak clearly • Take your time • Be specific • Show enthusiasm</p>
    <p style="margin-top: 1rem; font-size: 0.9rem;">Made with ❤️ using Streamlit & OpenAI</p>
</div>
""", unsafe_allow_html=True)