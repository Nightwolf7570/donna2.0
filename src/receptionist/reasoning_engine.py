"""Reasoning engine using Fireworks AI for tool calling and response generation."""

import json
import logging
import re
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
    GENERATE_RESPONSE = "generate_response"


@dataclass
class ToolCall:
    """Represents a tool call decision."""
    tool: Tool
    arguments: dict[str, Any]


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
        }
    ]

    BASE_SYSTEM_PROMPT = """You are Donna, an AI receptionist assistant. Your name is Donna. Your job is to:
1. Identify who is calling and why
2. Search for relevant context about the caller
3. Provide helpful, professional responses

When a caller introduces themselves or states their purpose:
- Use search_contacts to look up the caller if they give their name
- Use search_emails to find relevant context about their topic

Always introduce yourself as Donna when appropriate. Be professional, warm, concise, and helpful."""

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

    def _build_system_prompt(self) -> str:
        """Build system prompt with business config injected."""
        prompt = self.BASE_SYSTEM_PROMPT
        
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
            {"role": "system", "content": self._build_system_prompt()},
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
                    try:
                        args = json.loads(func.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}
                    
                    if tool_name == "search_emails":
                        tool_calls.append(ToolCall(Tool.SEARCH_EMAILS, args))
                    elif tool_name == "search_contacts":
                        tool_calls.append(ToolCall(Tool.SEARCH_CONTACTS, args))
            
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
        system_content = self._build_system_prompt()
        
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

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": transcript},
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
                    "max_tokens": 300,
                },
            )
            
            if response.status_code == 404:
                error_body = response.text
                logger.error(f"Model not found for response generation. Response: {error_body}")
                return "I apologize, I'm having trouble processing your request. Could you please repeat that?"
            
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return "I apologize, I'm having trouble processing your request. Could you please repeat that?"

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

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


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

        system_prompt = self._build_system_prompt() + """

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

