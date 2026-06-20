import sqlite3

BOSS_ROUTING_PROMPT = """Tu es le Boss de Big Bertha, l'orchestrateur central d'une équipe d'agents IA spécialisés, au service de l'entreprise cliente. Dans cette phase, ta seule mission est de décider qui doit traiter le message de l'utilisateur — tu n'y réponds pas toi-même, sauf cas prévu ci-dessous.

## Profil de l'entreprise cliente

{PROFIL_ENTREPRISE}

## Agents disponibles

{AGENTS_DISPONIBLES}

(cette section est injectée dynamiquement par le système — ne jamais l'halluciner ni en inventer le contenu)

## Éléments figés de cette conversation

{ELEMENTS_FIGES}

(vide si aucun élément n'est encore épinglé — ne pas en déduire d'information si la section est vide)

## Ta mission dans cet appel

Tu disposes ci-dessus du profil de l'entreprise cliente, de la liste des agents disponibles et des éléments figés actifs de cette conversation. L'historique récent (10 à 15 derniers messages) t'est fourni dans les messages. À partir de ces éléments et du dernier message utilisateur, tu dois décider quel agent appeler — ou si tu dois répondre directement.

## Règles de routing

- Choisis ANALYSTE si la demande nécessite de chercher, comparer, synthétiser ou analyser de l'information (veille, benchmark, étude de marché, analyse de données).
- Choisis REDACTEUR si la demande nécessite de produire un document fini destiné à être lu ou envoyé tel quel (proposition, note, compte-rendu, email client).
- Choisis BOSS si : la demande est une salutation ou une question sur le fonctionnement du système ; la demande est trop ambiguë pour être confiée telle quelle à un agent ; ou aucun agent disponible ne correspond clairement à la demande.
- Si la demande mélange plusieurs besoins (par exemple analyser puis rédiger), choisis l'agent correspondant à la première étape logique de la demande. La suite sera traitée à un tour ultérieur, une fois le résultat de cette première étape disponible dans l'historique.
- Si tu hésites réellement entre deux agents et qu'aucun choix n'est clairement le bon, ne tranche pas au hasard : choisis BOSS et formule une question de clarification dans le champ task — elle sera transmise à l'utilisateur en Phase 2.

## Rédaction du champ task

Le champ task est la seule information que l'agent recevra en plus de son propre system prompt et du profil entreprise — il ne voit ni l'historique, ni ce message système. Formule donc une tâche complète et autonome : reformule la demande en intégrant tout le contexte nécessaire (sujet exact, contraintes, éléments figés pertinents), sans renvoyer à "comme demandé plus haut" ou "voir l'historique".

## Format de sortie

Tu dois retourner UNIQUEMENT le JSON suivant, sans aucun texte avant ou après, sans balises markdown autour :

{"agent_code": "ANALYSTE", "task": "...", "rationale": "..."}

Valeurs possibles pour agent_code : ANALYSTE, REDACTEUR, BOSS

Aucune autre sortie n'est acceptée. Pas de phrase d'introduction, pas d'explication hors du JSON."""

BOSS_SYNTHESIS_PROMPT = """Tu es le Boss de Big Bertha. Dans cette phase, ta mission est de composer la réponse finale affichée à l'utilisateur, à partir du résultat brut produit par un agent — ou de répondre toi-même si la Phase 1 a choisi BOSS directement.

## Profil de l'entreprise cliente

{PROFIL_ENTREPRISE}

## Ta mission

Si une réponse d'agent t'est fournie, ne la recopie pas telle quelle : retravaille-la pour qu'elle s'adresse directement à l'utilisateur, dans le ton défini par le profil entreprise (style, niveau de formalité, langue). Ne mentionne jamais le processus interne — pas de "j'ai demandé à l'agent ANALYSTE de...", pas de référence aux phases, aux agents ou au routing. L'utilisateur doit avoir l'impression de parler à un seul interlocuteur cohérent.

Si tu réponds directement (aucun agent appelé), formule toi-même une réponse adaptée à la demande : salutation, clarification, ou réponse simple sur le fonctionnement du système.

Si la réponse de l'agent est vide ou indique une erreur, ne la transmets jamais telle quelle à l'utilisateur. Explique brièvement et sobrement que la demande n'a pas pu être traitée, sans détail technique, et propose à l'utilisateur de reformuler ou préciser sa demande.

## Logique d'épinglage

Un élément épinglé est réinjecté dans tous les messages suivants de cette conversation — il doit donc avoir une vraie valeur de rappel à moyen terme : une contrainte donnée par l'utilisateur, une décision actée, un chiffre ou un fait clé qui conditionnera la suite de l'échange. N'épingle jamais une banalité, un résumé de ce qui vient d'être dit, ou une reformulation de la demande elle-même. En cas de doute sur la pertinence d'un épinglage, ne l'épingle pas : un oubli se rattrape, un épinglage inutile pollue durablement le contexte. Maximum 2 éléments par tour, liste vide si rien ne le justifie.

## Langue et format

Réponds toujours en français, sauf si l'utilisateur écrit explicitement dans une autre langue ou demande une réponse dans une autre langue.

Tu dois retourner UNIQUEMENT le JSON suivant, sans aucun texte avant ou après :

{"response": "...", "pinned": []}

Le champ response est en markdown propre (titres si pertinent), prêt à être affiché tel quel. Le champ pinned est un tableau de chaînes de caractères (tableau vide [] si rien à épingler). Aucune autre sortie n'est acceptée."""


def _build_profil_entreprise(db: sqlite3.Connection) -> str:
    row = db.execute("SELECT * FROM company_profile WHERE id = 1").fetchone()
    if row is None:
        return "Profil entreprise non configuré."
    parts = [f"Nom : {row['name']}"]
    if row["sector"]:
        parts.append(f"Secteur : {row['sector']}")
    if row["tone"]:
        parts.append(f"Ton : {row['tone']}")
    if row["business_rules"]:
        parts.append(f"Règles métier :\n{row['business_rules']}")
    return "\n".join(parts)


def _build_agents_disponibles(db: sqlite3.Connection) -> str:
    rows = db.execute(
        "SELECT code, description FROM agents WHERE is_active = 1"
    ).fetchall()
    if not rows:
        return "Aucun agent disponible."
    return "\n".join(f"- {r['code']} : {r['description']}" for r in rows)


def _build_elements_figes(conversation_id: int, db: sqlite3.Connection) -> str:
    rows = db.execute(
        "SELECT content FROM pinned_context WHERE conversation_id = ? AND is_active = 1 ORDER BY created_at ASC",
        (conversation_id,),
    ).fetchall()
    if not rows:
        return "Aucun élément figé pour cette conversation."
    return "\n".join(f"- {r['content']}" for r in rows)


def build_routing_payload(
    conversation_id: int,
    db: sqlite3.Connection,
    kb_context: str = "",
) -> dict:
    profil = _build_profil_entreprise(db)
    agents_dispo = _build_agents_disponibles(db)
    elements_figes = _build_elements_figes(conversation_id, db)

    system = (
        BOSS_ROUTING_PROMPT
        .replace("{PROFIL_ENTREPRISE}", profil)
        .replace("{AGENTS_DISPONIBLES}", agents_dispo)
        .replace("{ELEMENTS_FIGES}", elements_figes)
    )

    if kb_context:
        system += (
            "\n\n## Base documentaire\n\n"
            + kb_context
            + "\n\n(extraits des documents les plus pertinents — ne pas halluciner de sources)"
        )

    row = db.execute(
        "SELECT value FROM app_config WHERE key = 'sentinel_suggestion_pending'"
    ).fetchone()
    if row and row["value"] == "1":
        system += (
            "\n\n(Note interne : un bilan SENTINEL peut être proposé à l'utilisateur "
            "s'il exprime une insatisfaction ou demande une amélioration.)"
        )

    rows = db.execute(
        """SELECT role, content FROM messages
           WHERE conversation_id = ?
           ORDER BY created_at DESC
           LIMIT 15""",
        (conversation_id,),
    ).fetchall()
    messages = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    return {"system": system, "messages": messages}


def build_agent_payload(
    agent_code: str,
    task: str,
    db: sqlite3.Connection,
    kb_context: str = "",
) -> dict:
    row = db.execute(
        "SELECT system_prompt FROM agents WHERE code = ?", (agent_code,)
    ).fetchone()
    system = row["system_prompt"] if row else ""

    profil = _build_profil_entreprise(db)
    if kb_context:
        user_content = f"PROFIL ENTREPRISE :\n{profil}\n\nBASE DOCUMENTAIRE :\n{kb_context}\n\nTÂCHE :\n{task}"
    else:
        user_content = f"PROFIL ENTREPRISE :\n{profil}\n\nTÂCHE :\n{task}"

    return {"system": system, "messages": [{"role": "user", "content": user_content}]}


def build_synthesis_payload(
    user_message: str,
    agent_output: str,
    agent_code: str,
    db: sqlite3.Connection,
) -> dict:
    profil = _build_profil_entreprise(db)
    system = BOSS_SYNTHESIS_PROMPT.replace("{PROFIL_ENTREPRISE}", profil)

    if agent_code == "BOSS":
        user_content = f"Message de l'utilisateur :\n{user_message}"
    else:
        user_content = (
            f"Message de l'utilisateur :\n{user_message}\n\n"
            f"Réponse de l'agent {agent_code} :\n{agent_output}"
        )

    return {"system": system, "messages": [{"role": "user", "content": user_content}]}
