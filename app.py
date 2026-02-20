from flask import Flask, render_template, request, jsonify, g, send_from_directory
import sqlite3
import os
import re

app = Flask(__name__)
DATABASE = 'golf_balls_v2.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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

# Introduction page
@app.route('/')
def index():
    return render_template('intro.html')

# Main browse page
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
    
    return render_template('index.html', 
                          eras=eras, 
                          patterns=patterns, 
                          countries=countries,
                          conditions=conditions,
                          stats=stats)

@app.route('/api/search')
def search():
    db = get_db()
    
    # Get query parameters
    query = request.args.get('q', '').strip()
    era = request.args.get('era', '')
    pattern = request.args.get('pattern', '')
    country = request.args.get('country', '')
    condition = request.args.get('condition', '')
    min_val = request.args.get('min_value', '')
    max_val = request.args.get('max_value', '')
    sort = request.args.get('sort', 'value_mid')
    order = request.args.get('order', 'DESC')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Build query
    where_clauses = []
    params = []
    
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
            'rarity_score': row['rarity_score']
        })
    
    return jsonify({
        'results': results,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
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
    
    return render_template('detail.html', ball=ball, images=ball_images)

@app.route('/api/ball/<int:record_no>')
def api_ball_detail(record_no):
    db = get_db()
    row = db.execute('SELECT * FROM golf_balls WHERE record_no = ?', (record_no,)).fetchone()
    if row is None:
        return jsonify({'error': 'Not found'}), 404
    
    return jsonify(dict(row))

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
    
    top_valuable = db.execute('''
        SELECT record_no, ball_name, era, value_mid, manufacturer, condition_grade
        FROM golf_balls
        ORDER BY value_mid DESC
        LIMIT 20
    ''').fetchall()
    
    return render_template('stats.html',
                          by_pattern=by_pattern,
                          by_era=by_era,
                          by_country=by_country,
                          by_condition=by_condition,
                          top_valuable=top_valuable)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8085)
