
import streamlit as st
import os
import re
import time
from dotenv import load_dotenv
from google import genai

# =====================================
# 1. PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="AI Mock Interview Generator",
    page_icon="🎯",
    layout="centered"
)

# =====================================
# 2. LOAD CSS
# =====================================

def load_css():
    try:
        with open("style.css", "r", encoding="utf-8") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )
    except FileNotFoundError:
        st.warning("style.css file not found.")

load_css()

# =====================================
# 3. PAGE HEADER
# =====================================

st.title("🎯 AI Mock Interview Generator")

st.markdown(
    """
    <p style="text-align:center; color:#64748b;">
    Practice interviews, improve your answers and build confidence with AI.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()

# =====================================
# 4. GEMINI API CONFIGURATION
# =====================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("Gemini API key not found. Please check your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# =====================================
# 5. SESSION STATE
# =====================================

defaults = {
    "questions": [],
    "current_index": 0,
    "results": [],
    "evaluated": False,
    "role": "",
    "interview_started": False,
    "selected_model": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =====================================
# 6. GEMINI MODEL DETECTION
# =====================================

def detect_models():

    try:
        available_models = []

        for model in client.models.list():

            actions = model.supported_actions or []

            if "generateContent" in actions:
                available_models.append(model.name)

        if not available_models:
            raise Exception("No supported Gemini models found.")

        return available_models

    except Exception as e:
        raise Exception(f"Model detection failed: {e}")


# =====================================
# 7. SELECT WORKING MODEL
# =====================================

def select_model():

    models = detect_models()

    # Prefer the suggested model if available
    preferred_models = [
        "models/gemini-3.8-flash"
    ]

    ordered_models = (
        [m for m in preferred_models if m in models]
        + [m for m in models if m not in preferred_models]
    )

    for model in ordered_models:

        try:

            response = client.models.generate_content(
                model=model,
                contents="Reply with the word SUCCESS."
            )

            if response.text:
                return model

        except Exception:
            continue

    raise Exception(
        "All available Gemini models failed. "
        "Please try again later or check your API quota."
    )


# =====================================
# 8. COMMON AI RESPONSE FUNCTION
# =====================================

def generate_ai_response(prompt):

    model = st.session_state.selected_model

    if not model:
        raise Exception("No working Gemini model is selected.")

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            if not response.text:
                raise Exception("Gemini returned an empty response.")

            return response.text

        except Exception as e:

            error = str(e)

            if "503" in error or "UNAVAILABLE" in error:

                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue

            elif "429" in error or "RESOURCE_EXHAUSTED" in error:

                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue

            raise Exception(error)

    raise Exception("Unable to generate AI response.")


# =====================================
# 9. GENERATE INTERVIEW QUESTIONS
# =====================================

def generate_questions(role, level, interview_type, count):

    prompt = f"""
    Act as an experienced professional interviewer.

    Generate exactly {count} interview questions.

    Job Role: {role}
    Experience Level: {level}
    Interview Type: {interview_type}

    Instructions:
    1. Generate relevant interview questions.
    2. Keep questions suitable for the selected experience level.
    3. Use simple English.
    4. Include practical questions where appropriate.
    5. Return only numbered questions.
    """

    response = generate_ai_response(prompt)

    questions = []

    for line in response.splitlines():

        line = line.strip()

        line = re.sub(
            r"^\s*(?:\d+[\.\)\-]|[-•])\s*",
            "",
            line
        )

        if line:
            questions.append(line)

    questions = questions[:count]

    if not questions:
        raise Exception("No questions were generated.")

    return questions


# =====================================
# 10. EVALUATE ANSWERS
# =====================================

def evaluate_answer(question, answer, role):

    prompt = f"""
    Act as a professional interview evaluator.

    Job Role: {role}

    Interview Question:
    {question}

    Candidate Answer:
    {answer}

    Evaluate the answer honestly.

    Give the response in this format:

    Score: X/10

    Feedback:
    Explain the answer quality.

    Strengths:
    Mention what the candidate did well.

    Areas to Improve:
    Explain what is missing.

    Better Sample Answer:
    Give a simple, natural interview-ready answer.

    Give a score between 0 and 10.
    Evaluate correctness, clarity and relevance.
    Use simple English.
    """

    return generate_ai_response(prompt)


# =====================================
# 11. SIDEBAR SETTINGS
# =====================================

st.sidebar.title("Interview Settings")

role = st.sidebar.text_input(
    "Job Role",
    placeholder="Example: Python Developer"
)

level = st.sidebar.selectbox(
    "Experience Level",
    ["Fresher", "Intermediate", "Experienced"]
)

interview_type = st.sidebar.selectbox(
    "Interview Type",
    ["Technical", "HR", "Project-Based", "Mixed"]
)

count = st.sidebar.slider(
    "Number of Questions",
    min_value=3,
    max_value=10,
    value=5
)

st.sidebar.divider()

st.sidebar.caption(
    "Prepare yourself for your next interview with AI."
)


# =====================================
# 12. WELCOME SECTION
# =====================================

st.markdown(
    """
    <div style="
        background: linear-gradient(120deg,#4f46e5,#7c3aed);
        padding:25px;
        border-radius:12px;
        text-align:center;
        color:white;
        margin-bottom:20px;
    ">
        <h2 style="color:white;">
            Welcome to Your AI Interview Practice
        </h2>
        <p style="color:white;">
            Select your interview preferences and start practising.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# =====================================
# 13. GENERATE QUESTIONS
# =====================================

if st.button("🚀 Start Mock Interview"):

    if not role.strip():

        st.warning("Please enter your job role in the sidebar.")

    else:

        try:

            with st.spinner(
                "Preparing your interview questions..."
            ):

                # Automatically detect and test available models
                st.session_state.selected_model = select_model()

                questions = generate_questions(
                    role,
                    level,
                    interview_type,
                    count
                )

            st.session_state.questions = questions
            st.session_state.current_index = 0
            st.session_state.results = []
            st.session_state.evaluated = False
            st.session_state.role = role
            st.session_state.interview_started = True

            st.success("Your interview is ready!")

            st.rerun()

        except Exception as e:

            st.error(f"Unable to generate questions: {e}")


# =====================================
# 14. INTERVIEW SECTION
# =====================================

if st.session_state.interview_started:

    questions = st.session_state.questions

    total = len(questions)

    index = st.session_state.current_index

    if index < total:

        st.divider()

        st.subheader(
            f"Question {index + 1} of {total}"
        )

        st.progress((index + 1) / total)

        question = questions[index]

        st.info(question)

        answer = st.text_area(
            "Write your answer below:",
            height=150,
            placeholder="Type your answer here...",
            key=f"answer_{index}"
        )

        # =================================
        # EVALUATE ANSWER
        # =================================

        if not st.session_state.evaluated:

            if st.button("📊 Submit & Evaluate Answer"):

                if not answer.strip():

                    st.warning("Please enter your answer first.")

                else:

                    try:

                        with st.spinner(
                            "AI is evaluating your answer..."
                        ):

                            feedback = evaluate_answer(
                                question,
                                answer,
                                st.session_state.role
                            )

                        st.session_state.results.append({
                            "question": question,
                            "answer": answer,
                            "feedback": feedback
                        })

                        st.session_state.evaluated = True

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Unable to evaluate answer: {e}"
                        )

        # =================================
        # DISPLAY FEEDBACK
        # =================================

        if st.session_state.evaluated:

            result = st.session_state.results[index]

            st.subheader("🤖 AI Feedback")

            st.markdown(result["feedback"])

            if index < total - 1:

                if st.button("➡️ Next Question"):

                    st.session_state.current_index += 1

                    st.session_state.evaluated = False

                    st.rerun()

            else:

                st.success("🎉 Interview Completed!")

                # =================================
                # FINAL SCORE
                # =================================

                st.divider()

                st.subheader("🏆 Final Performance Report")

                scores = []

                for item in st.session_state.results:

                    match = re.search(
                        r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10",
                        item["feedback"],
                        re.IGNORECASE
                    )

                    if match:

                        score = float(match.group(1))

                        if 0 <= score <= 10:
                            scores.append(score)

                if scores:

                    average = sum(scores) / len(scores)

                    st.metric(
                        "Average Interview Score",
                        f"{average:.1f}/10"
                    )

                    st.progress(average / 10)

                    if average >= 8:
                        st.success("Excellent performance!")

                    elif average >= 6:
                        st.info("Good performance! Keep practising.")

                    else:
                        st.warning(
                            "Keep practising to improve your interview skills."
                        )

                else:

                    st.warning("Unable to calculate the average score.")

                st.write(
                    f"Questions attempted: {len(st.session_state.results)}"
                )

                # =================================
                # COMPLETE REVIEW
                # =================================

                st.subheader("📚 Review Your Answers")

                for i, item in enumerate(
                    st.session_state.results
                ):

                    with st.expander(f"Question {i + 1}"):

                        st.write("Question:", item["question"])

                        st.write("Your Answer:", item["answer"])

                        st.markdown(item["feedback"])

                # =================================
                # RESTART INTERVIEW
                # =================================

                if st.button("🔄 Start New Interview"):

                    st.session_state.questions = []
                    st.session_state.current_index = 0
                    st.session_state.results = []
                    st.session_state.evaluated = False
                    st.session_state.interview_started = False
                    st.session_state.selected_model = None

                    st.rerun()


# =====================================
# 15. FOOTER
# =====================================

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#64748b;">
        <p>AI Mock Interview Generator</p>
        <p>Built using Python | Streamlit | Gemini AI</p>
    </div>
    """,
    unsafe_allow_html=True
)
