import os
import json
from datetime import datetime
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, AuthenticationError
from dotenv import load_dotenv
from prompt_loader import prompt_loader


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError(
        "OpenAI API key not found. Please set OPENAI_API_KEY in your .env file. "
        "Get your API key from: https://platform.openai.com/api-keys"
    )

client = OpenAI(api_key=api_key)

MODEL = "gpt-4o-mini"
MAX_QUESTIONS = 7
SAVE_DIR = "saved_sessions"
MAX_SESSIONS_PER_USER = 20


def validate_api_key() -> bool:
    """
    Validate that the OpenAI API key is valid by making a minimal API call

    Returns:
        True if API key is valid

    Raises:
        AuthenticationError: If API key is invalid
        ConnectionError: If unable to connect to OpenAI API
        RuntimeError: If API validation fails for other reasons
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1,
            temperature=0
        )
        return True
    except AuthenticationError:
        raise AuthenticationError(
            "Invalid OpenAI API key. Please check your OPENAI_API_KEY in .env file. "
            "Get a valid API key from: https://platform.openai.com/api-keys"
        )
    except APIConnectionError:
        raise ConnectionError(
            "Unable to connect to OpenAI API. Please check your internet connection."
        )
    except RateLimitError:
        raise RuntimeError(
            "OpenAI API rate limit reached. Your key is valid but you've exceeded your quota. "
            "Check your usage at https://platform.openai.com/usage"
        )
    except APIError as e:
        raise RuntimeError(f"OpenAI API error during validation: {str(e)}")


class InterviewSession:
    """Manages the state and flow of an AI interview session"""

    def __init__(
        self,
        job_description: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        question_max_tokens: int = 150,
        feedback_max_tokens: int = 700
    ):
        """
        Initialize interview session with job description and optional OpenAI settings

        Args:
            job_description: The job posting text to base interview on
            model: OpenAI model to use (default: "gpt-4o-mini")
            temperature: Creativity level 0.0-1.0 (default: 0.7 for balanced natural conversation)
            question_max_tokens: Max tokens for interview questions (default: 150 = ~2-3 sentences)
            feedback_max_tokens: Max tokens for final feedback (default: 700 = comprehensive analysis)

        Raises:
            ValueError: If job description is invalid
            AuthenticationError: If API key is invalid
            ConnectionError: If unable to connect to OpenAI API
            RuntimeError: If API validation fails
        """
        if not job_description:
            raise ValueError("You must enter a job description")

        validate_api_key()

        self.model = model
        self.temperature = temperature
        self.question_max_tokens = question_max_tokens
        self.feedback_max_tokens = feedback_max_tokens

        self._validate_job_description(job_description.strip())

        self.job_description = job_description.strip()
        self.conversation_history = []
        self.current_question_num = 0
        self.is_active = True
        self.session_id = None
        self.created_at = datetime.now().isoformat()
        self.last_saved_at = None

        self.prompt_versions = prompt_loader.get_all_versions()

        self._initialize_conversation()

    def _validate_job_description(self, job_description: str):
        """
        Validate that the job description is meaningful and not gibberish

        Args:
            job_description: The job description text to validate

        Raises:
            ValueError: If the job description appears invalid or is gibberish
        """
        if len(job_description.split()) < 20:
            raise ValueError("Job description must contain at least 20 words")

        validation_prompt = prompt_loader.render("validation_prompt.j2", job_description=job_description)

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a job description validator. Respond only with VALID or INVALID."},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0,
                max_tokens=10 
            )

            result = response.choices[0].message.content.strip().upper()

            if result != "VALID":
                raise ValueError(
                    "The text you entered doesn't appear to be a valid job description. "
                    "Please paste an actual job posting with role information, required skills, and responsibilities."
                )

        except RateLimitError:
            raise RuntimeError(
                "OpenAI API rate limit reached. Please wait a moment and try again, "
                "or check your API usage at https://platform.openai.com/usage"
            )
        except APIConnectionError:
            raise ConnectionError(
                "Unable to connect to OpenAI API. Please check your internet connection and try again."
            )
        except AuthenticationError:
            raise RuntimeError(
                "Invalid OpenAI API key. Please check your OPENAI_API_KEY in .env file."
            )
        except APIError as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def _initialize_conversation(self):
        """Set up the initial system prompt for the interview"""
        system_prompt = prompt_loader.render("system_prompt.j2", job_description=self.job_description, max_questions=MAX_QUESTIONS)
        
        self.conversation_history.append({
            "role": "system",
            "content": system_prompt
        })

    def get_first_question(self) -> str:
        """
        Generate the first interview question

        Returns:
            The AI's first question as text

        Raises:
            ConnectionError: If unable to connect to OpenAI API
            RuntimeError: If API request fails
        """
        initial_prompt = prompt_loader.render("initial_prompt.j2")

        self.conversation_history.append({
            "role": "user",
            "content": initial_prompt
        })

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=self.temperature,
                max_tokens=self.question_max_tokens
            )

            ai_response = response.choices[0].message.content

            is_hallucination, explanation = self._detect_hallucinated_requirements(ai_response)

            if is_hallucination:
                correction_prompt = f"""CRITICAL REMINDER: The previous response may have referenced skills or requirements NOT in the original job description.

ONLY ask about:
1. Skills explicitly mentioned in: {self.job_description[:200]}...
2. General behavioral questions (background, motivation, experience)
3. Why they're interested in this specific role

DO NOT ask about specific technologies or tools unless they appear in the job description above.

Now provide your first question as the interviewer."""

                self.conversation_history.append({
                    "role": "system",
                    "content": correction_prompt
                })

                try:
                    response = client.chat.completions.create(
                        model=self.model,
                        messages=self.conversation_history,
                        temperature=self.temperature,
                        max_tokens=self.question_max_tokens
                    )
                    ai_response = response.choices[0].message.content
                    self.conversation_history.pop()
                except Exception:
                    self.conversation_history.pop()

            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })

            self.current_question_num = 1
            return ai_response

        except RateLimitError:
            raise RuntimeError(
                "OpenAI API rate limit reached. Please wait a moment and try again, "
                "or check your API usage at https://platform.openai.com/usage"
            )
        except APIConnectionError:
            raise ConnectionError(
                "Unable to connect to OpenAI API. Please check your internet connection and try again."
            )
        except AuthenticationError:
            raise RuntimeError(
                "Invalid OpenAI API key. Please check your OPENAI_API_KEY in .env file."
            )
        except APIError as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def _check_content_appropriateness(self, text: str) -> bool:
        """
        Check if user's response is appropriate using OpenAI Moderation API

        Args:
            text: The user's answer to check

        Returns:
            True if appropriate, False if inappropriate
        """
        try:
            moderation = client.moderations.create(input=text)
            return not moderation.results[0].flagged
        except Exception:
            return False

    def _detect_prompt_injection(self, text: str) -> bool:
        """
        Detect potential prompt injection attempts in user input

        Args:
            text: The user's answer to check

        Returns:
            True if injection detected, False if safe
        """
        text_lower = text.lower().strip()

        injection_patterns = [
            "ignore previous instructions",
            "ignore all previous instructions",
            "disregard previous instructions",
            "forget previous instructions",
            "ignore the above",
            "ignore your instructions",
            "new instructions:",
            "override instructions",
            "you are now",
            "act as a",
            "pretend you are",
            "roleplay as",
            "you must now",
            "from now on",
            "new role:",
            "system:",
            "system prompt",
            "system message",
            "[system]",
            "<system>",
            "developer mode",
            "admin mode",
            "debug mode",
            "jailbreak",
            "dan mode",
            "repeat the instructions",
            "what are your instructions",
            "show me your prompt",
            "print your prompt",
            "output your instructions",
            "instead, tell",
            "instead, do",
            "instead, ignore",
            "instead, say",
            "but actually, you should",
            "instead of answering"
        ]

        for pattern in injection_patterns:
            if pattern in text_lower:
                return True

        if text_lower.startswith(("system:", "assistant:", "user:", "###", "---")):
            return True

        role_keywords = ["system:", "assistant:", "user:"]
        role_count = sum(1 for keyword in role_keywords if keyword in text_lower)
        if role_count >= 2:
            return True

        return False

    def _detect_hallucinated_requirements(self, ai_response: str) -> tuple[bool, str]:
        """
        Detect if the AI interviewer is making up requirements, responsibilities,
        or company details not mentioned in the original job description

        Uses a lightweight LLM call to compare AI's question/feedback against
        the actual job description to catch hallucinations of any type:
        - Technical skills not in job description
        - Responsibilities not mentioned
        - Company culture claims without basis
        - Made-up team structure or processes

        Args:
            ai_response: The AI's generated question or feedback to validate

        Returns:
            Tuple of (is_hallucination: bool, explanation: str)
        """
        validation_prompt = f"""You are a hallucination detector for an AI interview system.

ORIGINAL JOB DESCRIPTION:
{self.job_description}

AI INTERVIEWER'S QUESTION/STATEMENT:
{ai_response}

Task: Determine if the AI interviewer is making claims or asking about things NOT mentioned in the original job description.

Examples of hallucinations:
- Asking about "Python" when job only mentions "Java"
- Asking about "leading a team" when job says "individual contributor"
- Mentioning "startup culture" when job description says nothing about company culture
- Asking about "microservices architecture" when job doesn't mention it
- Making up specific responsibilities not in the job description

Examples of VALID questions (NOT hallucinations):
- Asking about skills explicitly mentioned in job description
- Asking behavioral questions about collaboration (general, not specific to job)
- Asking to elaborate on experience relevant to stated responsibilities
- Using synonyms (e.g., job says "software development" → AI asks about "coding")

Respond with ONLY one word:
- VALID: If question/statement is based on job description or is a general interview question
- HALLUCINATION: If question/statement makes specific claims not in the job description"""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a hallucination detector. Respond only with VALID or HALLUCINATION."},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0,
                max_tokens=20 
            )

            result = response.choices[0].message.content.strip().upper()

            if "HALLUCINATION" in result:
                return True, "The AI interviewer asked about something not mentioned in the job description"
            else:
                return False, ""

        except Exception:
            return False, ""

    def process_answer(self, user_answer: str) -> str:
        """
        Process user's answer and get next question or feedback

        Args:
            user_answer: Transcribed text of user's spoken answer

        Returns:
            AI's response (next question or final feedback)

        Raises:
            ConnectionError: If unable to connect to OpenAI API
            RuntimeError: If API request fails
        """
        if not user_answer or len(user_answer.strip()) < 5:
            return "I didn't catch that. Could you please repeat your answer?"

        if self._detect_prompt_injection(user_answer):
            return "I noticed some unusual patterns in your response. Please answer the interview question directly and professionally."

        if not self._check_content_appropriateness(user_answer):
            return "I appreciate your response, but let's keep this interview professional. Could you please answer the question appropriately?"

        sanitized_answer = user_answer.strip()

        self.conversation_history.append({
            "role": "user",
            "content": sanitized_answer
        })

        if self.current_question_num >= MAX_QUESTIONS:
            prompt = prompt_loader.render("feedback_prompt.j2")

            self.conversation_history.append({
                "role": "system",
                "content": prompt
            })

            self.is_active = False
        else:
            self.current_question_num += 1
            prompt = prompt_loader.render("next_question_prompt.j2", current_question=self.current_question_num, max_questions=MAX_QUESTIONS)

            self.conversation_history.append({
                "role": "system",
                "content": prompt
            })

        try:
            is_feedback = self.current_question_num >= MAX_QUESTIONS
            token_limit = self.feedback_max_tokens if is_feedback else self.question_max_tokens

            response = client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=self.temperature,
                max_tokens=token_limit
            )

            ai_response = response.choices[0].message.content

            is_hallucination, explanation = self._detect_hallucinated_requirements(ai_response)

            if is_hallucination:
                self.conversation_history.pop()

                correction_prompt = f"""CRITICAL REMINDER: The previous response may have referenced skills, responsibilities, or requirements NOT in the original job description.

ONLY ask about:
1. Skills explicitly mentioned in: {self.job_description[:200]}...
2. General behavioral questions (teamwork, problem-solving, communication)
3. Clarifications about their stated experience

DO NOT ask about specific technologies, tools, or responsibilities unless they appear in the job description above.

Now provide your {"next question" if self.current_question_num < MAX_QUESTIONS else "feedback"}."""

                self.conversation_history.append({
                    "role": "system",
                    "content": correction_prompt
                })

                try:
                    response = client.chat.completions.create(
                        model=self.model,
                        messages=self.conversation_history,
                        temperature=self.temperature,
                        max_tokens=token_limit
                    )
                    ai_response = response.choices[0].message.content
                except Exception:
                    pass

            self.conversation_history.pop()
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })

            return ai_response

        except RateLimitError:
            self.conversation_history.pop()
            raise RuntimeError(
                "OpenAI API rate limit reached. Please wait a moment and try again."
            )
        except APIConnectionError:
            self.conversation_history.pop()
            raise ConnectionError(
                "Unable to connect to OpenAI API. Please check your internet connection."
            )
        except AuthenticationError:
            self.conversation_history.pop()
            raise RuntimeError(
                "Invalid OpenAI API key. Please check your credentials."
            )
        except APIError as e:
            self.conversation_history.pop()
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    @staticmethod
    def _cleanup_old_sessions():
        """
        Remove oldest sessions if we exceed MAX_SESSIONS_PER_USER limit.
        This prevents disk from filling up with too many saved sessions.
        """
        sessions = InterviewSession.list_saved_sessions()

        if len(sessions) >= MAX_SESSIONS_PER_USER:
            num_to_delete = len(sessions) - MAX_SESSIONS_PER_USER + 1

            sessions_to_delete = sessions[-num_to_delete:]

            for session in sessions_to_delete:
                try:
                    InterviewSession.delete_session(session["session_id"])
                except Exception:
                    continue

    def save_session(self, session_id: str = None) -> str:
        """
        Save the current interview session to disk

        Args:
            session_id: Optional session ID to use. If None, generates a new one.

        Returns:
            The session ID used for saving

        Raises:
            RuntimeError: If unable to save session
        """
        self._cleanup_old_sessions()

        if not os.path.exists(SAVE_DIR):
            try:
                os.makedirs(SAVE_DIR, mode=0o700, exist_ok=True)
            except OSError as e:
                raise RuntimeError(f"Unable to create save directory: {str(e)}")

        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.session_id = session_id
        self.last_saved_at = datetime.now().isoformat()

        session_data = {
            "session_id": self.session_id,
            "job_description": self.job_description,
            "conversation_history": self.conversation_history,
            "current_question_num": self.current_question_num,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_saved_at": self.last_saved_at,
            "prompt_versions": self.prompt_versions,
            "model": self.model,
            "temperature": self.temperature,
            "question_max_tokens": self.question_max_tokens,
            "feedback_max_tokens": self.feedback_max_tokens
        }

        file_path = os.path.join(SAVE_DIR, f"{session_id}.json")
        try:
            fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'w') as f:
                json.dump(session_data, f, indent=2)
            return session_id
        except (IOError, OSError) as e:
            raise RuntimeError(f"Unable to save session: {str(e)}")

    @classmethod
    def load_session(cls, session_id: str) -> 'InterviewSession':
        """
        Load a saved interview session from disk

        Args:
            session_id: The session ID to load

        Returns:
            InterviewSession object with restored state

        Raises:
            FileNotFoundError: If session file doesn't exist
            RuntimeError: If unable to load or parse session
        """
        file_path = os.path.join(SAVE_DIR, f"{session_id}.json")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Session not found: {session_id}")

        try:
            with open(file_path, 'r') as f:
                session_data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Unable to load session: {str(e)}")

        instance = cls.__new__(cls)
        instance.job_description = session_data["job_description"]
        instance.conversation_history = session_data["conversation_history"]
        instance.current_question_num = session_data["current_question_num"]
        instance.is_active = session_data["is_active"]
        instance.session_id = session_data["session_id"]
        instance.created_at = session_data["created_at"]
        instance.last_saved_at = session_data["last_saved_at"]

        instance.prompt_versions = session_data.get("prompt_versions", {})

        instance.model = session_data.get("model", "gpt-4o-mini")
        instance.temperature = session_data.get("temperature", 0.7)
        instance.question_max_tokens = session_data.get("question_max_tokens", 150)
        instance.feedback_max_tokens = session_data.get("feedback_max_tokens", 700)

        return instance

    @staticmethod
    def list_saved_sessions() -> list:
        """
        List all saved interview sessions

        Returns:
            List of dictionaries with session info (id, created_at, last_saved_at)
        """
        if not os.path.exists(SAVE_DIR):
            return []

        sessions = []
        try:
            for filename in os.listdir(SAVE_DIR):
                if filename.endswith('.json'):
                    file_path = os.path.join(SAVE_DIR, filename)
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            sessions.append({
                                "session_id": data.get("session_id", filename[:-5]),
                                "created_at": data.get("created_at"),
                                "last_saved_at": data.get("last_saved_at"),
                                "current_question": data.get("current_question_num", 0),
                                "is_active": data.get("is_active", True)
                            })
                    except (IOError, json.JSONDecodeError):
                        continue
        except OSError:
            return []

        sessions.sort(key=lambda x: x.get("last_saved_at", ""), reverse=True)
        return sessions

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """
        Delete a saved interview session

        Args:
            session_id: The session ID to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        file_path = os.path.join(SAVE_DIR, f"{session_id}.json")
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                return True
            return False
        except OSError:
            return False


def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio to text using Whisper API

    Args:
        audio_file_path: Path to audio file (mp3, wav, etc.)

    Returns:
        Transcribed text

    Raises:
        FileNotFoundError: If audio file doesn't exist
        ValueError: If file is too large, corrupted, or invalid format
        ConnectionError: If unable to connect to OpenAI API
        RuntimeError: If API request fails
    """
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    try:
        file_size = os.path.getsize(audio_file_path)
    except OSError as e:
        raise ValueError(f"Unable to read audio file: {str(e)}")

    if file_size == 0:
        raise ValueError("Audio file is empty (0 bytes)")

    if file_size > 25 * 1024 * 1024:
        raise ValueError("Audio file too large (max 25MB)")

    try:
        with open(audio_file_path, "rb") as audio_file:
            audio_file.read(10)
            audio_file.seek(0) 

            try:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en",
                    prompt="This is a professional job interview answer. May contain technical terms like Python, JavaScript, React, AWS, API, CI/CD, Docker, Kubernetes, SQL, PostgreSQL, Git, GitHub, microservices, and other programming languages, frameworks, cloud services, and industry-standard acronyms. Speaker may use natural conversational fillers and professional phrases."
                )
            except RateLimitError:
                raise RuntimeError(
                    "OpenAI API rate limit reached. Please wait a moment and try again."
                )
            except APIConnectionError:
                raise ConnectionError(
                    "Unable to connect to OpenAI API. Please check your internet connection."
                )
            except AuthenticationError:
                raise RuntimeError(
                    "Invalid OpenAI API key. Please check your credentials."
                )
            except APIError as e:
                if "invalid" in str(e).lower() or "format" in str(e).lower():
                    raise ValueError(
                        "Invalid or corrupted audio file. Please ensure it's a valid audio format (mp3, wav, etc.)"
                    )
                raise RuntimeError(f"OpenAI API error during transcription: {str(e)}")

    except IOError as e:
        raise ValueError(f"Unable to read audio file: {str(e)}")

    hallucination_phrases = [
        "thanks for watching",
        "thank you for watching",
        "please subscribe",
        "like and subscribe",
        "don't forget to subscribe",
        "see you next time",
        "see you soon",
        "see you later",
        "bye",
        "goodbye",
        "music",
        "[music]",
        "subtitles by",
        ".",
        "you"
    ]

    text = transcript.text.strip().lower()

    if any(phrase in text for phrase in hallucination_phrases) and len(text.split()) < 10:
        return ""

    return transcript.text


def text_to_speech(text: str, output_path: str = "question.mp3", voice: str = "nova") -> str:
    """
    Convert text to speech using OpenAI TTS API

    Args:
        text: The text to speak
        output_path: Where to save the audio file
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)

    Returns:
        Path to the generated audio file

    Raises:
        ValueError: If text is empty or too long
        PermissionError: If unable to write to output path
        ConnectionError: If unable to connect to OpenAI API
        RuntimeError: If API request fails
    """
    if not text or len(text.strip()) == 0:
        raise ValueError("Text cannot be empty")

    if len(text) > 4096:
        raise ValueError("Text too long for TTS (max 4096 characters)")

    valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    if voice not in valid_voices:
        voice = "nova"

    output_dir = os.path.dirname(output_path) or "."
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            raise PermissionError(f"Cannot create directory for audio file: {str(e)}")

    if not os.access(output_dir, os.W_OK):
        raise PermissionError(f"No write permission for directory: {output_dir}")

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )

        response.stream_to_file(output_path)
        return output_path

    except RateLimitError:
        raise RuntimeError(
            "OpenAI API rate limit reached. Please wait a moment and try again."
        )
    except APIConnectionError:
        raise ConnectionError(
            "Unable to connect to OpenAI API. Please check your internet connection."
        )
    except AuthenticationError:
        raise RuntimeError(
            "Invalid OpenAI API key. Please check your credentials."
        )
    except APIError as e:
        raise RuntimeError(f"OpenAI API error during text-to-speech: {str(e)}")
    except IOError as e:
        raise PermissionError(f"Unable to write audio file to {output_path}: {str(e)}")
