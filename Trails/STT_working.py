import speech_recognition as sr

# Initialize recognizer
r = sr.Recognizer()

# Use the microphone as the source for input
with sr.Microphone() as source:
    print("Say something:")
    audio = r.listen(source)

    try:
        # Use Google's speech recognition
        text = r.recognize_google(audio)
        print(f"You said: {text}")
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
