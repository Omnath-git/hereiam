# utils/profile_generator.py
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.helpers import safe_json_loads


def generate_profile_html(user, app):
    """Generate beautiful, modern HTML profile page"""
    try:
        skills = safe_json_loads(user.skills)
        education = safe_json_loads(user.education)
        experience = safe_json_loads(user.experience)
        projects = safe_json_loads(user.projects)
        certifications = safe_json_loads(user.certifications)
        languages = safe_json_loads(user.languages)
        achievements = safe_json_loads(user.achievements)
        
        # Create safe filename with TIMESTAMP
        full_name = (user.full_name or 'User').replace(' ', '_')
        domain = (user.domain or 'General').replace(' ', '_')
        city = (user.city or 'City').replace(' ', '_')
        state = (user.state or 'State').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"{full_name}_{domain}_{city}_{state}_{timestamp}.html"
        filename = secure_filename(filename)
        filepath = os.path.join(app.config['PROFILES_FOLDER'], filename)
        
        # Delete old profile
        if user.profile_url and user.profile_url != filename:
            old_path = os.path.join(app.config['PROFILES_FOLDER'], user.profile_url)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass
        
        # Profile photo
        profile_photo_url = f"../static/{user.profile_photo}" if user.profile_photo else "../static/uploads/profile_photos/avatar.png"
        
        # Privacy
        if user.show_email:
            email_display = user.email
            email_link = f"mailto:{user.email}"
        else:
            parts = user.email.split('@')
            email_display = parts[0][:3] + '***@' + parts[1] if len(parts) == 2 else 'Hidden'
            email_link = "#"
        
        if user.show_mobile:
            mobile_display = user.mobile
            mobile_link = f"tel:{user.mobile}"
        else:
            mobile_display = user.mobile[:3] + '****' + user.mobile[-3:] if len(user.mobile) >= 10 else 'Hidden'
            mobile_link = "#"
        
        # ⭐ Fix: Experience display - blank nahi, balki sahi value ya empty
        if user.experience_years and user.experience_years.strip() and user.experience_years.lower() != 'fresher':
            experience_display = user.experience_years
        elif user.experience_years and user.experience_years.lower() == 'fresher':
            experience_display = 'Fresher'
        else:
            experience_display = ''
        
        # Build HTML
        html = build_complete_html(
            user, profile_photo_url,
            email_display, email_link,
            mobile_display, mobile_link,
            experience_display,
            skills, education, experience, projects,
            certifications, languages, achievements
        )
        
        # Save
        os.makedirs(app.config['PROFILES_FOLDER'], exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Profile generated: {filename}")
        return filename
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def build_complete_html(user, photo_url, email_display, email_link, mobile_display, mobile_link,
                        experience_display, skills, education, experience, projects,
                        certifications, languages, achievements):
    """Build complete HTML - all f-strings properly escaped"""
    
    # Pre-build all sections
    about_html = build_about_section(user)
    skills_html = build_skills_section(skills)
    experience_html = build_experience_section(experience)
    education_html = build_education_section(education)
    projects_html = build_projects_section(projects)
    certifications_html = build_certifications_section(certifications)
    languages_html = build_languages_section(languages)
    achievements_html = build_achievements_section(achievements)
    social_links = build_social_links(user)
    
    # Combine sections
    sections_html = (about_html + skills_html + experience_html + 
                    education_html + projects_html + certifications_html +
                    languages_html + achievements_html)
    
    # Experience display with fallback
    exp_display = experience_display if experience_display else 'Fresher'
    
    # Hero meta items
    hero_meta_items = ''
    if experience_display:
        hero_meta_items += f'<span class="hero-meta-item"><i class="fas fa-clock"></i> {experience_display}</span>\n'
    hero_meta_items += f'<span class="hero-meta-item"><i class="fas fa-map-marker-alt"></i> {user.city}, {user.state}</span>\n'
    if user.expected_salary:
        hero_meta_items += f'<span class="hero-meta-item"><i class="fas fa-rupee-sign salary"></i> {user.expected_salary}</span>\n'
    if user.notice_period:
        hero_meta_items += f'<span class="hero-meta-item"><i class="fas fa-calendar-alt notice"></i> {user.notice_period}</span>\n'
    
    # Sidebar info items
    sidebar_info = ''
    sidebar_info += f'<div class="sidebar-info-item"><i class="fas fa-clock"></i> {exp_display}</div>\n'
    sidebar_info += f'<div class="sidebar-info-item"><i class="fas fa-map-marker-alt"></i> {user.city}, {user.state}</div>\n'
    sidebar_info += f'<div class="sidebar-info-item"><i class="fas fa-envelope"></i> {email_display}</div>\n'
    sidebar_info += f'<div class="sidebar-info-item"><i class="fas fa-phone"></i> {mobile_display}</div>\n'
    if user.expected_salary:
        sidebar_info += f'<div class="sidebar-info-item"><i class="fas fa-rupee-sign"></i> {user.expected_salary}</div>\n'
    if user.notice_period:
        sidebar_info += f'<div class="sidebar-info-item"><i class="fas fa-calendar-alt"></i> {user.notice_period}</div>\n'
    
    # Sidebar social card
    sidebar_social = ''
    if social_links:
        sidebar_social = f'''<div class="sidebar-card">
            <h4 style="font-weight:700;margin-bottom:12px;color:var(--dark);">
                <i class="fas fa-link me-2" style="color:var(--primary);"></i>Connect
            </h4>
            <div class="social-links">{social_links}</div>
        </div>'''
    
    # Contact social
    contact_social = ''
    if social_links:
        contact_social = f'<div class="social-links" style="margin-top:20px;">{social_links}</div>'
    
    # Current year
    current_year = datetime.now().year
    
    # ⭐ BUILD COMPLETE HTML - using .format() to avoid f-string nesting issues
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{full_name} - {domain} | Professionals Data Bank">
    <title>{full_name} - {domain} | Professionals Data Bank</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #6366f1;
            --primary-light: #818cf8;
            --primary-dark: #4f46e5;
            --primary-bg: #eef2ff;
            --secondary: #64748b;
            --dark: #0f172a;
            --dark-2: #1e293b;
            --light: #f8fafc;
            --light-2: #f1f5f9;
            --white: #ffffff;
            --success: #10b981;
            --success-light: #d1fae5;
            --warning: #f59e0b;
            --warning-light: #fef3c7;
            --danger: #ef4444;
            --danger-light: #fee2e2;
            --info: #3b82f6;
            --info-light: #dbeafe;
            --purple: #8b5cf6;
            --gradient-1: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            --gradient-2: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            --gradient-hero: linear-gradient(160deg, #eef2ff 0%, #e0e7ff 30%, #f8fafc 100%);
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
            --shadow-lg: 0 10px 25px -5px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.05);
            --shadow-xl: 0 20px 40px -10px rgba(0,0,0,0.1);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 20px;
            --radius-2xl: 24px;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
            background: var(--light);
            color: var(--dark-2);
            line-height: 1.7;
            -webkit-font-smoothing: antialiased;
        }}
        
        /* ============ NAVBAR ============ */
        .navbar {{
            background: rgba(255,255,255,0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            padding: 14px 0;
            border-bottom: 1px solid rgba(226,232,240,0.8);
            transition: all 0.3s;
        }}
        .navbar.scrolled {{ box-shadow: var(--shadow-lg); }}
        .nav-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .nav-brand {{
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--dark);
        }}
        .nav-brand-icon {{
            width: 38px;
            height: 38px;
            background: var(--gradient-1);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1rem;
        }}
        .nav-links {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .nav-link {{
            color: var(--secondary);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.85rem;
            padding: 8px 14px;
            border-radius: var(--radius-sm);
            transition: all 0.2s;
        }}
        .nav-link:hover {{ color: var(--primary); background: var(--primary-bg); }}
        
        /* ============ HERO ============ */
        .hero {{
            background: var(--gradient-hero);
            padding: 140px 0 80px;
            position: relative;
            overflow: hidden;
        }}
        .hero::before {{
            content: '';
            position: absolute;
            top: -100px;
            right: -100px;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%);
            border-radius: 50%;
        }}
        .hero::after {{
            content: '';
            position: absolute;
            bottom: -80px;
            left: -80px;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%);
            border-radius: 50%;
        }}
        .hero-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            align-items: center;
            gap: 60px;
            position: relative;
            z-index: 1;
        }}
        .hero-content {{ flex: 1; }}
        .hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: white;
            color: var(--primary);
            padding: 6px 14px;
            border-radius: 50px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 16px;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--primary-bg);
        }}
        .hero-badge i {{ font-size: 0.7rem; }}
        .hero-name {{
            font-family: 'Playfair Display', serif;
            font-size: 3.8rem;
            font-weight: 800;
            color: var(--dark);
            line-height: 1.1;
            margin-bottom: 12px;
            letter-spacing: -1px;
        }}
        .hero-title-text {{
            font-size: 1.2rem;
            color: var(--primary);
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .hero-summary {{
            font-size: 1rem;
            color: var(--secondary);
            margin-bottom: 24px;
            max-width: 600px;
            line-height: 1.7;
        }}
        .hero-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 24px;
        }}
        .hero-meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: white;
            padding: 10px 18px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.85rem;
            box-shadow: var(--shadow-sm);
            border: 1px solid #e2e8f0;
            color: var(--dark-2);
        }}
        .hero-meta-item i {{ color: var(--primary); font-size: 0.9rem; }}
        
        .hero-photo-wrapper {{
            flex-shrink: 0;
            position: relative;
        }}
        .hero-photo-ring {{
            position: absolute;
            inset: -15px;
            border-radius: 50%;
            border: 3px dashed var(--primary-light);
            opacity: 0.4;
            animation: spin 30s linear infinite;
        }}
        @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
        .hero-photo {{
            width: 260px;
            height: 260px;
            border-radius: 50%;
            overflow: hidden;
            border: 6px solid white;
            box-shadow: var(--shadow-xl);
            position: relative;
            z-index: 1;
        }}
        .hero-photo img {{ width: 100%; height: 100%; object-fit: cover; }}
        
        /* ============ MAIN LAYOUT ============ */
        .main-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: grid;
            grid-template-columns: 1fr 340px;
            gap: 32px;
            margin-top: -30px;
            position: relative;
            z-index: 10;
        }}
        
        /* ============ SECTION CARD ============ */
        .section-card {{
            background: white;
            border-radius: var(--radius-xl);
            padding: 24px 28px;
            margin-bottom: 20px;
            box-shadow: var(--shadow-sm);
            border: 1px solid #f1f5f9;
            transition: all 0.3s;
        }}
        .section-card:hover {{ box-shadow: var(--shadow-lg); transform: translateY(-2px); }}
        .section-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 18px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--light-2);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section-title i {{ color: var(--primary); font-size: 1.1rem; }}
        .section-subtitle {{ color: var(--secondary); font-size: 0.88rem; margin-bottom: 16px; line-height: 1.7; }}
        
        /* ============ SKILLS ============ */
        .skills-container {{ display: flex; flex-wrap: wrap; gap: 6px; }}
        .skill-item {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: var(--primary-bg);
            color: var(--primary-dark);
            padding: 6px 14px;
            border-radius: 50px;
            font-size: 0.82rem;
            font-weight: 600;
            transition: all 0.3s;
            border: 1px solid transparent;
        }}
        .skill-item:hover {{ background: var(--primary); color: white; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(99,102,241,0.3); }}
        .skill-item.skill-level-expert {{ background: linear-gradient(135deg, #dbeafe, #ede9fe); border-color: #c4b5fd; }}
        .skill-item.skill-level-advanced {{ background: #f0fdf4; border-color: #bbf7d0; }}
        
        /* ============ EXPERIENCE ============ */
        .exp-list {{ display: flex; flex-direction: column; gap: 12px; }}
        .exp-card {{
            background: var(--light); border-radius: var(--radius-md); padding: 14px 16px;
            border-left: 3px solid var(--primary); transition: all 0.3s;
        }}
        .exp-card:hover {{ background: white; box-shadow: var(--shadow-md); }}
        .exp-card.current {{ border-left-color: var(--success); background: #f0fdf4; }}
        .exp-card-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; flex-wrap: wrap; }}
        .exp-title {{ font-weight: 700; font-size: 0.9rem; color: var(--dark); }}
        .exp-company {{ font-weight: 600; font-size: 0.82rem; color: var(--primary); }}
        .exp-duration {{ font-size: 0.7rem; background: var(--primary-bg); color: var(--primary-dark); padding: 3px 10px; border-radius: 50px; font-weight: 600; white-space: nowrap; }}
        .exp-duration.current-dur {{ background: #d1fae5; color: #065f46; }}
        .exp-desc {{ font-size: 0.8rem; color: var(--secondary); margin-top: 6px; }}
        
        /* ============ EDUCATION ============ */
        .edu-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }}
        .edu-card {{
            background: var(--light); border-radius: var(--radius-md); padding: 14px;
            border-top: 3px solid var(--primary); transition: all 0.3s;
        }}
        .edu-card:hover {{ background: white; box-shadow: var(--shadow-md); }}
        .edu-degree {{ font-weight: 700; font-size: 0.85rem; color: var(--dark); margin-bottom: 2px; }}
        .edu-inst {{ font-size: 0.78rem; color: var(--secondary); }}
        .edu-year {{ display: inline-block; font-size: 0.68rem; color: var(--primary); font-weight: 600; margin-top: 4px; }}
        
        /* ============ PROJECTS ============ */
        .proj-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px; }}
        .proj-card {{
            background: var(--light); border-radius: var(--radius-md); padding: 14px;
            border: 1px solid #e5e7eb; transition: all 0.3s;
        }}
        .proj-card:hover {{ background: white; box-shadow: var(--shadow-md); transform: translateY(-2px); }}
        .proj-name {{ font-weight: 700; font-size: 0.85rem; color: var(--dark); margin-bottom: 4px; }}
        .proj-desc {{ font-size: 0.75rem; color: var(--secondary); margin-bottom: 6px; }}
        .proj-tech {{ display: flex; flex-wrap: wrap; gap: 3px; }}
        .proj-tech-tag {{ background: white; color: var(--secondary); padding: 2px 7px; border-radius: 20px; font-size: 0.65rem; font-weight: 500; border: 1px solid #e5e7eb; }}
        
        /* ============ CERTIFICATIONS ============ */
        .cert-list {{ display: flex; flex-wrap: wrap; gap: 6px; }}
        .cert-tag {{
            display: flex; align-items: center; gap: 5px;
            background: linear-gradient(135deg, #fef3c7, #fef9c3); padding: 6px 12px;
            border-radius: 50px; font-weight: 600; font-size: 0.75rem; color: #92400e;
        }}
        .cert-tag i {{ color: var(--warning); font-size: 0.7rem; }}
        
        /* ============ LANGUAGES ============ */
        .lang-list {{ display: flex; flex-wrap: wrap; gap: 6px; }}
        .lang-tag {{
            background: white; border: 2px solid #e2e8f0; padding: 6px 14px;
            border-radius: 50px; font-weight: 600; font-size: 0.78rem; color: var(--dark-2);
            transition: all 0.3s;
        }}
        .lang-tag:hover {{ border-color: var(--primary); color: var(--primary); }}
        
        /* ============ ACHIEVEMENTS ============ */
        .ach-list {{ display: flex; flex-direction: column; gap: 8px; }}
        .ach-item {{
            display: flex; gap: 10px; padding: 10px 12px;
            background: linear-gradient(135deg, #faf5ff, #f5f3ff);
            border-radius: var(--radius-sm); border-left: 3px solid var(--purple);
            font-size: 0.82rem; color: var(--dark-2); font-weight: 500;
        }}
        .ach-item i {{ color: var(--warning); font-size: 0.9rem; margin-top: 2px; flex-shrink: 0; }}
        
        /* ============ SIDEBAR ============ */
        .sidebar-card {{
            background: white; border-radius: var(--radius-lg); padding: 18px;
            margin-bottom: 14px; box-shadow: var(--shadow-sm); border: 1px solid #f1f5f9;
            text-align: center;
        }}
        .sidebar-avatar {{ width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 4px solid white; box-shadow: var(--shadow-md); margin-bottom: 8px; }}
        .sidebar-name {{ font-weight: 700; font-size: 1rem; color: var(--dark); margin-bottom: 2px; }}
        .sidebar-domain {{ color: var(--primary); font-weight: 600; font-size: 0.78rem; margin-bottom: 10px; }}
        .sidebar-info {{ text-align: left; }}
        .sidebar-info-item {{
            display: flex; align-items: center; gap: 8px; padding: 6px 0;
            border-bottom: 1px solid var(--light-2); font-size: 0.75rem; color: var(--secondary);
        }}
        .sidebar-info-item:last-child {{ border-bottom: none; }}
        .sidebar-info-item i {{ width: 16px; color: var(--primary); text-align: center; font-size: 0.75rem; }}
        
        /* ============ CONTACT ============ */
        .contact-bar {{
            background: var(--gradient-2); border-radius: var(--radius-lg); padding: 28px;
            text-align: center; color: white; margin-top: 20px;
        }}
        .contact-bar h2 {{ font-family: 'Playfair Display', serif; font-size: 1.5rem; margin-bottom: 4px; }}
        .contact-bar p {{ opacity: 0.8; font-size: 0.85rem; margin-bottom: 16px; }}
        .contact-btns {{ display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }}
        .contact-btn {{
            display: inline-flex; align-items: center; gap: 6px; padding: 10px 20px;
            border-radius: 50px; font-weight: 600; text-decoration: none; transition: all 0.3s; font-size: 0.82rem;
        }}
        .contact-btn-email {{ background: white; color: var(--dark); }}
        .contact-btn-email:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,.2); color: var(--dark); }}
        .contact-btn-phone {{ background: rgba(255,255,255,.15); color: white; border: 1px solid rgba(255,255,255,.25); }}
        .contact-btn-phone:hover {{ background: rgba(255,255,255,.25); transform: translateY(-2px); color: white; }}
        
        /* ============ SOCIAL ============ */
        .social-links {{ display: flex; justify-content: center; gap: 8px; margin-top: 10px; }}
        .social-link {{ width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; color: white; font-size: 0.85rem; transition: all 0.3s; text-decoration: none; }}
        .social-link:hover {{ transform: translateY(-3px); color: white; }}
        .social-link.linkedin {{ background: #0077b5; }}
        .social-link.github {{ background: #333; }}
        .social-link.website {{ background: var(--success); }}
        
        /* ============ FOOTER ============ */
        .footer {{ text-align: center; padding: 20px; color: var(--secondary); font-size: 0.72rem; border-top: 1px solid #e2e8f0; margin-top: 16px; }}
        
        /* ============ RESPONSIVE ============ */
        @media (max-width: 1024px) {{
            .main-container {{ grid-template-columns: 1fr; }}
        }}
        @media (max-width: 640px) {{
            .hero-container {{ flex-direction: column-reverse; text-align: center; gap: 20px; }}
            .hero-name {{ font-size: 2rem; }}
            .hero-photo {{ width: 140px; height: 140px; }}
            .hero-meta {{ justify-content: center; }}
            .edu-grid, .proj-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <nav class="navbar" id="navbar">
        <div class="nav-container">
            <a href="#" class="nav-brand">
                <span class="nav-brand-icon"><i class="fas fa-database"></i></span>
                Professionals Data Bank
            </a>
            <div class="nav-links">
                <a href="#about" class="nav-link">About</a>
                <a href="#skills" class="nav-link">Skills</a>
                <a href="#experience" class="nav-link">Experience</a>
                <a href="#education" class="nav-link">Education</a>
                <a href="#projects" class="nav-link">Projects</a>
                <a href="#contact" class="nav-link">Contact</a>
            </div>
        </div>
    </nav>
    
    <section class="hero">
        <div class="hero-container">
            <div class="hero-content">
                <div class="hero-badge"><i class="fas fa-check-circle"></i> Verified Professional</div>
                <h1 class="hero-name">{full_name}</h1>
                <p class="hero-title-text">{domain}</p>
                {summary_html}
                <div class="hero-meta">
                    {hero_meta_items}
                </div>
            </div>
            <div class="hero-photo-wrapper">
                <div class="hero-photo-ring"></div>
                <div class="hero-photo">
                    <img src="{photo_url}" alt="{full_name}" onerror="this.src='../static/uploads/profile_photos/avatar.png'">
                </div>
            </div>
        </div>
    </section>
    
    <div class="main-grid" style="max-width:1200px;margin:0 auto;padding:0 24px;display:grid;grid-template-columns:1fr 300px;gap:20px;margin-top:-20px;position:relative;z-index:10;">
        <div>
            {sections_html}
        </div>
        <div>
            <div class="sidebar-card">
                <img src="{photo_url}" alt="{full_name}" class="sidebar-avatar" onerror="this.src='../static/uploads/profile_photos/avatar.png'">
                <h3 class="sidebar-name">{full_name}</h3>
                <p class="sidebar-domain">{domain}</p>
                <div class="sidebar-info">
                    {sidebar_info}
                </div>
            </div>
            
            <div class="sidebar-card">
                <h6 style="font-weight:700;margin-bottom:10px;color:var(--dark);"><i class="fas fa-chart-pie me-2" style="color:var(--primary);"></i>Quick Stats</h6>
                <div class="sidebar-info">
                    <div class="sidebar-info-item"><i class="fas fa-tools"></i> <strong>{skills_count}</strong> Skills</div>
                    <div class="sidebar-info-item"><i class="fas fa-briefcase"></i> <strong>{exp_count}</strong> Experiences</div>
                    <div class="sidebar-info-item"><i class="fas fa-graduation-cap"></i> <strong>{edu_count}</strong> Education</div>
                    <div class="sidebar-info-item"><i class="fas fa-project-diagram"></i> <strong>{proj_count}</strong> Projects</div>
                    <div class="sidebar-info-item"><i class="fas fa-certificate"></i> <strong>{cert_count}</strong> Certs</div>
                </div>
            </div>
            {sidebar_social}
        </div>
    </div>
    
    <div style="max-width:1200px;margin:0 auto;padding:0 24px;">
        <div class="contact-bar" id="contact">
            <h2>Get In Touch</h2>
            <p>Interested in collaborating? Reach out!</p>
            <div class="contact-btns">
                <a href="{email_link}" class="contact-btn contact-btn-email"><i class="fas fa-envelope"></i> {email_display}</a>
                <a href="{mobile_link}" class="contact-btn contact-btn-phone"><i class="fas fa-phone"></i> {mobile_display}</a>
            </div>
            {contact_social}
        </div>
    </div>
    
    <footer class="footer">
        <p>&copy; {current_year} {full_name} | Powered by <strong>Professionals Data Bank</strong></p>
    </footer>
    
    <script>
        window.addEventListener('scroll', function() {{
            document.getElementById('navbar').classList.toggle('scrolled', window.scrollY > 50);
        }});
        document.querySelectorAll('a[href^="#"]').forEach(function(link) {{
            link.addEventListener('click', function(e) {{
                e.preventDefault();
                var target = document.querySelector(this.getAttribute('href'));
                if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }});
        }});
    </script>
</body>
</html>'''
    
    # ⭐ Format the template with actual values
    summary_html = f'<p class="hero-summary">{user.summary[:200]}...</p>' if user.summary else ''
    
    return html.format(
        full_name=user.full_name or 'Professional',
        domain=user.domain or 'General',
        photo_url=photo_url,
        email_display=email_display,
        email_link=email_link,
        mobile_display=mobile_display,
        mobile_link=mobile_link,
        summary_html=summary_html,
        hero_meta_items=hero_meta_items,
        sections_html=sections_html,
        sidebar_info=sidebar_info,
        sidebar_social=sidebar_social,
        contact_social=contact_social,
        skills_count=len(skills),
        exp_count=len(experience),
        edu_count=len(education),
        proj_count=len(projects),
        cert_count=len(certifications),
        current_year=current_year,
    )


# ============================================================
# SECTION BUILDERS
# ============================================================

def build_about_section(user):
    if not user.summary:
        return ''
    return f'''
    <div class="section-card" id="about">
        <h2 class="section-title"><i class="fas fa-user"></i> About Me</h2>
        <p style="font-size:0.88rem;color:var(--secondary);line-height:1.7;">{user.summary}</p>
    </div>'''


def build_skills_section(skills):
    if not skills:
        return ''
    expert = skills[:3]
    advanced = skills[3:6] if len(skills) > 3 else []
    rest = skills[6:] if len(skills) > 6 else []
    
    html = ''.join([f'<span class="skill-item skill-level-expert"><i class="fas fa-star"></i> {s}</span>' for s in expert])
    html += ''.join([f'<span class="skill-item skill-level-advanced"><i class="fas fa-check-circle"></i> {s}</span>' for s in advanced])
    html += ''.join([f'<span class="skill-item">{s}</span>' for s in rest])
    
    return f'''
    <div class="section-card" id="skills">
        <h2 class="section-title"><i class="fas fa-cogs"></i> Skills & Expertise</h2>
        <div class="skills-container">{html}</div>
        <div style="margin-top:8px;display:flex;gap:12px;font-size:0.68rem;color:var(--secondary);">
            <span><span class="skill-item skill-level-expert" style="font-size:0.65rem;padding:2px 8px;"><i class="fas fa-star"></i></span> Expert</span>
            <span><span class="skill-item skill-level-advanced" style="font-size:0.65rem;padding:2px 8px;"><i class="fas fa-check-circle"></i></span> Advanced</span>
        </div>
    </div>'''


def build_experience_section(experience):
    if not experience:
        return ''
    html = ''
    for exp in experience:
        is_current = 'present' in exp.get('duration', '').lower()
        html += f'''
        <div class="exp-card{' current' if is_current else ''}">
            <div class="exp-card-header">
                <div>
                    <div class="exp-title">{exp.get('title', '')}</div>
                    <div class="exp-company">{exp.get('company', '')}</div>
                </div>
                <span class="exp-duration{' current-dur' if is_current else ''}">{exp.get('duration', '')}</span>
            </div>
            {f'<p class="exp-desc">{exp.get("description", "")}</p>' if exp.get('description') else ''}
        </div>'''
    
    return f'''
    <div class="section-card" id="experience">
        <h2 class="section-title"><i class="fas fa-briefcase"></i> Work Experience</h2>
        <div class="exp-list">{html}</div>
    </div>'''


def build_education_section(education):
    if not education:
        return ''
    html = ''
    for edu in education:
        html += f'''
        <div class="edu-card">
            <div class="edu-degree">{edu.get('degree', '')}</div>
            <div class="edu-inst">{edu.get('institution', '')}</div>
            <span class="edu-year">{edu.get('year', '')}</span>
        </div>'''
    
    return f'''
    <div class="section-card" id="education">
        <h2 class="section-title"><i class="fas fa-graduation-cap"></i> Education</h2>
        <div class="edu-grid">{html}</div>
    </div>'''


def build_projects_section(projects):
    if not projects:
        return ''
    html = ''
    for proj in projects:
        tech_tags = ''
        if proj.get('technologies'):
            for tech in proj['technologies'].split(',')[:4]:
                tech_tags += f'<span class="proj-tech-tag">{tech.strip()}</span>'
        
        html += f'''
        <div class="proj-card">
            <div class="proj-name"><i class="fas fa-code me-1" style="color:var(--primary);"></i> {proj.get('name', '')}</div>
            <p class="proj-desc">{proj.get('description', '')}</p>
            {f'<div class="proj-tech">{tech_tags}</div>' if tech_tags else ''}
        </div>'''
    
    return f'''
    <div class="section-card" id="projects">
        <h2 class="section-title"><i class="fas fa-project-diagram"></i> Projects</h2>
        <div class="proj-grid">{html}</div>
    </div>'''


def build_certifications_section(certifications):
    if not certifications:
        return ''
    html = ''.join([f'<span class="cert-tag"><i class="fas fa-certificate"></i> {c}</span>' for c in certifications])
    
    return f'''
    <div class="section-card" id="certifications">
        <h2 class="section-title"><i class="fas fa-certificate"></i> Certifications</h2>
        <div class="cert-list">{html}</div>
    </div>'''


def build_languages_section(languages):
    if not languages:
        return ''
    html = ''.join([f'<span class="lang-tag"><i class="fas fa-language me-1"></i> {l}</span>' for l in languages])
    
    return f'''
    <div class="section-card" id="languages">
        <h2 class="section-title"><i class="fas fa-language"></i> Languages</h2>
        <div class="lang-list">{html}</div>
    </div>'''


def build_achievements_section(achievements):
    if not achievements:
        return ''
    html = ''.join([f'<div class="ach-item"><i class="fas fa-trophy"></i> <span>{a}</span></div>' for a in achievements])
    
    return f'''
    <div class="section-card" id="achievements">
        <h2 class="section-title"><i class="fas fa-trophy"></i> Achievements & Awards</h2>
        <div class="ach-list">{html}</div>
    </div>'''


def build_social_links(user):
    """Build social links HTML"""
    links = ''
    if user.linkedin:
        links += f'<a href="{user.linkedin}" target="_blank" class="social-link linkedin" title="LinkedIn"><i class="fab fa-linkedin-in"></i></a>'
    if user.github:
        links += f'<a href="{user.github}" target="_blank" class="social-link github" title="GitHub"><i class="fab fa-github"></i></a>'
    if user.portfolio:
        links += f'<a href="{user.portfolio}" target="_blank" class="social-link website" title="Website"><i class="fas fa-globe"></i></a>'
    return links