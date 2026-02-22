from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# 1. NEW: Profile Model to store body stats
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(default=25)
    height = models.FloatField(default=170.0, help_text="in cm")
    weight = models.FloatField(default=70.0, help_text="in kg")
    
    def get_bmi(self):
        # BMI = kg / m^2
        height_m = self.height / 100
        if height_m <= 0: return 0
        bmi = self.weight / (height_m ** 2)
        return round(bmi, 1)
    
    def get_bmi_status(self):
        bmi = self.get_bmi()
        if bmi < 18.5: return "Underweight"
        if 18.5 <= bmi < 24.9: return "Normal"
        if 25 <= bmi < 29.9: return "Overweight"
        return "Obese"
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to auto-create Profile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

# 2. UPDATED: HealthLog to use BMI
class HealthLog(models.Model):
    LOG_TYPES = (
        ('EXERCISE', 'Physical Exercise'),
        ('FOOD', 'Food Intake'),
    )
    
    EXERCISE_CHOICES = (
        ('Running', 'Jogging / Running'),
        ('Gym', 'Gym / Weights'),
        ('Sport', 'Sports (Football, Tennis, etc)'),
        ('Yoga', 'Yoga'),
        ('None', 'None'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    
    # Common Fields
    sleep_hours = models.FloatField(default=0.0)
    water_intake = models.FloatField(default=0.0)
    
    # Exercise
    exercise_type = models.CharField(max_length=50, choices=EXERCISE_CHOICES, default='None', blank=True)
    calories_burned = models.IntegerField(default=0)
    
    # Food
    calories_intake = models.IntegerField(default=0)
    protein = models.FloatField(default=0.0, help_text="Grams")
    carbs = models.FloatField(default=0.0, help_text="Grams")
    fats = models.FloatField(default=0.0, help_text="Grams")

    # Results
    health_score = models.IntegerField(default=0)
    suggestion = models.TextField(blank=True, null=True)

    def calculate_metrics(self):
        score = 50 # Base Score
        tips = []

        # --- NEW LOGIC: BMI Impact ---
        # We try to get the profile. If it fails (rare), assume normal.
        try:
            bmi_status = self.user.userprofile.get_bmi_status()
        except:
            bmi_status = "Normal"

        # Sleep Logic
        if 7 <= self.sleep_hours <= 9:
            score += 20
        elif self.sleep_hours < 5:
            score -= 10
            tips.append("Your sleep is very low. Prioritize rest.")
        
        # Water Logic
        if self.water_intake >= 8:
            score += 15
        else:
            tips.append("Drink more water (Target: 8 glasses).")

        # Exercise Logic (Adjusted by BMI)
        if self.log_type == 'EXERCISE':
            if self.calories_burned > 1200:
                score += 15
                tips.append("Great workout!")
            
            # Bonus points for working out if Overweight/Obese
            if bmi_status in ["Overweight", "Obese"] and self.calories_burned > 1300:
                score += 10
                tips.append("Excellent effort towards weight management!")
        
        # Diet Logic (Adjusted by BMI)
        if self.log_type == 'FOOD':
            if self.protein > 70:
                score += 10
            
            # Penalty for high calories if Overweight
            if bmi_status in ["Overweight", "Obese"] and self.calories_intake > 2200:
                score -= 10
                tips.append(f"Calorie intake is high for your BMI status ({bmi_status}).")
            elif bmi_status == "Underweight" and self.calories_intake < 1500:
                score -= 10
                tips.append("You need more calories to reach a healthy weight.")

        self.health_score = min(100, max(0, score))
        self.suggestion = " ".join(tips) if tips else "Good routine. Keep it up!"

    def save(self, *args, **kwargs):
        self.calculate_metrics()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.date}"