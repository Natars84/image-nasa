import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import json
import sys
import os

urlRequete = "https://images-api.nasa.gov/search?"

#Le dossier créé sera là où se trouve le script
dossierImage = os.getcwd() + "/imageNASA/"

#On tente de créer le dossier d'accueil des documents
try:
	os.mkdir(dossierImage)
except OSError: #Si erreur: il existe déjà
	pass

##########################
#Traitement des arguments#
##########################
critereRecherche = dict()
argumentRecu = dict()
listeCritereRecherche = ['q', 'center', 'description', 'keywords', 'location', 'media_type', 'nasa_id', 'photographer', 'secondary_creator', 'title', 'year_start', 'year_end']

#On récupère les arguments
listeArgument = sys.argv
listeArgument.pop(0) #Suppression du nom du script dans la liste des arguments

#On procède au découpage des arguments en fonction du '='
for argument in listeArgument:
	argumentDecoupe = argument.split('=')

	#Pour chacun des arguments, on vérifie si il y a une correspondance avec l'un
	#des critères de recherche possible
	for critereRecherchePossible in listeCritereRecherche:
		if critereRecherchePossible == argumentDecoupe[0]:
			#Si tel est le cas, on place le critère et sa valeur dans le
			#dictionnaire des critères recus
			critereRecherche[argumentDecoupe[0]] = argumentDecoupe[1]

############################
#Construction de la requete#
############################

#Une fois tous les arguments réceptionnés, on fait les changements necessaires afin
#qu'ils puissent être envoyés dans une requête HTTP
for cle, valeur in critereRecherche.items():
	critereRecherche[cle] = valeur.replace(" ", "%20")

#Une fois terminé, on construit la requête HTTP
for cle, valeur in critereRecherche.items():
	urlRequete = urlRequete + cle + "=" + valeur + "&"

#On supprime le dernier caractère (&) inutilise
urlRequete = urlRequete[0:-1]


###########################
#  Requête et traitement  #
#   des données reçues    #
###########################

# Permet d'exécuter une requête
def envoyerRequeteGET(url):
	try:
		session = requests.Session()
		retry = Retry(connect=3, backoff_factor=0.5)
		adapter = HTTPAdapter(max_retries = retry)
		session.mount('http://', adapter)
		session.mount('https://', adapter)

		reponse = session.get(url)

	except:
		print("La dernière requête envoyée a rencontré une erreur")
		print("Requête: " + url)
		exit()


	statutHTTP = statutRequeteCorrect(reponse)
	if statutHTTP:
		return reponse

	else:
		print("La dernière requête envoyée a rencontré une erreur")
		print("Requête: " + url)
		print("Statut HTTP: " + statutHTTP)
		exit()

# Vérifie que le code de retour HTTP soit correct
def statutRequeteCorrect(reponseRequete):
	if reponseRequete.status_code >= 200 and reponseRequete.status_code <= 399:
		return True
	else:
		return False

# Créé une liste qui associe, pour chaque images, son nasa_id à son lien de téléchargement
def listerInfosImages(json):
	listeImages = []
	items = json["collection"]["items"]

	for image in items:
		nasa_id = image["data"][0]["nasa_id"]
		collection = image["href"]
		lien = extraireLienTelechargementImage(collection)

		listeImages.append([nasa_id, lien])

	return listeImages

# Permet d'obtenir le lien de téléchargement direct d'une image à partir de l'URL de sa collection
def extraireLienTelechargementImage(collectionLink):
	listeLienImages = envoyerRequeteGET(collectionLink).json()

	return listeLienImages[0]


# On récupère les données trouvées par le serveur suivant les critères de recherche fournis
reponse = envoyerRequeteGET(urlRequete)

# On décode les données JSON reçues sous forme de dicrionnaire
donnees = reponse.json()

# Récupération du nombre d'éléments trouvés
nombreOccurence = int(donnees["collection"]["metadata"]["total_hits"])

# On affiche le nmbre de résultats trouvés et on demande à l'utilisateur s'il faut lancer le téléchargement
# La boucle est là pour s'assurer que l'on obtiens une réponse correcte

valeurRecueCorrecte = False
while not valeurRecueCorrecte:

	print(str(nombreOccurence) + " éléments trouvés. Voulez-vous lancer le téléchargement ?")
	print("1: OUI ; 2: NON")
	choix = input("Réponse: ")

	# Une fois que l'utilisateur a fait son choix, on détermine s'il est correcte
	# CàD soit '1', soit '2'

	if choix == '1':
		print("\nOK, lancement du téléchargement")
		valeurRecueCorrecte = True
	elif choix == '2':
		print("\nOK, abandon du téléchargement et fin du programme")
		valeurRecueCorrecte = True
		exit()
	else:
		valeurRecueCorecte = False

		# Si la valeur saisie par l'utilisateur est incorrecte
		if not valeurRecueCorrecte:
			print("\nLa valeur saisie est incorrecte, veuillez réessayer")

#print("Downloooooooooooooooooooooooooooooooooooooooooooooooooooad !!!")

listeImages = listerInfosImages(donnees)

for image in listeImages:
	print(image[0] + " => " + image[1])
