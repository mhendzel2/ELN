from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Experiment(db.Model):
    """Main experiment entry"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    researcher = db.Column(db.String(100))
    tags = db.Column(db.String(500))
    
    # Relationships
    images = db.relationship('Image', backref='experiment', lazy=True, cascade='all, delete-orphan')
    gels = db.relationship('Gel', backref='experiment', lazy=True, cascade='all, delete-orphan')
    quantifications = db.relationship('Quantification', backref='experiment', lazy=True, cascade='all, delete-orphan')
    bioinformatics = db.relationship('BioinformaticsAnalysis', backref='experiment', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.date.isoformat(),
            'researcher': self.researcher,
            'tags': self.tags.split(',') if self.tags else []
        }

class Image(db.Model):
    """Microscopy and general imaging data"""
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200))
    image_type = db.Column(db.String(50))  # microscopy, western, etc.
    magnification = db.Column(db.String(50))
    scale_bar = db.Column(db.Float)  # in micrometers
    notes = db.Column(db.Text)
    metadata = db.Column(db.Text)  # JSON string for additional metadata
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'experiment_id': self.experiment_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'image_type': self.image_type,
            'magnification': self.magnification,
            'scale_bar': self.scale_bar,
            'notes': self.notes,
            'upload_date': self.upload_date.isoformat()
        }

class Gel(db.Model):
    """Gel electrophoresis data"""
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200))
    gel_type = db.Column(db.String(50))  # SDS-PAGE, agarose, etc.
    num_lanes = db.Column(db.Integer)
    lane_labels = db.Column(db.Text)  # JSON string
    marker_info = db.Column(db.Text)
    notes = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bands = db.relationship('GelBand', backref='gel', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'experiment_id': self.experiment_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'gel_type': self.gel_type,
            'num_lanes': self.num_lanes,
            'lane_labels': self.lane_labels,
            'marker_info': self.marker_info,
            'notes': self.notes,
            'upload_date': self.upload_date.isoformat()
        }

class GelBand(db.Model):
    """Individual bands detected in gels"""
    id = db.Column(db.Integer, primary_key=True)
    gel_id = db.Column(db.Integer, db.ForeignKey('gel.id'), nullable=False)
    lane_number = db.Column(db.Integer)
    position = db.Column(db.Float)  # Position in pixels or relative units
    intensity = db.Column(db.Float)
    molecular_weight = db.Column(db.Float)  # kDa
    area = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'gel_id': self.gel_id,
            'lane_number': self.lane_number,
            'position': self.position,
            'intensity': self.intensity,
            'molecular_weight': self.molecular_weight,
            'area': self.area
        }

class Quantification(db.Model):
    """Quantification results from image analysis"""
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    source_type = db.Column(db.String(50))  # image, gel, etc.
    source_id = db.Column(db.Integer)  # ID of the source (image_id or gel_id)
    measurement_type = db.Column(db.String(100))  # cell count, band intensity, etc.
    value = db.Column(db.Float)
    unit = db.Column(db.String(50))
    statistics = db.Column(db.Text)  # JSON string for mean, std, etc.
    method = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'experiment_id': self.experiment_id,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'measurement_type': self.measurement_type,
            'value': self.value,
            'unit': self.unit,
            'statistics': self.statistics,
            'method': self.method,
            'notes': self.notes,
            'created_date': self.created_date.isoformat()
        }

class BioinformaticsAnalysis(db.Model):
    """Bioinformatics analysis results"""
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    analysis_type = db.Column(db.String(100))  # RNA-seq, genomics, proteomics, etc.
    input_files = db.Column(db.Text)  # JSON list of input filenames
    output_files = db.Column(db.Text)  # JSON list of output filenames
    parameters = db.Column(db.Text)  # JSON string of analysis parameters
    results_summary = db.Column(db.Text)
    pipeline = db.Column(db.String(200))
    version = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'experiment_id': self.experiment_id,
            'analysis_type': self.analysis_type,
            'input_files': self.input_files,
            'output_files': self.output_files,
            'parameters': self.parameters,
            'results_summary': self.results_summary,
            'pipeline': self.pipeline,
            'version': self.version,
            'notes': self.notes,
            'created_date': self.created_date.isoformat()
        }
