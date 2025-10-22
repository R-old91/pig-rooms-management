import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

# ============================================================================
# SECTION 1 : PARAMÈTRES CONFIGURABLES
# ============================================================================

st.set_page_config(page_title="Gestion Salles Élevage Porcin", layout="wide")

st.title("🐷 Visualisation des Salles d'Élevage Porcin")


# Sidebar pour les paramètres
with st.sidebar:
    st.header("⚙️ Paramètres de conduite")
    
    # Paramètres généraux
    st.subheader("Configuration générale")
    VIDE_SANITAIRE = st.number_input("Vide sanitaire (jours)", value=7, min_value=0, max_value=14,
                                     help="Durée obligatoire de vide sanitaire entre deux bandes")
    
    INTERVALLE_BANDES = st.number_input("Intervalle entre bandes (jours)", value=21, min_value=1,
                                       help="Nombre de jours entre l'entrée de deux bandes successives")
    
    # Calcul automatique du nombre de bandes
    nb_bandes_calcule = round(147 / INTERVALLE_BANDES)
    
    NB_BANDES = st.number_input("Nombre de bandes", value=nb_bandes_calcule, min_value=1, 
                               help=f"Calculé automatiquement : 147j / {INTERVALLE_BANDES}j = {nb_bandes_calcule} bandes")
    
    # Date de référence = DATE DE SAILLIE de B1
    st.subheader("Date de référence")
    DATE_SAILLIE_B1 = st.date_input(
        "Date de SAILLIE de la Bande 1",
        value=datetime(2025, 7, 25)
    )
    
    st.markdown("---")
    
    # Durées d'occupation - TRUIES
    st.subheader("🐖 Circuit Truies")
    st.info("⚠️ Cycle = 147 jours à partir de la saillie")
    
    JOURS_AVANT_SAILLIE = st.number_input("Jours avant saillie en AS", value=5, min_value=0)
    DUREE_ATTENTE_SAILLIE = st.number_input("Attente Saillie (total)", value=35, min_value=1)
    DUREE_GESTANTE = st.number_input("Gestante", value=77, min_value=1)
    DUREE_MATERNITE = st.number_input("Maternité", value=35, min_value=1)
    
    # Validation du cycle truie
    CYCLE_TRUIE_TOTAL = DUREE_ATTENTE_SAILLIE + DUREE_GESTANTE + DUREE_MATERNITE
    CYCLE_TRUIE_ATTENDU = 147
    
    if CYCLE_TRUIE_TOTAL != CYCLE_TRUIE_ATTENDU:
        st.error(f"⚠️ ALERTE : AS + G + M = {CYCLE_TRUIE_TOTAL}j ≠ {CYCLE_TRUIE_ATTENDU}j !")
        st.warning(f"Le cycle doit être exactement {CYCLE_TRUIE_ATTENDU} jours")
    else:
        st.success(f"✅ Cycle truie = {CYCLE_TRUIE_TOTAL} jours")
    
    # Durées d'occupation - PRODUITS
    st.subheader("🐷 Circuit Produits")
    st.info("⚠️ PS + E ne doit pas dépasser 152 jours")
    
    DUREE_POST_SEVRAGE = st.number_input("Post-Sevrage", value=35, min_value=1)
    DUREE_ENGRAISSEMENT = st.number_input("Engraissement", value=119, min_value=1)
    
    # Validation du circuit produits
    CIRCUIT_PRODUITS_TOTAL = DUREE_POST_SEVRAGE + DUREE_ENGRAISSEMENT
    CIRCUIT_PRODUITS_MAX = 152
    
    if CIRCUIT_PRODUITS_TOTAL > CIRCUIT_PRODUITS_MAX:
        st.error(f"⚠️ ALERTE : PS + E = {CIRCUIT_PRODUITS_TOTAL}j > {CIRCUIT_PRODUITS_MAX}j !")
    else:
        st.success(f"✅ Circuit produits = {CIRCUIT_PRODUITS_TOTAL} jours")
    
    st.markdown("---")
    
    # Calcul du dimensionnement optimal
    st.subheader("📊 Dimensionnement optimal")
    st.caption(f"Avec vide sanitaire de {VIDE_SANITAIRE}j")
    
    import math
    nb_optimal = {
        'AS': math.ceil((DUREE_ATTENTE_SAILLIE + VIDE_SANITAIRE) / INTERVALLE_BANDES),
        'G': math.ceil((DUREE_GESTANTE + VIDE_SANITAIRE) / INTERVALLE_BANDES),
        'M': math.ceil((DUREE_MATERNITE + VIDE_SANITAIRE) / INTERVALLE_BANDES),
        'PS': math.ceil((DUREE_POST_SEVRAGE + VIDE_SANITAIRE) / INTERVALLE_BANDES),
        'E': math.ceil((DUREE_ENGRAISSEMENT + VIDE_SANITAIRE) / INTERVALLE_BANDES)
    }
    
    st.info(f"🧹 **Vide sanitaire actuel : {VIDE_SANITAIRE} jours**\n\n"
            f"Modifiez ce paramètre pour voir l'impact sur le dimensionnement.")
    
    # Nombre de salles
    st.subheader("🏠 Nombre de salles")
    NB_SALLES_ATTENTE = st.number_input("Attente Saillie", value=nb_optimal['AS'], min_value=1)
    NB_SALLES_GESTANTE = st.number_input("Gestante", value=nb_optimal['G'], min_value=1)
    NB_SALLES_MATERNITE = st.number_input("Maternité", value=nb_optimal['M'], min_value=1)
    NB_SALLES_PS = st.number_input("Post-Sevrage", value=nb_optimal['PS'], min_value=1)
    NB_SALLES_ENGRAISSEMENT = st.number_input("Engraissement", value=nb_optimal['E'], min_value=1)

# Convertir date en datetime pour les calculs
DATE_SAILLIE_B1 = datetime.combine(DATE_SAILLIE_B1, datetime.min.time())

# ============================================================================
# SECTION 2 : CALCUL DES DATES ET OCCUPATIONS
# ============================================================================

# Couleurs par bande
COULEURS_BANDES = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FF9800',  
    '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2',
    '#F8B739', '#52B788', '#E63946', '#06FFA5'
]

def calculer_toutes_occupations_truies():
    """
    Calcule TOUTES les occupations truies.
    Point de référence = Date de SAILLIE
    Cycle = 147 jours à partir de la saillie
    """
    occupations = []
    
    for bande in range(1, NB_BANDES + 1):
        # Date de saillie de cette bande
        date_saillie_bande = DATE_SAILLIE_B1 + timedelta(days=(bande - 1) * INTERVALLE_BANDES)
        
        # Calculer plusieurs cycles (147j)
        for cycle in range(50):
            date_saillie_cycle = date_saillie_bande + timedelta(days=cycle * CYCLE_TRUIE_ATTENDU)
            
            if date_saillie_cycle > datetime.now() + timedelta(days=365):
                break
            
            # Attente Saillie (commence AVANT la saillie)
            date_entree_as = date_saillie_cycle - timedelta(days=JOURS_AVANT_SAILLIE)
            date_sortie_as = date_entree_as + timedelta(days=DUREE_ATTENTE_SAILLIE)
            
            occupations.append({
                'bande': bande,
                'cycle': cycle,
                'type_salle': 'Attente Saillie',
                'date_entree': date_entree_as,
                'date_sortie': date_sortie_as,
                'duree_totale': DUREE_ATTENTE_SAILLIE,
                'id_unique': f"B{bande}_C{cycle}_AS"
            })
            
            # Gestante (commence après AS)
            date_entree_g = date_sortie_as
            date_sortie_g = date_entree_g + timedelta(days=DUREE_GESTANTE)
            
            occupations.append({
                'bande': bande,
                'cycle': cycle,
                'type_salle': 'Gestante',
                'date_entree': date_entree_g,
                'date_sortie': date_sortie_g,
                'duree_totale': DUREE_GESTANTE,
                'id_unique': f"B{bande}_C{cycle}_G"
            })
            
            # Maternité (commence après Gestante = mise bas)
            date_mise_bas = date_sortie_g
            date_sevrage = date_mise_bas + timedelta(days=DUREE_MATERNITE)
            
            occupations.append({
                'bande': bande,
                'cycle': cycle,
                'type_salle': 'Maternité',
                'date_entree': date_mise_bas,
                'date_sortie': date_sevrage,
                'duree_totale': DUREE_MATERNITE,
                'date_sevrage': date_sevrage,
                'id_unique': f"B{bande}_C{cycle}_M"
            })
    
    return occupations

def calculer_toutes_occupations_produits():
    """Calcule TOUTES les occupations produits"""
    occupations = []
    
    for bande in range(1, NB_BANDES + 1):
        # Date de saillie de cette bande
        date_saillie_bande = DATE_SAILLIE_B1 + timedelta(days=(bande - 1) * INTERVALLE_BANDES)
        # Le cycle commence à l'ENTRÉE en AS, pas à la saillie !
        date_entree_as_bande = date_saillie_bande - timedelta(days=JOURS_AVANT_SAILLIE)
        
        for cycle in range(50):
            # Cycle commence à l'entrée AS (147j à partir de l'entrée AS)
            date_debut_cycle = date_entree_as_bande + timedelta(days=cycle * CYCLE_TRUIE_ATTENDU)
            
            # Date de sevrage = début du cycle + 147j
            date_sevrage = date_debut_cycle + timedelta(days=CYCLE_TRUIE_ATTENDU)
            
            if date_sevrage > datetime.now() + timedelta(days=365):
                break
            
            # Post-Sevrage (les porcelets entrent le jour du sevrage)
            occupations.append({
                'bande': bande,
                'cycle': cycle,
                'type_salle': 'Post-Sevrage',
                'date_entree': date_sevrage,
                'date_sortie': date_sevrage + timedelta(days=DUREE_POST_SEVRAGE),
                'duree_totale': DUREE_POST_SEVRAGE,
                'date_sevrage': date_sevrage,
                'id_unique': f"B{bande}_S{cycle}_PS"
            })
            
            # Engraissement (entre immédiatement après PS)
            date_entree_e = date_sevrage + timedelta(days=DUREE_POST_SEVRAGE)
            occupations.append({
                'bande': bande,
                'cycle': cycle,
                'type_salle': 'Engraissement',
                'date_entree': date_entree_e,
                'date_sortie': date_entree_e + timedelta(days=DUREE_ENGRAISSEMENT),
                'duree_totale': DUREE_ENGRAISSEMENT,
                'date_sevrage': date_sevrage,
                'id_unique': f"B{bande}_S{cycle}_E"
            })
    
    return occupations

# ============================================================================
# SECTION 3 : AFFECTATION AVEC VIDE SANITAIRE DE 7 JOURS
# ============================================================================

def affecter_salles_simple(toutes_occupations):
    """Affectation simple : chaque bande prend LA salle vide avec respect du vide sanitaire de 7j"""
    date_actuelle = datetime.now()
    
    salles_config = {
        'Attente Saillie': NB_SALLES_ATTENTE,
        'Gestante': NB_SALLES_GESTANTE,
        'Maternité': NB_SALLES_MATERNITE,
        'Post-Sevrage': NB_SALLES_PS,
        'Engraissement': NB_SALLES_ENGRAISSEMENT
    }
    
    toutes_occupations_triees = sorted(toutes_occupations, key=lambda x: x['date_entree'])
    
    salles_disponibilite = {}
    for type_salle, nb_salles in salles_config.items():
        salles_disponibilite[type_salle] = [
            {'num_salle': i, 'date_liberation': datetime(2000, 1, 1), 'historique': [], 'premiere_utilisation': None}
            for i in range(nb_salles)
        ]
    
    conflits = []
    sur_dimensionnements = []
    
    # Tracker quand chaque type de salle atteint le régime de croisière
    dates_regime_croisiere = {}
    
    for occ in toutes_occupations_triees:
        type_salle = occ['type_salle']
        date_entree = occ['date_entree']
        date_sortie = occ['date_sortie']
        
        salles = salles_disponibilite[type_salle]
        # Une salle est vide si date_liberation (sortie + 7j de vide) <= date_entree
        salles_vides = [s for s in salles if s['date_liberation'] <= date_entree]
        
        # Vérifier si toutes les salles de ce type ont déjà été utilisées
        toutes_salles_utilisees = all(s['premiere_utilisation'] is not None for s in salles)
        
        # Si toutes utilisées et pas encore noté la date de régime de croisière
        if toutes_salles_utilisees and type_salle not in dates_regime_croisiere:
            dates_regime_croisiere[type_salle] = date_entree
        
        if len(salles_vides) == 0:
            conflits.append({
                'type_salle': type_salle,
                'bande': occ['bande'],
                'date_entree': date_entree,
                'id': occ['id_unique']
            })
            salle_choisie = min(salles, key=lambda s: s['date_liberation'])
        
        elif len(salles_vides) > 1:
            # Enregistrer le surdimensionnement seulement si en régime de croisière
            sur_dimensionnements.append({
                'type_salle': type_salle,
                'nb_vides': len(salles_vides),
                'date': date_entree,
                'en_regime_croisiere': toutes_salles_utilisees
            })
            # Prendre celle libérée le PLUS TÔT pour rotation équilibrée
            salle_choisie = min(salles_vides, key=lambda s: s['date_liberation'])
        
        else:
            salle_choisie = salles_vides[0]
        
        # Marquer la première utilisation
        if salle_choisie['premiere_utilisation'] is None:
            salle_choisie['premiere_utilisation'] = date_entree
        
        # IMPORTANT : date_liberation = date_sortie + 7 jours de vide sanitaire
        salle_choisie['date_liberation'] = date_sortie + timedelta(days=VIDE_SANITAIRE)
        salle_choisie['historique'].append({
            'id_unique': occ['id_unique'],
            'date_entree': date_entree,
            'date_sortie': date_sortie,
            'date_liberation': date_sortie + timedelta(days=VIDE_SANITAIRE),
            'bande': occ['bande'],
            'duree_totale': occ['duree_totale']
        })
    
    # Filtrer les surdimensionnements pour ne garder que ceux en régime de croisière
    sur_dim_reel = [s for s in sur_dimensionnements if s['en_regime_croisiere']]
    
    etat_salles = {}
    
    for type_salle, nb_salles in salles_config.items():
        etat_salles[type_salle] = []
        
        for num_salle in range(nb_salles):
            salle_info = salles_disponibilite[type_salle][num_salle]
            historique = salle_info['historique']
            
            if not historique:
                etat_salles[type_salle].append({'statut': 'jamais_utilisee'})
                continue
            
            occupation_actuelle = None
            for occ_hist in historique:
                if occ_hist['date_entree'] <= date_actuelle < occ_hist['date_sortie']:
                    occupation_actuelle = occ_hist
                    break
            
            if occupation_actuelle:
                jours_dans_salle = (date_actuelle - occupation_actuelle['date_entree']).days
                
                etat_salles[type_salle].append({
                    'statut': 'occupée',
                    'bande': occupation_actuelle['bande'],
                    'date_entree': occupation_actuelle['date_entree'],
                    'date_sortie': occupation_actuelle['date_sortie'],
                    'jours_dans_salle': jours_dans_salle,
                    'duree_totale': occupation_actuelle['duree_totale'],
                    'progression': (jours_dans_salle / occupation_actuelle['duree_totale'] * 100),
                    'id_unique': occupation_actuelle['id_unique']
                })
            else:
                occupations_passees = [h for h in historique if h['date_sortie'] <= date_actuelle]
                
                if occupations_passees:
                    dernier_occ = max(occupations_passees, key=lambda h: h['date_sortie'])
                    
                    # Vérifier si en vide sanitaire ou déjà disponible
                    date_fin_vide = dernier_occ['date_liberation']
                    
                    if date_actuelle < date_fin_vide:
                        # En cours de vide sanitaire
                        jours_vide_ecoules = (date_actuelle - dernier_occ['date_sortie']).days
                        jours_vide_restants = (date_fin_vide - date_actuelle).days
                        
                        etat_salles[type_salle].append({
                            'statut': 'vide_sanitaire',
                            'date_liberation': dernier_occ['date_sortie'],
                            'date_disponible': date_fin_vide,
                            'jours_vide_ecoules': jours_vide_ecoules,
                            'jours_vide_restants': jours_vide_restants,
                            'derniere_bande': dernier_occ['bande'],
                            'prochaine_entree': None,
                            'prochaine_bande': None
                        })
                    else:
                        # Vide sanitaire terminé, salle disponible
                        jours_vide_total = (date_actuelle - dernier_occ['date_sortie']).days
                        
                        occupations_futures = [h for h in historique if h['date_entree'] > date_actuelle]
                        prochaine_occ = min(occupations_futures, key=lambda h: h['date_entree']) if occupations_futures else None
                        
                        etat_salles[type_salle].append({
                            'statut': 'disponible',
                            'date_liberation': dernier_occ['date_sortie'],
                            'date_disponible': date_fin_vide,
                            'jours_disponible': (date_actuelle - date_fin_vide).days,
                            'derniere_bande': dernier_occ['bande'],
                            'prochaine_entree': prochaine_occ['date_entree'] if prochaine_occ else None,
                            'prochaine_bande': prochaine_occ['bande'] if prochaine_occ else None
                        })
                else:
                    etat_salles[type_salle].append({'statut': 'jamais_utilisee'})
    
    return etat_salles, conflits, sur_dim_reel, dates_regime_croisiere

# ============================================================================
# SECTION 4 : VISUALISATION
# ============================================================================

def creer_jauge_salle(etat_salle, num_salle, type_salle):
    """Crée une jauge pour une salle"""
    
    if etat_salle['statut'] == 'occupée':
        bande = etat_salle['bande']
        progression = etat_salle['progression']
        jours = etat_salle['jours_dans_salle']
        duree = etat_salle['duree_totale']
        couleur = COULEURS_BANDES[(bande - 1) % len(COULEURS_BANDES)]
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=progression,
            number={'suffix': "%", 'font': {'size': 36, 'color': couleur}},
            delta={'reference': 100, 'suffix': "%", 'font': {'size': 18}},
            title={
                'text': f"<b>{type_salle} {num_salle}</b><br><span style='font-size:20px; color:{couleur}'>Bande {bande}</span><br><span style='font-size:16px; color:#666'>Jour {int(jours)}/{int(duree)}</span>",
                'font': {'size': 22}
            },
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': couleur},
                'bar': {'color': couleur, 'thickness': 0.75},
                'bgcolor': "white",
                'borderwidth': 3,
                'bordercolor': couleur,
                'steps': [{'range': [0, 100], 'color': '#F5F5F5'}],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': progression
                }
            }
        ))
        
        fig.update_layout(
            height=320,
            margin=dict(l=20, r=20, t=90, b=20),
            paper_bgcolor='white',
            font={'family': "Arial"}
        )
        
    elif etat_salle['statut'] == 'vide_sanitaire':
        jours_ecoules = etat_salle['jours_vide_ecoules']
        jours_restants = etat_salle['jours_vide_restants']
        couleur = '#9E9E9E'  
        
        progression_vide = (jours_ecoules / VIDE_SANITAIRE * 100)
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=progression_vide,
            number={'suffix': "%", 'font': {'size': 36, 'color': couleur}},
            title={
                'text': f"<b>{type_salle} {num_salle}</b><br><span style='font-size:20px; color:{couleur}'>🧹 Vide sanitaire</span><br><span style='font-size:16px; color:#666'>{jours_ecoules}j / {VIDE_SANITAIRE}j (reste {jours_restants}j)</span>",
                'font': {'size': 22}
            },
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': couleur},
                'bar': {'color': couleur, 'thickness': 0.75},
                'bgcolor': "white",
                'borderwidth': 3,
                'bordercolor': couleur,
                'steps': [{'range': [0, 100], 'color': '#FFF3E0'}],
                'threshold': {
                    'line': {'color': "green", 'width': 3},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
        
        fig.update_layout(
            height=320,
            margin=dict(l=20, r=20, t=90, b=20),
            paper_bgcolor='white',
            font={'family': "Arial"}
        )
    
    elif etat_salle['statut'] == 'disponible':
        jours_dispo = etat_salle['jours_disponible']
        couleur = '#4CAF50'  # Vert pour disponible
        
        fig = go.Figure(go.Indicator(
            mode="number",
            value=jours_dispo,
            number={'suffix': "j", 'font': {'size': 36, 'color': couleur}},
            title={
                'text': f"<b>{type_salle} {num_salle}</b><br><span style='font-size:20px; color:{couleur}'>✅ Disponible</span><br><span style='font-size:16px; color:#999'>Prochaine: B{etat_salle['prochaine_bande'] if etat_salle['prochaine_bande'] else '?'}</span>",
                'font': {'size': 22}
            }
        ))
        
        fig.update_layout(
            height=320,
            margin=dict(l=20, r=20, t=90, b=20),
            paper_bgcolor='white',
            font={'family': "Arial"}
        )
        
    else:
        return None
    
    return fig

def afficher_jauges_par_deux(etats_salles, type_salle, prefix):
    """Affiche les jauges deux par deux"""
    for i in range(0, len(etats_salles), 2):
        cols = st.columns(2)
        
        with cols[0]:
            etat = etats_salles[i]
            fig = creer_jauge_salle(etat, i+1, type_salle)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_{i}")
            else:
                st.info(f"{type_salle} {i+1} : Jamais utilisée")
        
        if i + 1 < len(etats_salles):
            with cols[1]:
                etat = etats_salles[i+1]
                fig = creer_jauge_salle(etat, i+2, type_salle)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_{i+1}")
                else:
                    st.info(f"{type_salle} {i+2} : Jamais utilisée")

def afficher_jauges_par_trois(etats_salles, type_salle, prefix):
    """Affiche les jauges trois par trois"""
    cols = st.columns(3)
    
    for i in range(len(etats_salles)):
        with cols[i % 3]:
            etat = etats_salles[i]
            fig = creer_jauge_salle(etat, i+1, type_salle)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_{i}")
            else:
                st.info(f"{type_salle} {i+1} : Jamais utilisée")

# ============================================================================
# SECTION 5 : INTERFACE PRINCIPALE
# ============================================================================

date_actuelle = datetime.now()
st.info(f"📅 **Date actuelle** : {date_actuelle.strftime('%d/%m/%Y %H:%M')}")

with st.spinner("Calcul des occupations..."):
    toutes_occupations_truies = calculer_toutes_occupations_truies()
    toutes_occupations_produits = calculer_toutes_occupations_produits()
    toutes_occupations = toutes_occupations_truies + toutes_occupations_produits

etat_salles, conflits, sur_dim, dates_regime = affecter_salles_simple(toutes_occupations)

with st.expander("📊 Diagnostic de la configuration", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if conflits:
            st.error(f"⚠️ **{len(conflits)} CONFLITS**")
            st.caption("Pas assez de salles")
        else:
            st.success("✅ **Aucun conflit**")
    
    with col2:
        if sur_dim:
            nb_sur_dim = len(set([(s['type_salle'], s['date']) for s in sur_dim]))
            st.error(f"⚠️ **{nb_sur_dim} surdimensionnements**")
            st.caption("Plusieurs salles vides en régime de croisière")
        else:
            st.success("✅ **Dimensionnement optimal**")
            st.caption("Jamais 2+ salles vides simultanément")
    
    with col3:
        # Compter les vides sanitaires en cours
        vides_en_cours = []
        disponibles = []
        for type_salle, etats in etat_salles.items():
            vides = [e for e in etats if e['statut'] == 'vide_sanitaire']
            dispos = [e for e in etats if e['statut'] == 'disponible']
            vides_en_cours.extend(vides)
            disponibles.extend(dispos)
        
        if vides_en_cours:
            st.metric("Vides en cours", f"{len(vides_en_cours)} salles", 
                     delta=f"🧹 Nettoyage actif")
        elif disponibles:
            st.metric("Salles disponibles", f"{len(disponibles)} salles",
                     delta=f"✅ Prêtes")
        else:
            st.info("Toutes occupées")
    
    # Afficher les dates de régime de croisière
    if dates_regime:
        st.markdown("---")
        st.markdown("**📅 Dates de régime de croisière** (toutes salles utilisées au moins 1x) :")
        cols_regime = st.columns(5)
        types_salles = ['Attente Saillie', 'Gestante', 'Maternité', 'Post-Sevrage', 'Engraissement']
        for idx, type_salle in enumerate(types_salles):
            with cols_regime[idx]:
                if type_salle in dates_regime:
                    st.caption(f"**{type_salle}**")
                    st.write(dates_regime[type_salle].strftime('%d/%m/%Y'))
                else:
                    st.caption(f"**{type_salle}**")
                    st.write("🔄 Démarrage...")

st.markdown("---")

# Affichage Circuit Truies
st.header("🐖 Circuit Truies")
st.markdown("")

st.subheader("Attente Saillie")
afficher_jauges_par_deux(etat_salles['Attente Saillie'], "AS", "as")

st.markdown("---")

st.subheader("Gestante")
if NB_SALLES_GESTANTE <= 3:
    afficher_jauges_par_trois(etat_salles['Gestante'], "G", "g")
else:
    afficher_jauges_par_deux(etat_salles['Gestante'], "G", "g")

st.markdown("---")

st.subheader("Maternité")
afficher_jauges_par_deux(etat_salles['Maternité'], "M", "m")

st.markdown("---")

# Affichage Circuit Produits
st.header("🐷 Circuit Produits")
st.markdown("")

st.subheader("Post-Sevrage")
afficher_jauges_par_deux(etat_salles['Post-Sevrage'], "PS", "ps")

st.markdown("---")

st.subheader("Engraissement")
if NB_SALLES_ENGRAISSEMENT <= 3:
    afficher_jauges_par_trois(etat_salles['Engraissement'], "E", "e")
else:
    afficher_jauges_par_deux(etat_salles['Engraissement'], "E", "e")

st.markdown("---")
st.subheader("🎨 Légende")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("**Couleurs des bandes :**")
    cols = st.columns(min(7, NB_BANDES))
    for i in range(min(7, NB_BANDES)):
        with cols[i]:
            couleur = COULEURS_BANDES[i % len(COULEURS_BANDES)]
            st.markdown(f"<div style='background-color:{couleur}; padding:15px; text-align:center; color:white; font-weight:bold; border-radius:10px; margin:4px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>Bande {i+1}</div>", unsafe_allow_html=True)

