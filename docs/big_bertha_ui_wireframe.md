# Wireframe — Big Bertha (V1)

Document figé. SPA HTML/CSS/JS vanilla, pas de framework, pas d'auth.

Amendements intégrés au contrat API à la suite de ce document :
- A1 : `GET /api/jobs/{id}` expose `agent_code` dès `AGENT_RUNNING`
- A2 : `PATCH /api/conversations/{id}` ajouté (édition du titre)

---

## Décisions D1-D5

**D1 — Panneau droit (éléments épinglés) : toujours visible, pas de toggle.**
Le plus simple à implémenter (zéro état à gérer). Toggle possible en V2 si besoin de place sur petits écrans.

**D2 — Indicateur de progression : texte simple, pas de barre visuelle.**
Les 3 phases n'ont pas de durée comparable ni prévisible — une barre de progression laisserait croire à une précision qu'on n'a pas. Texte changeant selon le statut + points animés CSS.

**D3 — Titre de conversation : éditable via un champ en haut de la zone centrale, pas dans la sidebar.**
La sidebar (260px) est trop contrainte pour de l'édition de texte. Nécessite l'ajout de `PATCH /api/conversations/{id}` — voir amendement A2.

**D4 — Liste de conversations : hauteur fixe, scroll interne.**
Cohérent avec `GET /api/conversations` sans pagination : pas de chargement progressif côté backend, scroll CSS (`overflow-y: auto`) suffit.

**D5 — Badge agent sur les messages Boss : jamais affiché.**
Contredit directement la règle figée (system prompt Boss Phase 2 : "ne jamais mentionner le processus interne"). Aucun badge, ni visible ni au survol, sur les messages persistés. L'unique mention du nom de l'agent est l'indicateur de progression éphémère pendant `AGENT_RUNNING` — statut de traitement, pas attribution sur le message final.

---

## Page chat.html

### Layout global

Page en 100vh, pas de scroll au niveau du `body`. Trois colonnes flexbox :
- Sidebar gauche : 260px fixe
- Zone centrale : `flex: 1`, fluide
- Panneau droit : 280px fixe

Pas de header séparé. Le nom "Big Bertha" est en haut de la sidebar.

---

### Zone 1 — Sidebar gauche

**Position** : fixe à gauche, 260px, 100vh.

**Contenu, de haut en bas :**
1. Nom "Big Bertha" (texte, pas de logo graphique en V1)
2. Bouton "+ Nouvelle conversation", pleine largeur, hors zone de scroll
3. Liste des conversations (zone scrollable, `overflow-y: auto`) :
   - chaque item : titre (ou *"Sans titre"* en italique gris si `title = null`) + date relative dérivée de `updated_at` (ex : "Aujourd'hui 10:42", "Hier", "18 juin")
   - icône poubelle visible uniquement au survol de l'item
4. Lien "⚙ Paramètres" en bas, séparé par une bordure haute

**États :**
- *Chargement initial* → "Chargement..." dans la zone de liste
- *Liste vide* → "Aucune conversation pour l'instant. Cliquez sur Nouvelle conversation pour commencer."
- *Erreur réseau* → "Impossible de charger les conversations." + bouton "Réessayer"
- *Conversation active* → fond légèrement teinté + bordure gauche colorée sur l'item
- *Clic sur "Nouvelle conversation"* → `POST /api/conversations` sans `title` → item apparaît en tête ("Sans titre"), zone centrale bascule dessus à l'état vide, focus sur le champ de saisie
- *Clic sur l'icône poubelle* → confirmation : **"Supprimer cette conversation ? Cette action est irréversible."** → si confirmé : `DELETE /api/conversations/{id}`, item supprimé ; si c'était la conversation active : bascule sur la suivante, ou sur état "aucune conversation sélectionnée" s'il n'en reste plus

---

### Zone 2 — Zone centrale (fil de messages)

**Position** : `flex: 1`, hauteur 100vh moins la zone de saisie (zone 3).

**En-tête de la zone**
Titre de la conversation affiché en haut (D3). Cliquable pour passer en mode édition (devient un champ texte, validation au blur ou touche Entrée → `PATCH /api/conversations/{id}`). Si pas de titre : *"Sans titre"* en placeholder éditable.

**Messages**
- *Message utilisateur* : aligné à droite, fond coloré, largeur max ~70%, texte brut (pas de rendu markdown)
- *Message Boss* : aligné à gauche, fond neutre avec bordure légère, largeur max ~70%, contenu rendu en markdown (titres, listes, gras — cohérent avec `final_response`)
- Pas d'avatar, pas de nom au-dessus des bulles (cohérent avec D5)
- Scroll interne à cette zone, auto-scroll vers le bas à chaque nouveau message ou changement de statut

**Indicateur de progression du job en cours**
Remplace temporairement l'emplacement de la prochaine réponse Boss, aligné à gauche :

| Statut du job | Texte affiché |
|---|---|
| PENDING · ROUTING | "Le Boss analyse votre demande..." |
| AGENT_RUNNING | "{Nom de l'agent} au travail..." (ex : "Analyste au travail...") |
| SYNTHESIZING | "Synthèse en cours..." |

Points animés CSS accompagnant le texte. Le nom de l'agent est disponible dès `AGENT_RUNNING` via l'amendement A1 (`agent_code` exposé depuis `AGENT_RUNNING`). Dès `DONE`, l'indicateur disparaît et le message Boss final s'affiche (pas d'animation en V1).

**Erreur (`status = ERROR`)**
Indicateur remplacé par un message visuel distinct (fond/bordure rouge clair), aligné à gauche :
- si `error_message` renseigné : **"Une erreur est survenue : {error_message}"**
- sinon : **"Une erreur est survenue lors du traitement de votre demande. Merci de réessayer."**

Pas de retry automatique en V1. Champ de saisie redevient actif.

**État vide** (conversation sans aucun message)
Texte centré : **"Posez votre première question à Big Bertha."**

**Point d'architecture pour Cascade** : l'état de polling d'un job doit être géré par `conversation_id`, pas globalement à la page. Si l'utilisateur change de conversation pendant qu'un job tourne sur une autre, revenir sur cette conversation doit réafficher l'indicateur à son état courant sans relancer le job.

---

### Zone 3 — Zone de saisie

**Position** : bas de la zone centrale, hauteur fixe (~70-80px), ne scrolle jamais.

**Contenu** : `textarea` à auto-redimension limitée à 3 lignes max + bouton "Envoyer" à droite.

**Comportement :**
- Entrée seule → envoie ; Shift+Entrée → retour à la ligne
- Bouton actif uniquement si champ non vide (après `trim()`)
- À l'envoi : `POST /api/conversations/{id}/messages` ; message utilisateur s'affiche immédiatement (optimiste — D3 du contrat API renvoie seulement `job_id`) ; champ se vide
- **État désactivé** : champ et bouton grisés dès l'envoi jusqu'à `DONE` ou `ERROR`
- **Réactivation** : à `DONE` ou `ERROR`, champ et bouton actifs, focus remis automatiquement

---

### Zone 4 — Panneau droit (contexte)

**Position** : fixe à droite, 280px, 100vh, toujours visible (D1).

**Contenu :**
1. Titre de section : "Contexte de la conversation"
2. Sous-section "Éléments épinglés" — `GET /api/conversations/{id}/pinned` :
   - chaque item : texte + icône source discrète (distinction `boss`/`user` sans texte explicite) + bouton "✕" au survol
   - état vide : *"Aucun élément épinglé pour l'instant."* en gris
3. Bouton "+ Épingler un élément" → mini-formulaire inline (textarea + "Épingler" / "Annuler"), pas de modale

**Comportement :**
- *Désépinglage* : suppression immédiate à l'écran (optimiste), `DELETE /api/pinned/{id}` en arrière-plan ; en cas d'échec : réafficher l'item + **"Échec de la suppression, réessayez."**
- *Ajout manuel* : `POST /api/conversations/{id}/pinned` ; item apparaît après 201 (pas d'optimiste — on a besoin de l'`id` retourné pour le désépinglage ultérieur) ; formulaire se referme
- Bouton "Épingler" désactivé si textarea vide (après `trim()`)

---

## Page settings.html

Layout : sections empilées, largeur max ~700px centrée. Lien **"← Retour au chat"** en haut.

### Section 1 — Profil entreprise

Champs : Nom (input, requis) · Secteur (input) · Ton (textarea courte) · Règles métier (textarea plus grande). Bouton "Enregistrer".

- *Chargement* : `GET /api/company-profile` pré-remplit ; si 404 : formulaire vide + **"Aucun profil configuré, complétez les champs ci-dessous."**
- *Soumission* : `PUT /api/company-profile` avec les 4 champs complets (jamais un diff — rappel du piège `INSERT OR REPLACE` du contrat API)
- *Validation* : si Nom vide → bordure rouge + **"Le nom est obligatoire."**
- *Confirmation* : texte discret **"Profil enregistré."** (disparaît après 3 secondes)

### Section 2 — Configuration modèle

Champs : model_id (input) · host + port (inputs courts, côte à côte) · clé OpenRouter (input `type="password"` + bouton œil).

- *Chargement* : `GET /api/config` pré-remplit model_id/host/port ; le champ clé **reste toujours vide** + texte indicatif sous le champ : **"Laissez vide pour conserver la clé actuelle."**
- *Soumission* : `PUT /api/config` n'envoie que les champs modifiés ; si le champ clé reste vide, il n'est pas inclus dans le body
- Bouton "Enregistrer" unique pour les 4 champs

### Section 3 — Agents actifs (lecture seule)

`GET /api/agents` → 2 cartes (nom + description). Aucune action possible en V1.

### Section 4 — Logs erreurs récents

`GET /api/logs` → zone de texte scrollable, police monospace.
- *État vide* → **"Aucun log disponible."**
- Bouton "Rafraîchir" manuel en haut de la section (pas de rafraîchissement auto en V1)

---

## Navigation

- `index.html` : redirection via `window.location.href` vers `chat.html`
- Lien "Paramètres" : bas de la sidebar de `chat.html`
- Pas de session, pas d'auth, aucune route protégée

---

## Récapitulatif des textes d'erreur et messages système

| Contexte | Texte exact |
|---|---|
| Liste conversations — erreur réseau | "Impossible de charger les conversations." |
| Liste conversations — vide | "Aucune conversation pour l'instant. Cliquez sur Nouvelle conversation pour commencer." |
| Confirmation suppression conversation | "Supprimer cette conversation ? Cette action est irréversible." |
| Job en erreur, avec message | "Une erreur est survenue : {error_message}" |
| Job en erreur, sans message | "Une erreur est survenue lors du traitement de votre demande. Merci de réessayer." |
| Échec désépinglage | "Échec de la suppression, réessayez." |
| Aucun élément épinglé | "Aucun élément épinglé pour l'instant." |
| Conversation sans message | "Posez votre première question à Big Bertha." |
| Profil — nom manquant | "Le nom est obligatoire." |
| Profil — succès | "Profil enregistré." |
| Config — indication clé OpenRouter | "Laissez vide pour conserver la clé actuelle." |
| Logs — vides ou absent | "Aucun log disponible." |
