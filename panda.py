import os
import pyttsx3
import speech_recognition as sr
import sounddevice as sd
import numpy as np
import webbrowser
import requests
from datetime import datetime
import pygame
import tkinter as tk
from tkinter import scrolledtext, Frame, messagebox
from PIL import Image, ImageTk
import time
import pymysql as sql
import hashlib
import random

pygame.mixer.init()

NEWS_API_KEY = '24d46fa8a64d4769a65b19b9b0eb1ee6'
CRICKET_API_KEY = '87f3008e-3b53-434d-a94f-eba20d31a986'

recognizer = sr.Recognizer()
plans = []

con = sql.connect(host="localhost", user="root", password="root", database="PANDA_AI")

current_user_id = None
root = tk.Tk()

def show_about_me():
    about_text = (
        "About Me:\n"
        "I am VerBot, your voice assistant designed to help you with various tasks. "
        #"I can assist you with managing your plans, fetching the latest news, "
        #"providing cricket scores, and much more! Feel free to explore my features."
    )
    messagebox.showinfo("About Me", about_text)


def register_user(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c = con.cursor()
    try:
        c.execute('INSERT INTO User (Username, Password) VALUES (%s, %s)', (username, hashed_password))
        con.commit()
        display_text.insert(tk.END, "User registered successfully.\n")
    except sql.IntegrityError:
        display_text.insert(tk.END, "Username already exists. Please choose another.\n")
    finally:
        c.close()


def login_user(username, password):
    global current_user_id
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c = con.cursor()
    c.execute('SELECT UserID FROM User WHERE Username = %s AND Password = %s', (username, hashed_password))
    user = c.fetchone()
    c.close()
    if user:
        current_user_id = user[0]  # Store the UserID
        display_text.insert(tk.END, f"Welcome back, {username}!\n")
        return user
    else:
        display_text.insert(tk.END, "Invalid credentials. Please try again.\n")
        return None


def open_registration_window():
    reg_window = tk.Toplevel(root)
    reg_window.title("Register")
    reg_window.iconbitmap(r"C:\Tushar\Coding nd Stuff\Minor Project\Chatbot\account.ico")

    tk.Label(reg_window, text="Username:").grid(row=0, column=0)
    tk.Label(reg_window, text="Password:").grid(row=1, column=0)

    username_entry = tk.Entry(reg_window)
    password_entry = tk.Entry(reg_window, show="*")
    username_entry.grid(row=0, column=1)
    password_entry.grid(row=1, column=1)

    def register():
        username = username_entry.get()
        password = password_entry.get()
        register_user(username, password)

    tk.Button(reg_window, text="Register", command=register).grid(row=2, columnspan=2)


def open_login_window():
    login_window = tk.Toplevel(root)
    login_window.title("Login")
    login_window.iconbitmap(r"C:\Tushar\Coding nd Stuff\Minor Project\Chatbot\account.ico")

    tk.Label(login_window, text="Username:").grid(row=0, column=0)
    tk.Label(login_window, text="Password:").grid(row=1, column=0)

    username_entry = tk.Entry(login_window)
    password_entry = tk.Entry(login_window, show="*")
    username_entry.grid(row=0, column=1)
    password_entry.grid(row=1, column=1)

    def login():
        username = username_entry.get()
        password = password_entry.get()
        login_user(username, password)

    tk.Button(login_window, text="Login", command=login).grid(row=2, columnspan=2)


def add_plan(plan):
    if current_user_id is not None:
        plans.append(plan)
        display_text.insert(tk.END, f"Plan added: {plan}\n")
        say(f"Plan added: {plan}")
        c = con.cursor()
        c.execute('INSERT INTO plans (plan_name, UserID) VALUES (%s, %s)', (plan, current_user_id))
        con.commit()
        c.close()
    else:
        display_text.insert(tk.END, "Please log in to add plans.\n")
        say("You need to log in first.")


def delete_plan(plan):
    if current_user_id is not None:
        if plan in plans:
            plans.remove(plan)
            display_text.insert(tk.END, f"Plan deleted: {plan}\n")
            say(f"Plan deleted: {plan}")
            c = con.cursor()
            c.execute('DELETE FROM plans WHERE plan_name = %s AND UserID = %s', (plan, current_user_id))
            con.commit()
            if c.rowcount == 0:
                display_text.insert(tk.END, f"Plan not found or does not belong to you: {plan}\n")
                say(f"Plan not found or does not belong to you: {plan}")
            c.close()
        else:
            display_text.insert(tk.END, f"Plan not found: {plan}\n")
            say(f"Plan not found: {plan}")
    else:
        display_text.insert(tk.END, "Please log in to delete plans.\n")
        say("You need to log in first.")


def view_plans():
    if current_user_id is not None:
        c = con.cursor()
        c.execute('SELECT plan_name FROM plans WHERE UserID = %s', (current_user_id,))
        rows = c.fetchall()
        all_plans = [row[0] for row in rows]
        c.close()

        if all_plans:
            display_text.insert(tk.END, f"Current Plans:\n" + "\n".join(all_plans) + "\n")
            say("Here are your current plans: " + ", ".join(all_plans))
        else:
            display_text.insert(tk.END, "No plans available for you.\n")
            say("You have no plans.")
    else:
        display_text.insert(tk.END, "Please log in to view your plans.\n")
        say("You need to log in first.")


def say(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def record_audio():
    duration = 5
    fs = 44100
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float64')
    sd.wait()
    return np.int16(audio_data * 32767).tobytes()


def stop_music():
    pygame.mixer.music.stop()
    display_text.insert(tk.END, "Music stopped.\n")
    say("Music stopped.")


def recognize_audio():
    try:
        audio_bytes = record_audio()
        audio = sr.AudioData(audio_bytes, 44100, 2)
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        return None


def get_current_time():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    return current_time


def fetch_latest_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        news_data = response.json()

        if news_data['status'] == 'ok':
            articles = news_data['articles'][:5]
            headlines = [f"{i + 1}. {article['title']}" for i, article in enumerate(articles)]
            return "\n".join(headlines)
        else:
            return "Failed to fetch news."
    except Exception as e:
        return "Sorry, I couldn't fetch the news right now."


def fetch_cricket_score():
    try:
        url = f"https://api.cricapi.com/v1/currentMatches?apikey={CRICKET_API_KEY}"
        response = requests.get(url)
        cricket_data = response.json()

        if cricket_data['status'] == 'success':
            match = cricket_data['data'][0]
            team1 = match['teamInfo'][0]['name']
            team2 = match['teamInfo'][1]['name']
            score1 = match['score'][0]['r'] if match['score'] else 'N/A'
            score2 = match['score'][1]['r'] if len(match['score']) > 1 else 'N/A'
            return f"{team1}: {score1}, {team2}: {score2}"
        else:
            return "Failed to fetch cricket scores."
    except Exception as e:
        return "Sorry, I couldn't fetch the cricket scores right now."


stopwatch_running = False
stopwatch_start_time = None
elapsed_time = 0


def start_stopwatch():
    global stopwatch_running, stopwatch_start_time
    if not stopwatch_running:
        stopwatch_running = True
        stopwatch_start_time = time.time()
        display_text.insert(tk.END, "Stopwatch started.\n")
        update_stopwatch()
    else:
        display_text.insert(tk.END, "Stopwatch is already running.\n")


def stop_stopwatch():
    global stopwatch_running
    if stopwatch_running:
        stopwatch_running = False
        display_text.insert(tk.END, "Stopwatch stopped.\n")
        stopwatch_label.pack_forget()
    else:
        display_text.insert(tk.END, "Stopwatch is not running.\n")


def reset_stopwatch():
    global stopwatch_running, stopwatch_start_time, elapsed_time
    stopwatch_running = False
    elapsed_time = 0
    stopwatch_label.config(text=f"Elapsed time: {elapsed_time:.2f} seconds")
    display_text.insert(tk.END, "Stopwatch reset.\n")


def update_stopwatch():
    global elapsed_time
    if stopwatch_running:
        elapsed_time = time.time() - stopwatch_start_time
        stopwatch_label.config(text=f"Elapsed time: {elapsed_time:.2f} seconds")
        root.after(100, update_stopwatch)

introduction_shown = False

def introduce():
    global introduction_shown
    if introduction_shown:
        return
    greetings = ["Hello!", "Hi!", "Greetings!", "Hey!"]
    greeting = random.choice(greetings)
    current_time = get_current_time()
    introduction_text = (
        f"{greeting} I am VerBot, your voice-activated assistant. "
        #f"The current time is {current_time}. "
        #"I can help you with the following features:\n"
        #"- Play music\n"
        #"- Fetch the latest news\n"
        #"- Start a stopwatch\n"
        #"- Open Google, Instagram, or YouTube\n"
        #"- Get the latest cricket scores\n"
        #"- Manage your plans\n"
        #"- Show the current time\n"
        "How can I assist you today?"
    )
    display_text.insert(tk.END, introduction_text + "\n")
    root.update()
    time.sleep(2)
    say(introduction_text)
    introduction_shown = True

def toggle_fullscreen(event=None):
    root.attributes('-fullscreen', not root.attributes('-fullscreen'))


def on_enter(e):
    e.widget['bg'] = '#FFE4E1'


def on_leave(e):
    e.widget['bg'] = 'lightblue'


def toggle_dropdown():
    if dropdown_frame.winfo_viewable():
        dropdown_frame.place_forget()
    else:
        dropdown_frame.place(x=10, y=70)


def on_start_speech():
    recognized_text = recognize_audio()
    if recognized_text:
        say(recognized_text)
        display_text.insert(tk.END, f"You said: {recognized_text}\n")

        if "goodbye panda" in recognized_text.lower():
            display_text.insert(tk.END, "Goodbye! Stopping the music and exiting...\n")
            pygame.mixer.music.stop()
            root.quit()


        if "kill yourself" in recognized_text.lower():
            display_text.insert(tk.END, "Goodbye! Stopping the music and exiting...\n")
            pygame.mixer.music.stop()
            root.quit()

        if "die" in recognized_text.lower():
            display_text.insert(tk.END, "Goodbye! Stopping the music and exiting...\n")
            pygame.mixer.music.stop()
            root.quit()

        if "mar ja" in recognized_text.lower():
            display_text.insert(tk.END, "Goodbye! Stopping the music and exiting...\n")
            pygame.mixer.music.stop()
            root.quit()


        if "time" in recognized_text.lower():
            current_time = get_current_time()
            display_text.insert(tk.END, f"Current time: {current_time}\n")
            say(f"The current time is {current_time}")

        if "latest news" in recognized_text.lower():
            latest_news = fetch_latest_news()
            display_text.insert(tk.END, f"Latest News:\n{latest_news}\n")
            say("Here are the top headlines.")

        if "cricket score" in recognized_text.lower():
            cricket_score = fetch_cricket_score()
            display_text.insert(tk.END, f"Cricket Score: {cricket_score}\n")
            say("Here is the latest cricket score.")

        if "music" in recognized_text.lower():
            music_path = r"C:\Tushar\Coding nd Stuff\Minor Project\Chatbot\art-of-samples-wild-helga-house-music-intro-245399.mp3"
            if os.path.exists(music_path):
                say("Playing music now.")
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play()
                display_text.insert(tk.END, "Playing music...\n")
            else:
                say("Sorry, the music file does not exist.")
                display_text.insert(tk.END, "Music file not found!\n")

        if "open google" in recognized_text.lower():
            webbrowser.open("https://www.google.com")
            display_text.insert(tk.END, "Opening Google...\n")
            say("Opening Google.")

        if "open youtube" in recognized_text.lower():
            webbrowser.open("https://www.youtube.com")
            display_text.insert(tk.END, "Opening YouTube...\n")
            say("Opening YouTube.")

        if "open instagram" in recognized_text.lower():
            webbrowser.open("https://www.instagram.com")
            display_text.insert(tk.END, "Opening Instagram...\n")
            say("Opening Instagram.")

        if "open gpt" in recognized_text.lower():
            webbrowser.open("https://chatgpt.com/")
            display_text.insert(tk.END, "Opening Chatgpt...\n")
            say("Opening Chatgpt.")

        if "start stopwatch" in recognized_text.lower():
            start_stopwatch()
            stopwatch_label.pack()

        if "stop stopwatch" in recognized_text.lower():
            stop_stopwatch()

        if "add plan" in recognized_text.lower():
            plan = recognized_text.lower().replace("add plan", "").strip()
            if plan:
                add_plan(plan)
            else:
                say("Please specify a plan to add.")

        if "delete plan" in recognized_text.lower():
            plan = recognized_text.lower().replace("delete plan", "").strip()
            if plan:
                delete_plan(plan)
            else:
                say("Please specify a plan to delete.")

        if "view plans" in recognized_text.lower():
            view_plans()

    else:
        say("Sorry, I did not catch that.")
        display_text.insert(tk.END, "Sorry, could not understand you.\n")



root.title("Panda AI")
root.attributes('-fullscreen', True)
root.bind('<Escape>', toggle_fullscreen)
root.iconbitmap(r"C:\Tushar\Coding nd Stuff\Minor Project\Chatbot\cute_panda.ico")

bg_image = Image.open(r"C:\Tushar\Coding nd Stuff\Minor Project\Chatbot\bear.jpg")
bg_image = bg_image.resize((root.winfo_screenwidth(), root.winfo_screenheight()), Image.LANCZOS)
bg_photo = ImageTk.PhotoImage(bg_image)

bg_label = tk.Label(root, image=bg_photo)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

display_text = scrolledtext.ScrolledText(root, height=10, width=55, bg='white', fg='black', font=('Arial', 14))
display_text.pack(pady=10,padx=10,expand=True)

project_info = tk.Label(root, text="Project created by Sumit Verma and Tushar Tawakley", fg='black', font=('Georgia', 15), padx=10,
                        pady=10)
project_info.pack(side=tk.BOTTOM, padx=10, pady=10)

stopwatch_label = tk.Label(root, text=f"Elapsed time: 0.00 seconds", bg='lightblue', fg='black', font=('Arial', 14))
stopwatch_label.pack(pady=10)
stopwatch_label.pack_forget()

control_frame = tk.Frame(root)
control_frame.pack(pady=20)

icon_image = Image.open(r"C:\Tushar\Coding nd Stuff\Minor Project\Chatbot\sign-in.png")
icon_image = icon_image.resize((50, 50), Image.LANCZOS)
icon = ImageTk.PhotoImage(icon_image)

main_button = tk.Button(root, image=icon, command=toggle_dropdown, borderwidth=0)
main_button.place(x=10, y=10)

dropdown_frame = Frame(root, bg='lightblue')

about_icon_image = Image.open(r"C:\Tushar\Coding nd Stuff\Minor Project\Chatbot\about-us.ico")
about_icon_image = about_icon_image.resize((50, 50), Image.LANCZOS)
about_icon = ImageTk.PhotoImage(about_icon_image)

about_button = tk.Button(root, image=about_icon, command=show_about_me, borderwidth=0)
about_button.place(x=70, y=10)

register_button = tk.Button(dropdown_frame, text="Register", command=open_registration_window,
                            fg='black', font=('tahoma', 14))
register_button.pack(pady=5)
register_button.bind("<Enter>", on_enter)
register_button.bind("<Leave>", on_leave)

login_button = tk.Button(dropdown_frame, text="Login", command=open_login_window, fg='black',
                         font=('tahoma', 14))
login_button.pack(pady=5)
login_button.bind("<Enter>", on_enter)
login_button.bind("<Leave>", on_leave)

start_icon_image = Image.open(r"C:\Tushar\Coding nd Stuff\Minor Project\Chatbot\mic.ico")
start_icon_image = start_icon_image.resize((40, 40), Image.LANCZOS)
start_icon = ImageTk.PhotoImage(start_icon_image)

start_button = tk.Button(control_frame, image=start_icon, command=on_start_speech, borderwidth=0)
start_button.grid(row=0, column=0, padx=10)

stop_icon_image = Image.open(r"C:\Tushar\Coding nd Stuff\Minor Project\Chatbot\slash.ico")
stop_icon_image = stop_icon_image.resize((50, 50), Image.LANCZOS)
stop_icon = ImageTk.PhotoImage(stop_icon_image)

stop_music_button = tk.Button(control_frame, image=stop_icon, command=stop_music, borderwidth=0)
stop_music_button.grid(row=0, column=1, padx=10)

exit_icon_image = Image.open(r"C:\Tushar\Coding nd Stuff\Minor Project\Chatbot\exit-to-app-button.ico")
exit_icon_image = exit_icon_image.resize((50, 50), Image.LANCZOS)
exit_icon = ImageTk.PhotoImage(exit_icon_image)

exit_button = tk.Button(control_frame, image=exit_icon, command=root.quit, borderwidth=0)
exit_button.grid(row=0, column=2, padx=10)

root.after(1000, introduce)

root.mainloop()
