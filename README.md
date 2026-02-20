# Humphrey Golf - Antique Golf Ball Collection Database

A complete web-based version of **"The Collectible Golf Balls Directory, Folio I: Gutta-Percha Golf Balls 1845–1903"** by Kevin W. McGimpsey.

**Live Demo:** http://192.168.86.116:8085

**GitHub Repo:** https://github.com/haskewc/humphrey-golf

---

## 📚 What's Included

### The Book (Web Version)
A complete digital version of the directory with all chapters:

1. **Welcome** — Title page with book cover
2. **About the Author** — Kevin McGimpsey biography
3. **Andrew Forgan** — The first golf ball collector (180 balls, 1907)
4. **Condition Grading System** — A1-A5 balls, W1-W4 wrappers, B1-B3 boxes
5. **Common Ball Name Styles** — 11 different naming conventions
6. **Highlights 1845-1903** — History of gutta-percha balls
7. **Golf Ball Valuation Guide** — Factors affecting value, price ranges
8. **Patterns, Sizes, Weights** — Technical specifications
9. **How to Use This Directory** — Complete user guide
10. **The Golf Ball Directory** — Interactive database (551 balls)
11. **Acknowledgements** — Credits and thanks

### Interactive Database
- **551 antique golf balls** from 1845–1903
- **Search & Filter** by name, era, pattern, country, condition, value
- **Condition grades** (A1-A5) extracted and filterable
- **Image upload** — Add photos to any ball record
- **Statistics** — Distribution by pattern, country, condition, value

### Data Quality (V2 Database)
- **Cleaned era formats** — "Early 1890s", "Mid 1880s", "Late 1890s"
- **Proper case text** — Fixed ALL CAPS entries
- **Condition grades** — Parsed from auction remarks
- **Chronological sorting** — Eras sort correctly by date

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/haskewc/humphrey-golf.git
cd humphrey-golf

# Install dependencies
pip install flask

# Run the application
python app.py

# Open browser to http://localhost:8085
```

---

## 📖 Navigation

| Page | URL | Description |
|------|-----|-------------|
| **Home** | `/` | Welcome introduction |
| **The Book** | `/book` | Complete digital book |
| **Browse** | `/browse` | Searchable database |
| **Statistics** | `/stats` | Analytics & charts |

---

## 🗄️ Database Schema (V2)

```sql
CREATE TABLE golf_balls (
    record_no INTEGER PRIMARY KEY,
    ball_name TEXT,
    ball_name_format TEXT,
    era TEXT,              -- "Early 1890s", "Mid 1880s", etc.
    era_start INTEGER,     -- For sorting
    era_sort INTEGER,      -- Chronological sort key
    cover_pattern TEXT,
    manufacturer TEXT,
    specs TEXT,
    patents_legal TEXT,
    auction_remarks TEXT,
    condition_grade TEXT,  -- A1, A2, A3, A4, A5, W1, W3
    value_mid REAL,
    currency TEXT,
    country TEXT,          -- Scotland, England, USA, Unknown
    rarity_score INTEGER
);
```

---

## 🎨 Design

- **Color palette:** Forest green, gold accents, parchment backgrounds
- **Typography:** Playfair Display (headings), Source Sans Pro (body)
- **Responsive:** Works on desktop, tablet, and mobile
- **Book styling:** Matches the scholarly aesthetic of the original publication

---

## 💾 File Structure

```
humphrey-golf/
├── app.py                      # Flask application
├── golf_balls_v2.db           # Cleaned SQLite database
├── golf_balls_backup_v1.db    # Original backup
├── requirements.txt
├── static/
│   ├── css/style.css          # Styling
│   ├── js/app.js              # Frontend JavaScript
│   ├── images/                # Book cover, etc.
│   ├── book_content/          # Book structure JSON
│   └── uploads/               # User-uploaded ball photos
├── templates/
│   ├── base.html              # Base template
│   ├── intro.html             # Homepage
│   ├── book_base.html         # Book chapter template
│   ├── book_*.html            # Individual chapters
│   ├── index.html             # Browse page
│   ├── detail.html            # Ball detail page
│   └── stats.html             # Statistics page
└── docs/
    └── ROADMAP.md             # Future enhancements
```

---

## 📊 Statistics

- **551** golf balls catalogued
- **$200 - $250,000** value range
- **1845 - 1903** era coverage
- **48** unique eras
- **17** cover patterns
- **71** balls with condition grades
- **3** countries (Scotland, England, USA)

---

## 🔮 Future Enhancements

- [ ] Image search for balls without photos
- [ ] Manufacturer profile pages with maps
- [ ] Historical advertisement gallery
- [ ] User accounts and wishlists
- [ ] Price trend tracking
- [ ] Mobile app

---

## 📄 License

Data copyright Kevin W. McGimpsey. Code provided for educational purposes.

---

## 🙏 Credits

- **Data:** Kevin W. McGimpsey
- **Development:** Humphrey (OpenClaw AI)
- **Design:** Based on the original book by Nick Sample
