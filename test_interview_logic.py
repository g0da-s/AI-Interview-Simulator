"""Unit tests for interview_logic.py"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from interview_logic import InterviewSession, validate_api_key, transcribe_audio, text_to_speech
from openai import AuthenticationError, APIConnectionError, RateLimitError, APIError


class TestValidateApiKey:
    """Test API key validation"""
    
    @patch('interview_logic.client.chat.completions.create')
    def test_validate_api_key_success(self, mock_create):
        """Test successful API key validation"""
        mock_create.return_value = Mock()
        assert validate_api_key() is True
        mock_create.assert_called_once()
    
    @patch('interview_logic.client.chat.completions.create')
    def test_validate_api_key_auth_error(self, mock_create):
        """Test invalid API key raises AuthenticationError"""
        mock_create.side_effect = AuthenticationError("Invalid API key", response=Mock(), body={})
        
        with pytest.raises(AuthenticationError) as exc_info:
            validate_api_key()
        assert "Invalid OpenAI API key" in str(exc_info.value)
    
    @patch('interview_logic.client.chat.completions.create')
    def test_validate_api_key_connection_error(self, mock_create):
        """Test connection error raises ConnectionError"""
        mock_create.side_effect = APIConnectionError("Connection failed")
        
        with pytest.raises(ConnectionError) as exc_info:
            validate_api_key()
        assert "Unable to connect to OpenAI API" in str(exc_info.value)


class TestInterviewSession:
    """Test InterviewSession class"""
    
    @patch('interview_logic.prompt_loader')
    def test_init_with_defaults(self, mock_prompt_loader):
        """Test session initialization with default parameters"""
        session = InterviewSession()
        
        assert session.job_description is None
        assert session.questions == []
        assert session.answers == []
        assert session.current_question_number == 0
        assert session.is_complete is False
        assert session.session_id is not None
        assert len(session.session_id) == 32  # UUID hex length
    
    @patch('interview_logic.prompt_loader')
    def test_init_with_custom_job(self, mock_prompt_loader):
        """Test session initialization with custom job description"""
        job_desc = "Senior Python Developer"
        session = InterviewSession(job_description=job_desc)
        
        assert session.job_description == job_desc
    
    @patch('interview_logic.prompt_loader')
    def test_add_question(self, mock_prompt_loader):
        """Test adding questions to session"""
        session = InterviewSession()
        question = "Tell me about yourself"
        
        session._add_question(question)
        
        assert len(session.questions) == 1
        assert session.questions[0] == question
    
    @patch('interview_logic.prompt_loader')
    def test_add_answer(self, mock_prompt_loader):
        """Test adding answers to session"""
        session = InterviewSession()
        answer = "I'm a software developer with 5 years experience"
        
        session._add_answer(answer)
        
        assert len(session.answers) == 1
        assert session.answers[0] == answer
    
    @patch('interview_logic.prompt_loader')
    def test_get_conversation_history_empty(self, mock_prompt_loader):
        """Test conversation history when empty"""
        session = InterviewSession()
        history = session.get_conversation_history()
        
        assert history == []
    
    @patch('interview_logic.prompt_loader')
    def test_get_conversation_history_with_data(self, mock_prompt_loader):
        """Test conversation history with questions and answers"""
        session = InterviewSession()
        session._add_question("Question 1")
        session._add_answer("Answer 1")
        session._add_question("Question 2")
        
        history = session.get_conversation_history()
        
        expected = [
            {"role": "assistant", "content": "Question 1"},
            {"role": "user", "content": "Answer 1"},
            {"role": "assistant", "content": "Question 2"}
        ]
        assert history == expected
