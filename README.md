# 🎤 AI Interview Simulator

An interactive voice-based interview practice application powered by OpenAI's GPT-4 and Whisper APIs. Practice realistic job interviews with an AI interviewer that adapts questions based on actual job descriptions.

## ✨ Features

- **Voice-Based Interviews**: Record your answers using your microphone
- **Real Job Descriptions**: Paste actual job postings for tailored interview questions
- **7-Question Interview Flow**: Structured practice session with follow-up questions
- **AI-Powered Feedback**: Comprehensive performance analysis with ratings
- **Multiple AI Voices**: Choose from 6 different voice options for the interviewer
- **Session Management**: Pause and resume interviews anytime
- **Performance Scoring**: Visual score cards across multiple evaluation categories
- **Interview Transcripts**: Download complete conversation history
- **Customizable AI Settings**: Adjust model, temperature, and token limits

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- UV package manager ([Install UV](https://github.com/astral-sh/uv))

### Installation

1. **Clone the repository**
   ```bash
   git clone <https://github.com/TuringCollegeSubmissions/gsmulk-AE.1.4.git>
   cd gsmulk-AE.1.4
   ```

2. **Install dependencies with UV**
   ```bash
   uv sync
   ```

   This will automatically create a virtual environment and install all dependencies.

3. **Set up environment variables**

   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```

4. **Run the application**
   ```bash
   uv run streamlit run app2.py
   ```

5. **Open your browser**

   Navigate to `http://localhost:8501`

## 📖 How to Use

### Starting an Interview

1. **Paste a job description** - Copy and paste the full job posting
2. **Choose interviewer voice** - Select from 6 voice options (Nova recommended)
3. **Optional: Configure AI settings** - Adjust model, temperature, and response length
4. **Click "Start Interview"** - Begin your practice session

### During the Interview

1. **Listen to the question** - Audio plays automatically
2. **Click the microphone** - Start recording your answer
3. **Speak your response** - Aim for 30-90 seconds
4. **Click again to stop** - Review and edit the transcription
5. **Submit your answer** - AI generates the next question

### After Completion

- **View performance scores** - See ratings across 4 categories
- **Read detailed feedback** - Get comprehensive analysis
- **Download transcript** - Save the complete interview for review

## 🎙️ Voice Options

- **Alloy** - Neutral, balanced tone
- **Echo** - Male voice
- **Fable** - Male, British accent
- **Onyx** - Male, deep voice
- **Nova** - Female, warm tone (recommended)
- **Shimmer** - Female, soft voice

## ⚙️ Advanced Settings

### AI Model Selection

- **GPT-4o Mini** (Default) - Fast and cost-effective
- **GPT-4o** - More sophisticated responses
- **GPT-4 Turbo** - Advanced reasoning
- **GPT-3.5 Turbo** - Budget-friendly option

### Temperature (0.0 - 1.0)

- **0.0-0.3** - Focused, consistent questions
- **0.7** (Default) - Balanced, natural conversation
- **0.8-1.0** - Creative, varied questions

### Token Limits

- **Question tokens**: 150 (default) - Controls question length
- **Feedback tokens**: 700 (default) - Controls feedback detail

## 📁 Project Structure

```
gsmulk-AE.1.4/
├── app2.py                 # Main Streamlit application
├── interview_logic.py      # Core interview session logic
├── prompt_loader.py        # Jinja2 template management
├── prompts/                # AI prompt templates
│   ├── system_prompt.j2
│   ├── validation_prompt.j2
│   ├── initial_prompt.j2
│   ├── next_question_prompt.j2
│   └── feedback_prompt.j2
├── saved_sessions/         # Paused interview sessions
├── pyproject.toml          # Python dependencies (UV)
├── .env                    # Environment variables (create this)
└── README.md               # This file
```

## 🔒 Security Features

- **CSRF Protection** - Session token validation
- **Rate Limiting** - 50 API calls per session, 3-second cooldown
- **Prompt Injection Detection** - Blocks malicious input patterns
- **Content Moderation** - OpenAI moderation API integration
- **Hallucination Detection** - Prevents AI from inventing job requirements
- **Secure File Permissions** - 600 (owner-only) for saved files

## 💾 Session Management

### Pause & Resume

Interviews are automatically saved after each answer. You can:

- **Pause** - Save your progress and return later
- **Resume** - Continue from where you left off
- **Delete** - Remove old sessions (max 20 sessions per user)

### Session Files

Sessions are stored in `saved_sessions/` as JSON files with:
- Complete conversation history
- Current question number
- Job description
- AI model settings
- Prompt template versions

## 📊 Performance Evaluation

### Scoring Categories

1. **Technical Competency** - Job-specific skills and knowledge
2. **Communication Skills** - Clarity and articulation
3. **Cultural Fit** - Alignment with role expectations
4. **Overall Recommendation** - Final hiring decision

### Rating Scale

- **75-100%** - Excellent performance
- **50-74%** - Good performance
- **Below 50%** - Needs improvement

## 📦 Dependencies

Key packages (see `pyproject.toml` for complete list):

- **streamlit** - Web application framework
- **openai** - OpenAI API client
- **audio-recorder-streamlit** - Voice recording widget
- **python-dotenv** - Environment variable management
- **jinja2** - Template engine for prompts

## 🛠️ Configuration

### Environment Variables

```bash
OPENAI_API_KEY=sk-...  # Required: Your OpenAI API key
```

### Constants (in `interview_logic.py`)

```python
MODEL = "gpt-4o-mini"           # Default AI model
MAX_QUESTIONS = 7               # Interview length
SAVE_DIR = "saved_sessions"     # Session storage
MAX_SESSIONS_PER_USER = 20      # Session limit
```

## ❓ Troubleshooting

### "API key not found" error
- Ensure `.env` file exists in project root
- Verify `OPENAI_API_KEY` is set correctly
- Check API key is valid at [OpenAI Platform](https://platform.openai.com/api-keys)

### Recording issues
- Grant microphone permissions in your browser
- Use Chrome/Edge for best compatibility
- Check audio input device in system settings

### Rate limit errors
- Wait 3 seconds between API calls
- Refresh page to reset session counter
- Check API usage at [OpenAI Usage Dashboard](https://platform.openai.com/usage)

### Session not loading
- Session file may be corrupted - delete and restart
- Check `saved_sessions/` directory permissions
- Ensure sufficient disk space

## 🔧 Development

### Prompt Templates

Templates use Jinja2 syntax in `prompts/` directory:

- **system_prompt.j2** - Interview session initialization
- **validation_prompt.j2** - Job description validation
- **initial_prompt.j2** - First question generation
- **next_question_prompt.j2** - Follow-up question logic
- **feedback_prompt.j2** - Final performance evaluation

Each template includes version tracking for reproducibility.

---

**Note**: This application requires an active OpenAI API key and will incur usage costs based on your API calls. Monitor your usage at [platform.openai.com/usage](https://platform.openai.com/usage).
