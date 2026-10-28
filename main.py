import pandas as pd
import requests
import os
from google.cloud import bigquery
import simplejson

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

def get_federal_state(gerit_file: str) -> None:

    gerit_file = os.path.join(PROJECT_PATH, gerit_file)

    inst_df = pd.DataFrame(columns=['inst_name', 'plz', 'ror_id', 'dfg_inst_id', 'federal_state'])

    df = pd.read_excel(gerit_file)

    for index, row in df.iterrows():
        plz = row['Postleitzahl vor Ort']
        r = requests.get(url=f'https://openplzapi.org/de/Localities?postalCode={plz}')
        data = r.json()

        inst_name = row['Name deutsch']
        ror_id = row['ROR-ID']
        dfg_inst_id = row['DFG-Inst-ID']
        federal_state = None

        if len(data) != 0:
            federal_state = data[0].get('federalState').get('name')

        inst = dict(
            inst_name=[inst_name],
            plz=[plz],
            ror_id=[ror_id],
            dfg_inst_id=[dfg_inst_id],
            federal_state=[federal_state],
        )

        df2 = pd.DataFrame.from_dict(inst)

        inst_df = pd.concat(objs=[inst_df, df2], ignore_index=True)

    inst_df.loc[(inst_df.inst_name == 'Universität Mannheim'), 'federal_state'] = 'Baden-Württemberg'
    inst_df.loc[(inst_df.inst_name == 'Universität zu Köln'), 'federal_state'] = 'Nordrhein-Westfalen'
    inst_df.loc[(inst_df.inst_name == 'Universität Trier'), 'federal_state'] = 'Rheinland-Pfalz'
    inst_df.loc[(inst_df.inst_name == 'Humboldt-Universität zu Berlin'), 'federal_state'] = 'Berlin'

    inst_df.to_csv(path_or_buf='raw_data/inst_with_federal_state.csv', index=False)

def get_kb_inst_data(kb_table: str) -> pd.DataFrame:

    client = bigquery.Client()

    kb_inst_df = client.query(
        f"""
        SELECT 
            DISTINCT
            kb_name.name AS parent_inst_name,
            ror AS parent_ror_id,
            dfg_instituts_id AS dfg_inst_id,
            current_sectors[SAFE_OFFSET(0)] AS inst_type,
        FROM {kb_table}_suppl AS kb
        JOIN {kb_table} AS kb_name
            ON kb.inst_id = kb_name.inst_id
        """
    ).to_dataframe()

    return kb_inst_df

def get_oal_inst_data(oal_table: str) -> pd.DataFrame:

    client = bigquery.Client()

    oal_inst_df = client.query(
        f"""
        WITH inst_data AS (
          SELECT  
            DISTINCT
            id AS parent_inst_id,
            ror AS parent_ror_id,
            id AS inst_id,
            ror AS ror_id,
            display_name AS parent_inst_name,
            display_name AS inst_name,
            'main' AS relationship
          FROM {oal_table} AS inst
          WHERE country_code = 'DE'
          UNION ALL 
          SELECT  
            DISTINCT
            inst.id AS parent_inst_id,
            inst.ror AS parent_ror_id,
            associated_institutions.id AS inst_id,
            associated_institutions.ror AS ror_id,
            inst.display_name AS parent_inst_name,
            associated_institutions.display_name AS inst_name,
            associated_institutions.relationship AS relationship
          FROM {oal_table} AS inst
          LEFT JOIN UNNEST(associated_institutions) AS associated_institutions
          WHERE inst.country_code = 'DE' AND relationship NOT IN ('parent')
        ) 
        SELECT 
          DISTINCT
            inst_data.inst_name,
            relationship,
            inst_data.inst_id,
            parent_inst_id,
            inst_data.ror_id,
            parent_ror_id
        FROM inst_data 
        """
    ).to_dataframe()

    return oal_inst_df

def create_output_file(gerit_file: str,
                       kb_table: str,
                       oal_table: str,
                       output_file: str,
                       use_cache: bool=True) -> None:


    gerit_csv = os.path.join(PROJECT_PATH, 'raw_data/inst_with_federal_state.csv')

    if os.path.exists(gerit_csv):
        if use_cache:
            pass
        else:
            get_federal_state(gerit_file)
    else:
        get_federal_state(gerit_file)


    gerit_data = pd.read_csv(filepath_or_buffer=gerit_csv)

    kb_data = get_kb_inst_data(kb_table)
    oal_data = get_oal_inst_data(oal_table)

    # os.remove(gerit_csv)

    gerit_data.rename(columns={'inst_name': 'parent_inst_name'}, inplace=True)

    df = oal_data.merge(kb_data, on='parent_ror_id', how='inner')
    df = df.merge(gerit_data[['federal_state', 'dfg_inst_id']], on='dfg_inst_id', how='left')
    df = df[['inst_name', 'parent_inst_name', 'relationship', 'inst_type', 'federal_state', 'inst_id', 'parent_inst_id',
             'ror_id', 'parent_ror_id']]

    update_df = pd.read_csv(filepath_or_buffer=os.path.join(PROJECT_PATH, 'rules/update.txt'), sep=' ')
    for _, row in update_df.iterrows():
        df.loc[(df.inst_name == row.inst_name) & (
                    df.parent_inst_name == row.parent_inst_name), 'relationship'] = row.relationship

    df = df[df.relationship != 'related']

    df.sort_values(by=['inst_type', 'parent_inst_name', 'relationship'],
                   ascending=False,
                   inplace=True)

    with open(os.path.join(PROJECT_PATH, output_file), 'w') as f:
        result = [simplejson.dumps(record, ensure_ascii=False, ignore_nan=True) for record in
                  df.to_dict(orient='records')]
        for line in result:
            f.write(line + '\n')


if __name__ == '__main__':
    create_output_file(
        gerit_file='raw_data/institutionen_gerit_202610.xlsx',
        kb_table='openalex-475813.oal_b_20260330.add_institution_lookup_kb',
        oal_table='subugoe-collaborative.openalex_walden.institutions',
        output_file='data/oal_kb_inst_map.jsonl',
        use_cache=True
    )


