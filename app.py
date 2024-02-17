from flask import Flask, request, render_template, redirect, flash, make_response, session
from flask_debugtoolbar import DebugToolbarExtension
from surveys import surveys

#key names will use to store some things in session;

RESPONSES_KEY = "responses"
CURRENT_SURVEY_KEY = 'current_survey'

app = Flask(__name__)
app.config['SECRET_KEY'] =  "never-tell!"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)

@app.route("/")
def show_pick_survey_form():
    """show pick-a-survey form"""

    return render_template("pick-survey.html", survey=surveys)

@app.route("/", methods=["POST"])
def pick_survey():
    """select a survey."""

    survey_id = request.form['survey_code']

    # don't let them re-take a survey until cookie times out
    if request.cookies.get(f"completed_{survey_id}"):
        return render_template("already-done.html")
    
    survey = surveys[survey_id]
    session[CURRENT_SURVEY_KEY] = survey_id

    return render_template("survey_start.html", survey=survey)


@app.route('/begin', methods=["POST"])
def start_survey():
    """Clear the session of responses."""

    session[RESPONSES_KEY] = []

    return redirect("/questions/0")

@app.route("/answer", methods=["POST"])
def handle_question():
    """Save response and redirect to next question"""

    #get the response choice
    choice = request.form['answer']
    text = request.form.get("text", "")

    # add this response to the list in the session
    responses = session[RESPONSES_KEY]
    responses.append({"choice": choice, "text":text})

    # add this response to the session
    session[RESPONSES_KEY] = responses
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]

    if (len(responses) == len(survey.questions)):
        #they've answered all the questions! Thank them.
        return redirect('/complete')
    
    else:
        return redirect(f"/questions/{len(responses)}")
    
@app.route("/questions/<int:qid>")
def show_question(qid):
    """Display current question."""

    responses = session.get(RESPONSES_KEY)
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = survey[survey_code]

    if (responses is None):
        # trying to access question page too soon
        return redirect("/")
    
    if(len(responses) == len(survey.questions)):
        # they've answered all the questions! Thank them.
        return redirect("/complete")
    
    if (len(responses) != qid):
        # trying to access questions out of order.
        flash(f"Invalid question id: {qid}.")
        return redirect(f"questions/{len(responses)}")
    
    question = survey.questions[qid]

    return render_template(
        "question.html", question_num=qid, question=question)
    
@app.route("/complete")
def say_thanks():
    """Thank user and list responses."""

    survey_id = session[CURRENT_SURVEY_KEY]
    survey = survey[survey_id]
    responses = session[RESPONSES_KEY]

    html = render_template("complete.html", survey=survey, responses=responses)

    # Set cookie noting this survey is done so they can't re-do it
    response = make_response(html)
    response.set_cookie(f"completed_{survey_id}", "yes", max_age=60)

    return response
