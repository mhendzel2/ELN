import os
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from models import db, Experiment, Image, Gel, GelBand, Quantification, BioinformaticsAnalysis
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///eln.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))

CORS(app)
db.init_app(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tif', 'tiff', 'gif', 'bmp', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Experiment endpoints
@app.route('/api/experiments', methods=['GET', 'POST'])
def experiments():
    if request.method == 'GET':
        experiments = Experiment.query.order_by(Experiment.date.desc()).all()
        return jsonify([exp.to_dict() for exp in experiments])
    
    elif request.method == 'POST':
        data = request.json
        experiment = Experiment(
            title=data.get('title'),
            description=data.get('description'),
            researcher=data.get('researcher'),
            tags=','.join(data.get('tags', []))
        )
        db.session.add(experiment)
        db.session.commit()
        return jsonify(experiment.to_dict()), 201

@app.route('/api/experiments/<int:exp_id>', methods=['GET', 'PUT', 'DELETE'])
def experiment_detail(exp_id):
    experiment = Experiment.query.get_or_404(exp_id)
    
    if request.method == 'GET':
        result = experiment.to_dict()
        result['images'] = [img.to_dict() for img in experiment.images]
        result['gels'] = [gel.to_dict() for gel in experiment.gels]
        result['quantifications'] = [q.to_dict() for q in experiment.quantifications]
        result['bioinformatics'] = [bio.to_dict() for bio in experiment.bioinformatics]
        return jsonify(result)
    
    elif request.method == 'PUT':
        data = request.json
        experiment.title = data.get('title', experiment.title)
        experiment.description = data.get('description', experiment.description)
        experiment.researcher = data.get('researcher', experiment.researcher)
        experiment.tags = ','.join(data.get('tags', []))
        db.session.commit()
        return jsonify(experiment.to_dict())
    
    elif request.method == 'DELETE':
        db.session.delete(experiment)
        db.session.commit()
        return '', 204

# Image endpoints
@app.route('/api/experiments/<int:exp_id>/images', methods=['POST'])
def upload_image(exp_id):
    experiment = Experiment.query.get_or_404(exp_id)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid collisions
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        image = Image(
            experiment_id=exp_id,
            filename=filename,
            original_filename=secure_filename(file.filename),
            image_type=request.form.get('image_type'),
            magnification=request.form.get('magnification'),
            scale_bar=float(request.form.get('scale_bar')) if request.form.get('scale_bar') else None,
            notes=request.form.get('notes')
        )
        db.session.add(image)
        db.session.commit()
        return jsonify(image.to_dict()), 201
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/images/<int:img_id>', methods=['GET', 'DELETE'])
def image_detail(img_id):
    image = Image.query.get_or_404(img_id)
    
    if request.method == 'GET':
        return jsonify(image.to_dict())
    
    elif request.method == 'DELETE':
        # Delete file from disk
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(image)
        db.session.commit()
        return '', 204

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Gel endpoints
@app.route('/api/experiments/<int:exp_id>/gels', methods=['POST'])
def upload_gel(exp_id):
    experiment = Experiment.query.get_or_404(exp_id)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        gel = Gel(
            experiment_id=exp_id,
            filename=filename,
            original_filename=secure_filename(file.filename),
            gel_type=request.form.get('gel_type'),
            num_lanes=int(request.form.get('num_lanes')) if request.form.get('num_lanes') else None,
            lane_labels=request.form.get('lane_labels'),
            marker_info=request.form.get('marker_info'),
            notes=request.form.get('notes')
        )
        db.session.add(gel)
        db.session.commit()
        return jsonify(gel.to_dict()), 201
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/gels/<int:gel_id>', methods=['GET', 'DELETE'])
def gel_detail(gel_id):
    gel = Gel.query.get_or_404(gel_id)
    
    if request.method == 'GET':
        result = gel.to_dict()
        result['bands'] = [band.to_dict() for band in gel.bands]
        return jsonify(result)
    
    elif request.method == 'DELETE':
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], gel.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(gel)
        db.session.commit()
        return '', 204

# Quantification endpoints
@app.route('/api/experiments/<int:exp_id>/quantifications', methods=['GET', 'POST'])
def quantifications(exp_id):
    experiment = Experiment.query.get_or_404(exp_id)
    
    if request.method == 'GET':
        quants = Quantification.query.filter_by(experiment_id=exp_id).all()
        return jsonify([q.to_dict() for q in quants])
    
    elif request.method == 'POST':
        data = request.json
        quant = Quantification(
            experiment_id=exp_id,
            source_type=data.get('source_type'),
            source_id=data.get('source_id'),
            measurement_type=data.get('measurement_type'),
            value=data.get('value'),
            unit=data.get('unit'),
            statistics=json.dumps(data.get('statistics', {})),
            method=data.get('method'),
            notes=data.get('notes')
        )
        db.session.add(quant)
        db.session.commit()
        return jsonify(quant.to_dict()), 201

# Bioinformatics endpoints
@app.route('/api/experiments/<int:exp_id>/bioinformatics', methods=['GET', 'POST'])
def bioinformatics(exp_id):
    experiment = Experiment.query.get_or_404(exp_id)
    
    if request.method == 'GET':
        analyses = BioinformaticsAnalysis.query.filter_by(experiment_id=exp_id).all()
        return jsonify([a.to_dict() for a in analyses])
    
    elif request.method == 'POST':
        data = request.json
        analysis = BioinformaticsAnalysis(
            experiment_id=exp_id,
            analysis_type=data.get('analysis_type'),
            input_files=json.dumps(data.get('input_files', [])),
            output_files=json.dumps(data.get('output_files', [])),
            parameters=json.dumps(data.get('parameters', {})),
            results_summary=data.get('results_summary'),
            pipeline=data.get('pipeline'),
            version=data.get('version'),
            notes=data.get('notes')
        )
        db.session.add(analysis)
        db.session.commit()
        return jsonify(analysis.to_dict()), 201

# Search endpoint
@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    experiments = Experiment.query.filter(
        db.or_(
            Experiment.title.contains(query),
            Experiment.description.contains(query),
            Experiment.tags.contains(query)
        )
    ).all()
    
    return jsonify([exp.to_dict() for exp in experiments])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
