# Hasura-Fusion Auth User Creation Generic Script
This is a generic script to dump users into any Hasura Table & Fusion Auth (via User Service).

## Configuration
### Hasura:
- `HASURA_URL`: Hasura Graphql Endpoint
- `HASURA_SECRET`: Hasura Admin Secret
- `TABLE_MUTATION_NAME`: plane name of Mutation query; will be used to fetch resultant object (not must as of now)
- `TABLE_MUTATION`: complete mutation query with variables in placeholder like `{VARIABLE_VALUE}`
- `HASURA_DUMP`: To enable/disable dumping in Hasura via script; 1 = Enable, 2 = Disable

### Fusion Auth:
- `APPLICATION_ID`: FA application ID
- `CREATE_USER_URL`: User Service POST endpoint URL for user Signup
- `CREATE_USER_AUTHORIZATION`: FA API key
- `FA_DUMP`: To enable/disable dumping in Hasura via script; 1 = Enable, 2 = Disable

### Environment Setup:
- Copy `env.example` to `.env` & configure all the above variables
- Use `sample.csv` file as reference & create/upload a new file named `.sample.csv` containing:
  - All the columns which are present in mutation query configured above via variable: `TABLE_MUTATION`
  - The columns `fa_username`,`fa_password`,`fa_roles`,`fa_user_reg_data_json`,`fa_user_reg_data_variables` are special columns and are being used to pass username, pass, roles, custom user registration data via generic approach. All these columns must be present (even though no data needs to be passed for roles, user registration).
> Note: The order of columns is not necessarily to be maintained in any specific order.

## Running
Simply hit `docker-compose up --build`.

## Limitations
- Only fresh users can be dumped into Fusion Auth. Support for adding a new registration to be added..