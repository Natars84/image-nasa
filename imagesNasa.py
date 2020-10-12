import requests
import json
import sys
import os

urlAPI_NASA = "https://images-api.nasa.gov/search?"
urlRequete = urlAPI_NASA

dossierImage = "/home/pi/imageNASA/"

#On tente de creer le dossier d'accueil des documents
try:
	os.mkdir(dossierImage)
except OSError: #Si erreur: il existe deja
	pass

##########################
#Traitement des arguments#
##########################
critereRecherche = dict()
argumentRecu = dict()
listeCritereRecherche = ['q', 'center', 'description', 'keywords', 'location', 'media_type', 'nasa_id', 'photographer', 'secondary_creator', 'title', 'year_start', 'year_end']

#On recupere les arguments
listeArgument = sys.argv
listeArgument.pop(0) #Suppression du nom du script dans la liste des arguments

#On procede au decoupage des arguments en fonction du '='
for argument in listeArgument:
	argumentDecoupe = argument.split('=')

	#Pour chacun des arguments, on verifie si il y a une correspondance avec l'un
	#des criteres de recherche possible
	for critereRecherchePossible in listeCritereRecherche:
		if critereRecherchePossible == argumentDecoupe[0]:
			#Si tel est le cas, on place le critere et sa valeur dans le
			#dictionnaire des criteres recus
			critereRecherche[argumentDecoupe[0]] = argumentDecoupe[1]

############################
#Construction de la requete#
############################

#Une fois tous les arguments receptionnes, on fait les changements necessaires afin
#qu'ils puissent etre envoyes dans une requete HTTP
for cle, valeur in critereRecherche.items():
	critereRecherche[cle] = valeur.replace(" ", "%20")

#Une fois termine, on construit la requete HTTP
for cle, valeur in critereRecherche.items():
	urlRequete = urlRequete + cle + "=" + valeur + "&"

#On supprime le dernier caractere (&) inutilise
urlRequete = urlRequete[0:-1]


############################
#Recuperation et traitement#
#   du fichier JSON recu   #
############################

#La fonction extrait dans le fichier JSON le nombre TOTAL de documents trouves
def nombreResultatTrouve(resultatRequeteGET):
        json = resultatRequeteGET.json()

	#On extrait le nombre de resultats trouves par le site web
        return json["collection"]["metadata"]["total_hits"]

#La fonction extrait du fichier JSON les liens vers le "sous fichier" JSON contenant
#un ou plusieurs liens (en fonction du type de doucument) vers le document
def extraireLienVersCollectionJSON(fichierJSON):
	lienFichierCollectionJSON = []

	#On recupere les resultats sous forme de fichier JSON
	items = fichierJSON["collection"]["items"]

	#On determine le nombre de resultats presents dans le fichier JSON
	nombreResultatATraiter = len(items)

	#Pour chacun des resultat, on extrait l'URL du fichier "collection.json"
	for numeroResultat in range(nombreResultatATraiter):
		lienFichierCollectionJSON.append(items[numeroResultat]["href"])

	#Une fois le fichier traite, on renvoie la liste generee
	return lienFichierCollectionJSON

#On decoupe la chaine en fonction du . et recupere l'extension
def extensionFichierURL(urlFichierDistant):
	chaineDecoupe = urlFichierDistant.split('.')
	extensionFichier = chaineDecoupe[len(chaineDecoupe) - 1]

	return str(extensionFichier)

def telechargerDocument(lienATraiter, nomFichier):

	#On verifie que chaque lien est accessible puis on le telecharge
	reponse = requests.get(lienATraiter)
	if reponse.status_code == 200:
		nomFichier = dossierImage + str(nomFichier) + "." + extensionFichierURL(lienATraiter)
		with open(nomFichier, "wb") as file:
			file.write(reponse.content)
			return 1
	else:
		return 0

#On envoie la requete et recupere les resultats
reponseServeur = requests.get(urlRequete)

if reponseServeur.status_code >= 400 and reponseServeur.status_code < 500:
	sys.exit('Erreur de requete')
elif reponseServeur.status_code >= 500:
	sys.exit('Erreur au niveau du serveur, veuillez reessayer ulterieurement')
else:
	pass

#On verifie si on a trouve quelque chose
nombreResultat = nombreResultatTrouve(reponseServeur)
if nombreResultat == 0:
	sys.exit('Aucun resultat trouve')
else:
	print nombreResultat, ' documents trouves'

print 'Debut du telechargement'

#Si on a des resultats, alors on recupere les liens vers les "sous-fichiers" JSON
#contenant le lien direct vers le document sous un ou plusieurs formats.
#Le premier lien est le document original (entre autres pour les images)
nombreDocumentATelecharger = nombreResultat
numeroPage = 1

urlRequete = urlRequete + '&page='

while nombreDocumentATelecharger > 0:
	#On fait une nouvelle requete en indiquant la page de resultat
	#sur laquelle travailler
	reponseServeur = requests.get(urlRequete + str(numeroPage))

	for lienFichierCollectionJSON in extraireLienVersCollectionJSON(reponseServeur.json()):
		#On recupere le fichier collection.json
		reponseServeur = requests.get(lienFichierCollectionJSON)

		#On extrait le 1er lien du fichier (document original)
		json = reponseServeur.json()
		lienATelecharger = json[0]
		nomFichierATelecharger = (nombreResultat - nombreDocumentATelecharger) + 1

		#On telecharge le fichier et on indique le resultat du telechargement
		telechargementReussi = telechargerDocument(lienATelecharger, nomFichierATelecharger)
		if telechargementReussi:
			print 'Document ', nomFichierATelecharger, ': OK'
		else:
			print 'Document ', nomFichierATelecharger, ': echec'

		nombreDocumentATelecharger -= 1

	numeroPage += 1
