# Abbildung der deutschen Forschungslandschaft in OpenAlex: Vorschlag für eine Institutionszuordnung

## Beschreibung

Bei der Analyse von Publikationen in OpenAlex stößt man häufig auf Schwierigkeiten, wenn es darum geht, 
die zugehörigen Einrichtungen gezielt nach bestimmten Kriterien zu filtern. So fehlt die 
Möglichkeit, Einrichtungen nach ihrem Typ zu unterscheiden – etwa zwischen Universitäten, Fachhochschulen oder Forschungsinstituten. 
Auch eine Filterung nach dem Bundesland ist nicht direkt möglich, was die räumliche Analyse von Forschungsaktivitäten erschwert. 
Zudem werden viele Einrichtungen in OpenAlex in mehrere Teileinheiten aufgeteilt, wie beispielsweise die Universität selbst, 
die Universitätsbibliothek, die Universitätsmedizin oder spezialisierte Forschungseinrichtungen. 
Dadurch wird die Datenabfrage komplexer, die Ergebnisse schwerer vergleichbar und die Analyse insgesamt aufwendiger – besonders 
wenn man übergeordnete Strukturen oder regionale Verteilungen untersuchen möchte. Diese Probleme möchte ich mit dem folgenden Datensatz lösen.

## Datensatz

Für das Datenset wurden die folgenden Datenquellen miteinander kombiniert:

- [GERiT](https://gerit.org/de/)
- [OpenAlex](https://openalex.org)
- [Kompetenznetzwerk Bibliometrie](https://bibliometrie.info)

Um die Daten nachzunutzen, stehen folgende Optionen zur Verfügung:

- [Google BigQuery](https://console.cloud.google.com/bigquery?ws=!1m4!1m3!3m2!1ssubugoe-collaborative!2sresources): subugoe-collaborative.resources.oal_kb_inst_map (frei zugänglich)
- [GitHub](data/oal_kb_inst_map.jsonl): Die Datei `oal_kb_inst_map.jsonl` enthält das komplette Datenset

### Datenschema

| Datenfeld | Datentyp | Beschreibung |
| --- | --- | --- |
| inst_name | STRING | Name der Einrichtung (aus OpenAlex) |
| parent_inst_name | STRING | Name der übergeordneten Einrichtung (aus dem KB) |
| relationship | STRING | ROR-Beziehung |
| inst_type | STRING | Klassifikation der übergeordneten Einrichtung (z.B. Universität oder Fachhochschule) |
| federal_state | STRING | Bundesland |
| inst_id | STRING | OpenAlex Institution ID |
| parent_inst_id | STRING | OpenAlex Institution ID der übergeordneten Einrichtung |
| ror_id | STRING | ROR ID (aus OpenAlex) |
| parent_ror_id | STRING | ROR ID der übergeordneten Einrichtung |

```json
{
  "inst_name": "Niedersächsische Staats- und Universitätsbibliothek Göttingen", 
  "parent_inst_name": "Georg-August-Universität Göttingen", 
  "relationship": "child", 
  "inst_type": "uni", 
  "federal_state": "Niedersachsen", 
  "inst_id": "https://openalex.org/I4387154063", 
  "parent_inst_id": "https://openalex.org/I74656192",
  "ror_id": "https://ror.org/05745n787", 
  "parent_ror_id": "https://ror.org/01y9bpm73"
}
```

## Beispiele

### Wie erhalte ich den Publikationsoutput von Einrichtungen in OpenAlex gefiltert nach deutschen Universitäten?

```sql
SELECT 
  parent_inst_name AS university_name, 
  COUNT(DISTINCT(doi)) AS number_of_articles
FROM subugoe-collaborative.openalex_walden.works AS oal
LEFT JOIN UNNEST(authorships) AS aut
LEFT JOIN UNNEST(aut.affiliations) AS aff
LEFT JOIN UNNEST(aff.institution_ids) AS oal_inst_id 
JOIN subugoe-collaborative.resources.oal_kb_inst_map AS kb
  ON oal_inst_id = kb.inst_id
WHERE publication_year = 2025 
  AND type = 'article'
  AND inst_type = 'uni'
GROUP BY parent_inst_name
ORDER BY n DESC
LIMIT 10
```

| university_name | number_of_articles |
| --- | --- |
| Freie Universität Berlin | 10497 |
| Humboldt-Universität zu Berlin | 10083 |
| Ludwig-Maximilians-Universität München (LMU) | 9794 |
| Technische Universität München (TUM) | 9394 |
| Ruprecht-Karls-Universität Heidelberg | 9229 |
| Rheinisch-Westfälische Technische Hochschule Aachen | 8551 |
| Charité - Universitätsmedizin Berlin | 7768 |
| Universität Hamburg | 7416 |
| Technische Universität Dresden | 6321 |
| Friedrich-Alexander-Universität Erlangen-Nürnberg | 5695 |

### In welchem Bundesland werden die meisten Publikationen veröffentlicht?

```sql
SELECT  
  federal_state,
  COUNT(DISTINCT(doi)) AS number_of_articles
FROM subugoe-collaborative.openalex_walden.works AS oal
LEFT JOIN UNNEST(authorships) AS aut
LEFT JOIN UNNEST(aut.affiliations) AS aff
LEFT JOIN UNNEST(aff.institution_ids) AS oal_inst_id 
JOIN subugoe-collaborative.resources.oal_kb_inst_map AS kb
  ON oal_inst_id = kb.inst_id
WHERE publication_year = 2025 
  AND type = 'article'
  AND inst_type = 'uni'
GROUP BY federal_state 
ORDER BY number_of_articles DESC
```

| federal_state | number_of_articles |
| --- | --- |
| Nordrhein-Westfalen | 38696 |
| Bayern | 31845 |
| Baden-Württemberg | 25973 |
| Berlin | 16124 |
| Niedersachsen | 14872 |
| Hessen | 12888 |
| Sachsen | 11735 |
| Hamburg | 8466 |
| Rheinland-Pfalz | 6435 |
| Schleswig-Holstein | 5628 |
| Thüringen | 4550 |
| Sachsen-Anhalt | 4175 |
| Brandenburg | 3991 |
| Mecklenburg-Vorpommern | 3774 |
| Bremen | 2474 |
| Saarland | 2437 |

### Welche Einrichtungen in OpenAlex gehören zur Universität Göttingen?

```sql
SELECT *
FROM `subugoe-collaborative.resources.oal_kb_inst_map` 
WHERE parent_inst_name = 'Georg-August-Universität Göttingen'
```

| inst_name | parent_inst_name | relationship | inst_type | federal_state | inst_id | parent_inst_id | ror_id | parent_ror_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| University of Göttingen | Georg-August-Universität Göttingen | main | uni | Niedersachsen | https://openalex.org/I74656192 | https://openalex.org/I74656192 | https://ror.org/01y9bpm73 | https://ror.org/01y9bpm73 |
| Gesellschaft für wissenschaftliche Datenverarbeitung mbH Göttingen | Georg-August-Universität Göttingen | child | uni | Niedersachsen | https://openalex.org/I4210091733 | https://openalex.org/I74656192 | https://ror.org/00cd95c65 | https://ror.org/01y9bpm73 |
| Universitätsmedizin Göttingen | Georg-August-Universität Göttingen | child | uni | Niedersachsen | https://openalex.org/I4210116730 | https://openalex.org/I74656192 | https://ror.org/021ft0n22 | https://ror.org/01y9bpm73 |
| Institute for Small Business Economics | Georg-August-Universität Göttingen | child | uni | Niedersachsen | https://openalex.org/I4210126419 | https://openalex.org/I74656192 | https://ror.org/031q2en94 | https://ror.org/01y9bpm73 |
| Niedersächsische Staats- und Universitätsbibliothek Göttingen | Georg-August-Universität Göttingen | child | uni | Niedersachsen | https://openalex.org/I4387154063 | https://openalex.org/I74656192 | https://ror.org/05745n787 | https://ror.org/01y9bpm73 |
| Multiscale Bioimaging | Georg-August-Universität Göttingen | child | uni | Niedersachsen | https://openalex.org/I4387156107 | https://openalex.org/I74656192 | https://ror.org/05xy1nn52 | https://ror.org/01y9bpm73 |
| Göttingen Campus Institut für Dynamic biologischer Netzwerke | Georg-August-Universität Göttingen | child | uni | Niedersachsen | https://openalex.org/I4405259601 | https://openalex.org/I74656192 | https://ror.org/02f04tm31 | https://ror.org/01y9bpm73 |
| Universitätsverlag Göttingen | Georg-August-Universität Göttingen | child | uni | Niedersachsen | https://openalex.org/I4405263319 | https://openalex.org/I74656192 | https://ror.org/057621003 | https://ror.org/01y9bpm73 |
| Campus-Institut Data Science (CIDAS) | Georg-August-Universität Göttingen | child | uni | Niedersachsen | https://openalex.org/I4405263634 | https://openalex.org/I74656192 | https://ror.org/044sxzm68 | https://ror.org/01y9bpm73 |

## Nutzung von KI

Die Dokumentation wurde mit Hilfe von [GWDG Chat AI](https://docs.hpc.gwdg.de/services/ai-services/chat-ai/index.html) und [Qwen](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507-FP8) erstellt. 

## Kontakt

Nick Haupka, Staats- und Universitätsbibliothek Göttingen. nick.haupka@sub.uni-goettingen.de