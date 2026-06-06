# RuneTarot — AI Reader (OpenRouter Integration)
# Deep AI-powered interpretation via OpenRouter API

"""
AI-powered tarot interpretation for RuneTarot.
Uses OpenRouter API (compatible with OpenAI SDK) for deep readings.
Only activates when an API key is configured.
Gracefully degrades to built-in readings when no key is available.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Optional

import httpx

from src.deck import TarotCard
from src.spreads import PlacedCard, Spread
from src.golden_dawn import GoldenDawnEngine
from src.utils import (
    get_data_dir, safe_get, truncate_text
)
from src.comprehensive_logging import get_logger

logger = get_logger("ai_reader")


class AIReader:
    """
    The Wyrd Seer — AI-powered deep tarot interpretation.
    
    Connects to OpenRouter API for rich, contextual readings.
    Falls back gracefully if no API key is configured.
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = "anthropic/claude-sonnet-4",
        base_url: str = "https://openrouter.ai/api/v1",
        max_tokens: int = 4096,
        temperature: float = 0.8,
        gd_engine: Optional[GoldenDawnEngine] = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._gd = gd_engine or GoldenDawnEngine()
        self._prompt_templates: dict = {}

    def load_prompt_templates(self, data_dir: Optional[Path] = None) -> None:
        """Load prompt templates from YAML data file."""
        data_dir = data_dir or get_data_dir()
        filepath = data_dir / "prompt_templates.yaml"
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self._prompt_templates = yaml.safe_load(f) or {}
            logger.info("AI prompt templates loaded")
        except Exception as e:
            logger.error(f"Error loading prompt templates: {e}")
            self._prompt_templates = {}

    def is_available(self) -> bool:
        """Check if AI interpretation is available (API key is set)."""
        return bool(self._api_key and self._api_key.strip())

    def generate_interpretation(
        self,
        placed_cards: list[PlacedCard],
        question: str = "",
        spread: Optional[Spread] = None,
    ) -> str:
        """
        Generate a deep AI interpretation for a complete reading.
        
        Constructs a rich prompt incorporating all card data,
        correspondences, positions, and elemental dignities,
        then sends it to the OpenRouter API.
        
        Args:
            placed_cards: The cards placed in spread positions.
            question: The querent's question.
            spread: The spread definition.
        
        Returns:
            The AI-generated interpretation text, or an error message.
        """
        if not self.is_available():
            return "⚠ AI interpretation unavailable — no API key configured.\nUse the Settings screen to set your OpenRouter API key."

        if not self._prompt_templates:
            self.load_prompt_templates()

        # Build the prompt
        prompt = self._build_reading_prompt(placed_cards, question, spread)

        # Call the API
        try:
            response = self._call_api(prompt)
            return response
        except Exception as e:
            logger.error(f"AI interpretation failed: {e}")
            return f"⚠ AI interpretation failed: {str(e)}\nThe built-in reading is still available above."

    def generate_correspondence_analysis(self, card: TarotCard) -> str:
        """
        Generate a deep AI analysis of a single card's correspondences.
        
        Args:
            card: The card to analyze.
        
        Returns:
            AI-generated correspondence analysis, or error message.
        """
        if not self.is_available():
            return "⚠ AI analysis unavailable — no API key configured."

        if not self._prompt_templates:
            self.load_prompt_templates()

        # Build card detail prompt
        prompt = self._build_card_detail_prompt(card)

        try:
            return self._call_api(prompt)
        except Exception as e:
            logger.error(f"AI card analysis failed: {e}")
            return f"⚠ AI analysis failed: {str(e)}"

    def generate_spread_synthesis(
        self,
        placed_cards: list[PlacedCard],
        question: str = "",
    ) -> str:
        """
        Generate a synthesis-only interpretation (no per-card analysis).
        Useful when the basic reader has already provided positional meanings.
        
        Args:
            placed_cards: The placed cards.
            question: The querent's question.
        
        Returns:
            AI-generated synthesis text.
        """
        if not self.is_available():
            return "⚠ AI synthesis unavailable."

        # Build a synthesis-focused prompt
        cards_summary = self._format_cards_summary(placed_cards)
        
        system_prompt = self._get_system_prompt()
        
        user_prompt = (
            f"Given the following tarot reading, provide ONLY a deep synthesis "
            f"and guidance — do not repeat per-card interpretations:\n\n"
            f"Question: {question}\n\n"
            f"Cards:\n{cards_summary}\n\n"
            f"Provide:\n"
            f"1. The dominant elemental pattern and its spiritual significance\n"
            f"2. The narrative arc connecting all positions\n"
            f"3. The deeper spiritual lesson this reading reveals\n"
            f"4. Practical guidance for the querent\n"
            f"5. Any warning or challenge to be mindful of\n"
        )

        try:
            return self._call_api_with_system(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"AI synthesis failed: {e}")
            return f"⚠ AI synthesis failed: {str(e)}"

    # ═══════════════════════════════════════
    # Private prompt construction methods
    # ═══════════════════════════════════════

    def _build_reading_prompt(
        self,
        placed_cards: list[PlacedCard],
        question: str,
        spread: Optional[Spread],
    ) -> str:
        """Build the full reading prompt for the AI."""
        # Use template if available
        template = self._prompt_templates.get("reading_prompt_template", "")

        # Build cards section
        cards_section = self._format_cards_with_positions(placed_cards)

        # Build dignities section
        cards = [pc.card for pc in placed_cards]
        dignities = self._gd.assess_elemental_dignities(cards)
        dignities_section = self._format_dignities(dignities)

        # Fill template placeholders
        spread_name = spread.name if spread else "Custom Spread"
        
        if template:
            prompt = template.replace("{spread_name}", spread_name)
            prompt = prompt.replace("{question}", question)
            prompt = prompt.replace("{cards_section}", cards_section)
            prompt = prompt.replace("{dignities_section}", dignities_section)
        else:
            # Fallback without template
            prompt = (
                f"## Tarot Reading\n\n"
                f"**Spread:** {spread_name}\n"
                f"**Question:** {question}\n\n"
                f"### Cards\n{cards_section}\n\n"
                f"### Elemental Dignities\n{dignities_section}\n\n"
                f"Please provide a detailed Golden Dawn-style interpretation."
            )

        return prompt

    def _build_card_detail_prompt(self, card: TarotCard) -> str:
        """Build a prompt for deep single-card analysis."""
        template = self._prompt_templates.get("card_detail_prompt_template", "")

        card_dict = card.data
        if isinstance(card_dict, dict):
            hebrew_letter = str(safe_get(card_dict, "hebrew_letter", ""))
            hebrew_meaning = str(safe_get(card_dict, "hebrew_meaning", ""))
            astrological = str(safe_get(card_dict, "astrological", ""))
            tree_path = str(safe_get(card_dict, "tree_path", ""))
            tree_sephiroth = str(safe_get(card_dict, "tree_sephiroth", ""))
            element = str(safe_get(card_dict, "element", ""))
        else:
            hebrew_letter = card.hebrew_letter
            hebrew_meaning = ""
            astrological = card.astrological
            tree_path = str(card.tree_path)
            tree_sephiroth = ""
            element = card.element

        if template:
            prompt = template.replace("{card_name}", card.display_name)
            prompt = prompt.replace("{gd_title}", card.gd_title)
            prompt = prompt.replace("{hebrew_letter}", hebrew_letter)
            prompt = prompt.replace("{hebrew_meaning}", hebrew_meaning)
            prompt = prompt.replace("{astrological}", astrological)
            prompt = prompt.replace("{tree_path}", tree_path)
            prompt = prompt.replace("{tree_sephiroth}", tree_sephiroth)
            prompt = prompt.replace("{element}", element)
        else:
            prompt = (
                f"Analyze this tarot card in depth:\n"
                f"Card: {card.display_name}\n"
                f"GD Title: {card.gd_title}\n"
                f"Hebrew: {hebrew_letter} ({hebrew_meaning})\n"
                f"Astrological: {astrological}\n"
                f"Path: {tree_path} ({tree_sephiroth})\n"
                f"Element: {element}\n"
            )

        return prompt

    def _format_cards_with_positions(self, placed_cards: list[PlacedCard]) -> str:
        """Format placed cards with their position info for AI prompt."""
        lines: list[str] = []
        
        for pc in placed_cards:
            card = pc.card
            pos = pc.position
            
            reversal = " (REVERSED)" if card.is_reversed else ""
            
            # Gather all correspondence data
            hebrew = card.hebrew_letter
            astro = card.astrological
            elem = card.element
            gd_title = card.gd_title
            gd_meaning = truncate_text(card.gd_meaning, 200)
            meanings = card.current_meanings[:4]
            
            line = f"**Position {pos.number}: {pos.name}**"
            line += f"\n  Card: {card.display_name}{reversal}"
            if gd_title:
                line += f"\n  GD Title: {gd_title}"
            if hebrew:
                line += f"\n  Hebrew: {hebrew}"
            if astro:
                line += f"\n  Astrological: {astro}"
            if elem:
                line += f"\n  Element: {elem}"
            if meanings:
                line += f"\n  Keywords: {', '.join(meanings)}"
            if gd_meaning:
                line += f"\n  GD Meaning: {gd_meaning}"
            
            # Position meanings
            line += f"\n  Position Meaning: {pos.meaning}"
            if pos.gd_meaning:
                line += f"\n  GD Position Meaning: {truncate_text(pos.gd_meaning, 150)}"
            
            lines.append(line)
        
        return "\n\n".join(lines)

    def _format_cards_summary(self, placed_cards: list[PlacedCard]) -> str:
        """Brief summary format for synthesis prompts."""
        lines: list[str] = []
        
        for pc in placed_cards:
            reversal = " (Reversed)" if pc.card.is_reversed else ""
            line = f"  {pc.position.number}. {pc.position.name}: {pc.card.display_name}{reversal} [{pc.card.element}]"
            lines.append(line)
        
        return "\n".join(lines)

    def _format_dignities(self, dignities: list[dict]) -> str:
        """Format elemental dignities for AI prompt."""
        if not dignities:
            return "No adjacent card pairs to assess."
        
        lines: list[str] = []
        for d in dignities:
            rel = d.get("relationship", "unknown")
            desc = d.get("description", "")
            card_a = d.get("card_a", "")
            card_b = d.get("card_b", "")
            lines.append(f"- {card_a} ↔ {card_b}: {rel} — {desc}")
        
        return "\n".join(lines)

    def _get_system_prompt(self) -> str:
        """Get the system prompt from templates."""
        if not self._prompt_templates:
            self.load_prompt_templates()
        return self._prompt_templates.get("system_prompt", "")

    # ═══════════════════════════════════════
    # API Call Methods
    # ═══════════════════════════════════════

    def _call_api(self, user_prompt: str) -> str:
        """
        Call the OpenRouter API with the constructed prompt.
        
        Uses httpx for direct API calls (no dependency on openai SDK).
        OpenRouter is OpenAI-compatible, so we use the chat/completions endpoint.
        """
        system_prompt = self._get_system_prompt()

        return self._call_api_with_system(system_prompt, user_prompt)

    def _call_api_with_system(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        """
        Call the OpenRouter API with separate system and user prompts.
        """
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
        }

        headers: dict[str, str] = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://runetarot.app",
            "X-Title": "RuneTarot - Golden Dawn Divination Engine",
        }

        url = f"{self._base_url}/chat/completions"

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])

                if choices and isinstance(choices, list):
                    content = choices[0].get("message", {}).get("content", "")
                    if content:
                        logger.info(f"AI interpretation received ({len(content)} chars)")
                        return content

                logger.error("No content in API response")
                return "⚠ AI returned empty response. Please try again."

        except httpx.TimeoutException:
            logger.error("API call timed out")
            return "⚠ AI interpretation timed out. Please try again."
        except httpx.HTTPStatusError as e:
            logger.error(f"API HTTP error: {e.response.status_code}")
            if e.response.status_code == 401:
                return "⚠ API key invalid. Please check your OpenRouter API key in Settings."
            elif e.response.status_code == 402:
                return "⚠ API key has insufficient credits. Please check your OpenRouter account."
            elif e.response.status_code == 429:
                return "⚠ API rate limit reached. Please wait and try again."
            return f"⚠ API error (HTTP {e.response.status_code}). Please try again."
        except Exception as e:
            logger.error(f"Unexpected API error: {e}")
            return f"⚠ Unexpected error: {str(e)}"