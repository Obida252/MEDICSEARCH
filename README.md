# Documentation du Projet MedicSearch

Ce dépôt regroupe un ensemble d’outils et d’applications visant à extraire, nettoyer et exploiter des données liées aux médicaments et à leurs effets indésirables. Le projet se décline en plusieurs sous-parties et outils, allant du scraping et traitement de données à une interface web destinée aux utilisateurs finaux (notamment via la page dans le dossier MedicSearch).

## Table des Matières

- [Description Générale](#description-generale)
- [Structure du Projet](#structure-du-projet)
- [Modules et Fonctionnalités](#modules-et-fonctionnalites)
  - [Extraction et Traitement de Données](#extraction-et-traitement-de-donnees)
  - [Scraping de Données](#scraping-de-donnees)
  - [Migration et Transformation des Données](#migration-et-transformation-des-donnees)
  - [Interface Web et Frontend](#interface-web-et-frontend)
- [Utilisation et Exécution](#utilisation-et-execution)
- [Tâches Restantes](#taches-restantes)
- [Contributions](#contributions)
- [Licence](#licence)

## Description Générale

Le projet MedicSearch a pour objectif principal le traitement et la mise en forme de données relatives aux médicaments. Les principales opérations incluent :

- **Extraction et Nettoyage** : Importation de données à partir de fichiers Excel et traitement par différentes fonctions Python.
- **Scraping de Données** : Récupération de contenus depuis des pages web et des documents en utilisant divers scripts Python et PHP.
- **Migrations vers des Bases de Données** : Transfert des données scrappées vers Neo4j et PostgreSQL.
- **Interface Utilisateur** : Interfaces web pour la consultation des données traitées.

## Structure du Projet

Le projet se divise en plusieurs dossiers et fichiers :

- **Racine du projet** : Contient les fichiers principaux et les données d'entrée.
- **Functions/** : Scripts Python pour le scraping, le nettoyage et la migration de données.
- **MedicSearch/** : Interface web principale avec les fichiers PHP.
- **Backup/** : Dossier où les données de sauvegarde doivent être chargées.

## Modules et Fonctionnalités

### Extraction et Traitement de Données

Les fichiers Excel importés sont traités par des scripts Python pour générer des mots-clés et assurer une cohérence des données.

### Scraping de Données

Les scripts Python et PHP permettent de récupérer des données depuis des pages web et de les structurer pour leur intégration.

### Migration et Transformation des Données

Des scripts permettent de migrer les données vers des bases relationnelles (PostgreSQL) et orientées graphe (Neo4j).

### Interface Web et Frontend

L'application web permet aux utilisateurs de naviguer et rechercher des informations sur les médicaments et leurs effets indésirables.

## Utilisation et Exécution

### Lancer l'Application Frontend

1. Configurer un serveur web pour pointer vers `MedicSearch/`.
2. Accéder à l'application via `http://localhost`.

### Exécuter les Scripts de Traitement

```sh
python Functions/nettoyage_liens_R.py
```

### Import dans les Bases de Données

1. Exécuter les scripts de traitement.
2. Lancer `mongodb_to_neo4j.py` ou `mongodb_to_postgresql.py` selon la base de données cible.
3. Utiliser `neo4j_import_script.py` pour vérifier l'importation.

## Tâches Restantes

- **Optimisation du Scraping** : Structurer les données pour une meilleure intégration.
- **Base Vectorielle avec Machine Learning** : Améliorer la recherche grâce à des modèles de langage et de similarité.

### Stratégie de Déploiement

Voici notre stratégie de déploiement adaptée pour le projet MedicSearch :

- **Hébergement Web et API**
  On va utiliser un service d’hébergement cloud managé comme [Azure App Service](https://azure.microsoft.com/fr-fr/services/app-service/) ou [AWS Elastic Beanstalk](https://aws.amazon.com/fr/elasticbeanstalk/). Ces services facilitent le déploiement et la gestion de nos applications web sans nous soucier de la gestion des serveurs.

- **Conteneurisation**
  On envisage d’encapsuler nos applications (scripts Python et PHP) dans des conteneurs Docker. Cela permettra une cohérence entre les environnements de développement et de production. On pourra ensuite déployer ces conteneurs via Azure Kubernetes Service (AKS) ou AWS Elastic Kubernetes Service (EKS) si nécessaire, ou plus simplement via Azure Container Instances ou AWS Fargate pour des charges moins importantes.

- **Bases de données**
  Pour les bases de données, on opte pour des solutions managées :
  - **PostgreSQL** : On va utiliser [Azure Database for PostgreSQL](https://azure.microsoft.com/fr-fr/services/postgresql/) ou Amazon RDS pour PostgreSQL, pour simplifier la gestion des sauvegardes et la scalabilité.
  - **Neo4j** : On va héberger notre instance Neo4j sur un serveur virtuel (VM) ou via une solution managée si disponible, en fonction des budgets et des contraintes du projet.

- **Budget et crédits universitaires**
  On va profiter des crédits étudiants/mooc offerts par Azure et AWS. Ces offres nous permettent d’explorer et de tester ces services sans surcoût important.

- **Sécurité et Scalabilité**
  Même pour un projet universitaire, on prévoit une configuration sécurisée (certificats SSL, mises à jour automatiques, etc.) et une scalabilité horizontale limitée (auto-scaling gratuit dans une certaine mesure) pour supporter des charges importantes occasionnellement.

### Améliorations avec LLM

- **Entraînement du Modèle**
  - **Préparation des Données** : On va structurer les données pour les rendre exploitables par le modèle.
  - **Sélection du Modèle** : On va choisir un modèle adapté à nos besoins de recherche et de similarité.
  - **Génération d'Embeddings** : On va créer des embeddings vectoriels pour améliorer la recherche par similarité.
  - **Implémentation de la Fonctionnalité de Recherche** : On va intégrer cette fonctionnalité dans notre interface utilisateur pour une meilleure expérience de recherche.

- **Bases de Données**
  - **Base Documentaire (MongoDB)** : On va stocker les données structurées et non structurées.
  - **Données Structurées** : On va organiser les données en tables pour faciliter les requêtes.
  - **Base Vectorielle (Qdrant)** : On va utiliser des embeddings vectoriels pour la recherche par similarité.
  - **Base de Données Graphique (Neo4j)** : On va stocker les relations entre les entités pour une meilleure compréhension des données.

En résumé, pour un projet universitaire comme le nôtre, l’utilisation des services managés d’Azure ou d’AWS nous permet de réduire les efforts de gestion de l’infrastructure tout en garantissant une bonne scalabilité et sécurité. La combinaison d’un hébergement web (App Service/Elastic Beanstalk), d’une conteneurisation (Docker) et de bases gérées nous offrira une solution solide et adaptable pour nos besoins de développement et d’expérimentation.

## Contributions

1. Forkez le dépôt.
2. Créez une branche (`git checkout -b feature/ma-fonction`).
3. Commitez vos modifications (`git commit -am 'Ajout d'une fonctionnalité'`).
4. Poussez la branche (`git push origin feature/ma-fonction`).
5. Ouvrez une Pull Request.

## Licence

Ce projet est sous licence [MIT](LICENSE).
