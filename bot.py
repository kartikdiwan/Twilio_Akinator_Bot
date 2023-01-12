from flask import Flask, request
import requests as req
from bs4 import BeautifulSoup
import random
from twilio.twiml.messaging_response import MessagingResponse
import numpy as np

app = Flask(__name__)

global questions
questions = {
    1: 'Is your character blue?',
    2: 'Does your character wear glasses?',
    3: 'Is your character male?',
    4: 'Is your character fat?',
    5: 'Is your character smart?',
    6: 'Is your character rich?'
}

global characters
characters = [
    {'name': 'Doraemon',         'answers': {1: 1, 2: 0, 3: 1, 4: 0.5, 5: 0.5, 6: 0.5}},
    {'name': 'Nobita',          'answers': {1: 0, 2: 1, 3: 1, 4: 0, 5: 0, 6: 0}},
    {'name': 'Sunio',          'answers': {1: 0, 2: 0, 3: 1, 4: 0, 5: 0.5, 6: 1}},
    {'name': 'Shizuka',          'answers': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0.75, 6: 0.5}},
    {'name': 'Jihaan',          'answers': {1: 0, 2: 0, 3: 1, 4: 1, 5: 0, 6: 0}},
    {'name': 'Dekisugi',          'answers': {1: 0, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0.5}},
]

answer_prob = {
    1: 1,
    2: 0,
    3: 0.5,
    4: 0.75,
    5: 0.25
}


def calculate_probabilites(questions_so_far, answers_so_far):
    probabilities = []
    for character in characters:
        probabilities.append({
            'name': character['name'],
            'probability': calculate_character_probability(character, questions_so_far, answers_so_far)
        })
    return probabilities

def calculate_character_probability(character, questions_so_far, answers_so_far):
    # Prior
    P_character = 1 / len(characters)

    # Likelihood
    P_answers_given_character = 1
    P_answers_given_not_character = 1
    for question, answer in zip(questions_so_far, answers_so_far):
        P_answers_given_character *= max(
            1 - abs(answer - character_answer(character, question)), 0.01)

        P_answer_not_character = np.mean([1 - abs(answer - character_answer(not_character, question))
                                          for not_character in characters
                                          if not_character['name'] != character['name']])
        P_answers_given_not_character *= max(P_answer_not_character, 0.01)

    # Evidence
    P_answers = P_character * P_answers_given_character + \
        (1 - P_character) * P_answers_given_not_character

    # Bayes Theorem
    P_character_given_answers = (
        P_answers_given_character * P_character) / P_answers

    return P_character_given_answers

def character_answer(character, question):
    if question in character['answers']:
        return character['answers'][question]
    return 0.5

layer = 0
questions_so_far = []
answers_so_far = []
probabilities = []

@app.route('/bot', methods=['POST'])
def bot():
    resp = MessagingResponse()
    msg = resp.message()
    global layer
    global questions_so_far
    global answers_so_far
    global probabilities

    if layer == 0: #Output First Message
        incoming_msg = request.values.get('Body', '').lower()
        msg.media('https://m.media-amazon.com/images/M/MV5BN2U0YmY3NTktNDAyOC00YThmLTk2OGYtM2E4MGQ1OWRiZWRlXkEyXkFqcGdeQXVyMTA0MTM5NjI2._V1_.jpg')
        msg.body("*Hello, This is the Akinator*\n\nPlease Choose a character from below and don't tell me:\n1) Doraemon\n2) Nobita\n3) Sunio\n4) Shizuka\n5) Jihaan\n6) Dekisugi\n-------------------------")
        layer = 1

    if layer > 0 and layer < 12 and layer % 2 == 0: #Input Answers
        incoming_msg = int(request.values.get('Body', '').lower())
        if incoming_msg < 1 or incoming_msg > 5:
            msg.body("Please only input numbers between 1-5!\nSession will now restart\nSend Hi again to restart!")
            layer = 0
            return str(resp)
        answers_so_far.append(answer_prob.get(incoming_msg))
        probabilities = calculate_probabilites(questions_so_far, answers_so_far)
        layer = layer + 1

    if layer > 0 and layer < 12 and layer % 2 == 1: #Print Questions
        questions_left = list(set(questions.keys()) - set(questions_so_far))
        next_question = random.choice(questions_left)
        msg.body("-------------------------\n*"+questions.get(next_question)+"*\n1) Yes\n2) No\n3) Don't Know\n4) Probably\n5) Probably Not")
        questions_so_far.append(next_question)
        layer = layer + 1
        return str(resp)

    if layer == 12:
        result = sorted(probabilities, key=lambda p: p['probability'], reverse=True)[0]
        final_answer = result.get("name")
        msg.body("I guessed : " + final_answer + "\nSend Hi again to restart!")
        url = "https://www.google.com/search?q=" + final_answer + "+doraemon&tbm=isch&sxsrf=AJOqlzXCcUK0Eg1CAhUkromhTl1XgFpinw%3A1673420993684&source=hp&biw=1920&bih=929&ei=wWC-Y-rpJ4H6hwOrmoXAAw&iflsig=AK50M_UAAAAAY75u0V_5scEk17t_PmBJsCiV42RciYLU&oq=d&gs_lcp=CgNpbWcQARgAMgQIIxAnMggIABCABBCxAzIICAAQgAQQsQMyCAgAEIAEELEDMggIABCABBCxAzIICAAQgAQQsQMyCAgAEIAEELEDMggIABCABBCxAzIICAAQgAQQsQMyCAgAEIAEELEDOgcIIxDqAhAnUOgFWOgFYOoQaAFwAHgAgAGCAYgBggGSAQMwLjGYAQCgAQGqAQtnd3Mtd2l6LWltZ7ABCg&sclient=img"
        page = req.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        image_tags = soup.find_all('img')
        links = []
        for image_tag in image_tags:
            links.append(image_tag['src'])
        msg.media(links[5])
        layer = 0
        questions_so_far = []
        answers_so_far = []
        probabilities = []
        return str(resp)

if __name__ == '__main__':
    app.run(port=4000)