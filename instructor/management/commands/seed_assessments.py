from datetime import datetime
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
from instructor.models import Assessment, Course, Lesson, Module, Question


# Original introductory questions: prompt, four options, correct option, explanation.
BANKS = {
    'reasoning': [
        ('What comes next: 2, 4, 8, 16, ...?', ['18', '24', '32', '64'], 'c', 'Each term is twice the previous term, so 16 × 2 = 32.'),
        ('A person faces north and turns right. Which direction are they facing?', ['West', 'East', 'South', 'North'], 'b', 'A right turn from north points east.'),
        ('All roses are flowers. Which statement must be true?', ['All flowers are roses', 'Every rose is a flower', 'No rose is a flower', 'All flowers are red'], 'b', 'The premise includes all roses in the set of flowers, but says nothing about other flowers.'),
        ('If CAT is coded as DBU by shifting each letter forward once, how is DOG coded?', ['EPH', 'CNG', 'FQI', 'EOG'], 'a', 'D becomes E, O becomes P and G becomes H.'),
    ],
    'aptitude': [
        ('What is 20% of 250?', ['25', '40', '50', '75'], 'c', '20/100 × 250 = 50.'),
        ('Two quantities are in the ratio 2:3 and total 100. What is the smaller quantity?', ['20', '40', '50', '60'], 'b', 'There are five equal parts. Two parts equal 2/5 × 100 = 40.'),
        ('Find the simple interest on Rs. 1,000 at 5% per year for two years.', ['50', '100', '150', '200'], 'b', 'Simple interest is principal × rate × time / 100 = 1,000 × 5 × 2 / 100.'),
        ('A vehicle covers 120 km in 3 hours. What is its average speed?', ['30 km/h', '40 km/h', '60 km/h', '90 km/h'], 'b', 'Average speed = total distance / total time = 120/3 = 40 km/h.'),
    ],
    'psc': [
        ('Which city is the capital of Kerala?', ['Kochi', 'Kozhikode', 'Thiruvananthapuram', 'Thrissur'], 'c', 'Thiruvananthapuram is the capital of Kerala.'),
        ('Which sea borders Kerala to the west?', ['Arabian Sea', 'Caspian Sea', 'Red Sea', 'Bay of Bengal'], 'a', 'Kerala lies along the Arabian Sea on the southwest coast of India.'),
        ('Who chaired the Drafting Committee of the Indian Constituent Assembly?', ['B. R. Ambedkar', 'Mahatma Gandhi', 'Sardar Patel', 'Rajendra Prasad'], 'a', 'B. R. Ambedkar chaired the Drafting Committee.'),
        ('In which year was the state of Kerala formed?', ['1947', '1950', '1956', '1960'], 'c', 'Kerala was formed on 1 November 1956 under the reorganisation of states.'),
    ],
    'psc-practice': [
        ('What is 15% of 200?', ['15', '20', '30', '40'], 'c', '15/100 × 200 = 30.'),
        ('Choose the correct sentence.', ['She go to school.', 'She goes to school.', 'She going school.', 'She gone to school.'], 'b', 'A third-person singular subject takes goes in the simple present tense.'),
        ('What comes next: 3, 6, 9, 12, ...?', ['13', '14', '15', '18'], 'c', 'The series adds three each time.'),
        ('Which English word means the same as rapid?', ['Slow', 'Quick', 'Quiet', 'Weak'], 'b', 'Rapid and quick both describe something happening fast.'),
    ],
    'upsc': [
        ('The Preamble describes India as which of the following?', ['A monarchy', 'A democratic republic', 'A military state', 'A colonial territory'], 'b', 'The Preamble describes India as a sovereign socialist secular democratic republic.'),
        ('Which institution is the lower house of the Indian Parliament?', ['Rajya Sabha', 'Lok Sabha', 'Supreme Court', 'Election Commission'], 'b', 'Lok Sabha is the House of the People and the lower house of Parliament.'),
        ('What is biodiversity?', ['Only the number of trees', 'The variety of living organisms', 'Only rainfall patterns', 'Only mineral reserves'], 'b', 'Biodiversity refers to the variety of life, including diversity within species, between species and of ecosystems.'),
        ('Which measure compares the general price level across time?', ['An inflation index', 'A literacy count', 'A river gauge', 'A population map'], 'a', 'Price indices track changes in prices and are used to measure inflation.'),
    ],
    'csat': [
        ('Read: All library members may borrow books. Ravi is a library member. What follows?', ['Ravi may borrow books', 'Ravi owns the library', 'Ravi must borrow daily', 'Only Ravi may borrow books'], 'a', 'The rule applies to every member, including Ravi. It does not require daily borrowing.'),
        ('What is the average of 10, 20 and 30?', ['10', '15', '20', '30'], 'c', 'The sum is 60, divided by three values gives 20.'),
        ('A table shows sales of 40 units on Monday and 60 on Tuesday. What is the increase?', ['20%', '25%', '50%', '60%'], 'c', 'The increase is 20 compared with the original 40: 20/40 × 100 = 50%.'),
        ('A task takes 12 person-hours. With equal productivity, how long do 3 people take together?', ['2 hours', '3 hours', '4 hours', '12 hours'], 'c', '12 person-hours divided by three people is four hours.'),
    ],
    'ai': [
        ('What is a training dataset used for?', ['Teaching a model patterns', 'Replacing electricity', 'Changing a screen size', 'Printing a report only'], 'a', 'Training data provides examples from which a model learns patterns.'),
        ('Which is an example of classification?', ['Predicting spam or not spam', 'Adding two fixed numbers', 'Copying a file', 'Sorting dates manually'], 'a', 'Classification predicts a discrete category such as spam or not spam.'),
        ('Why evaluate a model on separate test data?', ['To estimate performance on unseen examples', 'To increase screen brightness', 'To remove all errors automatically', 'To avoid using data'], 'a', 'Separate test data helps estimate generalisation beyond training examples.'),
        ('Can an AI-generated answer contain mistakes?', ['Yes', 'Never', 'Only on Mondays', 'Only without images'], 'a', 'Model outputs can be incorrect and need verification where accuracy matters.'),
    ],
    'data': [
        ('What does a missing value represent?', ['An unavailable observation', 'Always zero', 'Always a negative number', 'A column name'], 'a', 'Missingness means the value was not recorded or is unavailable; it is not necessarily zero.'),
        ('Which statistic is less affected by extreme outliers?', ['Median', 'Sum', 'Maximum', 'Range'], 'a', 'The median uses position rather than the magnitude of extreme values.'),
        ('Why split data into training and test sets?', ['To evaluate on unseen data', 'To guarantee perfect predictions', 'To delete duplicates only', 'To change file names'], 'a', 'A held-out set supports evaluation on examples not used for fitting.'),
        ('What does feature scaling change?', ['The numerical scale of features', 'The number of rows always', 'The file extension only', 'The target meaning always'], 'a', 'Scaling transforms feature ranges or distributions, often to support model training.'),
    ],
    'web': [
        ('Which language defines the structure of a web page?', ['HTML', 'CSS', 'SQL', 'Bash'], 'a', 'HTML provides semantic document structure.'),
        ('What is CSS primarily used for?', ['Styling and layout', 'Database backup', 'Password encryption', 'Server routing only'], 'a', 'CSS controls the presentation and layout of web content.'),
        ('Which HTTP method should a form use to change server data?', ['POST', 'GET', 'HEAD', 'OPTIONS only'], 'a', 'POST is intended for processing submitted data; GET should not cause state changes.'),
        ('Why validate form data on the server?', ['Browser checks can be bypassed', 'It changes every password', 'It removes all network delays', 'It replaces authentication'], 'a', 'Clients cannot be trusted to enforce validation, so the server must check submitted data.'),
    ],
    'mearn': [
        ('Which component in MERN is a database?', ['MongoDB', 'React', 'Express', 'Node.js'], 'a', 'MongoDB stores application data.'),
        ('What is React used to build?', ['User interfaces', 'Only database indexes', 'Operating system kernels', 'Network cables'], 'a', 'React is used to build component-based user interfaces.'),
        ('Where does Express usually run?', ['On a Node.js server', 'Only inside CSS', 'Inside an image file', 'Only in MongoDB storage'], 'a', 'Express is a server-side web framework commonly used with Node.js.'),
        ('What is JSON commonly used for?', ['Exchanging structured data', 'Drawing pixels only', 'Storing executable CSS', 'Encrypting all requests'], 'a', 'JSON represents structured values exchanged between clients and servers.'),
    ],
    'testing': [
        ('What is a test case?', ['Inputs, actions and expected results', 'Only a bug title', 'Only a release date', 'A password list'], 'a', 'A test case describes how to exercise behaviour and what result to expect.'),
        ('What does regression testing check?', ['Existing features after changes', 'Only new logos', 'Only server invoices', 'Only login names'], 'a', 'Regression tests detect whether changes broke previously working behaviour.'),
        ('Which is a useful boundary value for an allowed age range of 18 to 60?', ['17', '30 only', '40 only', '45 only'], 'a', '17 is just below the lower boundary and should be rejected.'),
        ('What should a good bug report include?', ['Reproduction steps and actual versus expected behaviour', 'Only an emoji', 'Only a guess', 'A hidden password'], 'a', 'Clear steps and expected versus actual outcomes make a defect reproducible.'),
    ],
}


def bank_key(title):
    title = title.lower()
    if 'csat' in title: return 'csat'
    if 'upsc' in title: return 'upsc'
    if 'psc' in title: return 'psc-practice' if 'language' in title else 'psc'
    if 'reasoning' in title: return 'reasoning'
    if 'aptitude' in title: return 'aptitude'
    if 'data science' in title: return 'data'
    if 'ai for' in title: return 'ai'
    if 'mearn' in title or 'mern' in title: return 'mearn'
    if 'testing' in title: return 'testing'
    if 'web development' in title: return 'web'
    return None


class Command(BaseCommand):
    help = 'Seed original introductory quizzes and live tests for recognised catalogue courses.'

    @transaction.atomic
    def handle(self, *args, **options):
        start = datetime(2026, 10, 29, 12, 0, tzinfo=ZoneInfo('Asia/Kolkata'))
        end = datetime(2026, 10, 29, 12, 30, tzinfo=ZoneInfo('Asia/Kolkata'))
        count = 0
        for course in Course.objects.all():
            key = bank_key(course.title)
            lessons = list(Lesson.objects.filter(module_object__course_object=course).select_related('module_object').order_by('module_object__order', 'order', 'pk'))
            if not key or not lessons:
                self.stdout.write(f'Skipped (needs a topic bank and lessons): {course.title}')
                continue
            for kind, lesson, title in [('quiz', lessons[0], 'First lesson checkpoint'), ('live', lessons[-1], 'Foundation live test')]:
                exam_test = kind == 'live' and key in ('psc', 'psc-practice', 'upsc', 'csat')
                module = lesson.module_object
                if exam_test:
                    module, _ = Module.objects.get_or_create(course_object=course, title='Scheduled Exam Tests')
                # Retain question and attempt records when moving an existing test.
                assessment = Assessment.objects.filter(module__course_object=course, kind=kind, title=title).first()
                created = assessment is None
                if created:
                    assessment = Assessment.objects.create(
                        module=module, kind=kind, title=title,
                        after_lesson=None if exam_test else lesson,
                        duration_minutes=10 if kind == 'quiz' else 30,
                        opens_at=start if kind == 'live' else None,
                        closes_at=end if kind == 'live' else None, published=True)
                elif exam_test and (assessment.module_id != module.pk or assessment.after_lesson_id):
                    assessment.module = module
                    assessment.after_lesson = None
                    assessment.save(update_fields=['module', 'after_lesson'])
                if not created:
                    continue
                for i, (prompt, choices, correct, explanation) in enumerate(BANKS[key][:2] if kind == 'quiz' else BANKS[key][2:], 1):
                    Question.objects.create(assessment=assessment, prompt=prompt, option_a=choices[0], option_b=choices[1], option_c=choices[2], option_d=choices[3], correct_answer=correct, explanation=explanation, order=i)
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Added {count} assessments. Live schedule: 29 Oct 2026, 12:00–12:30 PM IST.'))
