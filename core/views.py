from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.db.models import Avg
from .models import HealthLog
from .forms import CustomUserCreationForm, CustomLoginForm, HealthLogForm, UserUpdateForm, ProfileUpdateForm
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import get_template
from groq import Groq 

# --- CONFIGURATION ---
# PASTE YOUR GROQ KEY HERE
GROQ_API_KEY = "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"


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) # Use custom form
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST) # Use custom form
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomLoginForm()
    return render(request, 'core/login.html', {'form': form})
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    logs = HealthLog.objects.filter(user=request.user).order_by('-date')
    
    # 1. Calculate Average Sleep
    avg_sleep = logs.aggregate(Avg('sleep_hours'))['sleep_hours__avg'] or 0
    
    # 2. NEW: Calculate Average Health Score
    avg_health_score = logs.aggregate(Avg('health_score'))['health_score__avg'] or 0
    
    total_workouts = logs.filter(log_type='EXERCISE').count()
    latest_log = logs.first()
    
    user_name = request.user.first_name if request.user.first_name else request.user.email

    context = {
        'logs': logs[:5],
        'avg_sleep': round(avg_sleep, 1),
        'avg_health_score': int(avg_health_score), # Convert to integer for clean look
        'total_workouts': total_workouts,
        'latest_suggestion': latest_log.suggestion if latest_log else "Log data to get tips!",
        'user_name': user_name
    }
    return render(request, 'core/dashboard.html', context)
# ... existing imports ...

@login_required
def edit_log(request, log_id):
    # Get the specific log belonging to the user
    log = get_object_or_404(HealthLog, id=log_id, user=request.user)
    
    if request.method == 'POST':
        # Create form with POST data AND the existing log instance
        form = HealthLogForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        # Pre-fill form with existing data
        form = HealthLogForm(instance=log)
    
    # Reuse the add_log template but with a special 'is_edit' flag
    return render(request, 'core/add_log.html', {
        'form': form, 
        'is_edit': True
    })

@login_required
def delete_log(request, log_id):
    log = get_object_or_404(HealthLog, id=log_id, user=request.user)
    if request.method == 'POST':
        log.delete()
    return redirect('dashboard')

@login_required
def add_log(request):
    show_modal = False
    log_result = None
    
    if request.method == 'POST':
        form = HealthLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.save()
            
            # TRIGGER THE MODAL instead of redirecting
            show_modal = True
            log_result = log
            
            # Reset form for next entry
            form = HealthLogForm()
    else:
        form = HealthLogForm()
    
    return render(request, 'core/add_log.html', {
        'form': form, 
        'show_modal': show_modal, 
        'result': log_result
    })

@login_required
def tips_view(request):
    # Static list of tips to display
    tips = [
        {'icon': 'droplets', 'color': 'blue', 'title': 'Hydration First', 'desc': 'Drinking 8 glasses of water maintains energy and brain function.'},
        {'icon': 'moon', 'color': 'indigo', 'title': 'Quality Sleep', 'desc': '7-9 hours of sleep is crucial for muscle repair and memory consolidation.'},
        {'icon': 'utensils', 'color': 'green', 'title': 'Protein Power', 'desc': 'Include protein in every meal to maintain muscle mass and satiety.'},
        {'icon': 'heart-pulse', 'color': 'red', 'title': 'Cardio Health', 'desc': '150 mins of moderate aerobic activity a week strengthens your heart.'},
        {'icon': 'sun', 'color': 'orange', 'title': 'Vitamin D', 'desc': 'Get 15 mins of morning sunlight to boost mood and bone health.'},
        {'icon': 'brain', 'color': 'pink', 'title': 'Mental Check', 'desc': '5 mins of meditation daily reduces cortisol (stress) levels.'},
        {'icon': 'dumbbell', 'color': 'purple', 'title': 'Strength Training', 'desc': 'Lift weights 2x a week to improve bone density and metabolism.'},
        {'icon': 'apple', 'color': 'red', 'title': 'Limit Sugar', 'desc': 'Reducing processed sugar lowers risk of diabetes and fatigue.'},
        {'icon': 'footprints', 'color': 'teal', 'title': 'Keep Moving', 'desc': 'Aim for 10,000 steps a day to keep your metabolism active.'},
        {'icon': 'carrot', 'color': 'orange', 'title': 'Fiber Intake', 'desc': 'Vegetables and whole grains improve digestion and gut health.'},
        {'icon': 'smile', 'color': 'yellow', 'title': 'Social Connection', 'desc': 'Strong relationships boost longevity and mental well-being.'},
        {'icon': 'smartphone-off', 'color': 'gray', 'title': 'Digital Detox', 'desc': 'Avoid screens 1 hour before bed for better sleep quality.'},
    ]
    return render(request, 'core/tips.html', {'tips': tips})

@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=request.user.userprofile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.userprofile)
    
    # Calculate BMI for display
    profile = request.user.userprofile
    bmi = profile.get_bmi()
    bmi_status = profile.get_bmi_status()
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'bmi': bmi,
        'bmi_status': bmi_status
    }
    return render(request, 'core/profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: Update session so user isn't logged out after password change
            update_session_auth_hash(request, user) 
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
        # Apply styles manually to this built-in form
        for field in form.fields.values():
             field.widget.attrs['class'] = 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:border-teal-500 focus:ring-2 focus:ring-teal-200 outline-none transition-all'

    return render(request, 'core/change_password.html', {'form': form})

@login_required
def download_pdf(request):
    logs = HealthLog.objects.filter(user=request.user).order_by('-date')
    template_path = 'core/pdf_report.html'
    context = {'logs': logs, 'user': request.user}
    
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    # If you want to download immediately:
    response['Content-Disposition'] = 'attachment; filename="health_report.pdf"'
    
    # Find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # Create the PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def ai_analysis_view(request):
    logs = HealthLog.objects.filter(user=request.user).order_by('-date')[:7]
    profile = request.user.userprofile # Get Profile Data
    
    if not logs:
        return render(request, 'core/ai_analysis.html', {'error': "Not enough data!"})

    data_summary = ""
    for log in logs:
        data_summary += f"- Date: {log.date}, Type: {log.log_type}, Score: {log.health_score}, Sleep: {log.sleep_hours}h, Water: {log.water_intake}gls\n"

    # NEW: Add Profile Context to Prompt
    prompt = f"""
    Act as a professional Health Coach.
    USER PROFILE:
    - Name: {request.user.first_name}
    - Age: {profile.age}
    - Weight: {profile.weight}kg, Height: {profile.height}cm
    - BMI: {profile.get_bmi()} ({profile.get_bmi_status()})

    RECENT LOGS:
    {data_summary}
    
    Based on their BMI status ({profile.get_bmi_status()}) and logs, provide:
    1. A summary of their week.
    2. Three actionable improvements specific to their body type.
    3. Use a motivating tone.
    Format with HTML tags.
    """

    # ... Call Groq AI (Keep your existing code here) ...
    # (Just pasting the try/except block for brevity)
    try:
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", 
        )
        ai_response = chat_completion.choices[0].message.content
    except Exception as e:
        ai_response = f"Error: {e}"

    return render(request, 'core/ai_analysis.html', {'ai_response': ai_response})