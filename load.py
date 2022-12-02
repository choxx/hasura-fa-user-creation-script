import pandas as pd
import requests
import os
from dotenv import load_dotenv
import json
from time import sleep
from random import randrange
from requests import ReadTimeout


def user_service_create_user(username, password, roles, district, block, school_id, state='Himachal Pradesh'):
    data = {
        "registration": {
            "applicationId": f"{os.getenv('APPLICATION_ID')}",
            "preferredLanguages": ["en"],
            "roles": roles,
            "timezone": "Asia/Kolkata",
            "username": username,
            "usernameStatus": "ACTIVE",
            "data": {
                "roleData": {
                    "district": district,
                    "block": block,
                    "schoolId": '' if school_id == 'None' else school_id,
                    "state": state
                }
            }
        },
        "user": {
            "preferredLanguages": ["en"],
            "timezone": "Asia/Kolkata",
            "usernameStatus": "ACTIVE",
            "username": username,
            "password": password,
            "data": {
                "accountName": username
            }
        },
    }
    print(data)

    payload = json.dumps(data)
    headers = {
        'Authorization': f'{os.getenv("CREATE_USER_AUTHORIZATION")}',
        'x-application-id': f"{os.getenv('APPLICATION_ID')}",
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", f"{os.getenv('CREATE_USER_URL')}", headers=headers, data=payload)
    if 200 <= response.status_code < 300:
        data = json.loads(response.text)
        return data, None
    else:
        return None, json.loads(response.text)


def user_service_patch_user(user_id, block, district, role_data_user_type):
    data = {
        "data": {
            "roleData": {
                "block": block,
                "district": district,
                "userType": role_data_user_type
            }
        },
    }

    payload = json.dumps(data)
    headers = {
        'Authorization': f'{os.getenv("PATCH_USER_AUTHORIZATION")}',
        'x-application-id': f"{os.getenv('APPLICATION_ID')}",
        'Content-Type': 'application/json'
    }

    url = os.getenv('PATCH_USER_URL').replace(':userId', user_id)
    try:
        response = requests.request("PATCH", f"{url}", headers=headers, data=payload, timeout=10)
    except ReadTimeout as e:
        return None, {"error": str(e)}
    sleep(randrange(1, 10)/10)  # sleep for random time
    if 200 <= response.status_code < 300:
        data = json.loads(response.text)
        return data, None
    else:
        return None, json.loads(response.text)


def hasura_graphql_query(query):
    headers = {
        'x-hasura-admin-secret': f'{os.getenv("HASURA_SECRET")}',
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", f"{os.getenv('HASURA_URL')}", headers=headers, json={"query": query})
    if response.status_code == 200:
        data = json.loads(response.text)
        return data, None
    else:
        return None, json.loads(response.text)


def main():
    load_dotenv()
    fa_create_failed = []
    fa_patch_failed = []
    table_failed = []
    df = pd.read_csv(".sample.csv", encoding='utf-8', header=None)
    df = df.values.tolist()

    cnt = 0
    index = 0
    header_index_map = {}

    raw_mutation = os.getenv("TABLE_MUTATION", '')
    mutation_name = os.getenv("TABLE_MUTATION_NAME")  # we'll use this to parse response

    fa_create_user = os.getenv("FA_CREATE", '0') == '1'
    fa_update_user = os.getenv("FA_PATCH", '0') == '1'
    hasura_dump = os.getenv("HASURA_DUMP", '0') == '1'

    for d in df:
        mutation = raw_mutation
        if cnt == 0:
            # load the headers
            for k in d:
                header_index_map[k] = index
                index += 1
            if fa_create_user and ('fa_username' not in header_index_map or 'fa_password' not in header_index_map):
                print("Error!!! Both columns <fa_username> & <fa_password> must exists in CSV")
                exit(1)
            cnt = cnt + 1
            continue
        cnt = cnt + 1

        for k, v in header_index_map.items():
            mutation = mutation.replace("{" + k + "}", str(d[int(v)]))

        table_data = {}
        if hasura_dump:
            # print("Mutation:", mutation)
            table_data, status = hasura_graphql_query(mutation)
            print("TableData:", table_data['data'])
            if table_data is not None:
                print("For row: ", cnt, "TableId: ", table_data['data'][mutation_name]['id'])
            else:
                d.append(status)
                table_failed.append(d)
                print("Failed to insert into table for row: ", d)

        if fa_create_user:
            # check if there are roles in CSV
            if header_index_map['fa_roles'] and len(d[header_index_map['fa_roles']]) != 0:
                roles_list = [i.strip() for i in d[header_index_map['fa_roles']].split(',')]
            else:
                roles_list = []

            data, status = user_service_create_user(
                username=d[header_index_map['fa_username']],
                password=d[header_index_map['fa_password']],
                district=d[header_index_map['fa_district']],
                block=d[header_index_map['fa_block']],
                school_id=d[header_index_map['fa_school_id']],
                roles=roles_list
            )
            if data is not None:
                print("For row: ", cnt, "FA Username: ", d[header_index_map['fa_username']])
            else:
                d.append(status)
                fa_create_failed.append(d)
                print("Failed to create fusion auth id for row: ", cnt)

        if fa_update_user:
            # check if fa_user_id is passed as csv column; if not, throw error
            if header_index_map['fa_user_id'] and len(d[header_index_map['fa_user_id']]) == 0:
                print('You must pass `fa_user_id` column for updating a user.')
                exit(1)

            # check if there are roles in CSV
            # if header_index_map['fa_roles'] and len(d[header_index_map['fa_roles']]) != 0:
            #     roles_list = [i.strip() for i in d[header_index_map['fa_roles']].split(',')]
            # else:
            #     roles_list = []

            data, status = user_service_patch_user(
                user_id=d[header_index_map['fa_user_id']],
                block=d[header_index_map['fa_block']],
                district=d[header_index_map['fa_district']],
                role_data_user_type=d[header_index_map['fa_role_data_user_type']]
            )
            if data is not None:
                print("For row: ", cnt, "FA User ID: ", d[header_index_map['fa_user_id']])
            else:
                d.append(status)
                fa_patch_failed.append(d)
                print("Failed to PATCH fusion auth id for row: ", cnt)
    print("######################################################################")
    print("Failed FA Create entries", json.dumps(fa_create_failed))
    print("Failed FA Patch entries", json.dumps(fa_patch_failed))
    print("Failed Table entries", json.dumps(table_failed))


def get_dot_notation_var(input_dict, accessor_string):
    """Gets data from a dictionary using a dotted accessor-string"""
    current_data = input_dict
    for chunk in accessor_string.split('.'):
        current_data = current_data.get(chunk, {})
    return current_data


if __name__ == "__main__":
    main()
