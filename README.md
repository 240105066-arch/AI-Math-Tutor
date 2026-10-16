# AI Math Tutor 📐

AI Math Tutor is an interactive AI-powered geometry learning application designed for students in Grades 5–9.

The application supports differentiated learning through three difficulty levels: Basic, Standard, and Advanced.

## Features

### 📘 Formulas
Explore geometry formulas with interactive diagrams and adjustable measurements.

### 📝 Practice
Solve 45 prepared geometry problems across three difficulty levels, with hints and step-by-step solutions.

### 🤖 AI Generator
Generate new geometry problems using Google Gemini AI. Select a topic and difficulty level to receive adapted problems, hints, explanations, and geometric diagrams.

## Differentiated Learning

- **Basic:** Simple problems with direct formulas and guided explanations.
- **Standard:** Intermediate problems requiring mathematical reasoning and formula application.
- **Advanced:** Complex, multi-step problems and real-world applications.

## Technologies

- Python
- Streamlit
- Google Gemini API
- HTML, CSS, SVG

## How to Use

1. Open the web application.
2. Select Formulas, Practice, or AI Generator.
3. Choose your preferred difficulty level.
4. Solve problems and use hints or solutions when needed.

## Live Website

https://ai-math-tutor-6xsjffbkgjv5dbpwwlmf7m.streamlit.app/

## Run Locally

Install dependencies:

`pip install -r requirements.txt`

Create `.streamlit/secrets.toml` and add your own Gemini API key:

`GEMINI_API_KEY = "YOUR_API_KEY"`

Start the application:

`python -m streamlit run app.py`

## Educational Purpose

This project demonstrates how artificial intelligence and interactive multimedia can support differentiated mathematics education through adaptive tasks, visual learning, and personalized explanations.
