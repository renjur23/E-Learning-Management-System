"""Original introductory revision notes, generated privately for enrolled learners."""
from html import escape
from io import BytesIO

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import FileResponse
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views import View
from django.views.decorators.cache import never_cache
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak

from instructor.models import Course
from student.decorator import signin_required


# Each set contains four core concepts, a worked example and revision prompts.
NOTES = {
    'reasoning': (
        [('Recognise the pattern', 'For a number series, compare adjacent terms first. Check differences, ratios and alternating sequences. A pattern must explain every supplied term; a single matching pair is not enough.'),
         ('Translate statements carefully', 'Use simple diagrams for relationships and directions. For statements about groups, distinguish all, some and none. Do not reverse an implication: all squares are rectangles does not imply all rectangles are squares.'),
         ('Build a coding rule', 'Write letter positions where useful. Test whether the same shift, reversal or substitution works throughout the example before applying it to a new word.'),
         ('Work systematically', 'For arrangements, list fixed positions and exclusions before testing possibilities. Separate what is definitely true from what is merely possible. Recheck each proposed answer against every condition.')],
        'Series: 5, 9, 13, 17. The adjacent differences are all 4, so the next term is 21. Check the whole sequence, not only the final pair. For a turning problem, draw a compass and update the facing direction after each turn.',
        ['Explain why reversing an all statement can be invalid.', 'Create a number series using alternating rules.', 'Solve an arrangement using a table of allowed positions.']),
    'aptitude': (
        [('Percentages and ratios', 'A percentage is a fraction out of 100. To find p percent of a value, multiply by p/100. In a ratio a:b, the total number of equal parts is a+b. Keep the original base clear when comparing percentage changes.'),
         ('Averages and totals', 'The arithmetic mean equals the sum divided by the number of observations. Reconstruct the total before combining groups of different sizes. An average of group averages is valid only when the groups have equal sizes.'),
         ('Interest, work and speed', 'Simple interest equals principal times annual rate times years, divided by 100. For work questions, combine work rates rather than completion times. Average speed uses total distance divided by total elapsed time.'),
         ('Interpret the data', 'Read table headings, units and time periods before calculating. Distinguish percentage change from percentage-point change. Estimate the answer first, then calculate and compare with the available options.')],
        'A price of Rs. 800 rises by 15%. The increase is 800 x 15/100 = Rs. 120, giving Rs. 920. If the new price then falls by 15%, subtract 920 x 15/100 = Rs. 138. The final price is Rs. 782, not Rs. 800, because the base changed.',
        ['Find 18% of 300 and explain your method.', 'Split 180 in the ratio 4:5.', 'Explain why equal percentage increases and decreases do not cancel.']),
    'psc': (
        [('Kerala-focused general knowledge', 'Organise revision by history, social reform, geography and culture. Use a timeline for historical events and a map for districts, rivers and neighbouring states. Connect each person or event with its place and historical context.'),
         ('Constitution and institutions', 'Study the structure of government and the roles of its institutions. Distinguish the legislature, executive and judiciary. Read constitutional terms in context instead of memorising isolated words.'),
         ('Science and the economy', 'Build concept summaries for everyday science, health, environment and basic economic vocabulary. Separate definitions from examples. Use a cause-and-effect explanation to check whether you understand a concept.'),
         ('A revision routine', 'Read a topic, close the source and recall its main points. Review errors after practice. Maintain a dated current-affairs log and check the applicable official exam notification for the syllabus and eligibility requirements.')],
        'Create a three-column revision table: topic, key fact, reason it matters. For Kerala state formation, record 1 November 1956 and connect it with linguistic reorganisation of states. Then locate Kerala on a map and identify the Arabian Sea to the west.',
        ['Make a timeline of five Kerala social-reform milestones.', 'Explain the difference between a legislature and a court.', 'Write a short cause-and-effect summary of one science topic.']),
    'psc-practice': (
        [('Build arithmetic fluency', 'Revise fractions, percentages, ratios, averages and basic equations. Show intermediate steps until the method is reliable. Add shortcuts only after understanding why they work.'),
         ('Practise mental ability', 'Draw directions and family relationships instead of keeping every detail in memory. Test sequence rules against all terms. For puzzles, mark fixed facts separately from guesses.'),
         ('English language practice', 'Check subject-verb agreement, tense, articles and word meaning in context. Read the complete sentence before selecting an answer. Keep an error notebook with a corrected example and a short explanation.'),
         ('Malayalam language practice', 'Use an appropriate Malayalam grammar reference to revise word forms, sentence accuracy, meanings and reading comprehension. Note unfamiliar words in their original script in your own notebook and revise them in context.')],
        'The mean of five practice scores is 24. Their total is 5 x 24 = 120. If a sixth score of 30 is added, the new mean is (120 + 30)/6 = 25. In language questions, apply the same discipline: identify the governing rule before choosing an option.',
        ['Find the mean after adding a new observation to a group.', 'Correct a sentence and identify the grammar rule used.', 'Create a personal list of commonly confused Malayalam words.']),
    'upsc': (
        [('Connect general-studies subjects', 'Link history, geography, polity, economy and environment rather than studying them as isolated facts. For a topic, ask what happened, where, why and with what consequences.'),
         ('Read institutions and concepts', 'Explain the purpose of an institution before listing its functions. Distinguish constitutional principles, laws, policies and administrative practice. Use a reliable primary reference to verify important details.'),
         ('Analyse current affairs', 'Separate the event from the underlying issue. Record the stakeholders, causes, potential effects and policy choices. Date your notes and revisit information that can change.'),
         ('Structure written answers', 'Address the question directly. Use a short introduction, organised points supported by examples and a balanced ending. Distinguish description from analysis. Practise within a time limit and review clarity afterwards.')],
        'For a practice answer on urban flooding, organise the response into causes, effects and responses. Causes may include intense rainfall, obstructed drainage and loss of permeable land. Connect each proposed response to a cause instead of producing an unrelated list.',
        ['Compare a constitutional principle with an administrative policy.', 'Summarise a current issue using causes, stakeholders and effects.', 'Write a 150-word answer, then remove repetition.']),
    'csat': (
        [('Read for meaning', 'Identify the passage main idea before looking at the options. Distinguish what the text says from what you know externally. Prefer the answer supported by the passage without introducing extra assumptions.'),
         ('Reason from the premises', 'For deductions, write the premises as simple relationships. A conclusion must follow from those premises, not merely sound plausible. Use small counterexamples to reject overbroad conclusions.'),
         ('Use numeracy carefully', 'Keep fractions, ratios and percentages in compatible forms. Check units before combining values. For data interpretation, calculate from the relevant row or column rather than the whole table by default.'),
         ('Manage the paper', 'Start with questions you can solve accurately. Mark difficult items for a second pass. Use timed practice to learn which question types need more work. Consult the applicable official notification for examination rules.')],
        'A group has 36 people, of whom 12 use the bus. The bus share is 12/36 = 1/3, or about 33.3%. If 6 more bus users join, both numerator and denominator change: 18/42 = 3/7, or about 42.9%. Re-read what the question asks before comparing results.',
        ['Explain the difference between an inference and an assumption.', 'Turn a table into two accurate comparison statements.', 'Practise skipping and returning to a difficult question.']),
    'ai': (
        [('Learning from examples', 'Machine learning fits patterns from examples. Features describe the input and a target describes what a supervised model is learning to predict. The model does not automatically establish why a pattern exists.'),
         ('Types of tasks', 'Classification predicts categories. Regression predicts numerical values. Clustering groups similar observations without supplied class labels. Choose the task from the intended output, not from a tool name.'),
         ('Evaluate on unseen data', 'Separate training data from evaluation data. A model can fit training examples closely but perform poorly on new examples. Check errors and data quality as well as a single summary score.'),
         ('Use outputs critically', 'AI systems can make mistakes, reflect biases or produce unsupported claims. Verify important output, protect sensitive information and document where a system performs poorly.')],
        'Suppose a model labels 90 of 100 messages correctly. Its accuracy is 90%, but that number alone may hide poor detection of a rare spam category. Inspect which kinds of mistakes occur and compare results with the task goal.',
        ['Give one classification and one regression example.', 'Explain overfitting in your own words.', 'List two checks before trusting an AI-generated answer.']),
    'data': (
        [('Inspect before cleaning', 'Identify what each row represents, the meaning of each column and the expected data types. Check units, duplicates, missing values and impossible ranges before selecting a transformation.'),
         ('Treat missingness explicitly', 'A missing value is not automatically zero. Investigate why a value may be absent. Dropping or filling values can introduce bias, so document the method and its limitations.'),
         ('Prepare without leakage', 'Split data before fitting transformations that learn from it. Fit scaling or imputation parameters on training data and apply the same parameters to evaluation data. Keep target information out of inputs.'),
         ('Summarise and communicate', 'Use summaries and plots suited to the variable type. Outliers may reflect valid events or data errors. State the question, method, result and limitations so another reader can understand the analysis.')],
        'For observations 3, 4, 5 and 100, the mean is 28 while the median is 4.5. The large final observation pulls the mean upward. Investigate that observation rather than deleting it solely because it is unusual.',
        ['Explain when filling missing values with zero would be misleading.', 'Describe a leakage risk in preprocessing.', 'Compare the mean and median of a small dataset.']),
    'web': (
        [('Structure with HTML', 'Use semantic elements for headings, navigation, main content and forms. Labels should identify form controls. A clear document structure benefits keyboard users, assistive technology and future maintenance.'),
         ('Present with CSS', 'Use a consistent spacing scale, responsive layout and readable text. Flexbox and Grid help express layout relationships. Check narrow screens and visible keyboard focus instead of assuming desktop styling is sufficient.'),
         ('Add behaviour with JavaScript', 'Listen for events and update the interface in response. Handle failure states as well as success. A browser can improve feedback, but it cannot be the only authority for permissions or validation.'),
         ('Connect the backend', 'A Django view processes a request and returns a response. Models describe stored data and templates render the interface. Validate input on the server and use CSRF protection for state-changing forms.')],
        'A course-enrolment flow should show a course on GET, accept a deliberate form submission on POST, validate the signed-in user on the server and save the result only after its conditions are met. Display useful feedback if the operation fails.',
        ['Explain the roles of a Django model, view and template.', 'Build a labelled form with keyboard-visible focus.', 'Describe why browser validation alone is insufficient.']),
    'mearn': (
        [('Understand each layer', 'MongoDB stores data, Express handles server routes, React builds user interfaces and Node.js runs server-side JavaScript. In a MEAN variation, Angular is used for the interface. Keep responsibilities clear between layers.'),
         ('Design data exchanges', 'A client sends a request and a server returns a response, often using JSON. Check response status and handle failures. Validate the shape and meaning of incoming data on the server.'),
         ('Manage interface state', 'Represent loading, success, empty and error states explicitly. Reusable components should receive clear inputs. Avoid changing data invisibly in several places at once.'),
         ('Protect server operations', 'Authenticate users, check permissions and validate inputs before writing data. Keep credentials on the server. Do not trust a client-supplied price or account identifier without verification.')],
        'For a reading-list application, the interface sends a book title to a server route. The server checks the user and validates the title before saving a document. The response contains the saved record or a clear error, and the interface updates its state accordingly.',
        ['Trace a request from a React component to a database.', 'Explain the difference between authentication and permission checks.', 'Design an error state for a failed save.']),
    'testing': (
        [('Write observable expectations', 'A test case describes conditions, actions and expected outcomes. Focus on behaviour a user or another system can observe. Vague statements such as works correctly are hard to verify.'),
         ('Choose useful inputs', 'Use equivalence groups and boundary values to reduce repetition while covering meaningful cases. Check valid, invalid, missing and unexpected values where relevant.'),
         ('Test at suitable levels', 'Unit tests target small pieces of behaviour. Integration tests check collaborating components. End-to-end tests exercise broader workflows. Choose a level that can detect the failure reliably without unnecessary fragility.'),
         ('Report and prevent regressions', 'A useful bug report includes reproduction steps, expected and actual behaviour, and relevant context. After fixing a defect, add an appropriate regression check when it protects meaningful behaviour.')],
        'For a quantity field allowing 1 to 20, consider 0, 1, 20 and 21 as boundary cases. Also test missing and non-numeric input. Check both the validation message and whether invalid data was prevented from being saved.',
        ['Write a test case for an unsuccessful sign-in.', 'Identify boundary values for a minimum password length.', 'Explain when an integration test is more useful than a unit test.']),
}


def topic_key(title):
    text = title.lower()
    if 'csat' in text: return 'csat'
    if 'upsc' in text: return 'upsc'
    if 'psc' in text: return 'psc-practice' if 'language' in text else 'psc'
    if 'reasoning' in text: return 'reasoning'
    if 'aptitude' in text: return 'aptitude'
    if 'data science' in text: return 'data'
    if 'ai for' in text: return 'ai'
    if 'mearn' in text or 'mern' in text: return 'mearn'
    if 'testing' in text: return 'testing'
    if 'web development' in text: return 'web'
    return None


def build_notes(course):
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=A4, rightMargin=22*mm, leftMargin=22*mm, topMargin=25*mm, bottomMargin=22*mm, title=f'{course.title} - Study notes', author='LearnOrbit')
    ink, coral = colors.HexColor('#172b40'), colors.HexColor('#ad3e2d')
    body = ParagraphStyle('Body', fontName='Helvetica', fontSize=10.5, leading=16, textColor=ink, spaceAfter=11)
    heading = ParagraphStyle('Heading', parent=body, fontName='Helvetica-Bold', fontSize=14, leading=19, spaceBefore=12, spaceAfter=8, keepWithNext=True)
    title = ParagraphStyle('Title', parent=body, fontName='Times-Roman', fontSize=29, leading=33, spaceAfter=16)
    eyebrow = ParagraphStyle('Label', parent=body, fontSize=9, leading=12, textColor=coral, spaceAfter=10)
    def para(text, style=body):
        return Paragraph(escape(text), style)
    def page_frame(canvas, document):
        canvas.saveState()
        canvas.setFillColor(ink)
        canvas.rect(0, A4[1]-12*mm, A4[0], 12*mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 9)
        canvas.drawString(22*mm, A4[1]-8*mm, 'LearnOrbit / Study Studio')
        canvas.setFillColor(ink)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(22*mm, 12*mm, 'Introductory revision notes | Independent learning resource')
        canvas.drawRightString(A4[0]-22*mm, 12*mm, str(document.page))
        canvas.restoreState()
    key = topic_key(course.title)
    if key:
        concepts, example, prompts = NOTES[key]
    else:
        concepts = [(m.title, 'Review the lessons in this module. Summarise the main ideas, identify an example and record any questions you need to revisit.') for m in course.modules.all()][:4]
        example = 'Choose one concept from a lesson. State the problem, show the steps you would follow and check the result against the original requirement.'
        prompts = ['Summarise your most recent lesson without referring to the video.', 'Explain a concept using your own example.', 'Record one question to revisit.']
    story = [para('COURSE NOTES / CORE CONCEPTS', eyebrow), para(course.title, title), para('A concise companion for revising the introductory lessons. Use it alongside the course videos and your own practice, rather than as a complete syllabus.')]
    for i, (label, text) in enumerate(concepts, 1):
        story += [para(f'{i:02d} / {label}', heading), para(text)]
    story += [PageBreak(), para('APPLY / RECALL / REVISE', eyebrow), para('Turn knowledge into practice.', title), para('Worked example', heading), para(example), para('Check your understanding', heading)]
    for i, prompt in enumerate(prompts, 1):
        story.append(para(f'{i}. {prompt}'))
    story += [para('Your course roadmap', heading)]
    for module in course.modules.order_by('order', 'pk'):
        if module.lessons.exists() or not module.assessments.exists():
            story.append(para('- ' + module.title))
    story += [para('A useful revision habit', heading), para('After each lesson, write a three-line summary, work through one example and list any mistakes. Return to the topic later without looking at your notes first. Use course quizzes to identify gaps and review the explanations after submission.')]
    if key in ('psc', 'psc-practice', 'upsc', 'csat'):
        story.append(para('Exam preparation: these notes are independent introductory material. Confirm the applicable syllabus, eligibility and examination rules from the relevant official notification. Add dated current-affairs notes separately.'))
    doc.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    stream.seek(0)
    return stream


@method_decorator(signin_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class CourseNotesView(View):
    def get(self, request, pk):
        course = get_object_or_404(Course.objects.prefetch_related('modules__lessons', 'modules__assessments'), pk=pk)
        if not request.user.purchase.filter(is_paid=True, course_objects=course).exists():
            messages.info(request, 'Enrol in this course to download its study notes.')
            return redirect('course-detail', pk=pk)
        return FileResponse(build_notes(course), as_attachment=True, filename=f'{slugify(course.title) or "course"}-study-notes.pdf', content_type='application/pdf')
