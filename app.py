import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

# ============================================================================
# SECTION 1 : PARAMÈTRES CONFIGURABLES
# ============================================================================

st.set_page_config(page_title="Gestion Salles Élevage Porcin", layout="wide")

# st.title("🐷 Gestion des bandes en élevage Porcin")


with st.sidebar:
    st.header("⚙️ Paramètres de conduite")
    
    # ========================================================================
    # SECTION 1 : PARAMÈTRES PRINCIPAUX
    # ========================================================================
    
    st.subheader("Configuration principale")
    
    INTERVALLE_BANDES = st.selectbox(
        "Intervalle entre bandes",
        options=[7, 14, 21, 28, 35],
        index=2,
        format_func=lambda x: f"{x} jours",
        help="Nombre de jours entre l'entrée de deux bandes successives"
    )
    
    VIDE_SANITAIRE = st.slider(
        "Vide sanitaire",
        min_value=3,
        max_value=7,
        value=5,
        help="Durée de nettoyage entre deux bandes (entre 3 et 7 jours recommandé)"
    )
    
    # ========================================================================
    # RÉINITIALISATION si les paramètres principaux changent
    # ========================================================================
    
    suffixe_config = f"_I{INTERVALLE_BANDES}_V{VIDE_SANITAIRE}"
    
    # Date de référence
    DATE_SAILLIE_B1 = st.date_input(
        "Date de SAILLIE de la Bande 1",
        value=datetime(2025, 7, 25),
        help="Point de référence temporel pour la simulation"
    )
    
    # Initialiser la date de simulation dans session_state si nécessaire
    if 'date_simulation' not in st.session_state:
        st.session_state.date_simulation = datetime.now().date()
    
    # Date de simulation
    DATE_SIMULATION = st.date_input(
        "📅 Date de simulation",
        value=st.session_state.date_simulation,
        min_value=DATE_SAILLIE_B1,
        help="Choisissez une date pour voir l'état des salles à ce moment précis",
        key='date_simulation'
    )
    
    # Bouton de réinitialisation
    if st.button("🔄 Réinitialiser tous les paramètres", use_container_width=True, type="secondary"):
        # Supprimer toutes les clés de session_state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Réinitialiser la date à aujourd'hui
        st.session_state.date_simulation = datetime.now().date()
        st.rerun()
    
    st.markdown("---")
    # ========================================================================
    # SECTION 2 : CALCULS AUTOMATIQUES SIMPLIFIÉS
    # ========================================================================
    
    st.subheader("🤖 Calculs automatiques")
    
    import math
    
    # Calcul du nombre de bandes
    nb_bandes_calcule = round(147 / INTERVALLE_BANDES)
    NB_BANDES = nb_bandes_calcule
    
    st.info(f"**Nombre de bandes :** {NB_BANDES} bandes")
    
    # ========================================================================
    # CONTRAINTES PHYSIOLOGIQUES
    # ========================================================================
    
    DUREE_AS_FIXE = 35      # Fixe
    DUREE_PS_FIXE = 35      # Fixe
    DUREE_M_VISEE = 35      # Cible (flexible 32-35j)
    
    # ========================================================================
    # CALCUL DIRECT : Nb salles + vide résultant
    # ========================================================================
    
    # 1. Attente Saillie (35j fixe)
    nb_salles_as = math.ceil((DUREE_AS_FIXE + VIDE_SANITAIRE) / INTERVALLE_BANDES)
    vide_as = (nb_salles_as * INTERVALLE_BANDES) - DUREE_AS_FIXE
    duree_as_finale = DUREE_AS_FIXE
    
    # 2. Post-Sevrage (42j fixe)
    nb_salles_ps = math.ceil((DUREE_PS_FIXE + VIDE_SANITAIRE) / INTERVALLE_BANDES)
    vide_ps = (nb_salles_ps * INTERVALLE_BANDES) - DUREE_PS_FIXE
    duree_ps_finale = DUREE_PS_FIXE
    
    # 3. Maternité (vise 35j)
    nb_salles_m = math.ceil((DUREE_M_VISEE + VIDE_SANITAIRE) / INTERVALLE_BANDES)
    # On calcule d'abord le vide possible avec ce nombre de salles
    vide_m_brut = (nb_salles_m * INTERVALLE_BANDES) - DUREE_M_VISEE
    
    # 4. Gestante (ajustée pour cycle 147j)
    # On part d'une estimation puis on ajuste Maternité pour boucler
    duree_g_estimee = 147 - DUREE_AS_FIXE - DUREE_M_VISEE
    nb_salles_g = math.ceil((duree_g_estimee + VIDE_SANITAIRE) / INTERVALLE_BANDES)
    vide_g = (nb_salles_g * INTERVALLE_BANDES) - duree_g_estimee
    
    # Ajustement de Maternité pour cycle exact de 147j
    duree_m_finale = 147 - DUREE_AS_FIXE - duree_g_estimee
    
    # Si Maternité sort des limites 32-35j, on ajuste Gestante
    if duree_m_finale < 32:
        duree_m_finale = 32
        duree_g_finale = 147 - DUREE_AS_FIXE - duree_m_finale
        # Recalculer nb salles Gestante
        nb_salles_g = math.ceil((duree_g_finale + VIDE_SANITAIRE) / INTERVALLE_BANDES)
        vide_g = (nb_salles_g * INTERVALLE_BANDES) - duree_g_finale
        # Re-ajuster Maternité
        duree_m_finale = 147 - DUREE_AS_FIXE - duree_g_finale
    elif duree_m_finale > 35:
        duree_m_finale = 35
        duree_g_finale = 147 - DUREE_AS_FIXE - duree_m_finale
        nb_salles_g = math.ceil((duree_g_finale + VIDE_SANITAIRE) / INTERVALLE_BANDES)
        vide_g = (nb_salles_g * INTERVALLE_BANDES) - duree_g_finale
        duree_m_finale = 147 - DUREE_AS_FIXE - duree_g_finale
    else:
        duree_g_finale = duree_g_estimee
    
    vide_m = (nb_salles_m * INTERVALLE_BANDES) - duree_m_finale
    
    # 5. Engraissement (max 152 - PS)
    duree_e_max = 152 - DUREE_PS_FIXE
    nb_salles_e = math.ceil((duree_e_max + VIDE_SANITAIRE) / INTERVALLE_BANDES)
    duree_e_finale = min((nb_salles_e * INTERVALLE_BANDES) - VIDE_SANITAIRE, duree_e_max)
    vide_e = (nb_salles_e * INTERVALLE_BANDES) - duree_e_finale
    
    # ========================================================================
    # STOCKAGE DES RÉSULTATS
    # ========================================================================
    
    nb_optimal = {
        'AS': nb_salles_as,
        'G': nb_salles_g,
        'M': nb_salles_m,
        'PS': nb_salles_ps,
        'E': nb_salles_e
    }
    
    durees_optimales = {
        'AS': duree_as_finale,
        'G': duree_g_finale,
        'M': duree_m_finale,
        'PS': duree_ps_finale,
        'E': duree_e_finale
    }
    
    vides_reels = {
        'AS': vide_as,
        'G': vide_g,
        'M': vide_m,
        'PS': vide_ps,
        'E': vide_e
    }
    
    
    
    # Totaux et validations
    st.markdown("---")
    
    # Réduire la taille de police des metrics
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] {
            font-size: 20px;
        }
        [data-testid="stMetricLabel"] {
            font-size: 14px;
        }
        [data-testid="stMetricDelta"] {
            font-size: 12px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        total_salles = sum(nb_optimal.values())
        st.metric("**Salles**", f"{total_salles}", help="Nombre total de salles nécessaires")
    
    with col_info2:
        cycle_truies = durees_optimales['AS'] + durees_optimales['G'] + durees_optimales['M']
        delta_cycle = cycle_truies - 147
        if abs(delta_cycle) < 0.5:
            st.metric("**LCY**", f"{cycle_truies:.0f}j", delta="✅ Conforme", delta_color="normal", help="Longueur du cycle truies")
        else:
            st.metric("**LCY**", f"{cycle_truies:.0f}j", delta=f"{delta_cycle:+.0f}j", delta_color="inverse", help="Longueur du cycle truies")
    
    with col_info3:
        circuit_produits = durees_optimales['PS'] + durees_optimales['E']
        if circuit_produits <= 152:
            st.metric("**Produits**", f"{circuit_produits:.0f}j", delta="✅ Conforme", delta_color="normal", help="Circuit produits")
        else:
            delta_produits = circuit_produits - 152
            st.metric("**Produits**", f"{circuit_produits:.0f}j", delta=f"+{delta_produits:.0f}j", delta_color="inverse", help="Circuit produits")
    
    # Avertissements selon le contexte
    nb_vides_hors_cible = sum(1 for v in vides_reels.values() if v < 3 or v > 7)
    
    if INTERVALLE_BANDES == 7:
        st.info(f"""
        💡 **Conduite 7 jours** ({NB_BANDES} bandes, {total_salles} salles) :
        - Rotation très intensive nécessitant une organisation rigoureuse
        - Les vides sanitaires peuvent être allongés (ajustez manuellement si besoin)
        """)
    
    if nb_vides_hors_cible > 0:
        st.warning(f"""
        ⚠️ **{nb_vides_hors_cible} type(s) de salle avec vide hors cible (3-7j)**
        
        Vous pouvez :
        - Ajuster manuellement dans la section ci-dessous
        - Accepter ces vides (certains élevages fonctionnent ainsi)
        - Changer l'intervalle entre bandes
        """)
    elif all(3 <= v <= 7 for v in vides_reels.values()):
        st.success("🎯 **Configuration optimale** : Tous les vides sanitaires sont entre 3 et 7 jours !")
    
    st.markdown("---")

    # ========================================================================
    # SECTION 3 : AJUSTEMENTS MANUELS (OPTIONNEL)
    # ========================================================================
    
    with st.expander("🔧 Ajustements manuels (optionnel)", expanded=False):
        st.caption("Modifiez uniquement si vous avez des contraintes spécifiques")
        
        st.markdown("**Nombre de salles :**")
        st.number_input("Attente Saillie", value=nb_optimal['AS'], min_value=1, key="nb_as")
        st.number_input("Gestante", value=nb_optimal['G'], min_value=1, key="nb_g")
        st.number_input("Maternité", value=nb_optimal['M'], min_value=1, key="nb_m")
        st.number_input("Post-Sevrage", value=nb_optimal['PS'], min_value=1, key="nb_ps")
        st.number_input("Engraissement", value=nb_optimal['E'], min_value=1, key="nb_e")
        
        st.markdown("---")
        st.markdown("**Durées d'occupation (jours) :**")
        
        st.number_input("Jours avant saillie", value=5, min_value=0, key="jours_av")
        st.number_input("Attente Saillie (durée)", value=int(durees_optimales['AS']), min_value=1, key="duree_as")
        st.number_input("Gestante (durée)", value=int(durees_optimales['G']), min_value=1, key="duree_g")
        st.number_input("Maternité (durée)", value=int(durees_optimales['M']), min_value=1, key="duree_m")
        st.number_input("Post-Sevrage (durée)", value=int(durees_optimales['PS']), min_value=1, key="duree_ps")
        st.number_input("Engraissement (durée)", value=int(durees_optimales['E']), min_value=1, key="duree_e")
        
        # Validation des ajustements manuels
        if 'duree_as' in st.session_state:
            cycle_manuel = st.session_state['duree_as'] + st.session_state['duree_g'] + st.session_state['duree_m']
            if cycle_manuel != 147:
                st.error(f"⚠️ Cycle truies = {cycle_manuel}j (doit être 147j)")
            
            circuit_manuel = st.session_state['duree_ps'] + st.session_state['duree_e']
            if circuit_manuel > 152:
                st.error(f"⚠️ Circuit produits = {circuit_manuel}j (> 152j)")
            
            # Vérifier les vides sanitaires
            for nom, key_nb, key_duree in [
                ("AS", 'nb_as', 'duree_as'),
                ("G", 'nb_g', 'duree_g'),
                ("M", 'nb_m', 'duree_m'),
                ("PS", 'nb_ps', 'duree_ps'),
                ("E", 'nb_e', 'duree_e')
            ]:
                if key_nb in st.session_state and key_duree in st.session_state:
                    vide = (st.session_state[key_nb] * INTERVALLE_BANDES) - st.session_state[key_duree]
                    if vide < 3:
                        st.error(f"⚠️ {nom}: Vide = {int(vide)}j (< 3j minimum !)")
                    elif vide > 7:
                        st.warning(f"⚠️ {nom}: Vide = {int(vide)}j (> 7j)")
    
    # ========================================================================
    # RÉCUPÉRATION DES VALEURS avec clés dynamiques
    # ========================================================================
    
    # Nombre de salles : utiliser session_state avec clés dynamiques
    NB_SALLES_ATTENTE = st.session_state.get(f'nb_as{suffixe_config}', nb_optimal['AS'])
    NB_SALLES_GESTANTE = st.session_state.get(f'nb_g{suffixe_config}', nb_optimal['G'])
    NB_SALLES_MATERNITE = st.session_state.get(f'nb_m{suffixe_config}', nb_optimal['M'])
    NB_SALLES_PS = st.session_state.get(f'nb_ps{suffixe_config}', nb_optimal['PS'])
    NB_SALLES_ENGRAISSEMENT = st.session_state.get(f'nb_e{suffixe_config}', nb_optimal['E'])
    
    # Durées : utiliser session_state avec clés dynamiques
    JOURS_AVANT_SAILLIE = st.session_state.get(f'jours_av{suffixe_config}', 5)
    DUREE_ATTENTE_SAILLIE = st.session_state.get(f'duree_as{suffixe_config}', int(durees_optimales['AS']))
    DUREE_GESTANTE = st.session_state.get(f'duree_g{suffixe_config}', int(durees_optimales['G']))
    DUREE_MATERNITE = st.session_state.get(f'duree_m{suffixe_config}', int(durees_optimales['M']))
    DUREE_POST_SEVRAGE = st.session_state.get(f'duree_ps{suffixe_config}', int(durees_optimales['PS']))
    DUREE_ENGRAISSEMENT = st.session_state.get(f'duree_e{suffixe_config}', int(durees_optimales['E']))
# Convertir dates en datetime
DATE_SAILLIE_B1 = datetime.combine(DATE_SAILLIE_B1, datetime.min.time())
DATE_SIMULATION = datetime.combine(DATE_SIMULATION, datetime.min.time())
CYCLE_TRUIE_ATTENDU = 147

st.title("🐷 Simulateur de Gestion des Salles - Élevage Porcin")

# Variable pour l'ensemble de l'application
date_actuelle = DATE_SIMULATION

# ============================================================================
# FONCTION DE CALCUL D'ÉTAT À UNE DATE DONNÉE
# ============================================================================

def calculer_etat_salle_a_date(salle_id, df_bandes, date_simulation, vide_sanitaire):
    """
    Calcule l'état d'une salle à une date donnée.
    
    Returns:
        dict avec 'statut', 'bande', 'progression', 'jours_restants', 'date_liberation'
    """
    # Filtrer les occupations de cette salle
    occupations = df_bandes[df_bandes['salle_affectee'] == salle_id].copy()
    
    if occupations.empty:
        return {
            'statut': 'disponible',
            'bande': None,
            'progression': 0,
            'jours_restants': 0,
            'date_liberation': None
        }
    
    # Parcourir les périodes d'occupation
    for idx, row in occupations.iterrows():
        date_entree = row['date_entree']
        date_sortie = row['date_sortie']
        date_fin_vide = date_sortie + timedelta(days=vide_sanitaire)
        
        # CAS 1 : Salle occupée
        if date_entree <= date_simulation < date_sortie:
            duree_totale = (date_sortie - date_entree).days
            jours_ecoules = (date_simulation - date_entree).days
            progression = (jours_ecoules / duree_totale * 100) if duree_totale > 0 else 0
            jours_restants = (date_sortie - date_simulation).days
            
            return {
                'statut': 'occupee',
                'bande': row['bande'],
                'progression': progression,
                'jours_restants': jours_restants,
                'date_liberation': date_fin_vide
            }
        
        # CAS 2 : Salle en vide sanitaire
        elif date_sortie <= date_simulation < date_fin_vide:
            jours_vide_ecoules = (date_simulation - date_sortie).days
            progression_vide = (jours_vide_ecoules / vide_sanitaire * 100) if vide_sanitaire > 0 else 100
            jours_restants = (date_fin_vide - date_simulation).days
            
            return {
                'statut': 'vide',
                'bande': row['bande'],
                'progression': progression_vide,
                'jours_restants': jours_restants,
                'date_liberation': date_fin_vide
            }
    
    # CAS 3 : Salle disponible (toutes les occupations sont terminées)
    return {
        'statut': 'disponible',
        'bande': None,
        'progression': 0,
        'jours_restants': 0,
        'date_liberation': None
    }

# ============================================================================
# GÉNÉRATION DES DONNÉES
# ============================================================================
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
    date_actuelle = DATE_SIMULATION
    
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

def creer_jauge_salle(etat_salle, num_salle, type_salle, date_simulation):
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
        
        # Ajouter date DANS la jauge si simulation
        if date_simulation.date() != datetime.now().date():
            fig.add_annotation(
                text=f"{date_simulation.strftime('%d/%m/%Y')}",
                xref="paper", yref="paper",
                x=0.5, y=0.55,
                showarrow=False,
                font=dict(size=11, color="#666"),
                bgcolor="white",
                opacity=0.9
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
        
        # Ajouter date DANS la jauge si simulation
        if date_simulation.date() != datetime.now().date():
            fig.add_annotation(
                text=f"{date_simulation.strftime('%d/%m/%Y')}",
                xref="paper", yref="paper",
                x=0.5, y=0.55,
                showarrow=False,
                font=dict(size=11, color="#666"),
                bgcolor="white",
                opacity=0.9
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
        
        # Ajouter date DANS la jauge si simulation
        if date_simulation.date() != datetime.now().date():
            fig.add_annotation(
                text=f"{date_simulation.strftime('%d/%m/%Y')}",
                xref="paper", yref="paper",
                x=0.5, y=0.45,
                showarrow=False,
                font=dict(size=11, color="#666"),
                bgcolor="white",
                opacity=0.9
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
            fig = creer_jauge_salle(etat, i+1, type_salle, DATE_SIMULATION)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_{i}")
            else:
                st.info(f"{type_salle} {i+1} : Jamais utilisée")
        
        if i + 1 < len(etats_salles):
            with cols[1]:
                etat = etats_salles[i+1]
                fig = creer_jauge_salle(etat, i+2, type_salle, DATE_SIMULATION)
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
            fig = creer_jauge_salle(etat, i+1, type_salle, DATE_SIMULATION)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_{i}")
            else:
                st.info(f"{type_salle} {i+1} : Jamais utilisée")

# ============================================================================
# SECTION 5 : INTERFACE PRINCIPALE
# ============================================================================

date_actuelle = DATE_SIMULATION
st.info(f"📅 **Date actuelle** : {date_actuelle.strftime('%d/%m/%Y %H:%M')}")

with st.spinner("Calcul des occupations..."):
    toutes_occupations_truies = calculer_toutes_occupations_truies()
    toutes_occupations_produits = calculer_toutes_occupations_produits()
    toutes_occupations = toutes_occupations_truies + toutes_occupations_produits

etat_salles, conflits, sur_dim, dates_regime = affecter_salles_simple(toutes_occupations)

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
    
    # ========================================================================
    # AFFICHAGE AVEC DIAGNOSTIC (Version améliorée)
    # ========================================================================
    
    # st.success("**📊 Dimensionnement calculé**")
    
    # Préparer les données pour le tableau
    donnees_truies = []
    donnees_produits = []
    
    noms_types = {
        'AS': 'Attente Saillie',
        'G': 'Gestante',
        'M': 'Maternité',
        'PS': 'Post-Sevrage',
        'E': 'Engraissement'
    }
    
    contraintes = {
        'AS': '🔒 35j fixe',
        'G': '🔄 Variable',
        'M': '🟡 32-35j',
        'PS': '🔒 35j fixe',
        'E': '🔄 Variable'
    }
    
    for code in ['AS', 'G', 'M', 'PS', 'E']:
        vide = int(vides_reels[code])
        
        # Diagnostic du vide
        if vide < 3:
            statut = "❌ Trop court"
        elif 3 <= vide <= 7:
            statut = "✅ Optimal"
        elif 7 < vide <= 14:
            statut = "⚠️ Long"
        else:
            statut = "🔴 Très long"
        
        ligne = {
            'Type': noms_types[code],
            'Contrainte': contraintes[code],
            'Salles': nb_optimal[code],
            'Durée': f"{int(durees_optimales[code])}j",
            'Vide': f"{vide}j",
            'Statut': statut
        }
        
        if code in ['AS', 'G', 'M']:
            donnees_truies.append(ligne)
        else:
            donnees_produits.append(ligne)
    
    # Afficher les tableaux
    st.markdown("**🐖 Circuit Truies**")
    df_truies = pd.DataFrame(donnees_truies)
    st.dataframe(df_truies, use_container_width=True, hide_index=True)
    
    st.markdown("**🐷 Circuit Produits**")
    df_produits = pd.DataFrame(donnees_produits)
    st.dataframe(df_produits, use_container_width=True, hide_index=True)
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