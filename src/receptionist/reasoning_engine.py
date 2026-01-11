"""Reasoning engine using Fireworks AI for tool calling and response generation."""

import json
import logging
import re
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx

from .config import Settings
from .models import BusinessConfig

logger = logging.getLogger(__name__)


class Tool(Enum):
    """Available tools for the reasoning engine."""
    SEARCH_EMAILS = "search_emails"
    SEARCH_CONTACTS = "search_contacts"
    CHECK_CALENDAR = "check_calendar"
    SCHEDULE_MEETING = "schedule_meeting"
    END_CALL = "end_call"
    GENERATE_RESPONSE = "generate_response"


@dataclass
class ToolCall:
    """Represents a tool call decision."""
    tool: Tool
    arguments: dict[str, Any]


@dataclass
class CallOutcome:
    """Structured outcome of a call analysis."""
    summary: str
    decision: str  # handled, scheduled, escalated, rejected
    decision_label: str
    reasoning: str
    action_taken: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "decision": self.decision,
            "decision_label": self.decision_label,
            "reasoning": self.reasoning,
            "action_taken": self.action_taken,
        }


class ReasoningEngine:
    """Uses Fireworks AI for tool calling decisions and response generation.
    
    This class provides methods to:
    - Decide which tools to invoke based on transcript
    - Generate contextual responses
    - Extract caller information from transcripts
    - Synthesize context from search results
    """

    FIREWORKS_API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
    MODEL = "accounts/fireworks/models/minimax-m2p1"

    TOOL_SCHEMAS = [
        {
            "type": "function",
            "function": {
                "name": "search_emails",
                "description": "Search emails for relevant context about a topic or person",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant emails"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_contacts",
                "description": "Search contacts by name to find information about a person",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the person to search for"
                        }
                    },
                    "required": ["name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_calendar",
                "description": "Check calendar availability for a specific date to see what times are free or busy. Use this ONLY when the caller asks about availability without requesting to book.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date to check availability for (YYYY-MM-DD format)"
                        },
                        "time_preference": {
                            "type": "string",
                            "description": "Preferred time of day: morning, afternoon, or evening"
                        }
                    },
                    "required": ["date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "schedule_meeting",
                "description": "CREATE a new meeting on Google Calendar. USE THIS when caller wants to book, schedule, set up, or create a meeting/appointment. This actually creates the calendar event.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Meeting title or purpose (e.g., 'Project Planning', 'Doctor Appointment')"
                        },
                        "date": {
                            "type": "string",
                            "description": "Meeting date in YYYY-MM-DD format"
                        },
                        "time": {
                            "type": "string",
                            "description": "Start time in HH:MM 24-hour format (e.g., '21:00' for 9pm, '14:30' for 2:30pm)"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Duration in minutes. Default 60 for 1 hour."
                        },
                        "attendee_name": {
                            "type": "string",
                            "description": "Name of the caller if provided"
                        },
                        "attendee_email": {
                            "type": "string",
                            "description": "Email of the caller if provided"
                        }
                    },
                    "required": ["title", "date", "time"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "end_call",
                "description": "MUST USE when caller says: 'thank you', 'thanks', 'bye', 'goodbye', 'that's all', 'that's it', 'no thanks', 'I'm done', or any farewell. Also use after confirming a booking is complete.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "farewell_message": {
                            "type": "string",
                            "description": "Brief goodbye like 'You're welcome, goodbye!' or 'Have a great day!'"
                        }
                    },
                    "required": ["farewell_message"]
                }
            }
        }
    ]

    # Default timezone for calendar operations
    DEFAULT_TIMEZONE = "America/Los_Angeles"

    BASE_SYSTEM_PROMPT = """You are Donna, a friendly AI receptionist. Speak naturally and briefly.

RULES:
1. Output ONLY spoken words - no thinking, tags, or brackets
2. 1-2 sentences max
3. NEVER repeat yourself - if you already greeted them, don't greet again
4. NEVER say "How can I help?" more than once per call
5. Listen and respond to what they actually said

CONVERSATION FLOW:
- First response: Greet once, then LISTEN
- After that: Respond to their request, don't ask generic questions
- If they said something, acknowledge it specifically
- If they're done: Use end_call tool

CALENDAR: Pacific Time. Say "Done!" when booked.

ENDING CALLS - Use end_call when:
- Caller says goodbye/thanks/that's all
- Task is complete
- Conversation has concluded

NEVER DO: Repeat greetings, ask "how can I help" multiple times, ignore what caller said"""





    def __init__(self, settings: Settings | None = None, business_config: BusinessConfig | None = None):
        """Initialize the ReasoningEngine with Fireworks AI client.
        
        Args:
            settings: Application settings. If None, loads from environment.
            business_config: Business configuration with CEO/company info.
        """
        if settings is None:
            from .config import get_settings
            settings = get_settings()
        
        self._settings = settings
        self._api_key = settings.fireworks_api_key
        self._client = httpx.AsyncClient(timeout=30.0)
        self._business_config = business_config

    def set_business_config(self, config: BusinessConfig) -> None:
        """Update the business configuration."""
        self._business_config = config

    def _clean_ai_response(self, content: str) -> str:
        """Aggressively clean AI response to remove all reasoning/thinking artifacts."""
        
        # First pass: Remove all XML-style tags and their content
        content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<reasoning>.*?</reasoning>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<scratchpad>.*?</scratchpad>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<reflection>.*?</reflection>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<internal>.*?</internal>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<response>.*?</response>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<output>.*?</output>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<[^>]+>.*?</[^>]+>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'</?[a-z_]+/?>', '', content, flags=re.IGNORECASE)
        
        # Remove asterisk/bracket-wrapped actions (stage directions)
        content = re.sub(r'\*[^*]+\*', '', content)
        content = re.sub(r'\[[^\]]+\]', '', content)
        
        # Remove parenthetical asides about internal processing
        content = re.sub(r'\([^)]*(?:check|search|look|find|use|tool|calendar|email|system|internal)[^)]*\)', '', content, flags=re.IGNORECASE)
        
        # Reasoning indicators that signal internal thought (case insensitive)
        reasoning_patterns = [
            r"^(?:The user|They|So,?\s+the|According to|Looking at|Here,|Actually,|Following|My instructions)",
            r"^(?:I need to|I should|I will|I'll|Let me|I'm going to|I am going to)",
            r"^(?:First,|Then,|Next,|After that,|Finally,|Now,|Step \d)",
            r"^(?:The caller|This means|Based on|Given that|Since)",
            r"^(?:Checking|Searching|Looking up|Using|Calling|Invoking)",
            r"^(?:Okay so|Alright so|So basically|Hmm,|Well,\s+(?:the|I|let))",
        ]
        
        lines = content.split('\n')
        clean_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines at the start
            if not line_stripped and not clean_lines:
                continue
            
            # Skip lines with reasoning indicators
            if any(re.match(pattern, line_stripped, re.IGNORECASE) for pattern in reasoning_patterns):
                continue
            
            # Skip bullet points that look like reasoning
            if line_stripped.startswith("- ") and len(line_stripped) > 40:
                continue
            
            # Skip lines with emojis commonly used for internal notes
            if "❌" in line_stripped or "✓" in line_stripped or "✔" in line_stripped:
                continue
            
            # Skip numbered lists that look like internal steps
            if re.match(r'^\d+\.\s+', line_stripped) and any(
                word in line_stripped.lower() for word in ['check', 'search', 'find', 'use', 'look', 'call', 'need']
            ):
                continue
            
            # Skip lines that mention tools by name
            if any(tool in line_stripped.lower() for tool in ['search_emails', 'search_contacts', 'check_calendar', 'schedule_meeting']):
                continue
            
            clean_lines.append(line_stripped)
        
        content = ' '.join(clean_lines)
        
        # Remove remaining tool call narration patterns
        content = re.sub(r"(?:Let me|I'll|I will|I'm going to)\s+(?:check|search|look up|use|call|invoke|see|find).*?(?:\.|!|$)", '', content, flags=re.IGNORECASE)
        content = re.sub(r"(?:Using|Calling|Invoking|Checking|Looking at|Searching)\s+(?:the\s+)?(?:search_emails|search_contacts|check_calendar|schedule_meeting|calendar|tool|system).*?(?:\.|!|$)", '', content, flags=re.IGNORECASE)
        
        # Remove ellipsis lines
        content = re.sub(r'\.{3,}', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\s{2,}', ' ', content)
        content = content.strip()
        
        # Remove trailing/leading punctuation artifacts
        content = re.sub(r'^[.,!?\s]+', '', content)
        content = re.sub(r'\s+[.,]+$', '.', content)
        
        # If content is empty or too short after cleaning, return empty to trigger contextual fallback
        if len(content) < 5:
            return ""
        
        return content

    async def _build_system_prompt(self) -> str:
        """Build system prompt with business config and current date injected."""
        prompt = self.BASE_SYSTEM_PROMPT
        
        # Inject today's date for relative time understanding
        now = datetime.now()
        date_info = f"\n\nCURRENT DATE AND TIME: {now.strftime('%A, %B %d, %Y %H:%M')}"
        prompt += date_info
        
        if self._business_config:
            business_info = f"\n\nYou work for {self._business_config.ceo_name}."
            if self._business_config.company_name:
                business_info += f" The company is {self._business_config.company_name}."
            if self._business_config.company_description:
                business_info += f" {self._business_config.company_description}"
            prompt += business_info
        
        return prompt

    async def decide_action(
        self, transcript: str, context: dict[str, Any]
    ) -> list[ToolCall]:
        """Analyze transcript and decide which tools to invoke.
        
        Args:
            transcript: The transcribed caller speech.
            context: Current conversation context.
            
        Returns:
            List of tool calls to execute.
        """
        messages = [
            {"role": "system", "content": await self._build_system_prompt()},
        ]
        
        # Add conversation history if available
        if context.get("history"):
            for entry in context["history"][-5:]:  # Last 5 exchanges
                messages.append({"role": "user", "content": entry.get("user", "")})
                if entry.get("assistant"):
                    messages.append({"role": "assistant", "content": entry["assistant"]})
        
        messages.append({"role": "user", "content": transcript})

        try:
            response = await self._client.post(
                self.FIREWORKS_API_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.MODEL,
                    "messages": messages,
                    "tools": self.TOOL_SCHEMAS,
                    "tool_choice": "auto",
                    "max_tokens": 500,
                },
            )
            
            if response.status_code == 404:
                error_body = response.text
                logger.error(f"Model not found. Response: {error_body}. Try updating MODEL in reasoning_engine.py")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            tool_calls = []
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            
            if message.get("tool_calls"):
                for tc in message["tool_calls"]:
                    func = tc.get("function", {})
                    tool_name = func.get("name")
                    logger.info(f"AI called tool: {tool_name}")
                    try:
                        args = json.loads(func.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}
                    
                    if tool_name == "search_emails":
                        tool_calls.append(ToolCall(Tool.SEARCH_EMAILS, args))
                    elif tool_name == "search_contacts":
                        tool_calls.append(ToolCall(Tool.SEARCH_CONTACTS, args))
                    elif tool_name == "check_calendar":
                        tool_calls.append(ToolCall(Tool.CHECK_CALENDAR, args))
                    elif tool_name == "schedule_meeting":
                        tool_calls.append(ToolCall(Tool.SCHEDULE_MEETING, args))
                    elif tool_name == "end_call":
                        tool_calls.append(ToolCall(Tool.END_CALL, args))
            else:
                logger.warning(f"AI did not call any tools for: '{transcript[:50]}...'")
            
            # FALLBACK: If AI didn't call schedule_meeting but user is clearly asking to schedule
            if not tool_calls:
                schedule_keywords = ["schedule", "set up", "book", "appointment", "meeting", "p.m.", "pm", "a.m.", "am", "o'clock"]
                transcript_lower = transcript.lower()
                if any(kw in transcript_lower for kw in schedule_keywords):
                    logger.info("Fallback: Detected scheduling request, parsing manually")
                    parsed = self._parse_scheduling_request(transcript)
                    if parsed:
                        tool_calls.append(ToolCall(Tool.SCHEDULE_MEETING, parsed))
            
            return tool_calls
            
        except Exception as e:
            logger.error(f"Failed to decide action: {e}")
            return []

    async def generate_response(
        self, transcript: str, context: dict[str, Any]
    ) -> str:
        """Generate a contextual response based on gathered information.
        
        Args:
            transcript: The transcribed caller speech.
            context: Current conversation context including search results.
            
        Returns:
            Generated response text.
        """
        # Build system content with updated date and business info
        system_content = await self._build_system_prompt()
        
        # Add context from searches
        if context.get("contacts"):
            contacts_info = "\n".join([
                f"- {c.get('name', 'Unknown')}: {c.get('email', '')} ({c.get('company', '')})"
                for c in context["contacts"]
            ])
            system_content += f"\n\nKnown contacts:\n{contacts_info}"
        
        if context.get("emails"):
            emails_info = "\n".join([
                f"- From {e.get('sender', 'Unknown')}: {e.get('subject', 'No subject')}"
                for e in context["emails"][:3]
            ])
            system_content += f"\n\nRelevant emails:\n{emails_info}"
        
        # Add calendar context
        if context.get("calendar_busy"):
            busy_info = "\n".join(context["calendar_busy"])
            check_date = context.get("calendar_check_date", "the requested date")
            system_content += f"\n\nCalendar for {check_date}:\n{busy_info}\n(Other times are available)"
        elif context.get("calendar_available"):
            check_date = context.get("calendar_check_date", "the requested date")
            system_content += f"\n\nCalendar for {check_date}: All times are available."
        
        # Add meeting confirmation context
        if context.get("meeting_scheduled") and context.get("meeting_details"):
            details = context["meeting_details"]
            system_content += f"\n\nMEETING CONFIRMED: '{details.get('title')}' scheduled for {details.get('date')} at {details.get('time')} for {details.get('duration', 30)} minutes."
        elif context.get("meeting_error"):
            system_content += f"\n\nMEETING SCHEDULING FAILED: {context['meeting_error']}. Apologize and offer to try again."

        # Tell AI that caller has already been greeted
        if context.get("greeted"):
            system_content += """

IMPORTANT: You already greeted the caller with "Hello, this is Donna, your AI assistant. How may I help you today?"
DO NOT greet again or ask "how can I help" - just respond to what they said."""
        
        # Add strict instruction to prevent tool narration and thinking
        system_content += """

OUTPUT FORMAT: Reply with ONLY spoken words. 1-2 sentences. No greetings if already greeted. Respond to their actual request."""

        messages = [
            {"role": "system", "content": system_content},
        ]
        
        # Add conversation history before current message
        if context.get("history"):
            for entry in context["history"][-5:]:  # Last 5 exchanges
                messages.append({"role": "user", "content": entry.get("user", "")})
                if entry.get("assistant"):
                    messages.append({"role": "assistant", "content": entry["assistant"]})
        
        messages.append({"role": "user", "content": transcript})

        try:
            response = await self._client.post(
                self.FIREWORKS_API_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.MODEL,
                    "messages": messages,
                    "max_tokens": 100,  # Very short responses only
                    "temperature": 0.4,  # Lower temperature = less verbose/creative
                    "stop": ["<thinking>", "<reasoning>", "\n\n", "Let me"],  # Stop before reasoning
                },
            )
            
            if response.status_code == 404:
                error_body = response.text
                logger.error(f"Model not found for response generation. Response: {error_body}")
                return "I apologize, I'm having trouble processing your request. Could you please repeat that?"
            
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            
            # AGGRESSIVE FILTERING - Remove ALL reasoning/thinking patterns
            content = self._clean_ai_response(content)
            
            # If response got wiped, generate contextual fallback
            if len(content) < 10:
                if context.get("meeting_scheduled") and context.get("meeting_details"):
                    details = context["meeting_details"]
                    content = f"Done! I've scheduled '{details.get('title')}' for {details.get('time')} on {details.get('date')}. You're all set!"
                elif context.get("meeting_error"):
                    content = "I'm sorry, there was an issue scheduling that meeting. Would you like to try a different time?"
                elif context.get("calendar_busy"):
                    content = "I found some conflicts on the calendar. Let me tell you what times are available."
                else:
                    content = "How can I help you?"
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return "I apologize, I'm having trouble processing your request. Could you please repeat that?"

    def _parse_scheduling_request(self, transcript: str) -> dict[str, Any] | None:
        """Parse a scheduling request from transcript without AI.
        
        Returns dict with title, date, time if parsing succeeds, None otherwise.
        """
        from datetime import datetime, timedelta
        from dateutil import parser as date_parser
        
        transcript_lower = transcript.lower()
        
        # Check if PM/AM is mentioned anywhere in the string
        has_pm = bool(re.search(r'p\.?m\.?', transcript_lower))
        has_am = bool(re.search(r'a\.?m\.?', transcript_lower))
        
        # Try to extract the FIRST time mentioned (not the second in "8 to 9")
        # Order matters - more specific patterns first
        time_patterns = [
            r'(?:at|from|for)\s+(\d{1,2}):(\d{2})',  # at 8:00
            r'(?:at|from|for)\s+(\d{1,2})(?:\s|$|[^:\d])',  # at 8 (not followed by colon)
            r'(\d{1,2}):(\d{2})',  # 8:00 anywhere
            r'(\d{1,2})\s*(?:p\.?m\.?|a\.?m\.?)',  # 8pm anywhere
            r'(\d{1,2})\s*o\'?clock',  # 8 o'clock
        ]
        
        start_hour = None
        start_minute = 0
        
        for pattern in time_patterns:
            match = re.search(pattern, transcript_lower)
            if match:
                groups = match.groups()
                start_hour = int(groups[0])
                # Check if second group exists and is minutes
                if len(groups) >= 2 and groups[1] and groups[1].isdigit():
                    start_minute = int(groups[1])
                break
        
        if start_hour is None:
            return None
        
        # Apply PM/AM from anywhere in string
        if has_pm and start_hour < 12:
            start_hour += 12
        elif has_am and start_hour == 12:
            start_hour = 0
        # If no AM/PM specified and hour is small (1-7), assume PM for appointments
        elif not has_am and not has_pm and start_hour >= 1 and start_hour <= 7:
            start_hour += 12
        
        if start_hour is None:
            return None
        
        # Try to extract title/purpose - more patterns
        title_patterns = [
            r'called\s+["\']?([a-z\s]+?)(?:\s+at|\s+from|\s+for|["\'\.]|$)',  # called tea time at
            r'(?:set up|schedule|book)\s+(?:an?\s+)?([a-z\s]+?)\s+(?:at|from|for)\s+\d',  # set up tea time at 7
            r'(?:meeting|appointment)\s+(?:called|named|for)\s+["\']?([^"\'\.]+)',  # meeting called X
            r'about\s+["\']?([^"\'\.]+)["\']?',  # about project review
        ]
        
        title = "Appointment"
        for pattern in title_patterns:
            match = re.search(pattern, transcript_lower)
            if match:
                extracted = match.group(1).strip()
                # Clean up common words
                extracted = re.sub(r'^(an?|the|my)\s+', '', extracted)
                if extracted and len(extracted) > 2 and extracted not in ['appointment', 'meeting']:
                    title = extracted.title()
                    break
        
        # Default to today
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        
        # Check for day mentions
        if "tomorrow" in transcript_lower:
            date_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            # Check for day names
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for day in days:
                if day in transcript_lower:
                    try:
                        parsed = date_parser.parse(transcript, fuzzy=True)
                        if parsed.date() >= now.date():
                            date_str = parsed.strftime("%Y-%m-%d")
                    except:
                        pass
                    break
        
        time_str = f"{start_hour:02d}:{start_minute:02d}"
        
        logger.info(f"Parsed scheduling request: {title} on {date_str} at {time_str}")
        
        return {
            "title": title,
            "date": date_str,
            "time": time_str,
            "duration_minutes": 60
        }

    def extract_caller_info(self, transcript: str) -> dict[str, str | None]:
        """Extract caller name and purpose from transcript.
        
        Args:
            transcript: The transcribed caller speech.
            
        Returns:
            Dict with 'name' and 'purpose' keys (values may be None).
        """
        result: dict[str, str | None] = {"name": None, "purpose": None}
        
        # Common patterns for name introduction
        name_patterns = [
            r"(?:hi|hello|hey),?\s*(?:this is|it's|i'm|my name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"(?:this is|it's|i'm)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:calling|here|from)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:here|calling|speaking)",
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                result["name"] = match.group(1).strip()
                break
        
        # Common patterns for purpose
        purpose_patterns = [
            r"(?:calling|call)\s+(?:about|regarding|for)\s+(.+?)(?:\.|$)",
            r"(?:wanted to|want to|need to)\s+(?:talk|speak|discuss|ask)\s+(?:about|regarding)?\s*(.+?)(?:\.|$)",
            r"(?:following up|checking)\s+(?:on|about)\s+(.+?)(?:\.|$)",
            r"(?:question|inquiry)\s+(?:about|regarding)\s+(.+?)(?:\.|$)",
        ]
        
        for pattern in purpose_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                result["purpose"] = match.group(1).strip()
                break
        
        return result

    def synthesize_context(
        self,
        contact_results: list[dict[str, Any]],
        email_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Synthesize context from contact and email search results.
        
        Combines information from both sources to build a comprehensive
        context for response generation.
        
        Args:
            contact_results: List of contact search results with metadata.
            email_results: List of email search results with metadata.
            
        Returns:
            Synthesized context dict with 'contacts', 'emails', and 'summary' keys.
        """
        context: dict[str, Any] = {
            "contacts": [],
            "emails": [],
            "summary": "",
        }
        
        # Process contact results
        for contact in contact_results:
            contact_info = {
                "name": contact.get("name") or contact.get("metadata", {}).get("name", ""),
                "email": contact.get("email") or contact.get("metadata", {}).get("email", ""),
                "phone": contact.get("phone") or contact.get("metadata", {}).get("phone"),
                "company": contact.get("company") or contact.get("metadata", {}).get("company"),
            }
            if contact_info["name"]:
                context["contacts"].append(contact_info)
        
        # Process email results
        for email in email_results:
            email_info = {
                "sender": email.get("sender") or email.get("metadata", {}).get("sender", ""),
                "subject": email.get("subject") or email.get("metadata", {}).get("subject", ""),
                "content": email.get("content") or email.get("body", ""),
                "score": email.get("score", 0.0),
            }
            if email_info["sender"] or email_info["subject"]:
                context["emails"].append(email_info)
        
        # Build summary
        summary_parts = []
        
        if context["contacts"]:
            contact_names = [c["name"] for c in context["contacts"] if c["name"]]
            if contact_names:
                summary_parts.append(f"Found contacts: {', '.join(contact_names)}")
        
        if context["emails"]:
            email_subjects = [e["subject"] for e in context["emails"] if e["subject"]]
            if email_subjects:
                summary_parts.append(f"Related emails: {', '.join(email_subjects[:3])}")
        
        context["summary"] = ". ".join(summary_parts) if summary_parts else "No relevant context found."
        
        return context

    async def analyze_call_outcome(self, transcript_history: list[str]) -> CallOutcome:
        """Analyze a full call transcript to determine the outcome.
        
        Args:
            transcript_history: List of transcript segments from the call.
            
        Returns:
            Structured CallOutcome with decision and reasoning.
        """
        full_transcript = "\n".join(transcript_history)
        if not full_transcript.strip():
            return CallOutcome(
                summary="Empty call",
                decision="rejected",
                decision_label="No input",
                reasoning="Caller did not speak.",
                action_taken="No action."
            )

        system_prompt = await self._build_system_prompt() + """

You are analyzing a completed call log. Your job is to summarize the call and determine the final outcome.
Output a JSON object with the following fields:
- summary: A concise 1-sentence summary of what the caller wanted.
- decision: One of ['handled', 'scheduled', 'escalated', 'rejected'].
- decision_label: A short 2-3 word label for the decision (e.g., "Meeting booked", "Spam rejected").
- reasoning: Why you made this decision.
- action_taken: What specific action was taken during the call.

Decision Guidelines:
- scheduled: If a meeting, appointment, or follow-up was explicitly booked/confirmed.
- escalated: If the caller needs to speak to the boss/human and you couldn't resolve it, or if it's high priority.
- rejected: If it was spam, wrong number, or explicitly turned away.
- handled: If the caller's question was answered or issue resolved automatically without needing further action.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the call transcript:\n\n{full_transcript}"}
        ]

        try:
            response = await self._client.post(
                self.FIREWORKS_API_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.MODEL,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "max_tokens": 500,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            result = json.loads(content)
            
            return CallOutcome(
                summary=result.get("summary", "No summary available"),
                decision=result.get("decision", "handled"),
                decision_label=result.get("decision_label", "Call processed"),
                reasoning=result.get("reasoning", "No reasoning provided"),
                action_taken=result.get("action_taken", "Call logged")
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze call outcome: {e}")
            return CallOutcome(
                summary="Failed to analyze call",
                decision="handled",
                decision_label="Processing Error",
                reasoning=f"Error during analysis: {str(e)}",
                action_taken="Logged for review"
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()




