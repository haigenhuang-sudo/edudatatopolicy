import json
from flask import Flask, render_template
from services.fl_school_grades_service import get_school_grades_data
from services.ewi_service import get_ewi_data

app = Flask(__name__)

_school_grades_cache = None
_ewi_cache = None

@app.route('/')

@app.route('/about')
def about():
    return render_template('about.html', active='about')

@app.route('/projects')
def projects():
    return render_template('projects.html', active='projects')

@app.route('/projects/florida-school-grades')
def florida_school_grades():
    return render_template('projects/florida_school_grades.html', active='projects')

@app.route('/projects/early-warning-system')
def early_warning_system():
    return render_template('projects/early_warning_system.html', active='projects')

@app.route('/services')
def services():
    return render_template('services.html', active='services')

@app.route('/expertise')
def expertise():
    return render_template('expertise.html', active='expertise')

@app.route('/contact')
def contact():
    return render_template('contact.html', active='contact')

@app.route('/api/florida_school_grades')
def api_florida_school_grades():
    global _school_grades_cache
    if _school_grades_cache is None:
        _school_grades_cache = get_school_grades_data()
    return app.response_class(
        response=json.dumps(_school_grades_cache, default=str),
        mimetype='application/json'
    )

@app.route('/api/ewi')
def api_ewi():
    global _ewi_cache
    if _ewi_cache is None:
        _ewi_cache = get_ewi_data()
    return app.response_class(
        response=json.dumps(_ewi_cache, default=str),
        mimetype='application/json'
    )

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    return app.send_static_file('images/logo.png')

with app.app_context():
    _school_grades_cache = get_school_grades_data()
    _ewi_cache = get_ewi_data()

if __name__ == '__main__':
    app.run(debug=True)