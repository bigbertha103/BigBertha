# Prompt de clôture de session — BigBertha

> Exécuter ce prompt à la fin de chaque session de travail sur BigBertha.
> L'IA exécute les étapes séquentiellement et s'arrête aux points de validation.

---

## Prompt à copier-coller

```
Tu es Claude Code sur le projet BigBertha (V:\DEV\PROJETS\intelligence_artificielle\Big Bertha).

Lance le protocole de clôture de session en 5 étapes.

---

ÉTAPE 1 — SYNC
Vérifie que tu es sur la branche v2.
Lance : git pull
Signale tout conflit avant d'aller plus loin. Si conflit : STOP, résoudre avec moi.

ÉTAPE 2 — LECTURE SESSION
Relis la conversation de cette session. Extrais et liste :
a) Nouvelles décisions prises (technique, produit, commercial)
b) Nouveaux termes utilisés qui ne sont pas dans docs/BASE/langage.md
c) Éléments qui contredisent ou complètent un fichier docs/BASE/
d) Ce qui a été testé et le résultat (succès / échec / partiel)
e) Bugs découverts non encore corrigés

Présente cette liste avant de passer à l'étape 3.
→ VALIDATION : je confirme ou corrige la liste.

---

ÉTAPE 3 — REVUE BASE
Pour chaque fichier dans docs/BASE/ :
- Lis le champ last_updated
- Si la date dépasse 30 jours (ou si le champ est "—") : signale "À revoir"
- Compare le contenu avec les éléments extraits à l'étape 2

Propose la liste complète des modifications à appliquer :
- Fichier → type de modification (ajout / correction / suppression)
- Contenu proposé en 1-2 lignes

→ VALIDATION : j'approuve, modifie ou rejette chaque proposition.

---

ÉTAPE 4 — ÉCRITURE
Applique uniquement les modifications validées à l'étape 3.
Pour chaque fichier modifié :
- Mets à jour le champ last_updated avec la date du jour
- Mets à jour docs/BASE/INDEX.md si un nouveau fichier a été créé ou modifié

Si une décision figée a changé : mets à jour docs/BASE/elements_figes.md ET PROJET_CONTEXTE.md section 6.

Ajoute une ligne dans CHANGELOG.md pour chaque fichier docs/BASE modifié :
[DOC] docs/BASE/[fichier] — [description en une ligne]

→ VALIDATION : je vérifie les fichiers modifiés.

---

ÉTAPE 5 — COMMIT
Propose un message de commit au format :
doc(base): [liste courte des fichiers] — [résumé en une ligne]

→ VALIDATION : je confirme le commit.
Lance : git add [fichiers modifiés] && git commit -m "[message validé]"
Lance : git push origin v2

Clôture terminée.
```

---

## Notes d'utilisation

- Ce prompt s'exécute dans Claude Code (pas Cascade)
- Temps estimé : 10-15 minutes
- Ne jamais skipper l'étape 1 (sync) — risque de conflit avec l'autre personne
- Si la session était courte et sans décision : l'étape 3 peut ne produire aucune modification (normal)
