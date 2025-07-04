import os
import json
from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Resume, Skill, ChatSession, ChatMessage, JobListing
from scraper import scrape_website
from gemini_client import GeminiClient
from resume_parser import extract_skills_from_resume
from job_matcher import find_jobs_for_skills, calculate_job_compatibility
from utils import allowed_file, validate_job_url, parse_llm_response

# Initialize Gemini client
gemini_client = GeminiClient()

@app.route('/')
def index():
    return redirect(url_for('landing'))

@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('landing'))
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        flash('Login successful!', 'success')
        return redirect(url_for('chat'))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('landing'))

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name', '')
    
    if not username or not email or not password:
        flash('Please fill in all required fields', 'error')
        return redirect(url_for('landing'))
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'error')
        return redirect(url_for('landing'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists', 'error')
        return redirect(url_for('landing'))
    
    # Create new user
    user = User(username=username, email=email, name=name)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    session['username'] = user.username
    flash('Account created successfully!', 'success')
    return redirect(url_for('chat'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('landing'))

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        flash('Please login to access chat', 'error')
        return redirect(url_for('landing'))
    
    user_id = session['user_id']
    chat_sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()
    
    return render_template('chat.html', chat_sessions=chat_sessions)

@app.route('/start_chat', methods=['POST'])
def start_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    data = request.get_json()
    website_url = data.get('website_url')
    scrape_type = data.get('scrape_type', 'content')
    
    if not website_url:
        return jsonify({'error': 'Website URL is required'}), 400
    
    # Validate job URL
    if not validate_job_url(website_url):
        return jsonify({'error': 'URL must be related to jobs/careers'}), 400
    
    try:
        # Scrape the website
        scraped_data = scrape_website(website_url, scrape_type)
        
        if not scraped_data:
            return jsonify({'error': 'Failed to scrape website'}), 500
        
        # Create chat session
        chat_session = ChatSession(
            user_id=session['user_id'],
            website_url=website_url,
            scrape_type=scrape_type,
            scraped_data=scraped_data
        )
        
        db.session.add(chat_session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': chat_session.id,
            'message': 'Website scraped successfully! You can now chat with the data.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    data = request.get_json()
    session_id = data.get('session_id')
    message_content = data.get('message')
    
    if not session_id or not message_content:
        return jsonify({'error': 'Session ID and message are required'}), 400
    
    # Get chat session
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=session['user_id']).first()
    if not chat_session:
        return jsonify({'error': 'Chat session not found'}), 404
    
    try:
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            message_type='user',
            content=message_content
        )
        db.session.add(user_message)
        
        # Get AI response
        context = f"Website URL: {chat_session.website_url}\nScraped Data ({chat_session.scrape_type}):\n{chat_session.scraped_data}"
        ai_response = gemini_client.chat_with_context(message_content, context)
        
        # Parse AI response for better formatting
        formatted_response = parse_llm_response(ai_response)
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=session_id,
            message_type='assistant',
            content=formatted_response
        )
        db.session.add(ai_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': formatted_response,
            'user_message_id': user_message.id,
            'ai_message_id': ai_message.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_chat_history/<int:session_id>')
def get_chat_history(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=session['user_id']).first()
    if not chat_session:
        return jsonify({'error': 'Chat session not found'}), 404
    
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()
    
    return jsonify({
        'session': chat_session.to_dict(),
        'messages': [message.to_dict() for message in messages]
    })

@app.route('/jobs')
def jobs():
    if 'user_id' not in session:
        flash('Please login to view jobs', 'error')
        return redirect(url_for('landing'))
    
    user_id = session['user_id']
    
    # Get user skills
    user_skills = Skill.query.filter_by(user_id=user_id).all()
    
    if not user_skills:
        flash('Please add your resume in the profile to see relevant jobs', 'warning')
        return render_template('jobs.html', jobs=[], user_skills=[])
    
    # Get skill names
    skill_names = [skill.skill_name for skill in user_skills]
    
    try:
        # Find jobs based on skills
        jobs = find_jobs_for_skills(skill_names)
        
        # Calculate compatibility for each job
        for job in jobs:
            job['compatibility'] = calculate_job_compatibility(skill_names, job.get('skills_required', []))
        
        # Sort jobs by compatibility
        jobs.sort(key=lambda x: x.get('compatibility', 0), reverse=True)
        
        return render_template('jobs.html', jobs=jobs, user_skills=skill_names)
        
    except Exception as e:
        flash(f'Error loading jobs: {str(e)}', 'error')
        return render_template('jobs.html', jobs=[], user_skills=skill_names)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please login to view profile', 'error')
        return redirect(url_for('landing'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    resumes = Resume.query.filter_by(user_id=user_id).all()
    skills = Skill.query.filter_by(user_id=user_id).all()
    
    return render_template('profile.html', user=user, resumes=resumes, skills=skills)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Update name
    name = request.form.get('name')
    if name:
        user.name = name
    
    # Handle profile image upload
    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file and file.filename:
            # Check if file is an image
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                filename = secure_filename(f"profile_{user_id}_{file.filename}")
                
                # Create profile images directory
                profile_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles')
                os.makedirs(profile_dir, exist_ok=True)
                
                file_path = os.path.join(profile_dir, filename)
                file.save(file_path)
                
                # Save relative path in database
                user.profile_image = f"uploads/profiles/{filename}"
            else:
                flash('Please upload a valid image file (PNG, JPG, JPEG, GIF)', 'error')
                return redirect(url_for('profile'))
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    if 'resume' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('profile'))
    
    file = request.files['resume']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Extract skills from resume
            extracted_text, skills = extract_skills_from_resume(file_path)
            
            # Save resume record
            resume = Resume(
                user_id=session['user_id'],
                filename=filename,
                file_path=file_path,
                extracted_text=extracted_text
            )
            db.session.add(resume)
            
            # Save extracted skills
            for skill_name in skills:
                # Check if skill already exists
                existing_skill = Skill.query.filter_by(
                    user_id=session['user_id'],
                    skill_name=skill_name
                ).first()
                
                if not existing_skill:
                    skill = Skill(
                        user_id=session['user_id'],
                        skill_name=skill_name,
                        source='resume'
                    )
                    db.session.add(skill)
            
            db.session.commit()
            flash(f'Resume uploaded successfully! Extracted {len(skills)} skills.', 'success')
            
        except Exception as e:
            flash(f'Error processing resume: {str(e)}', 'error')
    else:
        flash('Please upload a PDF file', 'error')
    
    return redirect(url_for('profile'))

@app.route('/add_skill', methods=['POST'])
def add_skill():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    skill_name = request.form.get('skill_name')
    skill_level = request.form.get('skill_level', 'Intermediate')
    
    if not skill_name:
        flash('Skill name is required', 'error')
        return redirect(url_for('profile'))
    
    # Check if skill already exists
    existing_skill = Skill.query.filter_by(
        user_id=session['user_id'],
        skill_name=skill_name
    ).first()
    
    if existing_skill:
        flash('Skill already exists', 'warning')
        return redirect(url_for('profile'))
    
    skill = Skill(
        user_id=session['user_id'],
        skill_name=skill_name,
        skill_level=skill_level,
        source='manual'
    )
    
    db.session.add(skill)
    db.session.commit()
    
    flash('Skill added successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/delete_skill/<int:skill_id>', methods=['POST'])
def delete_skill(skill_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    skill = Skill.query.filter_by(id=skill_id, user_id=session['user_id']).first()
    if not skill:
        flash('Skill not found', 'error')
        return redirect(url_for('profile'))
    
    db.session.delete(skill)
    db.session.commit()
    
    flash('Skill deleted successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/analyze_job_compatibility', methods=['POST'])
def analyze_job_compatibility():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    data = request.get_json()
    job_url = data.get('job_url')
    
    if not job_url:
        return jsonify({'error': 'Job URL is required'}), 400
    
    try:
        # Get user skills
        user_skills = Skill.query.filter_by(user_id=session['user_id']).all()
        skill_names = [skill.skill_name for skill in user_skills]
        
        if not skill_names:
            return jsonify({'error': 'Please add skills to your profile first'}), 400
        
        # Scrape job details
        job_data = scrape_website(job_url, 'content')
        
        # Analyze compatibility and get preparation suggestions
        compatibility_analysis = gemini_client.analyze_job_compatibility(skill_names, job_data)
        
        return jsonify({
            'success': True,
            'analysis': compatibility_analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
