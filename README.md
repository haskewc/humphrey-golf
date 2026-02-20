# Humphrey Golf - Antique Golf Ball Collection Database

A web-based database and search interface for the Kevin McGimpsey "Collectible Golf Balls Directory" — featuring 552 antique gutta-percha golf balls from 1845–1903.

**Live Demo:** *(Coming soon)*

## Features

- **Browse** all 552 golf balls in the collection
- **Search** by name, manufacturer, era, or pattern
- **Filter** by cover pattern, era, value range, country of origin
- **Detailed views** with auction history, patents, and specifications
- **Statistics** pages showing distribution by pattern, country, and era
- **Responsive design** inspired by the original Folio publications

## Dataset

Source: Kevin McGimpsey's "Folio I: Gutta-Percha Golf Balls 1845–1903"
- 552 records of antique/collectible golf balls
- Values ranging from $200 to $250,000
- Historical data including patents, auction results, and provenance

## Tech Stack

- **Backend:** Python Flask + SQLite
- **Frontend:** HTML5, CSS3, vanilla JavaScript
- **Design:** Classic golf/scholarly aesthetic (forest green, gold accents, parchment backgrounds)
- **No external dependencies** for easy deployment

## Quick Start

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

## Project Structure

```
humphrey-golf/
├── app.py              # Flask application
├── golf_balls.db       # SQLite database (generated from CSV)
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css   # Styling
│   └── js/
│       └── app.js      # Frontend JavaScript
└── templates/
    ├── base.html       # Base template
    ├── index.html      # Main search page
    ├── detail.html     # Ball detail page
    └── stats.html      # Statistics page
```

## Database Schema

The SQLite database includes:
- `record_no` - Unique catalogue number
- `ball_name` - Name of the golf ball
- `era` - Time period (e.g., "1890s", "1902")
- `cover_pattern` - Moulded mesh, brambles, hand hammered, etc.
- `manufacturer` - Maker name and address
- `specs` - Weights, dimensions, specifications
- `patents_legal` - Patents, designs, legal notes
- `auction_remarks` - Auction results and valuation
- `value_mid` - Estimated value in USD
- `country` - Scotland, England, USA, or Unknown
- `rarity_score` - Calculated rarity score (1-7)

## Data Source

This project uses data from **Kevin W. McGimpsey's** authoritative reference work:
- *The Collectible Golf Balls Directory, Folio I: Gutta-Percha Golf Balls 1845–1903*
- Kevin is the British Golf Collectors Society's Murdoch Medal winner (2004)
- Former lead golf expert at Bonhams1793 auction house

## License

Data copyright Kevin W. McGimpsey. Code provided for educational purposes.

## Future Enhancements

- [ ] Image gallery for each ball
- [ ] User accounts and wishlists
- [ ] Dealer directory integration
- [ ] Price trend tracking
- [ ] Export to PDF/CSV
- [ ] Mobile app

## Credits

- **Data:** Kevin W. McGimpsey
- **Development:** Humphrey (OpenClaw AI)
