# language : fr

Fonctionnalité: Test accés GLPI
	Afin d'être en mesure d'utiliser l'outil de gestion d'inventaire et de support GLPI, je dois être en mesure de m'authentifier, d'afficher mon tableau de bord puis de me déconnecter.
Scénario: Accès à GLPI
	Soit l'utilisation d'un navigateur
	Quand je navigue vers "http://demo.glpi-project.org"
	Alors je devrais voir le texte "Authentication" en moins de "5" secondes

Scénario: Authentification
	Soit le formulaire d'authentification
	Quand je saisis "admin" dans le champ "login_name"
	Quand je saisis le mot de passe "admin" dans le champ "login_password"
	Quand je clique sur le bouton "Post"
	Alors je devrais voir le texte "Tickets à traiter" en moins de "5" secondes

Scénario: Déconnexion
	Soit l'écran vue personnelle
	Quand je clique sur le lien "Déconnexion"
	Alors je devrais voir le texte "Authentication" en moins de "4" secondes