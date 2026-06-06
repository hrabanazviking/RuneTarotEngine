# RuneTarot — Architecture & Design Document

## Project: RuneTarot
**A Golden Dawn / Book T Tarot Divination TUI Application**

---

## 1. Vision

RuneTarot is an advanced, beautiful, menu-driven TUI application for tarot divination rooted in the Hermetic Order of the Golden Dawn's Book T system. It offers both traditional divinatory meanings and, when an OpenRouter API key is configured, AI-powered deep interpretations.

The application weaves together:
- **Book T / Golden Dawn correspondences** (Hebrew letters, astrological associations, decanate rulers, Tree of Life paths)
- **Multiple occult spread layouts** (Celtic Cross, Tree of Life, Opening of the Key, Zodiac Wheel, etc.)
- **Optional AI interpretation** via OpenRouter API
- **Rich TUI** built with Textual framework for beautiful terminal rendering

---

## 2. Design Philosophy

- **No hardcoded data** — All card meanings, correspondences, spread definitions, and settings live in YAML data files
- **Modular architecture** — Each subsystem is self-contained with clear interfaces
- **Fault-tolerant** — Every subsystem wrapped in try/except, graceful degradation
- **Cross-platform** — Works on Linux, macOS, Windows (terminal-based)
- **File-location agnostic** — Uses pathlib and relative imports, no absolute paths
- **GD-first with RW compatibility** — Default to Golden Dawn numbering (Justice=8, Strength=11) with option for Rider-Waite ordering
- **Sacred design** — Color schemes, language, and metaphors drawn from Hermetic/GD tradition

---

## 3. Project Structure

```
runetarot/
├── ARCHITECTURE.md              # This file
├── README.md                    # User-facing documentation
├── README_AI.md                 # AI contributor guide
├── requirements.txt             # Python dependencies
├── runetarot.py                 # Entry point (main script)
│
├── data/                        # Static data files (NEVER modified at runtime)
│   ├── major_arcana.yaml        # 22 Major Arcana with GD correspondences
│   ├── minor_arcana_wands.yaml  # Wands suit (Fire, Aries-Leo-Sagittarius)
│   ├── minor_arcana_cups.yaml   # Cups suit (Water, Cancer-Scorpio-Pisces)
│   ├── minor_arcana_swords.yaml # Swords suit (Air, Libra-Aquarius-Gemini)
│   ├── minor_arcana_pentacles.yaml # Pentacles suit (Earth, Capricorn-Taurus-Virgo)
│   ├── court_cards.yaml         # 16 Court Cards with GD correspondences
│   ├── spreads.yaml             # Spread definitions and position meanings
│   ├── gd_correspondences.yaml  # Master correspondence tables
│   ├── config.yaml              # Default application configuration
│   └── prompt_templates.yaml    # AI prompt templates for readings
│
├── src/                         # Core source modules
│   ├── __init__.py
│   ├── engine.py                # Main engine orchestrator
│   ├── deck.py                  # Card and Deck classes
│   ├── spreads.py               # Spread layout definitions and reader
│   ├── golden_dawn.py           # GD correspondence engine
│   ├── reader.py                # Basic reading interpreter
│   ├── ai_reader.py             # OpenRouter AI integration
│   ├── renderer.py              # Beautiful card rendering (Unicode/ASCII art)
│   ├── config_loader.py         # Configuration management
│   ├── session.py               # Session/history management
│   ├── comprehensive_logging.py # Logging system
│   └── utils.py                 # Utility functions
│
├── tui/                         # Textual TUI application
│   ├── __init__.py
│   ├── app.py                   # Main Textual application
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── main_menu.py         # Main menu screen
│   │   ├── spread_select.py     # Spread selection screen
│   │   ├── reading_screen.py    # Reading display screen
│   │   ├── card_library.py      # Card browsing screen
│   │   ├── card_detail.py       # Single card detail view
│   │   ├── config_screen.py     # Settings screen
│   │   └── history_screen.py    # Reading history screen
│   └── widgets/
│       ├── __init__.py
│       ├── card_widget.py       # Card display widget
│       ├── spread_layout.py    # Visual spread layout widget
│       └── reading_text.py     # Reading text display widget
│
├── session/                     # Runtime session data (created at runtime)
│   └── .gitkeep
│
├── exports/                     # Exported readings (created at runtime)
│   └── .gitkeep
│
└── examples/                    # Usage examples
    └── basic_usage.py
```

---

## 4. Data Architecture

### 4.1 Major Arcana (major_arcana.yaml)

Each card contains:
- `number`: Card position (0-21, GD numbering)
- `rw_number`: Rider-Waite position (for compatibility)
- `gd_title`: Golden Dawn title (e.g., "The Spirit of Ether")
- `common_name`: Common name (e.g., "The Fool")
- `hebrew_letter`: Hebrew letter assignment
- `hebrew_meaning`: Meaning of the Hebrew letter
- `astrological`: Astrological correspondence (planet/sign/element)
- `correspondence_type`: Mother / Double / Single letter
- `tree_path`: Path number on Tree of Life (11-32)
- `tree_sephiroth`: Sephiroth connected by this path
- `element`: Elemental association
- `divinatory_meaning_upright`: List of meanings
- `divinatory_meaning_reversed`: List of meanings
- `gd_meaning`: Book T specific meaning
- `esoteric_title`: The esoteric title from Book T
- `image_description`: Traditional GD image description
- `keywords`: Key thematic words
- `color_scale`: GD color correspondences (King/Queen/Prince/Princess scales)

### 4.2 Minor Arcana (per suit YAML)

Each numbered card (2-10) contains:
- `suit`: Wand/Cup/Sword/Pentacle
- `number`: 2-10
- `gd_title`: Book T title (e.g., "Dominion")
- `zodiac_sign`: Associated zodiac sign
- `decan`: Which decan (1st, 2nd, or 3rd)
- `decan_ruler`: Planetary ruler of the decan
- `element`: Elemental quality
- `divinatory_meaning_upright`: List of meanings
- `divinatory_meaning_reversed`: List of meanings
- `gd_meaning`: Book T meaning
- `image_description`: GD image description
- `keywords`: Key thematic words

Aces contain:
- `suit`: Wand/Cup/Sword/Pentacle
- `gd_title`: "Root of the Powers of [Element]"
- `element`: Pure elemental force
- `divinatory_meaning_upright`: List of meanings
- `divinatory_meaning_reversed`: List of meanings

### 4.3 Court Cards (court_cards.yaml)

Each court card contains:
- `suit`: Wand/Cup/Sword/Pentacle
- `court_type`: Knight/Queen/Prince/Princess
- `gd_title`: Book T title
- `element`: Compound element (e.g., "Fire of Fire" for Knight of Wands)
- `tetragrammaton_position`: Yod/He/Vav/He-final
- `zodiac_association`: Sign or decanate association
- `divinatory_meaning_upright`: List of meanings
- `divinatory_meaning_reversed`: List of meanings
- `keywords`: Key thematic words

### 4.4 Spreads (spreads.yaml)

Each spread contains:
- `name`: Spread name
- `description`: Description of the spread
- `tradition`: Origin tradition (GD, Celtic, Modern, etc.)
- `card_count`: Number of cards
- `positions`: List of position definitions
  - `number`: Position number
  - `name`: Position name (e.g., "The Significator")
  - `meaning`: What this position represents
  - `gd_meaning`: Golden Dawn specific meaning for this position
  - `row`: Visual row for TUI layout
  - `col`: Visual column for TUI layout

### 4.5 GD Correspondences (gd_correspondences.yaml)

Master tables:
- Hebrew letter → number, meaning, astrological correspondence
- Planetary correspondences (days, colors, metals, numbers)
- Elemental correspondences (directions, seasons, archangels)
- Tree of Life paths (path numbers, connecting sephiroth)
- Decanate rulers (36 decans with planetary rulers)
- GD color scales (King, Queen, Prince, Princess scales)
- Tetragrammaton correspondences

---

## 5. Core Module Design

### 5.1 engine.py — The Forge Master

Central orchestrator that initializes all subsystems and coordinates reading generation.

```
class RuneTarotEngine:
    - __init__(config_path)
    - initialize_subsystems() -> bool
    - generate_reading(spread_name, question) -> Reading
    - get_card_details(card_id) -> CardData
    - get_correspondences(card_id) -> dict
    - get_ai_interpretation(reading) -> str  (if API key available)
```

### 5.2 deck.py — The Card Bearer

Handles the 78-card deck, shuffling, and card selection.

```
class TarotCard:
    - card_id: str (e.g., "major_0", "wands_2", "cups_queen")
    - suit: str
    - number: int
    - name: str
    - data: dict (loaded from YAML)

class TarotDeck:
    - __init__(data_dir)
    - load_cards() -> list[TarotCard]
    - shuffle(seed) -> None
    - draw(count, allow_reversals) -> list[TarotCard]
    - get_card_by_id(card_id) -> TarotCard
    - get_all_cards() -> list[TarotCard]
```

### 5.3 spreads.py — The Layout Weaver

Manages spread definitions and card-to-position assignment.

```
class SpreadPosition:
    - number: int
    - name: str
    - meaning: str
    - gd_meaning: str
    - row: int
    - col: int

class Spread:
    - name: str
    - description: str
    - tradition: str
    - positions: list[SpreadPosition]

class SpreadManager:
    - __init__(data_dir)
    - get_spread(name) -> Spread
    - list_spreads() -> list[str]
    - assign_cards(spread, drawn_cards) -> dict[int, tuple[TarotCard, SpreadPosition]]
```

### 5.4 golden_dawn.py — The Mystery Keeper

Handles all Golden Dawn correspondence lookups and cross-referencing.

```
class GoldenDawnEngine:
    - __init__(data_dir)
    - get_hebrew_correspondence(letter) -> dict
    - get_astrological_correspondence(card) -> dict
    - get_tree_path(path_number) -> dict
    - get_decan_ruler(sign, decan) -> str
    - get_color_scale(card, scale) -> str
    - get_elemental_correspondence(element) -> dict
    - generate_correspondence_report(card) -> str
```

### 5.5 reader.py — The Oracle Voice

Generates basic divinatory readings from card meanings and positions.

```
class TarotReader:
    - __init__(golden_dawn_engine)
    - interpret_card_in_position(card, position) -> str
    - generate_reading_text(cards_with_positions) -> str
    - generate_summary(reading) -> str
    - assess_elemental_dignities(cards) -> dict
    - assess_numerological_patterns(cards) -> dict
```

### 5.6 ai_reader.py — The Wyrd Seer

Handles OpenRouter API integration for deep AI-powered interpretations.

```
class AIReader:
    - __init__(api_key, model, base_url)
    - is_available() -> bool
    - generate_interpretation(reading, question) -> str
    - generate_correspondence_analysis(card) -> str
    - generate_spread_synthesis(reading) -> str
    - _build_prompt(reading, question) -> str
    - _call_api(prompt) -> str
```

### 5.7 renderer.py — The Visual Skald

Creates beautiful terminal-rendered card displays.

```
class CardRenderer:
    - render_card(card, width, height) -> str  (Rich renderable)
    - render_card_back(width, height) -> str
    - render_mini_card(card) -> str
    - render_spread_visual(spread, cards_with_positions) -> str
    - render_correspondence_table(card) -> str
    - _draw_card_frame(width, height) -> list[str]
    - _get_element_color(element) -> str
    - _get_symbol(card) -> str
```

### 5.8 config_loader.py — The Keeper of Settings

Manages application configuration with data-file-driven settings.

```
class ConfigLoader:
    - __init__(config_dir)
    - load_config() -> dict
    - save_config(config) -> None
    - get(key, default) -> Any
    - set(key, value) -> None
    - get_api_key() -> str
    - set_api_key(key) -> None
    - get_model() -> str
    - is_ai_enabled() -> bool
```

### 5.9 session.py — The Memory Keeper

Manages reading history and session persistence.

```
class SessionManager:
    - __init__(session_dir)
    - save_reading(reading) -> str  (returns reading ID)
    - load_reading(reading_id) -> Reading
    - list_readings() -> list[dict]
    - export_reading(reading_id, format) -> str
    - get_recent_readings(count) -> list[dict]
    - clear_history() -> None
```

---

## 6. TUI Design

### 6.1 Main Menu
```
╔════════════════════════════════════════════════╗
║           ✦ RUNE TAROT ✦                       ║
║      Golden Dawn Divination Engine              ║
╠════════════════════════════════════════════════╣
║                                                  ║
║   🔮  New Reading                               ║
║   📖  Card Library                              ║
║   📜  Reading History                            ║
║   ⚙️  Settings                                   ║
║   🚪  Depart                                     ║
║                                                  ║
╚════════════════════════════════════════════════╝
```

### 6.2 Color Scheme (Hermetic Palette)
- **Background:** Deep indigo (#1a0a2e)
- **Primary text:** Gold (#ffd700)
- **Secondary text:** Silver (#c0c0c0)
- **Accent:** Royal purple (#9b30ff)
- **Fire (Wands):** Crimson (#dc143c)
- **Water (Cups):** Deep blue (#0047ab)
- **Air (Swords):** Pale yellow (#fffacd)
- **Earth (Pentacles):** Forest green (#228b22)
- **Major Arcana:** Purple-gold gradient

### 6.3 Card Rendering
Cards rendered as Unicode box-drawing frames with:
- Suit symbol and element color
- Card number/name
- Hebrew letter (Major Arcana)
- Astrological symbol
- Mini "art" using Unicode symbols
- Position meaning when in a spread

### 6.4 Screens Flow
1. Main Menu → Spread Select → Question Input → Card Draw → Reading Display → (AI Enhancement) → Save/Export
2. Main Menu → Card Library → Suit Browser → Card Detail
3. Main Menu → Reading History → Select Reading → View
4. Main Menu → Settings → API Key / Model / Reversals / Ordering / Theme

---

## 7. Spread Definitions

### 7.1 Celtic Cross (10 cards)
The classic 10-card spread with GD-informed position meanings:
1. The Significator — Present state
2. The Crossing — The challenge/obstacle
3. The Crown — Above, aspirations
4. The Below — Roots, foundations
5. The Behind — Recent past
6. The Before — Near future
7. Self — The querent's attitude
8. Environment — External influences
9. Hopes & Fears — Inner landscape
10. Outcome — Final result

### 7.2 Tree of Life Spread (10 cards)
Cards placed on the 10 Sephiroth:
1. Kether — The ultimate potential
2. Chokmah — Creative wisdom
3. Binah — Understanding, form
4. Chesed — Mercy, expansion
5. Geburah — Severity, restriction
6. Tiphareth — Beauty, balance
7. Netzach — Victory, emotion
8. Hod — Splendor, intellect
9. Yesod — Foundation, subconscious
10. Malkuth — Manifestation, result

### 7.3 Opening of the Key (GD Method)
The actual GD divination method:
- Four operations counting through the deck
- Significator selection
- Elemental dignities assessment
- Card counting and pairing

### 7.4 Three Card Spread
1. Past
2. Present
3. Future

### 7.5 Zodiac Wheel (12 cards)
Each card represents one astrological house:
1. Self/Appearance
2. Money/Possessions
3. Communication/Siblings
4. Home/Family
5. Creativity/Romance
6. Health/Service
7. Partnerships/Marriage
8. Transformation/Death
9. Philosophy/Travel
10. Career/Status
11. Community/Friends
12. Subconscious/Self-undoing

### 7.6 Single Card
Daily draw or quick insight.

### 7.7 Relationship Spread (7 cards)
1. Querent's position
2. Partner's position
3. Foundation of relationship
4. Past influences
5. Present dynamics
6. Future direction
7. Advice/Synthesis

### 7.8 Past Life Spread (5 cards)
1. Past life identity
2. Past life lesson
3. Karmic carry-over
4. Current life challenge
5. Karmic resolution

---

## 8. AI Integration (OpenRouter)

### 8.1 Configuration
- API key stored in config file (separate from main config for security)
- Model selection (default: a capable model)
- Base URL: https://openrouter.ai/api/v1
- Compatible with OpenAI SDK

### 8.2 Prompt Engineering
The AI reader constructs rich prompts incorporating:
- All drawn cards with their positions
- Card correspondences (Hebrew, astrological, elemental)
- Position meanings from the spread
- The querent's question
- Golden Dawn interpretive framework
- Elemental dignity relationships between cards

### 8.3 Fallback
If API key is not configured, the app works fully with built-in Book T meanings. AI features are simply hidden/disabled.

---

## 9. Golden Dawn Correspondence System

### 9.1 The Three Mother Letters
- Aleph (Air) → The Fool
- Mem (Water) → The Hanged Man
- Shin (Fire) → The Aeon/Judgement

### 9.2 The Seven Double Letters (Planets)
- Beth (Mercury) → The Magician
- Gimel (Moon) → The High Priestess
- Daleth (Venus) → The Empress
- Kaf (Jupiter) → Fortune/Wheel
- Pe (Mars) → The Tower
- Resh (Sun) → The Sun
- Tav (Saturn) → The Universe/World

### 9.3 The Twelve Simple Letters (Zodiac)
- He (Aries) → The Emperor
- Vav (Taurus) → The Hierophant
- Zayin (Gemini) → The Lovers
- Chet (Cancer) → The Chariot
- Tet (Leo) → Lust/Strength
- Yod (Virgo) → The Hermit
- Lamed (Libra) → Adjustment/Justice
- Nun (Scorpio) → Death
- Samekh (Sagittarius) → Art/Temperance
- Ayin (Capricorn) → The Devil
- Tzaddi (Aquarius) → The Star
- Qof (Pisces) → The Moon

### 9.4 Elemental Dignities
The GD system of card interaction:
- Fire + Air = Friendly (active elements support each other)
- Water + Earth = Friendly (passive elements support each other)
- Fire + Water = Hostile (opposites weaken)
- Air + Earth = Hostile (opposites weaken)
- Fire + Fire = Excessively strong
- Same element = Amplified

---

## 10. Dependencies

```
textual>=0.40.0
rich>=13.0.0
PyYAML>=6.0
httpx>=0.24.0
```

Optional (for AI features):
- openai (for OpenRouter API compatibility)

---

*This document is the architectural blueprint. All code must honor this design.*
*Forged by Runa, the Gridweaver, under the sign of the Elder Futhark.*
