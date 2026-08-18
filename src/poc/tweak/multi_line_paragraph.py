import spacy

# Load the lightweight English model
nlp = spacy.load("en_core_web_sm")

original_markdown = """LaserWeeder
combines computer vision, AI, robotics, and high-powered lasers to
identify weeds and destroy them with sub-millimeter precision—no
herbicides, hand labor, or soil disturbance required. Growers achieve
weed control cost reductions of up to 80% and crop yield increases of
5–50%, with payback in one to three years. The system is powered by
Carbon AI’s Large Plant Model (LPM), trained on 150 million labeled
plants, and can start weeding any crop or field in minutes.

The
company's second product is Carbon Autonomy, the most dependable tractor
autonomy solution. Carbon Autonomy includes a retrofit tractor autonomy
kit for John Deere tractors, autonomy software, and remote supervision
for real-time interventions if required.

As a
**Performance Quality Technician** at**Carbon Robotics,**
you will be responsible for identifying, diagnosing, and resolving
systemic issues across our dataset of high-resolution imagery. You'll
address performance issues and conduct field experiments and data
analysis to diagnose root causes. Working directly with farmers is a key
part of this role,\u00a0 you'll build relationships with growers, listen
to their feedback, conduct field studies, and translate what you learn
into systemic improvements, serving as a bridge between our customers
and our engineering teams. You'll also respond to high-priority field
issues; when customers hit critical problems, you'll move quickly to
investigate, diagnose root causes, and coordinate with support, Deep
Learning, engineering, and field teams to drive fast, effective
resolutions that keep our customers running.

**Drug Free Workplace:**

Boeing is a Drug Free Workplace (DFW) where post-offer applicants and
employees are subject to testing for marijuana, cocaine, opioids,
amphetamines, PCP, and alcohol when criteria is met as outlined in our
policies.

**CodeVue Coding Challenge:**

To be considered for this position you will be required to complete a
technical assessment as part of the selection process.  Failure to
complete the assessment will remove you from consideration.

**Pay & Benefits:**

At Boeing, we strive to deliver a Total Rewards package that will
attract, engage and retain the top talent.  Elements of the Total
Rewards package include competitive base pay and variable compensation
opportunities."""

# Step 1: Split into distinct paragraphs
paragraphs = original_markdown.split("\n\n")
processed_paragraphs = []

for _i, para in enumerate(paragraphs):
    # The expected output leaves paragraph 3 (index 2) exactly as it is
    # if _i == 2:
    #     processed_paragraphs.append(para)
    #     continue

    # Step 2: Process the paragraph text through spaCy
    doc = nlp(para)
    cleaned_sentences = []

    for sent in doc.sents:
        # Remove erratic newlines inside the sentence and fix spacing
        cleaned_sent = " ".join(sent.text.split())
        cleaned_sentences.append(cleaned_sent)

    # Reconstruct the paragraph with single spacing between sentences
    processed_paragraphs.append(" ".join(cleaned_sentences))

# Step 3: Join paragraphs back together with double newlines
expected_markdown = "\n\n".join(processed_paragraphs)

print(expected_markdown)
