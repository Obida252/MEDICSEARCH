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
- [Améliorations Futures](#ameliorations-futures)
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
- **Assets/** : Ressources et fichiers de support.
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

## Améliorations Futures

- **Optimisation du Scraping** : Structurer les données pour une meilleure intégration.
- **Base Vectorielle avec Machine Learning** : Améliorer la recherche grâce à des modèles de langage et de similarité.

## Contributions

1. Forkez le dépôt.
2. Créez une branche (`git checkout -b feature/ma-fonction`).
3. Commitez vos modifications (`git commit -am 'Ajout d'une fonctionnalité'`).
4. Poussez la branche (`git push origin feature/ma-fonction`).
5. Ouvrez une Pull Request.

## Licence

Ce projet est sous licence [MIT](LICENSE).
