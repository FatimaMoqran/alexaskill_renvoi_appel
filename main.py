# -*- coding: utf-8 -*-

# Skill Téléphonie - v1.0
# main function: 
#   Lancement de Flask, exposition des API et réception des requètes Alexa
# Features :
#   Activer un renvoi d'appel
#   Quitter le bureau - activer un renvoi d'appel
# import les fonctions du fichier function.py 


import logging
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name, get_slot_value,request_util 
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard
from flask import Flask, request, jsonify
from flask_ask_sdk.skill_adapter import SkillAdapter
import functions
import json
import os

# récupération de la configuration prod ou dev: parametres environment récupéré d'openshift 
import os
if os.environ.get('environment') == 'develop':
    import config_dev as config
if os.environ.get('environment') == 'prod':
    import config_prod as config



# Nom du skill et textes

help_text = "je peux renvoyer vos appels et consulter votre messagerie. Que puis je faire pour vous?"


# Skill
sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# connection à la basededonnee 
client_bdd =functions.connect_bdd(config.mongodb_uri)

#les requêtes d'Alexa

# Request type : LaunchRequest

@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch."""
    #get the user_assistant_id 
    user_assistant_id = handler_input.request_envelope.session.user.user_id
    
    #launch skill function
    speech_text , reprompt_text = functions.launch_skill(client_bdd,config.mongodb_db,config.mongodb_collection,'alexa',user_assistant_id)
   
    return handler_input.response_builder.speak(speech_text).ask(reprompt_text).set_should_end_session(False).response

# Intent "Activer_Renvoi_Appel"
@sb.request_handler(can_handle_func=is_intent_name("Activer_Renvoi_Appel"))
def activer_renvoi_appel_handler(handler_input):
    """Hander for Activer_Renvoi_Appel"""
    print("RECEPTION INTENT ACTIVER RENVOI APPEL")
    # Get any existing slots or attributes from the incoming request
    #session_attr = handler_input.attributes_manager.session_attributes
    phonename_slot = get_slot_value(handler_input=handler_input, slot_name = "phonename")
    phonenumber_slot = get_slot_value(handler_input= handler_input,slot_name = "phonenumber")
    print('get slot values phonenumber_slot = {} phonename_slot = {}'.format(phonenumber_slot, phonename_slot))

    #get the user_assistant_id 
    user_assistant_id = handler_input.request_envelope.session.user.user_id

	# Appel au parcours d'activation du renvoi d'appel 
    speech_text = functions.parcours_activer_renvoi_appel(client_bdd,config.mongodb_db,config.mongodb_collection,'alexa',user_assistant_id,phonename_slot,phonenumber_slot)
    print("FIN INTENT ACTIVER RENVOI APPEL")
    return handler_input.response_builder.speak(speech_text).set_should_end_session(False).response

# Intent "Quitter_bureau"
@sb.request_handler(can_handle_func= is_intent_name("Quitter_Bureau"))
def quitter_bureau_handler(handler_input):
    """Handler for Quitter_Bureau Intent"""
    print("RECEPTION INTENT QUITTER BUREAU")

    #get the user_assistant_id 
    user_assistant_id = handler_input.request_envelope.session.user.user_id

	# Appel au parcours quitter le bureau 
    speech_text = functions.parcours_quitter_bureau(client_bdd,config.mongodb_db,config.mongodb_collection,'alexa',user_assistant_id)
    print("FIN INTENT QUITTER BUREAU")
     
    return handler_input.response_builder.speak(speech_text).set_should_end_session(False).response 

#Intent "annulation_renvoi_d_appels"
@sb.request_handler(can_handle_func= is_intent_name("Annulation_renvoi_d_appels"))
def annulation_renvoi_d_appels(handler_input):
    """Handler for Intent annulation_renvoi_d_appels"""
    print("RECEPTION INTENT ANNULATION RENVOI D APPELS")

     #get the user_assistant_id 
    user_assistant_id = handler_input.request_envelope.session.user.user_id

	# Appel au parcours Annulation renvoi d'appels
    speech_text, end_session = functions.parcours_annulation_renvoi_d_appel(client_bdd,config.mongodb_db,config.mongodb_collection,'alexa',user_assistant_id)
    print("FIN INTENT ANNULATION RENVOI D APPELS")
     
    return handler_input.response_builder.speak(speech_text).set_should_end_session(end_session).response 

#Intent "Retour_bureau"
@sb.request_handler(can_handle_func= is_intent_name("Retour_bureau"))
def retour_bureau(handler_input):
    """Handler for Intent de_retour"""
    print("RECEPTION INTENT RETOUR BUREAU")

    #get the user_assistant_id 
    user_assistant_id = handler_input.request_envelope.session.user.user_id

	# Appel au parcours Annulation renvoi d'appels
    speech_text, end_session = functions.parcours_retour_bureau(client_bdd,config.mongodb_db,config.mongodb_collection,'alexa',user_assistant_id)
    print("FIN INTENT RETOUR BUREAU")
     
    return handler_input.response_builder.speak(speech_text).set_should_end_session(end_session).response 
    
#Intent exprimer pour test
@sb.request_handler(can_handle_func= is_intent_name("exprimerIntent"))
def exprimer_intent_handler(handler_input):
    """Handler for exprimerIntent"""
    print("RECEPTION INTENT EXPRIMER")
    
    # Appel au parcours d'intention EXPRIMER
    
    phrases = get_slot_value(handler_input=handler_input, slot_name = "phrases")
    speech_text= "la phrase exprimée est:"+phrases 
    print(phrases)
    print("FIN INTENT EXPRIMER")
    end_session = False

    return handler_input.response_builder.speak(speech_text).set_should_end_session(end_session).response



# Intent Amazon : YES

@sb.request_handler(can_handle_func= is_intent_name("AMAZON.YesIntent"))
def Yes_intent_handler(handler_input):
    """Handler for AMAZON.YesIntent"""
    print("RECEPTION INTENT YES")
    
   #get the user_assistant_id 
    user_assistant_id = handler_input.request_envelope.session.user.user_id

    # Appel au parcours d'intention OUI
    speech_text, end_session = functions.parcours_intention_oui(client_bdd,config.mongodb_db,config.mongodb_collection,'alexa',user_assistant_id)
    print("FIN INTENT YES")

    return handler_input.response_builder.speak(speech_text).set_should_end_session(end_session).response

# Intent Amazon : NO

@sb.request_handler(can_handle_func= is_intent_name("AMAZON.NoIntent"))
def No_intent_handler(handler_input):
    """Handler for AMAZON.NoIntent"""
    print("RECEPTION INTENT NO")
    
     #get the user_assistant_id 
    user_assistant_id = handler_input.request_envelope.session.user.user_id

    # Appel au parcours d'intention NON
    speech_text, end_session = functions.parcours_intention_non(client_bdd,config.mongodb_db,config.mongodb_collection,'alexa',user_assistant_id)
    print("FIN INTENT NO")

    return handler_input.response_builder.speak(speech_text).set_should_end_session(end_session).response


# Intention StopIntent and CancelIntent

@sb.request_handler(
    can_handle_func=lambda handler_input:
        is_intent_name("AMAZON.CancelIntent")(handler_input) or
        is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    """Single handler for Cancel and Stop Intent."""
    # type: (HandlerInput) -> Response
    speech_text = "Au revoir"

    return handler_input.response_builder.speak(speech_text).response

#Intention HelpIntent 

@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    handler_input.response_builder.speak(help_text).ask(help_text)
    return handler_input.response_builder.response  

# Session End
@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    """Handler for Session End."""
    # type: (HandlerInput) -> Response
    return handler_input.response_builder.response 

# Fallback Intent 

@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input):
    """intention pour gérer les intentions non comprises par Alexa.
    """
    # type: (HandlerInput) -> Response
    speech = (
        "{} ne peut pas vous aider pour ça..  ").format(skill_name)
    reprompt = ("Je peux consulter vos messages et renvoyer vos appels")
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response

@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    # type: (HandlerInput, Exception) -> None
    print("Encountered following exception: {}".format(exception))
    #to do: changer le texte
    speech = "il y a un problème"
    handler_input.response_builder.speak(speech).ask(speech)

    return handler_input.response_builder.response

# Handler to be provided in lambda console.
lambda_handler = sb.lambda_handler()

#deploy on Kermit 
app = Flask(__name__)

skill_response = SkillAdapter(
    skill=sb.create(), skill_id = config.skill_id, app=app)

@app.route("/",methods=['GET','POST'])
def invoke_skill():
    return skill_response.dispatch_request()

    #API base de données 
    #GET collection
@app.route("/databases/<db_name>/collections/<db_collection>", methods= ['GET'])
def get_collection_api(db_name,db_collection):
    # API utilisant la connection créée dès le début du programme
    collection = functions.get_collection(client_bdd, db_name, db_collection)
    documents = collection.find()
    response = []
    for document in documents:
        del document['_id']
        response.append(document)
    return json.dumps(response)

#delete collection content
@app.route("/databases/<db_name>/collections/<db_collection>", methods= ['DELETE'])
def delete_collection_api(db_name,db_collection):
    result = functions.remove_data(client_bdd,db_name,db_collection)
    return 'nombre de documents supprimés :' + str(result.deleted_count)

#update collection content
@app.route("/databases/<db_name>/collections/<db_collection>/users/<db_user_id>", methods= ['PUT'])
def update_collection_api(db_name,db_collection,db_user_id):
    user_data = request.json
    print("type de db_user_id",type(db_user_id))
    print("type de user_data['user_id']",type(user_data['user_id']))
    if user_data['user_id']== int(db_user_id):
        user_query = {'user_id':int(db_user_id)}
        new_user_data = {"$set" : user_data}
        result = functions.update_data(client_bdd,db_name,db_collection,user_query,new_user_data)
        return_text = 'profil du user_id :'+ db_user_id + ' modifié.'
    else:
        return_text = 'erreur: modification du user_id interdite'
    return return_text
    
#return the type of platform and info (prod, dev)
@app.route("/environment", methods= ['GET'])
def get_environment():
    print(environment)
    return environment
    
if __name__ =='__main__':
    environment = os.environ.get('environment')
    app.run('0.0.0.0', debug=True)
 



