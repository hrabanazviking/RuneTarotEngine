# RuneTarot — Main Engine
# Central orchestrator that initializes all subsystems and coordinates readings

"""
The Forge Master — orchestrates the RuneTarot engine.
Initializes all subsystems in the correct order (no circular imports).
Coordinates reading generation from card draw through interpretation.
"""

from __future__ import annotations

from typing import Any, Optional

from src.config_loader import ConfigLoader
from src.deck import TarotDeck, TarotCard
from src.spreads import Spread, SpreadManager, PlacedCard
from src.golden_dawn import GoldenDawnEngine
from src.reader import TarotReader
from src.ai_reader import AIReader
from src.renderer import CardRenderer
from src.session import SessionManager, Reading
from src.comprehensive_logging import setup_logging, get_logger

logger = get_logger("engine")


class RuneTarotEngine:
    """
    The Forge Master — central orchestrator for RuneTarot.
    
    Initializes all subsystems, coordinates reading generation,
    and provides the public API for the TUI layer.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        # Initialize configuration first
        self._config = ConfigLoader()
        self._config.load_config()
        
        # Set up logging based on config
        log_level = self._config.get("logging.level", "WARNING")
        log_file = self._config.get("logging.file", "runetarot.log")
        setup_logging(level=log_level, log_file=log_file)
        
        logger.info("RuneTarot Engine initializing...")
        
        # Initialize subsystems (order matters — no circular dependencies)
        self._gd_engine: Optional[GoldenDawnEngine] = None
        self._deck: Optional[TarotDeck] = None
        self._spread_manager: Optional[SpreadManager] = None
        self._reader: Optional[TarotReader] = None
        self._ai_reader: Optional[AIReader] = None
        self._renderer: Optional[CardRenderer] = None
        self._session: Optional[SessionManager] = None
        
        self._initialized = False

    def initialize_subsystems(self) -> bool:
        """
        Initialize all subsystems in the correct order.
        
        Order matters:
        1. Golden Dawn engine (correspondence data — no dependencies)
        2. Deck (loads cards — depends on data dir only)
        3. Spread manager (loads spreads — depends on data dir only)
        4. Tarot reader (depends on GD engine)
        5. AI reader (depends on GD engine, config for API key)
        6. Card renderer (depends on GD engine)
        7. Session manager (depends on session dir only)
        """
        try:
            # 1. Golden Dawn correspondence engine
            self._gd_engine = GoldenDawnEngine()
            self._gd_engine.load()
            logger.info("Golden Dawn engine initialized")
            
            # 2. Tarot deck
            self._deck = TarotDeck()
            self._deck.load_cards()
            logger.info(f"Deck initialized — {self._deck.count()} cards")
            
            # 3. Spread manager
            self._spread_manager = SpreadManager()
            self._spread_manager.load_spreads()
            logger.info(f"Spread manager initialized — {len(self._spread_manager.list_spreads())} spreads")
            
            # 4. Basic tarot reader
            self._reader = TarotReader(self._gd_engine)
            logger.info("Basic reader initialized")
            
            # 5. AI reader (conditional on API key)
            self._ai_reader = AIReader(
                api_key=self._config.get_api_key(),
                model=self._config.get_model(),
                base_url=str(self._config.get("api.base_url", "https://openrouter.ai/api/v1")),
                max_tokens=int(self._config.get("api.max_tokens", 4096)),
                temperature=float(self._config.get("api.temperature", 0.8)),
                gd_engine=self._gd_engine,
            )
            self._ai_reader.load_prompt_templates()
            ai_status = "enabled" if self._ai_reader.is_available() else "disabled (no API key)"
            logger.info(f"AI reader initialized — {ai_status}")
            
            # 6. Card renderer
            self._renderer = CardRenderer(self._gd_engine)
            logger.info("Card renderer initialized")
            
            # 7. Session manager
            self._session = SessionManager()
            logger.info("Session manager initialized")
            
            self._initialized = True
            logger.info("✦ RuneTarot Engine fully initialized ✦")
            return True
            
        except Exception as e:
            logger.error(f"Engine initialization failed: {e}")
            self._initialized = False
            return False

    @property
    def is_initialized(self) -> bool:
        """Whether the engine has been fully initialized."""
        return self._initialized

    @property
    def config(self) -> ConfigLoader:
        """Access the configuration loader."""
        return self._config

    @property
    def deck(self) -> TarotDeck:
        """Access the tarot deck."""
        if not self._deck:
            raise RuntimeError("Engine not initialized — call initialize_subsystems() first")
        return self._deck

    @property
    def spread_manager(self) -> SpreadManager:
        """Access the spread manager."""
        if not self._spread_manager:
            raise RuntimeError("Engine not initialized")
        return self._spread_manager

    @property
    def gd_engine(self) -> GoldenDawnEngine:
        """Access the Golden Dawn correspondence engine."""
        if not self._gd_engine:
            raise RuntimeError("Engine not initialized")
        return self._gd_engine

    @property
    def reader(self) -> TarotReader:
        """Access the basic tarot reader."""
        if not self._reader:
            raise RuntimeError("Engine not initialized")
        return self._reader

    @property
    def ai_reader(self) -> AIReader:
        """Access the AI reader."""
        if not self._ai_reader:
            raise RuntimeError("Engine not initialized")
        return self._ai_reader

    @property
    def renderer(self) -> CardRenderer:
        """Access the card renderer."""
        if not self._renderer:
            raise RuntimeError("Engine not initialized")
        return self._renderer

    @property
    def session(self) -> SessionManager:
        """Access the session manager."""
        if not self._session:
            raise RuntimeError("Engine not initialized")
        return self._session

    def is_ai_available(self) -> bool:
        """Check if AI features are available."""
        if not self._ai_reader:
            return False
        return self._ai_reader.is_available()

    # ═══════════════════════════════════════
    # High-level reading generation
    # ═══════════════════════════════════════

    def generate_reading(
        self,
        spread_name: str,
        question: str = "",
        seed: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Generate a complete tarot reading.
        
        This is the primary public method. It:
        1. Selects the spread
        2. Draws cards
        3. Assigns cards to positions
        4. Generates the basic reading text
        5. Optionally generates AI interpretation
        6. Saves the reading to session
        
        Args:
            spread_name: Name of the spread to use.
            question: The querent's question.
            seed: Optional random seed for reproducibility.
        
        Returns:
            Dictionary with all reading data:
            - spread, placed_cards, reading_text, ai_interpretation,
              elemental_balance, reading_id
        """
        if not self._initialized:
            raise RuntimeError("Engine not initialized")
        
        # 1. Select spread
        spread = self._spread_manager.get_spread(spread_name)
        if not spread:
            raise ValueError(f"Spread '{spread_name}' not found")
        
        # 2. Draw cards
        allow_reversals = self._config.get("display.show_reversals", True)
        drawn_cards = self._deck.draw_full_hand(
            count=spread.card_count,
            allow_reversals=allow_reversals,
            seed=seed,
        )
        
        # 3. Assign cards to positions
        placed_cards = self._spread_manager.assign_cards(spread, drawn_cards)
        
        # 4. Generate basic reading text
        reading_text = self._reader.generate_reading_text(
            placed_cards, question, spread
        )
        
        # 5. Elemental balance
        cards = [pc.card for pc in placed_cards]
        elemental_balance = self._gd_engine.get_elemental_balance(cards)
        
        # 6. AI interpretation (if available)
        ai_interpretation = ""
        if self.is_ai_available():
            try:
                ai_interpretation = self._ai_reader.generate_interpretation(
                    placed_cards, question, spread
                )
            except Exception as e:
                logger.error(f"AI interpretation failed: {e}")
                ai_interpretation = ""
        
        # 7. Save reading
        reading_id = self._session.save_reading(
            placed_cards=placed_cards,
            reading_text=reading_text,
            question=question,
            spread=spread,
            ai_interpretation=ai_interpretation,
            elemental_balance=elemental_balance,
        )
        
        return {
            "spread": spread,
            "placed_cards": placed_cards,
            "reading_text": reading_text,
            "ai_interpretation": ai_interpretation,
            "elemental_balance": elemental_balance,
            "reading_id": reading_id,
        }

    def get_card_details(self, card_id: str) -> Optional[dict[str, Any]]:
        """
        Get detailed information about a single card.
        
        Args:
            card_id: The canonical card ID (e.g., "major_0", "wands_2").
        
        Returns:
            Dictionary with card data and correspondences, or None.
        """
        if not self._initialized:
            raise RuntimeError("Engine not initialized")
        
        card = self._deck.get_card_by_id(card_id)
        if not card:
            return None
        
        # Build detailed info
        result: dict[str, Any] = {
            "card": card,
            "correspondences": self._gd_engine.generate_correspondence_report(card),
            "render": self._renderer.render_card(card),
            "correspondence_table": self._renderer.render_correspondence_table(card),
        }
        
        return result

    def get_correspondences(self, card_id: str) -> str:
        """Get the correspondence report string for a card."""
        if not self._initialized:
            raise RuntimeError("Engine not initialized")
        
        card = self._deck.get_card_by_id(card_id)
        if not card:
            return "Card not found."
        
        return self._gd_engine.generate_correspondence_report(card)

    def get_ai_interpretation(self, card_id: str) -> str:
        """Get an AI deep analysis for a single card."""
        if not self._initialized:
            raise RuntimeError("Engine not initialized")
        
        card = self._deck.get_card_by_id(card_id)
        if not card:
            return "Card not found."
        
        return self._ai_reader.generate_correspondence_analysis(card)

    def refresh_ai_reader(self) -> None:
        """Re-initialize AI reader (e.g., after API key change)."""
        if self._ai_reader:
            self._ai_reader = AIReader(
                api_key=self._config.get_api_key(),
                model=self._config.get_model(),
                base_url=str(self._config.get("api.base_url", "https://openrouter.ai/api/v1")),
                max_tokens=int(self._config.get("api.max_tokens", 4096)),
                temperature=float(self._config.get("api.temperature", 0.8)),
                gd_engine=self._gd_engine,
            )
            self._ai_reader.load_prompt_templates()
            logger.info("AI reader refreshed")
