import google.generativeai as genai

# Paste your actual key here again
GENAI_API_KEY = 'AIzaSyDyqejQ8FJ6urV9vrBBLEsexw_pe-Nprg0' 

genai.configure(api_key=GENAI_API_KEY)

print("1. contacting Google AI...")
try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Hello, are you working?")
    print("2. SUCCESS! AI replied:")
    print(response.text)
except Exception as e:
    print("\nXXX FAILURE XXX")
    print("The exact error is:")
    print(e)