# Pipeline de données ML pour projets retail — Guide Neuraltech

## Schéma général
```
Sources données → Extraction → Normalisation → Stockage intermédiaire → Indexation RAG → Consommation IA
```

## Sources typiques en retail

| Source | Format courant | Fréquence de mise à jour |
|---|---|---|
| ERP (SAP, Microsoft Dynamics) | CSV, XML, API REST | Quotidien ou temps réel |
| PIM (Akeneo, Bynder) | JSON, CSV, PDF | Hebdomadaire |
| CRM | API, CSV export | Quotidien |
| Emails et documents fournisseurs | PDF, Word, Excel | Discontinu |
| Données de vente (caisse) | CSV, Parquet | Quotidien |
| Images produits | JPEG, PNG, WEBP | Occasionnel |

## Extraction

### Points d'attention critiques
- **Exports ERP** : souvent en CSV ou Excel avec des colonnes mal nommées et des encodages legacy (ISO-8859-1). Prévoir un ETL robuste avec gestion des erreurs.
- **Fiches produits PDF** : rarement nativement text-selectable (scan ou export depuis un logiciel propriétaire). OCR nécessaire — Tesseract v5 ou Google Document AI selon le budget.
- **Emails fournisseurs** : format MIME, pièces jointes hétérogènes (Excel, PDF, images). Parser MIME puis extraire les pièces jointes.

## Normalisation

### Encodage
Les données ERP legacy contiennent fréquemment des caractères mal encodés (é → é, etc.). Forcer l'encodage UTF-8 en sortie de toute extraction.

### Dates
Formats rencontrés sur les projets Neuraltech : DD/MM/YYYY (fiches produits FR), MM/DD/YYYY (données US), YYYY-MM-DD (APIs), timestamps Unix (logs caisse). Normaliser en ISO 8601 (YYYY-MM-DDTHH:MM:SSZ) dans le stockage intermédiaire.

### Codes produits
Les référentiels sont souvent différents entre ERP (code interne), PIM (code EAN/GTIN), et CRM (code client). Un mapping est nécessaire avant toute jointure ou indexation. Clé primaire recommandée : code EAN/GTIN.

## Indexation pour le RAG

### Stratégie de chunking (recommandations issues des missions Neuraltech)
- **Fiches produits** : 1 fiche = 1 chunk. Ne pas découper une fiche en plusieurs chunks (perte de cohérence sémantique).
- **Procédures internes** : chunking par section (titre H2 = frontière de chunk). Overlap de 100 tokens entre sections adjacentes.
- **Emails** : 1 email = 1 chunk si < 500 tokens, sinon découper par paragraphe.
- **Données structurées (prix, stocks)** : ne pas indexer en RAG. Accès via SQL ou API dédiée, injecté dans le prompt si nécessaire.

### Metadata obligatoires dans les embeddings
```json
{
  "source": "PIM / ERP / email",
  "date_mise_a_jour": "2026-06-15",
  "categorie_produit": "Épicerie / Mode / ...",
  "confidentialite": "public / interne / confidentiel"
}
```

### Fraîcheur des données
- **Indexation incrémentale** : traiter uniquement le delta (documents modifiés depuis la dernière indexation) plutôt que ré-indexer l'intégralité du corpus.
- **TTL (time-to-live)** : configurer une expiration sur les embeddings de données à forte péremption (prix, promotions). Une donnée expirée est retirée des résultats de recherche même si elle n'a pas été ré-indexée.
- **Alertes** : mettre en place une alerte si le taux de données fraîches passe sous 90% (indicateur de dérive de la KB).
