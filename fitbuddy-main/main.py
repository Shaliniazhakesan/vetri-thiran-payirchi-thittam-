import os
import json

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

load_dotenv()

app = FastAPI(title="FitBuddy - AI Fitness Plan Generator")

templates = Jinja2Templates(directory="templates")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()


def demo_plan(name, goal, intensity):

    plans = {
        "weight loss": [
            ("Day 1", "Cardio and mobility", "25-30 min comfortable walking and 5-10 min mobility"),
            ("Day 2", "Full body movement", "Bodyweight squats, wall push-ups and light core work"),
            ("Day 3", "Active recovery", "Easy walking, stretching and mobility"),
            ("Day 4", "Cardio and strength", "Moderate walking or cycling with simple bodyweight exercises"),
            ("Day 5", "Full body movement", "Light strength circuit with comfortable repetitions"),
            ("Day 6", "Fun activity", "Choose a safe activity you enjoy"),
            ("Day 7", "Recovery", "Gentle stretching and relaxed movement")
        ],
        "muscle gain": [
            ("Day 1", "Full body strength", "Squats, push-ups, rows and core exercises"),
            ("Day 2", "Recovery", "Walking and gentle mobility"),
            ("Day 3", "Upper body strength", "Push, pull and shoulder-focused movements"),
            ("Day 4", "Lower body strength", "Squat, hinge and calf-focused movements"),
            ("Day 5", "Recovery", "Light walking and stretching"),
            ("Day 6", "Full body strength", "Balanced full-body resistance session"),
            ("Day 7", "Recovery", "Gentle mobility and rest")
        ],
        "general wellness": [
            ("Day 1", "Cardio", "Comfortable walking or cycling"),
            ("Day 2", "Strength", "Simple full-body bodyweight exercises"),
            ("Day 3", "Mobility", "Stretching and mobility session"),
            ("Day 4", "Cardio", "Moderate walking, cycling or another enjoyable activity"),
            ("Day 5", "Strength", "Simple full-body strength session"),
            ("Day 6", "Outdoor activity", "Choose an enjoyable active hobby"),
            ("Day 7", "Recovery", "Gentle movement and relaxation")
        ]
    }

    selected = plans.get(goal.lower(), plans["general wellness"])

    return {
        "name": name,
        "goal": goal,
        "intensity": intensity,
        "days": [
            {
                "day": day,
                "focus": focus,
                "activity": activity
            }
            for day, focus, activity in selected
        ],
        "tip": "Focus on balanced meals, regular hydration and enough recovery. Increase activity gradually."
    }


def generate_plan(name, goal, intensity, feedback=""):

    if not GEMINI_API_KEY:
        return demo_plan(name, goal, intensity)

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
You are FitBuddy, a general wellness planning assistant.

Create a safe beginner-friendly 7-day activity plan.

User name: {name}
Goal: {goal}
Preferred intensity: {intensity}
Feedback: {feedback or "None"}

Return ONLY valid JSON:

{{
  "name": "{name}",
  "goal": "{goal}",
  "intensity": "{intensity}",
  "days": [
    {{
      "day": "Day 1",
      "focus": "short focus",
      "activity": "short activity description"
    }}
  ],
  "tip": "one concise nutrition or recovery tip"
}}

Avoid extreme exercise, unsafe dieting, starvation or medical treatment.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = response.text.strip()

        if text.startswith("`"):
            text = text.replace("`json", "")
            text = text.replace("`", "")
            text = text.strip()

        return json.loads(text)

    except Exception:
        return demo_plan(name, goal, intensity)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "plan": None,
            "message": None
        }
    )


@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    name: str = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    feedback: str = Form("")
):

    plan = generate_plan(name, goal, intensity, feedback)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "plan": plan,
            "message": "Your FitBuddy plan is ready!"
        }
    )


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "application": "FitBuddy",
        "gemini_configured": bool(GEMINI_API_KEY)
    }
