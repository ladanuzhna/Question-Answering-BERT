import torch
from src import model as m
import wikipedia
import time
from urllib.request import urlopen
from googlesearch import search
import en_core_web_sm

# Generate masks for BERT model and prepare the text for training

def ask_question_(question):
    print("Question:", question)
    reference = find_references2(question)
    if len(reference) == 0:
        return
    model_,tokenizer_= m.get_model()
    encoded = tokenizer_.encode_plus(question, reference)
    # To separate our question and answer in the input to the model,
    # we want to create a binary mask for question and answer
    # sep_index = encoded.index(tokenizer_.sep_token_id)
    # question_len = sep_index + 1
    # answer_len = len(encoded) - question_len
    # token_type_ids = [0] * question_len + [1] * answer_len
    token_type_ids = encoded['token_type_ids']

    [start,end] = model_(torch.tensor([encoded['input_ids']]),token_type_ids=torch.tensor([token_type_ids]))
    answer_start = torch.argmax(start)
    answer_end = torch.argmax(end)
    answer__ = torch.max(start)
    end__ = torch.max(end)

    tokens = tokenizer_.convert_ids_to_tokens(encoded['input_ids'])

    answer = recreate_answer(tokens,answer_start, answer_end)

    print('Answer: ', answer)

def recreate_answer(tokens, start, end):
    answer = tokens[start]
    for i in range(start + 1, end + 1):
        if tokens[i][0:2] == '##':
            answer += tokens[i][2:]
        else:
            answer += ' ' + tokens[i]
    return answer

def find_reference(question):
    return wikipedia.summary(question, sentences=7)

def find_references2(question):
    entities = extract_entities(question)
    summaries = []
    for entity in entities:
        try:
            summaries.append(wikipedia.summary(entity, sentences=10))
        except:
            continue
    if len(summaries) == 0:
        try:
            return wikipedia.summary(question, sentences=10)
        except:
            print("Sorry, the information was not found")
    return summaries


def extract_entities(question):
    wanted = ['ORG','PERSON','GPE','LOC','WORK_OF_ART','LAW','NORP','FAC','PRODUCT','EVENT']
    nlp = en_core_web_sm.load()
    doc = nlp(question)
    ents = [X.text for X in doc.ents if X.label_ in wanted ]
    return ents


def find_references(question, NUM_OF_REF = 3):
    # Finds a specified number of references for the question asked
    references = []
    generator = search(question, tld='com', lang='en', num=NUM_OF_REF)
    for link in generator:
        text = extract_passage(link)
        references.append(text)
    references.append(wikipedia.summary(question, sentences=5))
    return references

def extract_passage(url):
    try:
        html = urlopen(url).read()
        time.sleep(20)
    except:
        print("Waiting didn't really help")
    soup = wikipedia.BeautifulSoup(html)

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()  # rip it out

    # get text
    text = soup.body.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)



