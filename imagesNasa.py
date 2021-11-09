import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import time
import json
import sys
import os

#URL de base, sur laquelle on va venir greffer les critères de recherches
urlRequete = "https://images-api.nasa.gov/search?media_type=image&"

#Limite horaire maximale du nombre de requêtes envoyées par le script
limiteRequeteParHeure = 1000

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
listeCritereRecherche = ['q', 'center', 'description', 'keywords', 'location', 'nasa_id', 'photographer', 'secondary_creator', 'title', 'year_start', 'year_end']

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

# Permet de télécharer le fichier derrière l'URL spécifié à l'emplacement et avec le nom spécifié (chemin relatif)
def telechargerFichier(url, cheminRelatif):
	#Téléchargement du contenu du fichier
	contenuFichier = envoyerRequeteGET(url)

	#Écriture du contenu téléchargé dans le fichier
	fichier = open(cheminRelatif, 'wb')
	fichier.write(contenuFichier.content)
	fichier.close()

# Permet d'exécuter une requête
def envoyerRequeteGET(url):
	try:
		session = requests.Session()
		retry = Retry(connect=3, backoff_factor=0.5)
		adapter = HTTPAdapter(max_retries = retry)
		session.mount('http://', adapter)
		session.mount('https://', adapter)

		reponse = session.get(url)
		time.sleep(round(3600/limiteRequeteParHeure, 3))

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
		print("Statut HTTP: " + str(statutHTTP))
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

# Renvoie l'extension du fichier désigné via son URL
def extraireExtensionFichierURL(url):
	chaineDecoupe = url.split('.')
	extensionFichier = chaineDecoupe[len(chaineDecoupe) - 1]

	return str(extensionFichier)

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


# On parcours toutes les pages de résultats afin de récupérer les
# infos et le lien de téléchargement direct de chacune des images
telechargerLienPageSuivante = True
listeImagesGeneral = []
pageEnCours = 0
while telechargerLienPageSuivante:

	pageEnCours += 1
	print("Récupération des URLs (page " + str(pageEnCours) + ")", end='\r')

	#On récupère les infos des images de la page en cours,
	listeImagesPage = listerInfosImages(donnees)

	#Puis on les rajoutes au listing général
	listeImagesGeneral += listeImagesPage

	#On regarde ensuite s'il y a une autre page à traiter
	tailleTableauLienPage = len(donnees["collection"]["links"])
	actionLienPage = donnees["collection"]["links"][tailleTableauLienPage - 1]["rel"]

	#Si c'est le cas, on récupères les données de la page suivante, et on reboucle
	if actionLienPage == "next":
		donnees = envoyerRequeteGET(donnees["collection"]["links"][tailleTableauLienPage -1]["href"])
		donnees = donnees.json()

	#Sinon, on sort de la boucle
	elif actionLienPage == "prev":
		telechargerLienPageSuivante = False

print()

#Une fois que l'on a tout les résultats, on les traites
nombreImageTelecharge = 0
for image in listeImagesGeneral:
	nombreImageTelecharge += 1
	print("Téléchargement des images: " + str(nombreImageTelecharge) + "/" + str(nombreOccurence), end='\r')

	extensionFichier = extraireExtensionFichierURL(image[1])
	telechargerFichier(image[1], dossierImage + image[0] + '.' + extensionFichier)

print()
