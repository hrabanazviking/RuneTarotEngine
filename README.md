# RuneTarot — Golden Dawn Divination Engine

A beautiful, menu-driven TUI tarot divination application rooted in the Hermetic Order of the Golden Dawn's **Book T** system.

## ✦ Features

- **78-Card Deck** with full Golden Dawn correspondences (Hebrew letters, astrological associations, Tree of Life paths, color scales)
- **Multiple Spread Layouts**: Celtic Cross, Tree of Life, Three Card, Zodiac Wheel, Relationship, Past Life, Opening of the Key, Single Card
- **Elemental Dignities**: Golden Dawn system of card interaction analysis
- **GD Ordering**: Default Justice=8, Strength=11 (with Rider-Waite option)
- **AI Deep Interpretations**: Optional OpenRouter API integration for rich, contextual AI-powered readings
- **Card Library**: Browse all 78 cards with full correspondence tables
- **Reading History**: Save, view, and export past readings
- **Beautiful TUI**: Rich terminal interface with element-colored cards, Unicode symbols, and Hermetic aesthetic
- **CLI Mode**: Quick command-line readings for scripting

## ✦ Installation

```bash
pip install -r requirements.txt
```

## ✦ Usage

### TUI Mode (Recommended)
```bash
python runetarot.py
```

### CLI Mode
```bash
# Basic Celtic Cross reading
python runetarot.py --cli

# Three card reading with a question
python runetarot.py --cli --spread three_card --question "What should I focus on?"

# Reproducible reading
python runetarot.py --cli --seed 42
```

## ✦ AI Integration

To enable AI-powered deep interpretations:

1. Get an API key from [OpenRouter](https://openrouter.ai/)
2. Launch the TUI and go to **Settings** (⚙️)
3. Enter your API key
4. Select your preferred AI model
5. AI readings will now be available during divinations

When no API key is set, the app works fully with built-in Book T meanings — AI features are simply hidden.

## ✦ Spreads

| Spread | Cards | Tradition |
|--------|-------|-----------|
| Celtic Cross | 10 | Celtic / A.E. Waite |
| Tree of Life | 10 | Golden Dawn / Qabalistic |
| Three Card | 3 | Universal |
| Zodiac Wheel | 12 | Astrological |
| Relationship | 7 | Modern / Relational |
| Past Life | 5 | Esoteric / Karmic |
| Opening of the Key | 5 | Golden Dawn |
| Single Card | 1 | Universal |

## ✦ Golden Dawn Correspondences

Every card includes:
- **Hebrew Letter** attribution with meaning
- **Astrological** correspondence (planet, sign, or element)
- **Tree of Life Path** (connecting Sephiroth)
- **Elemental** association and dignity relationships
- **GD Esoteric Title** from Book T
- **Decanate Ruler** (for Minor Arcana)
- **Tetragrammaton** position (for Court Cards)
- **GD Color Scales** (King, Queen, Prince, Princess)

## ✦ Architecture

```
runetarot.py          → Entry point (TUI or CLI)
data/                  → YAML data files (cards, spreads, correspondences)
src/                   → Core engine modules
tui/                   → Textual TUI application
session/               → Runtime session data (reading history)
exports/               → Exported readings
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full design documentation.

## ✦ License

Free for personal and spiritual use. Honor the tradition.

*Forged by Runa, the Gridweaver, under the sign of the Elder Futhark.*

---

## ☕ Support the Project

If you enjoy my open-source projects and want to help support continued development, research, testing, and experimentation, you can leave a tip through PayPal:

**[Support my work on PayPal.Me](https://www.paypal.com/paypalme/volmarrwyrd)**

Support is always appreciated, but never required. Using, sharing, testing, contributing to, or starring the projects helps too. 🖤⚙️ᚱ

---
