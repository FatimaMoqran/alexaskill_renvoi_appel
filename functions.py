# -*- coding: utf-8 -*-

#import pymongo for working with mongodb
from pymongo import MongoClient


# Données de tests
mobile_renvoi_ko = "0666666666" # Test "si je dis ce numéro, la mise en place du renvoi sera KO" 
mobile_annulation_renvoi_ko = "0677777777" # Test "si je dis ce numéro, l'annulation du renvoi sera KO" 


#database functions
# connect à la base de donnée
def connect_bdd(db_uri):
    client = MongoClient(db_uri)
    return client 

#get collection with database client
def get_collection(db_client,db_name,db_collection):
    database = db_client[db_name]
    collection = database[db_collection]
    return collection

#insert data : permet de créer un user dans la bdd
def insert_bdd(db_client,db_name,db_collection ,data):
    database = db_client[db_name]
    collection = database[db_collection]
    collection.insert_one(data)
    return 

#remove data : supprime toutes les données pour une collection 
def remove_data( db_client,db_name, db_collection):
    database = db_client[db_name]
    collection = database[db_collection]
    remove = collection.delete_many({})
    return remove

#update data : update toute ou une partie du user_data 
def update_data(db_client, db_name, db_collection,db_query,new_data):
    database = db_client[db_name]
    collection = database[db_collection]
    update = collection.update_one(db_query,new_data, upsert = True )
    return update

#recuperer les données de l'utilisateur et les créer si besoin    
def get_user(db_client,db_name,db_collection,assistant_type,user_assistant_id):
    user_data = {}
    collection = get_collection(db_client = db_client,db_name=db_name,db_collection=db_collection)
    if assistant_type == "alexa":      
        user_query = {'profile.alexa_id':user_assistant_id }
        user_data = collection.find_one(user_query)
        if user_data == None:
            #determiner le user_id utilisé pour ce nouveau user
            last_user_id = collection.find_one({'user_id':{"$exists":True}},projection = {'user_id':1,"_id":0},sort = [("user_id",-1)])
            if last_user_id == None:
                user_id = 1
            else :
                user_id = last_user_id['user_id'] + 1
            user_data = {
                'user_id': user_id,
                'user_name': 'None', #user_name au format prenom.nom
                #profile : les données permanentes du user
                'profile':{ 
                    'alexa_id': user_assistant_id, #id user chez Amazon
                    'medias':{} #ensemble des médias du user 
                },
                #services : Etat des services du user
                'services':{
                    #redirect:indique si un renvoi est actif et si oui vers quel numéro 
                    'redirect':{
                        'status':'None', #peut prendre les valeurs 'None' 'ok 'ko
                        'number':'None' #contient le numéro si le renvoi est actif sinon est à None
                        }
                },
                #session :  Etat du user et de ses infos en cours de session
                'session':{
                    'dialog_status':'None', #contient le status du dialogue
                    'phonenumber':'None', #numero de téléphone indiqué par le user lors du dialogue
                    'phonename':'None'#nom de téléphone indiqué par le user lors du dialogue
                    }
                }
            collection.insert_one(user_data)
    return user_data 

#services functions

def launch_skill(client_bdd,mongodb_db,mongodb_collection,assistant_type,user_assistant_id):
    """ lancement du skill
        input:
            client_bdd : client connection à la base de donnée
            assistant_type: str contient le type de technologie utilisé
            user_assistant_id : str, contient l'identifiant du user pour le type de technologie utilisé 
        output:
            speech_text : texte prononcé par l'assistant
            reprompt_text: texte prononcé en cas de reprompt
    """
    #get the user_data
    print("START FUNCTION: launch skill")
    user_data = get_user(client_bdd,mongodb_db,mongodb_collection,assistant_type,user_assistant_id)
    print('user data :\n', user_data)

    #réinitialisation des données de session
    user_data['session']= {'dialog_status':'None','phonenumber':'None', 'phonename':'None'}

    # sauvegarde dans la base de donnée
    print("user_data suite à la réinitialisation\n", user_data)
    user_query = {'profile.alexa_id':user_assistant_id }

    #ajoute une variable new_user_data pour enregistrer les nouvelles données du user dans la base de donnée
    new_user_data = {"$set" : user_data}
    update_data(client_bdd,mongodb_db,mongodb_collection,user_query,new_user_data)

    speech_text = "Bienvenue chez tel pro dev  que puis-je faire pour vous? "
    reprompt_text = "je peux renvoyer vos appels et consulter votre messagerie. Que puis je faire pour vous?"
    
    print('END FUNCTION: launch skill')
    return speech_text, reprompt_text

def parcours_activer_renvoi_appel(client_bdd,mongodb_db, mongodb_collection,assistant_type,user_assistant_id ,phonename,phonenumber):
    """ activation du renvoi d'appel
        input:
            client_bdd : client connection à la base de donnée
            assistant_type: str contient le type de technologie utilisé
            user_assistant_id: str, contient l'identifiant du user pour le type de technologie utilisé
            phonename: str , le nom de téléphone récupéré par l'assistant
            phonenumber : str, le numero de téléphone récupéré par l'assistant
    """
    # Ce parcours vérifie si il y a un numéro de téléphone ou un nom de téléphone dans la requête
	# Si oui => on demande la confirmation ou si il faut stocker
	# Si non => on demande de fournir un numéro ou un nom de téléphonefun
    print('START FUNCTION: parcours_activer_renvoi_appel')
    #recupération du user_data
    user_data = get_user(client_bdd, mongodb_db, mongodb_collection,assistant_type,user_assistant_id)
    print('user data :\n', user_data)
    
    if  phonenumber:
        #stocker le numero telephone
        user_data['session']['phonenumber'] = phonenumber
        
        #vérifie si on a un téléphone associé au data  de l'utilisateur
        if phonenumber in user_data['profile']['medias'].values():
            speech_text = "Confirmez-vous le renvoi de vos appels fixe vers le {}".format(phonenumber)
            status="Activer_Renvoi_Appel-Demande_Renvoi_Confirmation" 
        #si on vient du status "Activer_Renvoi_Appel-Nom_Telephone_Inconnu"
        elif user_data['session']['dialog_status']== "Activer_Renvoi_Appel-Nom_Telephone_Inconnu":
             profile_phonename = user_data['session']['phonename']
             user_data['profile']['medias'][profile_phonename] = phonenumber
             speech_text = "Confirmez-vous le renvoi de vos appels fixe vers le {}".format(phonenumber)
             status = "Activer_Renvoi_Appel-Demande_Renvoi_Confirmation" 

        else :
            speech_text = "S'agit-il de votre numéro de mobile et souhaitez vous le stocker?"
            status="Activer_Renvoi_Appel-Demande_Stockage_Confirmation"
            
    elif phonename:
        #stocker le nom du telephone
        user_data['session']['phonename']= phonename

        #vérifie si le nom du téléphone fait partie des médias du user
        if phonename in user_data['profile']['medias'].keys():
            speech_text = "Confirmez vous le renvoi de vos appels fixes vers le {}?".format(user_data['profile']['medias'][phonename])
            status="Activer_Renvoi_Appel-Demande_Renvoi_Confirmation" 
        else:
            speech_text= "Je ne connais pas le numéro de votre {}. Merci de me l'indiquer".format(phonename)
            status="Activer_Renvoi_Appel-Nom_Telephone_Inconnu"
            

    else: 
        speech_text = "vers quel numéro voulez vous renvoyer vos appels?"
        status="Activer_Renvoi_Appel-Pas_Numero_Ou_Nom"
    
    # enregistre le dialog_status dans user_data 
    user_data['session']['dialog_status']=status 
    print('user data :\n', user_data)
    # sauvegarde dans la base de donnée
    user_query = {'profile.alexa_id':user_assistant_id}
    #ajoute une variable new_user_data pour enregistrer les nouvelles données du user dans la base de donnée
    new_user_data = {"$set" : user_data}
    update_data(client_bdd,mongodb_db,mongodb_collection,user_query,new_user_data)
    print('END FUNCTION: parcours_activer_renvoi_appel')

    return speech_text
    
def parcours_quitter_bureau(client_bdd,mongodb_db, mongodb_collection,assistant_type,user_assistant_id):
    """ intention quitter bureau
        input:
            client_bdd : client connection à la base de donnée
            assistant_type: str contient le type de technologie utilisé
            user_assistant_id  : str, contient l'identifiant du user pour le type de technologie utilisé
    """
    print('START FUNCTION: parcours_quitter_bureau')

    #recupération du user_data
    user_data = get_user(client_bdd, mongodb_db, mongodb_collection,assistant_type,user_assistant_id)
    print('user data :\n', user_data)

    #traitement
    speech_text = "Voulez vous renvoyer vos appels?"

    # enregistre le dialog_status dans user_data 
    user_data['session']['dialog_status']="Quitter_Bureau-Demande_Renvoi" 
    print('user data :\n', user_data)
    # sauvegarde dans la base de donnée
    user_query = {'profile.alexa_id':user_assistant_id }
    #ajoute une variable new_user_data pour enregistrer les nouvelles données du user dans la base de donnée
    new_user_data = {"$set" : user_data}
    update_data(client_bdd,mongodb_db,mongodb_collection,user_query,new_user_data)
    print('END FUNCTION: parcours_activer_quitter_bureau')

    return speech_text

def parcours_annulation_renvoi_d_appel(client_bdd,mongodb_db, mongodb_collection,assistant_type,user_assistant_id):
    """ intention annulation renvoi d'appel
        input:
            client_bdd : client connection à la base de donnée
            assistant_type: str contient le type de technologie utilisé
            user_assistant_id  : str, contient l'identifiant du user pour le type de technologie utilisé
    """
    print('START FUNCTION: parcours_annulation_renvoi_d_appel')

    #recupération du user_data
    user_data = get_user(client_bdd, mongodb_db, mongodb_collection,assistant_type,user_assistant_id)
    print('user data :\n', user_data)
    

    #traitement
    end_session = False
    if user_data['services']['redirect']['status'] == 'OK':
        speech_text = "Confirmez vous l'annulation du renvoi de vos appels fixe vers le {}?".format(user_data['services']['redirect']['number'])
        status = "Annulation_renvoi_d'appels-Demande_Confirmation"
    else : 
        speech_text = "Vos appels ne sont pas renvoyés actuellement."
        status = "Annulation_renvoi_d'appels-Renvoi_non_Actif"
        end_session = True

     # enregistre le dialog_status dans user_data 
    user_data['session']['dialog_status']= status 
    print('user data :\n', user_data)
    # sauvegarde dans la base de donnée
    user_query = {'profile.alexa_id':user_assistant_id }
    #ajoute une variable new_user_data pour enregistrer les nouvelles données du user dans la base de donnée
    new_user_data = {"$set" : user_data}
    update_data(client_bdd,mongodb_db,mongodb_collection,user_query,new_user_data)
    print('END FUNCTION: parcours_annulation_renvoi_d_appel')

    return speech_text , end_session 

def parcours_retour_bureau(client_bdd,assistant_type,user_assistant_id ):
    """ intention retour_bureau
        input:
            client_bdd : client connection à la base de donnée
            assistant_type: str contient le type de technologie utilisé
            user_assistant_id  : str, contient l'identifiant du user pour le type de technologie utilisé
    """
    print('START FUNCTION: parcours_retour_bureau')

    #recupération du user_data
    user_data = get_user(client_bdd, mongodb_db, mongodb_collection,assistant_type,user_assistant_id)
    print('user data :\n', user_data)

    #traitement
    end_session = False
    if user_data['services']['redirect']['status'] == 'OK':
        speech_text = "Vous avez un renvoi actif. Voulez vous annuler le renvoi de vos appels vers le {}".format(user_data['services']['redirect']['number'])
        status = "De_retour-Renvoi_actif"
    else :
        speech_text = "Bienvenue!"
        status = "De_retour-Renvoi_non_actif"
        end_session = True

    # enregistre le dialog_status dans user_data 
    user_data['session']['dialog_status']= status 
    print('user data :\n', user_data)
    # sauvegarde dans la base de donnée
    user_query = {'profile.alexa_id':user_assistant_id }
    #ajoute une variable new_user_data pour enregistrer les nouvelles données du user dans la base de donnée
    new_user_data = {"$set" : user_data}
    update_data(client_bdd,mongodb_db,mongodb_collection,user_query,new_user_data)
    print('END FUNCTION: parcours_de_retour')

    return speech_text , end_session 

def parcours_intention_oui(client_bdd,mongodb_db, mongodb_collection,assistant_type,user_assistant_id):
    """ intention oui
        input:
            client_bdd : client connection à la base de donnée
            assistant_type: str contient le type de technologie utilisé
            user_assistant_id: str, contient l'identifiant du user pour le type de technologie utilisé
    """
    print('START FUNCTION: intention_oui')

    #recupération du user_data
    user_data = get_user(client_bdd, mongodb_db, mongodb_collection, assistant_type,user_assistant_id)
    print('user data :\n', user_data)

    #traitement
    end_session = False 
    
	# Si on vient de l'intention Activer_Renvoi_Appel
    if user_data['session']['dialog_status'] == "Activer_Renvoi_Appel-Demande_Renvoi_Confirmation" :
        # Test du KO de la mise en place du renvoi
        if user_data['session']['phonenumber']== mobile_renvoi_ko:
            speech_text = "Un problème est survenu. Vous pouvez renvoyer vos appels en composant étoile 21 étoile depuis votre téléphone fixe suivi des 10 chiffres du numéro vers lequel vous souhaitez renvoyer vos appels suivi de la touche #"
            status = 'Activer_Renvoi_Appel-Renvoi_KO'
            redirect_status = 'KO'
        elif user_data['session']['phonename'] != 'None':
            user_data_phonename = user_data['session']['phonename']
            speech_text = "Le renvoi est activé. Vos appels fixe sont redirigés vers votre {} au {}".format(user_data['profile']['medias'][user_data_phonename], user_data_phonename)
            status = 'Activer_Renvoi_Appel-Renvoi_OK'
            redirect_status = 'OK'
            user_data['services']['redirect']= {'status':redirect_status,'number':user_data['profile']['medias'][user_data_phonename]}
        else: #on a donné un numéro de téléphone
            speech_text = "le renvoi est activé. Vos appels fixe sont redirigés vers le {}".format(user_data['session']['phonenumber'])
            status = 'Activer_Renvoi_Appel-Renvoi_OK'
            redirect_status = 'OK'
            user_data['services']['redirect']= {'status':redirect_status, 'number':user_data['session']['phonenumber']}
        end_session = True
        

    elif user_data["session"]["dialog_status"] == "Activer_Renvoi_Appel-Demande_Stockage_Confirmation":

        user_data['profile']['medias']['mobile']= user_data['session']['phonenumber'] #la variable phonenumber enregistré au début dans user_data['session'] est maintenant enregistré dans "phonenumbers"
        speech_text = "Confirmez vous le renvoi de vos appels fixes vers le {}?".format(user_data['profile']['medias']['mobile'])
        status="Activer_Renvoi_Appel-Demande_Renvoi_Confirmation"
        
    # Si on vient de l'intention Quitter_Bureau			
    elif user_data['session']['dialog_status' ]== "Quitter_Bureau-Demande_Renvoi":
        speech_text = "Très bien vers quel numéro dois-je renvoyer les appels?"
        status = 'Activer_Renvoi_Appel-Pas_Numero_Ou_Nom'

    #si on vient de l'intention annulation_renvoi_d_appel
    elif user_data['session']['dialog_status'] == "Annulation_renvoi_d'appels-Demande_Confirmation":
        #test du ko du renvoi d appel
        if user_data['services']['redirect']['number'] == mobile_annulation_renvoi_ko:
            speech_text = "Un problème est survenu. Vous pouvez annuler le renvoi d'appels en composant le dièse 21 dièse."
            status = "Annulation_renvoi_d_appels-Annulation_KO"
            
        else:
            speech_text = "Vos appels sont à nouveau redirigés vers votre ligne fixe"
            status = "Annulation_renvoi_d_appels-Annulation_Confirmée"
            user_data['services']['redirect']= {'status':'None', 'number':'None'}
        end_session = True

    #si on vient de l'intention retour bureau
    elif user_data['session']['dialog_status'] == "Retour_bureau-Renvoi_actif":
        speech_text = "Vos appels sont à nouveau redirigés vers votre ligne fixe"
        status = "Annulation_renvoi_d_appels-Annulation_Confirmée"
        user_data['services']['redirect']= {'status':'None', 'number':'None'}
        end_session = True
    else:
        speech_text = "Je ne sais pas gérer cette situation."
        status = user_data['session']['dialog_status']
        end_session = True

    
    # enregistre le dialog_status dans user_data 
    user_data['session']['dialog_status']= status 
    print('user data :\n', user_data)
    # sauvegarde dans la base de donnée
    user_query = {'profile.alexa_id':user_assistant_id }
    #ajoute une variable new_user_data pour enregistrer les nouvelles données du user dans la base de donnée
    new_user_data = {"$set" : user_data}
    update_data(client_bdd,mongodb_db,mongodb_collection,user_query,new_user_data)
    print('END FUNCTION: parcours_intention_oui')

    return speech_text,end_session

def parcours_intention_non(client_bdd,mongodb_db,mongodb_collection,assistant_type,user_assistant_id):
    """ intention non
        input:
            client_bdd : client connection à la base de donnée
            assistant_type: str contient le type de technologie utilisé
            user_assistant_id  : str, contient l'identifiant du user pour le type de technologie utilisé
    """
    print('START FUNCTION: intention_non')

    #recupération du user_data
    user_data = get_user(client_bdd,mongodb_db,mongodb_collection,assistant_type,user_assistant_id)
    print('user data :\n', user_data)

    #traitement
    end_session = False 

	# Si on vient de l'intention Activer_Renvoi_Appel
    if user_data['session']['dialog_status']== "Activer_Renvoi_Appel-Demande_Renvoi_Confirmation":
        speech_text = "Au revoir."
        end_session = True

    elif user_data['session']['dialog_status']== "Activer_Renvoi_Appel-Demande_Stockage_Confirmation":
        speech_text = "Confirmez-vous le renvoi de vos appels fixe vers le {}".format(user_data['session']['phonenumber'])
        user_data['session']['dialog_status']= "Activer_Renvoi_Appel-Demande_Renvoi_Confirmation"
		
    # Si on vient de l'intention Quitter_Bureau			
    elif user_data['session']['dialog_status']== "Quitter_Bureau-Demande_Renvoi":
        speech_text = "Au revoir."
        end_session = True 
    # Si on vient de l'intention Annulation renvoi d 'appel
    elif user_data['session']['dialog_status'] == "Annulation_renvoi_d'appels-Demande_Confirmation":
        speech_text = "Au revoir."
        end_session = True
    # Si on vient de l'intention Retour bureau
    elif user_data['session']['dialog_status'] == "Retour_bureau-Renvoi_actif":
        speech_text = "Au revoir"
        end_session = True
    else:
        speech_text = "Je ne sais pas gérer cette situation"

    # enregistre le dialog_status dans user_data 
    #user_data['session']['dialog_status']= status 
    print('user data :\n', user_data)
    # sauvegarde dans la base de donnée
    user_query = {'profile.alexa_id':user_assistant_id }
    #ajoute une variable new_user_data pour enregistrer les nouvelles données du user dans la base de donnée
    new_user_data = {"$set" : user_data}
    update_data(client_bdd,mongodb_db,mongodb_collection,user_query,new_user_data)
    print('END FUNCTION: parcours_intention_non')

    return speech_text,end_session