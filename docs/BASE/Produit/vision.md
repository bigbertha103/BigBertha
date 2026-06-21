---
owner: Kinder + tezcatlypoca
last_updated: 2026-06-21
review_every: 30j
---

# Vision produit — BigBertha

> Ce fichier répond à : qu'est-ce qu'on vend, à qui, pourquoi eux, comment on se différencie.

---

## Proposition de valeur

**La contextualisation professionnelle accessible aux PME.**

Claude, ChatGPT permettent déjà tout ce que fait BigBertha — mais ça demande du prompt engineering, du paramétrage et des couches de personnalisation que les PME n'ont ni le temps ni les compétences d'acquérir.

BigBertha apporte cette couche clé en main :
- Onboarding entreprise en ~5 minutes (idée — aucune spec à ce stade)
- Mémoire et règles intégrées en standard (anti-hallucination, anti-perte de contexte, anti-répétition)
- Agents calibrés sur le secteur et le ton de l'entreprise
- Apprentissage automatique sur les interactions réelles via SENTINEL

## Cible

**PME françaises, B2B.**

Ni les structures à contraintes de sécurité extrêmes (elles iront vers des acteurs sécurité spécialisés), ni les entreprises déjà bien outillées (elles iront directement vers Claude/ChatGPT en forfait payant).

Notre cible : les entreprises **au centre du triangle Sécurité / Performance / Personnalisation** — qui veulent un peu des trois sans pousser à l'extrême sur aucun.

- Secteur(s) : *(à préciser)*
- Profil décideur : *(à préciser)*

## Triangle de positionnement

| Pôle | Ce que les clients y cherchent | Extrême hors-cible |
|---|---|---|
| Sécurité | Souveraineté, RGPD, juridiction FR/UE | Type EDF → acteurs sécurité spécialisés |
| Performance | Coût, stabilité, fiabilité | Déjà outillé → Claude/ChatGPT direct |
| Personnalisation | Contexte profond, agents sur-mesure | Très avancé → Claude Projects/forfaits directs |

## Différenciation

- Déploiement on-premise ou serveur français (vs SaaS cloud)
- Apprentissage automatique sur les propres données du client
- Mono-tenant = données client jamais mixées avec d'autres
- Interlocuteur unique perçu (Boss) sur une équipe d'agents spécialisés
- Agents personnalisables par secteur et ton — pas un ChatGPT générique rebrandé

## Ce que BigBertha N'est PAS

- Pas un chatbot grand public
- Pas un SaaS multi-tenant
- Pas une interface vers ChatGPT rebrandée
- Pas pour les extrêmes sécurité (type EDF) ni les extrêmes performance (déjà bien outillés)

## Versioning produit

- **V1** (conceptuel) : un seul modèle, contexte générique, 2-3 agents en ordre fixe
- **V2** (en cours) : RAG + apprentissage continu (SENTINEL) — l'outil se personnalise avec le temps d'usage
