import os
from copy import deepcopy

import requests
import yaml

from common.recordlog import logs
from conf.operationConfig import OperationConfig
from conf.setting import DIR_BASE


class SwaggerParser:
    """
    Generate framework-compatible YAML cases from Swagger/OpenAPI documents.

    Supported inputs:
    - Swagger 2.0 parameters and definitions
    - OpenAPI 3.x requestBody and components.schemas
    - local $ref references such as #/definitions/Foo or #/components/schemas/Foo
    """

    def __init__(self):
        self.conf = OperationConfig()
        self.swagger_url = self.conf.get_section_swagger_url()
        relative_dir = self.conf.get_section_swagger_dir().strip("./")
        self.output_dir = os.path.join(DIR_BASE, relative_dir)
        self.swagger_data = {}
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_data(self):
        try:
            logs.info(f"Fetching Swagger/OpenAPI document: {self.swagger_url}")
            res = requests.get(self.swagger_url, timeout=15)
            res.raise_for_status()
            self.swagger_data = res.json()
            return self.swagger_data
        except Exception as e:
            logs.error(f"Swagger/OpenAPI fetch failed: {e}")
            return None

    def resolve_ref(self, ref):
        if not ref or not ref.startswith("#/"):
            return {}

        node = self.swagger_data
        for part in ref.lstrip("#/").split("/"):
            node = node.get(part, {})
            if not node:
                return {}
        return deepcopy(node)

    def normalize_schema(self, schema):
        if not isinstance(schema, dict):
            return {}
        if "$ref" in schema:
            return self.normalize_schema(self.resolve_ref(schema["$ref"]))
        if "schema" in schema:
            return self.normalize_schema(schema["schema"])
        return schema

    def mock_value(self, field_name, schema):
        schema = self.normalize_schema(schema)
        schema_type = schema.get("type")
        field_name = (field_name or "").lower()

        if "enum" in schema and schema["enum"]:
            return schema["enum"][0]
        if "token" in field_name:
            return "${get_extract_data(token)}"
        if "time" in field_name or schema.get("format") in ["date-time", "date"]:
            return "${timestamp()}"
        if "id" in field_name:
            return 1
        if "phone" in field_name or "tel" in field_name:
            return "13800000000"
        if "price" in field_name or "amount" in field_name or "freight" in field_name:
            return 100
        if schema_type in ["integer", "number"]:
            return 1
        if schema_type == "boolean":
            return True
        if schema_type == "array":
            item_schema = schema.get("items", {"type": "string"})
            return [self.mock_value(field_name, item_schema)]
        if schema_type == "object" or "properties" in schema:
            return self.build_mock_by_schema(schema)
        return "auto_string"

    def build_mock_by_schema(self, schema):
        schema = self.normalize_schema(schema)
        properties = schema.get("properties", {})
        if not properties:
            return {}

        mock_data = {}
        required = set(schema.get("required", []))
        selected_fields = required or set(properties.keys())
        for field_name, field_schema in properties.items():
            if field_name in selected_fields:
                mock_data[field_name] = self.mock_value(field_name, field_schema)
        return mock_data

    def build_parameters(self, operation):
        query_params = {}
        body_data = {}

        for param in operation.get("parameters", []):
            param = self.normalize_schema(param)
            name = param.get("name")
            if not name:
                continue

            location = param.get("in")
            if location in ["query", "path", "header", "formData"]:
                query_params[name] = self.mock_value(name, param)
            elif location == "body":
                body_data.update(self.build_mock_by_schema(param))

        request_body = operation.get("requestBody", {})
        content = request_body.get("content", {}) if isinstance(request_body, dict) else {}
        json_media = content.get("application/json") or content.get("*/*") or {}
        if json_media:
            body_data.update(self.build_mock_by_schema(json_media.get("schema", {})))

        return query_params, body_data

    def build_case(self, url, method, operation):
        query_params, body_data = self.build_parameters(operation)
        method_upper = method.upper()
        param_key = "params" if method.lower() == "get" else "json"
        params = query_params if param_key == "params" else body_data or query_params
        api_name = operation.get("summary") or operation.get("operationId") or f"{method_upper} {url}"

        case = {
            "baseInfo": {
                "api_name": api_name,
                "url": url,
                "method": method_upper,
                "header": {
                    "Content-Type": "application/json;charset=UTF-8"
                    if param_key == "json"
                    else "application/x-www-form-urlencoded;charset=UTF-8"
                },
            },
            "testCase": [
                {
                    "case_name": f"auto generated - {api_name} - success",
                    param_key: params or {"mock_key": "mock_value"},
                    "validation": [
                        {"contains": {"status_code": 200}},
                    ],
                }
            ],
        }

        if "security" in operation:
            case["baseInfo"]["header"]["token"] = "${get_extract_data(token)}"
        return [case]

    def write_case_file(self, url, case_structure):
        file_name = url.strip("/").replace("/", "_").replace("{", "").replace("}", "")
        file_name = file_name or "root"
        file_path = os.path.join(self.output_dir, f"{file_name}.yaml")
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(case_structure, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def generate_yaml(self):
        swagger_data = self.fetch_data()
        if not swagger_data:
            return

        count = 0
        for url, methods in swagger_data.get("paths", {}).items():
            for method, operation in methods.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue
                case_structure = self.build_case(url, method, operation)
                self.write_case_file(url, case_structure)
                count += 1

        logs.info(f"Swagger/OpenAPI parsing completed, generated {count} YAML case files.")
