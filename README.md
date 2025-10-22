🐷 Simulateur de Gestion des Salles en Élevage Porcin
Application interactive de simulation et visualisation de l'occupation des salles dans un élevage porcin en conduite en bandes.
📋 Table des matières

Description
Fonctionnalités
Installation
Utilisation
Concepts clés
Paramètres
Dimensionnement optimal
Interprétation des résultats
📖 Description
Cette application permet de simuler et visualiser l'occupation des différentes salles d'un élevage porcin organisé en conduite en bandes. Elle calcule automatiquement :

Les dates d'entrée et de sortie de chaque bande dans chaque type de salle
L'affectation optimale des salles selon une logique opportuniste
Les périodes de vide sanitaire
Les potentiels conflits (manque de salles) ou surdimensionnements (trop de salles)
Le dimensionnement optimal du nombre de salles nécessaires

L'application couvre l'ensemble du cycle de production :

Circuit truies : Attente Saillie → Gestante → Maternité
Circuit produits : Post-Sevrage → Engraissement


✨ Fonctionnalités
🎯 Visualisation en temps réel

Jauges interactives montrant l'état actuel de chaque salle
Affichage du pourcentage de progression pour les salles occupées
Suivi du vide sanitaire en cours (jours écoulés / jours restants)
Indicateur de disponibilité des salles

📊 Diagnostic automatique

Détection des conflits : bandes ne trouvant pas de salle disponible
Détection des surdimensionnements : plusieurs salles vides simultanément (en régime de croisière)
Calcul automatique du dimensionnement optimal selon vos paramètres
Statistiques sur les vides sanitaires

🔧 Paramétrage flexible

Modification de tous les paramètres de conduite
Calcul dynamique selon le nombre de bandes, l'intervalle et le vide sanitaire
Adaptation aux durées d'occupation spécifiques de votre élevage


🚀 Installation
Prérequis

Python 3.8 ou supérieur
pip (gestionnaire de paquets Python)

Installation des dépendances
bashpip install streamlit pandas plotly
Lancement de l'application
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

---

## 💡 Utilisation

### 1. Configuration de base

Dans la **barre latérale gauche**, configurez les paramètres fondamentaux :

#### Paramètres généraux
- **Vide sanitaire** : Durée obligatoire de nettoyage entre deux bandes (0-14 jours)
- **Nombre de bandes** : Nombre total de bandes en rotation (ex: 7 bandes)
- **Intervalle entre bandes** : Jours séparant l'entrée de deux bandes successives (ex: 21 jours)
- **Date de saillie Bande 1** : Point de référence temporel

#### Circuit Truies
- **Jours avant saillie en AS** : Temps d'attente du retour en chaleur (généralement 5 jours)
- **Attente Saillie (total)** : Durée totale en salle AS (incluant avant et après saillie)
- **Gestante** : Durée en salle de gestation
- **Maternité** : Durée d'allaitement

**⚠️ Contrainte physiologique** : AS + Gestante + Maternité = **147 jours** (cycle complet)

#### Circuit Produits
- **Post-Sevrage** : Durée après sevrage
- **Engraissement** : Durée jusqu'à l'abattage

**⚠️ Contrainte recommandée** : PS + Engraissement ≤ **152 jours**

### 2. Dimensionnement optimal

Le simulateur calcule automatiquement le **nombre optimal de salles** nécessaires selon la formule :
```
Nb_salles_optimal = ⌈(Durée + Vide_sanitaire) / Intervalle⌉
```

Ce calcul est affiché dans la sidebar sous "📊 Dimensionnement optimal".

### 3. Configuration du nombre de salles

Saisissez le nombre de salles **réellement disponibles** dans votre élevage pour chaque type.

💡 **Astuce** : L'application propose par défaut le dimensionnement optimal calculé. Si vous saisissez un nombre différent, le diagnostic vous indiquera s'il y a conflit ou surdimensionnement.

### 4. Lecture des résultats

#### États des salles (jauges)

- 🎯 **Jauge colorée** : Salle occupée par une bande (la couleur identifie la bande)
- 🧹 **Jauge grise** : Vide sanitaire en cours (progression affichée)
- ✅ **Jauge verte** : Salle disponible et prête à accueillir la prochaine bande

#### Diagnostic global

Trois indicateurs principaux :

1. **Conflits** 🔴
   - ⚠️ Alerte si une ou plusieurs bandes n'ont pas trouvé de salle disponible
   - → **Action** : Augmenter le nombre de salles du type concerné

2. **Surdimensionnement** 🟠
   - ⚠️ Alerte si plusieurs salles du même type sont vides simultanément (après la phase de démarrage)
   - → **Action** : Réduire le nombre de salles du type concerné

3. **État actuel** ℹ️
   - Nombre de salles en vide sanitaire ou disponibles

---

## 🧠 Concepts clés

### Conduite en bandes

Organisation de l'élevage où les animaux sont regroupés en **bandes** qui progressent de manière synchronisée à travers les différents stades de production.

**Avantages** :
- Gestion sanitaire optimisée (tout plein / tout vide)
- Planification facilitée
- Homogénéité des lots

### Cycle de 147 jours

Le cycle physiologique d'une truie reproductrice :
- **J0-J5** : Retour en chaleur après sevrage
- **J5** : Saillie / Insémination
- **J5-J119** : Gestation (114 jours)
- **J119-J147** : Allaitement (28 jours, variable selon conduite)

### Vide sanitaire

Période obligatoire de nettoyage et désinfection d'une salle entre deux bandes successives.

**Durée recommandée** : 7 jours minimum

**Impact sur le dimensionnement** : Plus le vide est long, plus il faut de salles.

### Affectation opportuniste

Logique d'affectation des salles :
1. Chaque bande prend **la première salle disponible** (vide sanitaire terminé)
2. Si plusieurs salles disponibles, prend celle **libérée le plus tôt** (pour rotation équilibrée)
3. En régime de croisière optimal : **exactement 1 salle vide** à chaque instant pour un type donné

### Phase de démarrage vs Régime de croisière

- **Phase de démarrage** : Période initiale où toutes les salles n'ont pas encore été utilisées au moins une fois
- **Régime de croisière** : Une fois que toutes les salles ont été utilisées, la rotation s'établit durablement

Les diagnostics de surdimensionnement ne sont pertinents qu'en **régime de croisière**.

---

## ⚙️ Paramètres

### Paramètres de conduite recommandés

#### Conduite 7 bandes / 21 jours

**Exemple avec 2 AS, 4 Gestante, 2 Maternité, 2 PS, 6 Engraissement :**
```
Vide sanitaire : 7 jours
Nombre de bandes : 7
Intervalle : 21 jours

Jours avant saillie : 5 jours
Attente Saillie : 35 jours
Gestante : 77 jours
Maternité : 35 jours

Post-Sevrage : 35 jours
Engraissement : 119 jours
```

#### Conduite 5 bandes / 14 jours (sevrage précoce)
```
Vide sanitaire : 7 jours
Nombre de bandes : 5
Intervalle : 14 jours

Jours avant saillie : 5 jours
Attente Saillie : 30 jours
Gestante : 82 jours
Maternité : 35 jours (dont 21j allaitement)

Post-Sevrage : 35 jours
Engraissement : 84 jours
```

---

## 📊 Dimensionnement optimal

### Formule de calcul
```
Nombre de salles = ⌈(Durée d'occupation + Vide sanitaire) / Intervalle entre bandes⌉
```

**Exemple** : Post-Sevrage de 35 jours, vide de 7 jours, intervalle de 21 jours
```
Nb salles PS = ⌈(35 + 7) / 21⌉ = ⌈2⌉ = 2 salles
Tableau de référence (Intervalle 21j, Vide 7j)
Type de salleDurée (j)Salles nécessairesAttente Saillie352Gestante774Maternité352Post-Sevrage352Engraissement1196
Impact du vide sanitaire
Vide (j)ASGMPSE3242265242267242261035337

🔍 Interprétation des résultats
✅ Configuration optimale
Indicateurs :

✅ Aucun conflit
✅ Dimensionnement optimal
Vide moyen : 7-10 jours
En régime de croisière : maximum 1 salle vide par type à tout instant

→ Votre configuration est parfaite !
⚠️ Manque de salles (Conflits)
Symptômes :

🔴 X conflits détectés
Une ou plusieurs bandes ne trouvent pas de salle disponible
Certaines bandes "disparaissent" temporairement

Solution :

Identifier le type de salle problématique (indiqué dans le diagnostic)
Augmenter le nombre de salles de ce type de 1
OU réduire la durée d'occupation si possible
OU augmenter l'intervalle entre bandes

📊 Surdimensionnement
Symptômes :

🟠 X surdimensionnements en régime de croisière
Plusieurs salles du même type vides simultanément

Conséquences :

Investissement inutile
Coûts d'entretien supérieurs

Solution :

Identifier le type de salle surdimensionné
Réduire le nombre de salles de ce type de 1
Vérifier qu'aucun conflit n'apparaît

🔄 Phase de démarrage
Normal de voir :

Plusieurs salles jamais utilisées
Plusieurs salles vides simultanément
Vides sanitaires très longs

→ Attendez le régime de croisière (dates affichées dans le diagnostic) pour évaluer le dimensionnement.

⚠️ Limitations
Simplifications du modèle

Homogénéité des bandes : Le modèle suppose que toutes les bandes ont exactement les mêmes durées d'occupation
Pas de mortalité : Pas de prise en compte des pertes
Pas de variabilité : Les durées sont fixes (pas de distribution probabiliste)
Pas de contraintes de capacité : Seul le nombre de salles est limité, pas le nombre de places

Hypothèses physiologiques

Cycle de 147 jours strictement respecté
Retour en chaleur immédiat après sevrage
Pas de réforme de truies
Pas de gestion des cochettes de renouvellement

Données en temps réel
L'application simule à partir d'une date de référence mais ne se connecte pas à un système de gestion d'élevage réel.

🤝 Support
Pour toute question ou suggestion d'amélioration, n'hésitez pas à contribuer ou à ouvrir une issue.

📝 Licence
Cette application est fournie à des fins éducatives et de simulation. Les résultats doivent être validés par un technicien d'élevage avant toute application en conditions réelles.

Développé avec ❤️ pour optimiser la gestion des élevages porcins