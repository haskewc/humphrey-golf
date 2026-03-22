from flask import Flask, render_template, request, jsonify, g, send_from_directory
import sqlite3
import os
import json

app = Flask(__name__)
DATABASE = 'golf_balls_v2.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_book_structure():
    with open('static/book_content/book_structure.json', 'r') as f:
        return json.load(f)

def get_current_folio(folio_num=1):
    """Get current folio data"""
    book = load_book_structure()
    for folio in book['folios']:
        if folio['number'] == folio_num:
            return folio
    return book['folios'][0]

def get_chapter_nav(folio, current_id):
    """Get previous and next chapter for navigation"""
    chapters = folio['chapters']
    current_idx = next((i for i, ch in enumerate(chapters) if ch['id'] == current_id), None)
    
    prev_ch = chapters[current_idx - 1] if current_idx and current_idx > 0 else None
    next_ch = chapters[current_idx + 1] if current_idx is not None and current_idx < len(chapters) - 1 else None
    
    return prev_ch, next_ch

# Book Routes
@app.route('/')
def index():
    return render_template('intro.html')

@app.route('/book')
@app.route('/book/folio/<int:folio_num>')
def book_welcome(folio_num=1):
    book = load_book_structure()
    folio = get_current_folio(folio_num)
    
    if folio.get('coming_soon'):
        return render_template('book_coming_soon.html', folio=folio, all_folios=book['folios'])
    
    chapter = next((ch for ch in folio['chapters'] if ch['id'] == 'welcome'), folio['chapters'][0])
    prev_ch, next_ch = get_chapter_nav(folio, chapter['id'])
    
    return render_template('book_welcome.html', 
                          folio=folio, 
                          chapter=chapter, 
                          all_folios=book['folios'],
                          prev_chapter=prev_ch, 
                          next_chapter=next_ch)

@app.route('/book/<chapter_id>')
@app.route('/book/folio/<int:folio_num>/<chapter_id>')
def book_chapter(chapter_id, folio_num=1):
    book = load_book_structure()
    folio = get_current_folio(folio_num)
    
    if folio.get('coming_soon'):
        return render_template('book_coming_soon.html', folio=folio, all_folios=book['folios'])
    
    # Map chapter IDs to templates
    template_map = {
        'welcome': 'book_welcome.html',
        'author-bio': 'book_author.html',
        'andrew-forgan': 'book_andrew_forgan.html',
        'condition-grades': 'book_condition.html',
        'ball-styles': 'book_ball_styles.html',
        'highlights': 'book_highlights.html',
        'valuation-guide': 'book_valuation.html',
        'patterns': 'book_patterns.html',
        'how-to-use': 'book_how_to_use.html',
        'acknowledgements': 'book_acknowledgements.html'
    }
    
    if chapter_id not in template_map:
        return "Chapter not found", 404
    
    chapter = next((ch for ch in folio['chapters'] if ch['id'] == chapter_id), None)
    if not chapter:
        return "Chapter not found", 404
    
    prev_ch, next_ch = get_chapter_nav(folio, chapter_id)
    return render_template(template_map[chapter_id], 
                          folio=folio, 
                          chapter=chapter,
                          all_folios=book['folios'],
                          prev_chapter=prev_ch, 
                          next_chapter=next_ch)

# Modern Collection & Analytics Routes
@app.route('/collection')
def modern_collection():
    db = get_db()
    eras = db.execute('SELECT DISTINCT era FROM golf_balls WHERE era IS NOT NULL ORDER BY era_sort, era').fetchall()
    patterns = db.execute('SELECT DISTINCT cover_pattern FROM golf_balls WHERE cover_pattern IS NOT NULL ORDER BY cover_pattern').fetchall()
    countries = db.execute('SELECT DISTINCT country FROM golf_balls WHERE country IS NOT NULL ORDER BY country').fetchall()
    conditions = db.execute('SELECT DISTINCT condition_grade FROM golf_balls WHERE condition_grade IS NOT NULL ORDER BY condition_grade').fetchall()
    stats = db.execute('SELECT COUNT(*) as total FROM golf_balls').fetchone()
    book = load_book_structure()
    return render_template('modern_collection.html',
                          eras=eras, patterns=patterns, countries=countries,
                          conditions=conditions, stats=stats, folios=book['folios'])

@app.route('/analytics')
def modern_analytics():
    return render_template('modern_dashboard.html')

@app.route('/api/analytics/extra')
def analytics_extra():
    """Additional analytics data for the modern dashboard"""
    db = get_db()

    # Rarity breakdown
    by_rarity = []
    rarity_rows = db.execute('''
        SELECT rarity_score, COUNT(*) as count
        FROM golf_balls
        WHERE rarity_score IS NOT NULL AND rarity_score > 0
        GROUP BY rarity_score
        ORDER BY rarity_score
    ''').fetchall()
    for row in rarity_rows:
        by_rarity.append({'rarity_score': row['rarity_score'], 'count': row['count']})

    # Scatter: value vs era (sampled for performance)
    scatter_rows = db.execute('''
        SELECT era_start, value_mid, folio
        FROM golf_balls
        WHERE era_start IS NOT NULL AND value_mid IS NOT NULL AND value_mid > 0
        ORDER BY RANDOM()
        LIMIT 600
    ''').fetchall()
    scatter_data = [{'era_start': r['era_start'], 'value_mid': r['value_mid'], 'folio': r['folio']} for r in scatter_rows]

    # Top 10 most valuable
    top_rows = db.execute('''
        SELECT ball_name, era, value_mid, folio, currency
        FROM golf_balls
        WHERE value_mid IS NOT NULL
        ORDER BY value_mid DESC
        LIMIT 10
    ''').fetchall()
    top_valuable = [dict(r) for r in top_rows]

    # Country avg value
    country_val_rows = db.execute('''
        SELECT country, AVG(value_mid) as avg_value, COUNT(*) as count
        FROM golf_balls
        WHERE country IS NOT NULL AND value_mid IS NOT NULL AND value_mid > 0
        GROUP BY country
        ORDER BY avg_value DESC
    ''').fetchall()
    country_avg_value = [{'country': r['country'], 'avg_value': r['avg_value'], 'count': r['count']} for r in country_val_rows]

    # Top patterns by folio (top 8 patterns, broken down by folio)
    top_patterns = db.execute('''
        SELECT cover_pattern FROM golf_balls
        WHERE cover_pattern IS NOT NULL AND cover_pattern != ''
        GROUP BY cover_pattern ORDER BY COUNT(*) DESC LIMIT 8
    ''').fetchall()
    pattern_names = [r['cover_pattern'] for r in top_patterns]

    pattern_by_folio = []
    for pname in pattern_names:
        folio_rows = db.execute('''
            SELECT folio, COUNT(*) as count
            FROM golf_balls
            WHERE cover_pattern = ?
            GROUP BY folio
        ''', (pname,)).fetchall()
        for fr in folio_rows:
            pattern_by_folio.append({'pattern': pname, 'folio': fr['folio'], 'count': fr['count']})

    return jsonify({
        'by_rarity': by_rarity,
        'scatter_data': scatter_data,
        'top_valuable': top_valuable,
        'country_avg_value': country_avg_value,
        'pattern_by_folio': pattern_by_folio
    })

# Browse/Database Routes
@app.route('/browse')
def browse():
    db = get_db()
    
    # Get filter options
    eras = db.execute('SELECT DISTINCT era FROM golf_balls WHERE era IS NOT NULL ORDER BY era_sort, era').fetchall()
    patterns = db.execute('SELECT DISTINCT cover_pattern FROM golf_balls WHERE cover_pattern IS NOT NULL ORDER BY cover_pattern').fetchall()
    countries = db.execute('SELECT DISTINCT country FROM golf_balls WHERE country IS NOT NULL ORDER BY country').fetchall()
    conditions = db.execute('SELECT DISTINCT condition_grade FROM golf_balls WHERE condition_grade IS NOT NULL ORDER BY condition_grade').fetchall()
    
    # Get stats
    stats = db.execute('''
        SELECT 
            COUNT(*) as total,
            AVG(value_mid) as avg_value,
            MAX(value_mid) as max_value,
            MIN(value_mid) as min_value
        FROM golf_balls
    ''').fetchone()
    
    # Load folios for filter
    book = load_book_structure()
    folios = book['folios']
    
    return render_template('index.html', 
                          eras=eras, 
                          patterns=patterns, 
                          countries=countries,
                          conditions=conditions,
                          stats=stats,
                          folios=folios)

@app.route('/api/search')
def search():
    db = get_db()
    
    # Get query parameters
    query = request.args.get('q', '').strip()
    folio = request.args.get('folio', '')  # Empty = all folios
    era = request.args.get('era', '')
    pattern = request.args.get('pattern', '')
    country = request.args.get('country', '')
    condition = request.args.get('condition', '')
    rarity = request.args.get('rarity', '')
    min_val = request.args.get('min_value', '')
    max_val = request.args.get('max_value', '')
    sort = request.args.get('sort', 'value_mid')
    order = request.args.get('order', 'DESC')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Build query
    where_clauses = []
    params = []
    
    # Folio filter
    if folio and folio != '':
        where_clauses.append('folio = ?')
        params.append(int(folio))
    
    if query:
        where_clauses.append('''
            (ball_name LIKE ? OR 
             manufacturer LIKE ? OR 
             ball_name_format LIKE ? OR
             specs LIKE ? OR
             auction_remarks LIKE ?)
        ''')
        like_term = f'%{query}%'
        params.extend([like_term] * 5)
    
    if era:
        where_clauses.append('era = ?')
        params.append(era)
    
    if pattern:
        where_clauses.append('cover_pattern = ?')
        params.append(pattern)
    
    if country:
        where_clauses.append('country = ?')
        params.append(country)
    
    if condition:
        where_clauses.append('condition_grade = ?')
        params.append(condition)

    if rarity:
        where_clauses.append('rarity_score = ?')
        params.append(int(rarity))

    if min_val:
        where_clauses.append('value_mid >= ?')
        params.append(float(min_val))
    
    if max_val:
        where_clauses.append('value_mid <= ?')
        params.append(float(max_val))
    
    where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
    
    # Validate sort column
    valid_sorts = ['value_mid', 'ball_name', 'era_sort', 'record_no', 'condition_grade']
    if sort not in valid_sorts:
        sort = 'value_mid'
    
    order = 'ASC' if order.upper() == 'ASC' else 'DESC'
    
    # Get total count
    count_sql = f'SELECT COUNT(*) FROM golf_balls WHERE {where_sql}'
    total = db.execute(count_sql, params).fetchone()[0]
    
    # Get results
    offset = (page - 1) * per_page
    sql = f'''
        SELECT * FROM golf_balls 
        WHERE {where_sql}
        ORDER BY {sort} {order}
        LIMIT ? OFFSET ?
    '''
    params.extend([per_page, offset])
    
    rows = db.execute(sql, params).fetchall()
    
    results = []
    for row in rows:
        results.append({
            'record_no': row['record_no'],
            'ball_name': row['ball_name'],
            'ball_name_format': row['ball_name_format'],
            'era': row['era'],
            'era_start': row['era_start'],
            'cover_pattern': row['cover_pattern'],
            'manufacturer': row['manufacturer'],
            'value_mid': row['value_mid'],
            'currency': row['currency'],
            'country': row['country'],
            'condition_grade': row['condition_grade'],
            'rarity_score': row['rarity_score'],
            'folio': row['folio']
        })
    
    return jsonify({
        'results': results,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
        'folio': folio
    })

@app.route('/ball/<int:record_no>')
def ball_detail(record_no):
    db = get_db()
    ball = db.execute('SELECT * FROM golf_balls WHERE record_no = ?', (record_no,)).fetchone()
    if ball is None:
        return "Ball not found", 404
    
    # Check for uploaded images
    ball_images = []
    ball_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'ball_{record_no}')
    if os.path.exists(ball_folder):
        ball_images = [f for f in os.listdir(ball_folder) if allowed_file(f)]
    
    # Load folios for navigation
    book = load_book_structure()
    
    return render_template('detail.html', ball=ball, images=ball_images, folios=book['folios'])

@app.route('/api/ball/<int:record_no>')
def api_ball_detail(record_no):
    db = get_db()
    row = db.execute('SELECT * FROM golf_balls WHERE record_no = ?', (record_no,)).fetchone()
    if row is None:
        return jsonify({'error': 'Not found'}), 404
    
    result = dict(row)
    result['folio'] = 1  # Current folio
    return jsonify(result)

@app.route('/uploads/ball_<int:record_no>/<filename>')
def uploaded_file(record_no, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], f'ball_{record_no}'), filename)

@app.route('/api/ball/<int:record_no>/upload', methods=['POST'])
def upload_image(record_no):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        ball_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'ball_{record_no}')
        os.makedirs(ball_folder, exist_ok=True)
        
        filename = f"{len(os.listdir(ball_folder)) + 1}_{file.filename}"
        filepath = os.path.join(ball_folder, filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'/uploads/ball_{record_no}/{filename}'
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/stats')
def stats():
    db = get_db()
    
    # Various statistics
    by_pattern = db.execute('''
        SELECT cover_pattern, COUNT(*) as count, AVG(value_mid) as avg_value
        FROM golf_balls
        WHERE cover_pattern IS NOT NULL
        GROUP BY cover_pattern
        ORDER BY count DESC
    ''').fetchall()
    
    by_era = db.execute('''
        SELECT era, COUNT(*) as count, AVG(value_mid) as avg_value
        FROM golf_balls
        WHERE era IS NOT NULL
        GROUP BY era
        ORDER BY era_sort
    ''').fetchall()
    
    by_country = db.execute('''
        SELECT country, COUNT(*) as count, AVG(value_mid) as avg_value
        FROM golf_balls
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY count DESC
    ''').fetchall()
    
    by_condition = db.execute('''
        SELECT condition_grade, COUNT(*) as count, AVG(value_mid) as avg_value
        FROM golf_balls
        WHERE condition_grade IS NOT NULL
        GROUP BY condition_grade
        ORDER BY condition_grade
    ''').fetchall()
    
    # Folio breakdown
    by_folio = db.execute('''
        SELECT folio, COUNT(*) as count, AVG(value_mid) as avg_value, currency
        FROM golf_balls
        WHERE folio IS NOT NULL
        GROUP BY folio
        ORDER BY folio
    ''').fetchall()
    
    top_valuable = db.execute('''
        SELECT record_no, ball_name, era, value_mid, manufacturer, condition_grade, folio, currency
        FROM golf_balls
        ORDER BY value_mid DESC
        LIMIT 20
    ''').fetchall()
    
    # Load folios
    book = load_book_structure()
    
    return render_template('stats.html',
                          by_pattern=by_pattern,
                          by_era=by_era,
                          by_country=by_country,
                          by_condition=by_condition,
                          by_folio=by_folio,
                          top_valuable=top_valuable,
                          folios=book['folios'])

# Dashboard Routes
@app.route('/dashboard')
def dashboard():
    """Render the dashboard page"""
    book = load_book_structure()
    return render_template('dashboard.html', folios=book['folios'])

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Return comprehensive stats for the dashboard"""
    db = get_db()
    
    # Get total counts
    total_balls = db.execute('SELECT COUNT(*) FROM golf_balls').fetchone()[0]
    total_manufacturers = db.execute('SELECT COUNT(DISTINCT manufacturer) FROM golf_balls').fetchone()[0]
    total_countries = db.execute('SELECT COUNT(DISTINCT country) FROM golf_balls WHERE country IS NOT NULL').fetchone()[0]
    
    # Most valuable ball
    most_valuable_row = db.execute('''
        SELECT ball_name, value_mid, folio, currency
        FROM golf_balls
        ORDER BY value_mid DESC
        LIMIT 1
    ''').fetchone()
    most_valuable = {
        "ball_name": most_valuable_row['ball_name'],
        "value": most_valuable_row['value_mid'],
        "folio": most_valuable_row['folio'],
        "currency": most_valuable_row['currency']
    }
    
    # By folio breakdown
    folio_names = {
        1: "Gutta-Percha",
        2: "Rubber-Core",
        3: "Wound Balls",
        4: "Post-War"
    }
    folio_currencies = {
        1: "USD",
        2: "GBP",
        3: "GBP",
        4: "GBP"
    }
    
    by_folio_rows = db.execute('''
        SELECT folio, COUNT(*) as count, AVG(value_mid) as avg_value, 
               MIN(value_mid) as min_value, MAX(value_mid) as max_value
        FROM golf_balls
        WHERE folio IS NOT NULL
        GROUP BY folio
        ORDER BY folio
    ''').fetchall()
    
    by_folio = []
    for row in by_folio_rows:
        percentage = round((row['count'] / total_balls) * 100, 1) if total_balls > 0 else 0
        by_folio.append({
            "folio": row['folio'],
            "name": folio_names.get(row['folio'], f"Folio {row['folio']}"),
            "count": row['count'],
            "avg_value": round(row['avg_value'], 2) if row['avg_value'] else 0,
            "min_value": row['min_value'],
            "max_value": row['max_value'],
            "currency": folio_currencies.get(row['folio'], "GBP"),
            "percentage": percentage
        })
    
    # Timeline data (balls per year, grouped by folio)
    timeline_rows = db.execute('''
        SELECT era_start, folio, COUNT(*) as count
        FROM golf_balls
        WHERE era_start IS NOT NULL AND folio IS NOT NULL
        GROUP BY era_start, folio
        ORDER BY era_start
    ''').fetchall()
    
    # Organize timeline data
    timeline_dict = {}
    for row in timeline_rows:
        year = row['era_start']
        folio = row['folio']
        count = row['count']
        if year not in timeline_dict:
            timeline_dict[year] = {"year": year}
        timeline_dict[year][f"folio_{folio}"] = count
    
    # Fill in zeros for missing folios
    timeline = []
    for year in sorted(timeline_dict.keys()):
        entry = timeline_dict[year]
        for folio_num in [1, 2, 3, 4]:
            key = f"folio_{folio_num}"
            if key not in entry:
                entry[key] = 0
        timeline.append(entry)
    
    # By country with flags
    country_flags = {
        "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "USA": "🇺🇸",
        "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
        "Ireland": "🇮🇪",
        "Japan": "🇯🇵",
        "Germany": "🇩🇪",
        "Australia": "🇦🇺",
        "Unknown": "🏳️"
    }
    
    by_country_rows = db.execute('''
        SELECT country, COUNT(*) as count
        FROM golf_balls
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY count DESC
    ''').fetchall()
    
    by_country = []
    for row in by_country_rows:
        by_country.append({
            "country": row['country'],
            "count": row['count'],
            "flag": country_flags.get(row['country'], "🏳️")
        })
    
    # Top 10 cover patterns
    by_pattern_rows = db.execute('''
        SELECT cover_pattern, COUNT(*) as count
        FROM golf_balls
        WHERE cover_pattern IS NOT NULL AND cover_pattern != ''
        GROUP BY cover_pattern
        ORDER BY count DESC
        LIMIT 10
    ''').fetchall()
    
    by_pattern = []
    for row in by_pattern_rows:
        by_pattern.append({
            "pattern": row['cover_pattern'],
            "count": row['count']
        })
    
    # By value range (histogram buckets)
    value_ranges = [
        ("Under £100", 0, 100),
        ("£100 - £500", 100, 500),
        ("£500 - £1,000", 500, 1000),
        ("£1,000 - £5,000", 1000, 5000),
        ("Over £5,000", 5000, float('inf'))
    ]
    
    by_value_range = []
    for label, min_val, max_val in value_ranges:
        if max_val == float('inf'):
            count = db.execute('SELECT COUNT(*) FROM golf_balls WHERE value_mid >= ?', (min_val,)).fetchone()[0]
        else:
            count = db.execute('SELECT COUNT(*) FROM golf_balls WHERE value_mid >= ? AND value_mid < ?', (min_val, max_val)).fetchone()[0]
        by_value_range.append({
            "range": label,
            "count": count
        })
    
    # Top 10 manufacturers
    top_manufacturers_rows = db.execute('''
        SELECT manufacturer, COUNT(*) as count, country
        FROM golf_balls
        GROUP BY manufacturer
        ORDER BY count DESC
        LIMIT 10
    ''').fetchall()
    
    top_manufacturers = []
    for row in top_manufacturers_rows:
        top_manufacturers.append({
            "name": row['manufacturer'],
            "count": row['count'],
            "country": row['country'] if row['country'] else "Unknown"
        })
    
    # Interesting facts
    interesting_facts = []
    
    # Most valuable ball fact
    interesting_facts.append(f"The most expensive ball is worth {most_valuable_row['currency']} {most_valuable_row['value_mid']:,.0f}")
    
    # Most common era/decade
    decade_counts = db.execute('''
        SELECT 
            CASE 
                WHEN era_start >= 1840 AND era_start < 1850 THEN '1840s'
                WHEN era_start >= 1850 AND era_start < 1860 THEN '1850s'
                WHEN era_start >= 1860 AND era_start < 1870 THEN '1860s'
                WHEN era_start >= 1870 AND era_start < 1880 THEN '1870s'
                WHEN era_start >= 1880 AND era_start < 1890 THEN '1880s'
                WHEN era_start >= 1890 AND era_start < 1900 THEN '1890s'
                WHEN era_start >= 1900 AND era_start < 1910 THEN '1900s'
                WHEN era_start >= 1910 AND era_start < 1920 THEN '1910s'
                WHEN era_start >= 1920 AND era_start < 1930 THEN '1920s'
                WHEN era_start >= 1930 AND era_start < 1940 THEN '1930s'
                WHEN era_start >= 1940 AND era_start < 1950 THEN '1940s'
                ELSE 'Unknown'
            END as decade,
            COUNT(*) as count
        FROM golf_balls 
        WHERE era_start IS NOT NULL
        GROUP BY decade
        ORDER BY count DESC
        LIMIT 1
    ''').fetchone()
    
    if decade_counts:
        interesting_facts.append(f"The {decade_counts['decade']} produced the most balls: {decade_counts['count']}")
    
    # Most common pattern
    top_pattern = db.execute('''
        SELECT cover_pattern, COUNT(*) as count
        FROM golf_balls
        WHERE cover_pattern IS NOT NULL AND cover_pattern != ''
        GROUP BY cover_pattern
        ORDER BY count DESC
        LIMIT 1
    ''').fetchone()
    
    if top_pattern:
        interesting_facts.append(f"Most common cover pattern: {top_pattern['cover_pattern']} ({top_pattern['count']} balls)")
    
    # Country with most balls
    top_country = db.execute('''
        SELECT country, COUNT(*) as count
        FROM golf_balls
        WHERE country IS NOT NULL AND country != 'Unknown'
        GROUP BY country
        ORDER BY count DESC
        LIMIT 1
    ''').fetchone()
    
    if top_country:
        interesting_facts.append(f"{top_country['country']} produced {top_country['count']} balls")
    
    return jsonify({
        "total_balls": total_balls,
        "total_manufacturers": total_manufacturers,
        "total_countries": total_countries,
        "most_valuable": most_valuable,
        "by_folio": by_folio,
        "timeline": timeline,
        "by_country": by_country,
        "by_pattern": by_pattern,
        "by_value_range": by_value_range,
        "top_manufacturers": top_manufacturers,
        "interesting_facts": interesting_facts
    })

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=8085)
else:
    # For production (gunicorn)
    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
