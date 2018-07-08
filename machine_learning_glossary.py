"""
This demonstrates a simple skill built with the Amazon Alexa Skills Kit to define the general terms of Machine Learning.
"""

from __future__ import print_function
import json
import boto3
import random

DEF = 'B' # key in the dictionary containing the definition of the term 
START_MESSAGE = ' has the following definition: \n'

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
    
def canfulfill_response(can_fulfill, can_understand, slot):
    if slot:
        return {
            "version":"1.0",
            "response":{
                "canFulfillIntent": {
                    "canFulfill": can_fulfill,
                    "slots":{
                        "term": {
                            "canUnderstand": can_understand,
                            "canFulfill": can_fulfill
                        }
                    }
                }
            }
        }
    else:
        return {
            "version":"1.0",
            "response":{
                "canFulfillIntent": {
                    "canFulfill": can_fulfill
                }
            }
        }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Machine Learning Glossary"
    speech_output = "Welcome to Machine Learning Glossary! " \
                    "This skill can get you acquainted with general machine learning terms. " \
                    "Please say 'define' followed by the term you want to know."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me a machine learning term "
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Thank you!"
    speech_output = "Thank you for trying Machine Learning Glossary. " \
                    "Have a nice day! "
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def load_definitions():
    
    bucket = 'mlglossary'
    key = 'alexa_mlg_release.json'

    s3 = boto3.resource('s3')

    content_object = s3.Object(bucket, key)
    file_content = content_object.get()['Body'].read()
    json_content = json.loads(file_content)
    return json_content
    

def get_definition(intent, session, definitions):
    term = intent['slots']['term']['value']
    
    session_attributes = {}
    card_title = 'What is ' + term
    should_end_session = True
    reprompt_text = None
    
    term_lower = term.lower()
    if term_lower in definitions:
        definition = definitions[term_lower][DEF]
    else:
        return build_response({}, build_speechlet_response("Oops! unknown term.",
             "Sorry, I don't know that term. We will update our glossary shortly.", None,
             should_end_session=True))
    speech_output = term + START_MESSAGE + definition
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
    

def get_random_term(intent, session, definitions):
    session_attributes = {}
    card_title = 'Surprise! Here is your term.'
    should_end_session = True
    
    reprompt_text = None
    
    term = random.choice(list(definitions.keys()))
    definition = definitions[term][DEF]
    speech_output = "Your random term is " + term + ". \n" + term + START_MESSAGE + definition
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def canfulfill_check(intent, session, definitions):
    term = intent['slots']['term']['value']
    term_lower = term.lower()
    if term_lower in definitions:
        return canfulfill_response(can_fulfill='YES', can_understand='YES', slot=True)
    else:
        return canfulfill_response(can_fulfill='NO', can_understand='NO', slot=True)
        
# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session, definitions):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to skill's intent handlers
    if intent_name == "define":
        return get_definition(intent, session, definitions)
    if intent_name == "random":
        return get_random_term(intent, session, definitions)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")
        
def on_canfulfill(canfulfill_request, session, definitions):
    """ Called when the Alexa queries this skill with CanFulfillIntentRequest"""
    
    print("on_canfulfill requestId=" + canfulfill_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    
    intent = canfulfill_request['intent']
    intent_name = canfulfill_request['intent']['name']
    
    if intent_name == "define":
        return canfulfill_check(intent, session, definitions)
    if intent_name == "random":
        return canfulfill_response(can_fulfill='YES', can_understand='YES', slot=False)


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    definitions = load_definitions()
    
    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'], definitions)
    elif event['request']['type'] == "CanFulfillIntentRequest":
        return on_canfulfill(event['request'], event['session'], definitions)
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
