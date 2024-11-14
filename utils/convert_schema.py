import os
import json

def json_schema_to_bq_fields(properties, required_fields):
    bq_fields = []
    for field_name, field_props in properties.items():
        field = {}
        field['name'] = field_name

        # Determine the field type
        json_type = field_props.get('type')
        if isinstance(json_type, list):
            # Handle types like ["string", "null"]
            json_type = [t for t in json_type if t != 'null'][0]

        if json_type == 'string':
            if field_props.get('format') == 'date-time':
                field['type'] = 'TIMESTAMP'
            else:
                field['type'] = 'STRING'
        elif json_type == 'integer':
            field['type'] = 'INT64'
        elif json_type == 'number':
            field['type'] = 'FLOAT64'
        elif json_type == 'boolean':
            field['type'] = 'BOOL'
        elif json_type == 'object':
            field['type'] = 'RECORD'
            field['fields'] = json_schema_to_bq_fields(field_props['properties'], field_props.get('required', []))
        elif json_type == 'array':
            field['type'] = 'RECORD'  # BigQuery handles arrays as repeated records
            field['mode'] = 'REPEATED'
            # Handle array items
            items_props = field_props.get('items')
            if items_props:
                if items_props.get('type') == 'object':
                    field['fields'] = json_schema_to_bq_fields(items_props['properties'], items_props.get('required', []))
                else:
                    # For simplicity, skip non-object arrays
                    continue
        else:
            field['type'] = 'STRING'  # Default to STRING for unknown types

        # Set the mode
        if field_name in required_fields:
            field['mode'] = 'REQUIRED'
        else:
            field['mode'] = 'NULLABLE'

        # Add description if available
        if 'description' in field_props:
            field['description'] = field_props['description']

        bq_fields.append(field)

    # Add an additional content_hash column
    field = {}
    field['name'] = 'content_hash'
    field['type'] = 'STRING'
    field['mode'] = 'NULLABLE'
    field['description'] = 'Content that was hashed in order to uniquely identify messages'
    bq_fields.append(field)

    return bq_fields

if __name__ == "__main__":
    # Load your JSON Schema
    with open('./utils/schema.json', 'r') as f:
        json_schema = json.load(f)

    # Start conversion from the root properties
    required_fields = json_schema.get('required', [])
    bq_schema = json_schema_to_bq_fields(json_schema['properties'], required_fields)

    # Ensure the 'schemas' directory exists
    schemas_dir = './infrastructure/schemas'
    os.makedirs(schemas_dir, exist_ok=True)

    # Save the BigQuery schema to a JSON file
    schema_file_path = os.path.join(schemas_dir, 'bq_schema.json')
    with open(schema_file_path, 'w') as f:
        json.dump(bq_schema, f, indent=2)
