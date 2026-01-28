#!/usr/bin/env python3
"""
Analyze OpenAPI schemas and generate parameter documentation
"""

import json
from pathlib import Path
from typing import Dict, Any, List

def extract_properties(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Extract input properties from OpenAPI schema"""
    try:
        # Navigate to the input schema
        paths = schema.get("paths", {})
        for path, methods in paths.items():
            post = methods.get("post", {})
            request_body = post.get("requestBody", {})
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            schema_ref = json_content.get("schema", {})

            # Resolve $ref if present
            if "$ref" in schema_ref:
                ref_path = schema_ref["$ref"].split("/")
                components = schema["components"]["schemas"]
                schema_name = ref_path[-1]
                resolved_schema = components.get(schema_name, {})
                properties = resolved_schema.get("properties", {})
                required = resolved_schema.get("required", [])
                return {
                    "properties": properties,
                    "required": required,
                    "components": components
                }
    except Exception as e:
        print(f"Error extracting properties: {e}")
    return {"properties": {}, "required": [], "components": {}}

def resolve_ref(ref: str, components: Dict) -> Dict:
    """Resolve $ref to actual schema"""
    if ref.startswith("#/components/schemas/"):
        schema_name = ref.split("/")[-1]
        return components.get(schema_name, {})
    return {}

def format_type(prop: Dict, components: Dict) -> str:
    """Format property type description"""
    if "$ref" in prop:
        ref_schema = resolve_ref(prop["$ref"], components)
        return f"object ({prop['$ref'].split('/')[-1]})"

    prop_type = prop.get("type", "")
    if "anyOf" in prop:
        types = [t.get("type", "?") for t in prop["anyOf"]]
        return " | ".join(types)

    if prop_type == "array":
        items = prop.get("items", {})
        if "$ref" in items:
            item_type = items["$ref"].split("/")[-1]
            return f"array<{item_type}>"
        item_type = items.get("type", "?")
        return f"array<{item_type}>"

    if prop_type == "number" or prop_type == "integer":
        minimum = prop.get("minimum")
        maximum = prop.get("maximum")
        if minimum is not None and maximum is not None:
            return f"{prop_type} ({minimum}-{maximum})"
        elif minimum is not None:
            return f"{prop_type} (≥{minimum})"
        elif maximum is not None:
            return f"{prop_type} (≤{maximum})"

    return prop_type

def analyze_schema(schema_file: Path) -> Dict[str, Any]:
    """Analyze a single schema file"""
    with open(schema_file) as f:
        schema = json.load(f)

    result = extract_properties(schema)
    properties = result["properties"]
    required = result["required"]
    components = result["components"]

    params = []
    for name, prop in properties.items():
        is_required = name in required
        param_type = format_type(prop, components)
        description = prop.get("description", "")
        default = prop.get("default")

        param_info = {
            "name": name,
            "type": param_type,
            "required": is_required,
            "description": description,
            "default": default
        }

        # Add enum values if present
        if "enum" in prop:
            param_info["enum"] = prop["enum"]

        params.append(param_info)

    return {
        "endpoint_id": schema_file.stem.replace("_", "/", 2),  # Convert filename back to endpoint_id
        "parameters": params,
        "required_count": len(required),
        "total_count": len(properties)
    }

def generate_markdown(analyses: List[Dict], output_file: Path):
    """Generate markdown documentation"""
    lines = ["# Model Parameter Reference\n"]
    lines.append(f"Generated from {len(analyses)} model schemas\n")
    lines.append("---\n")

    for analysis in sorted(analyses, key=lambda x: x["endpoint_id"]):
        endpoint = analysis["endpoint_id"]
        params = analysis["parameters"]

        lines.append(f"## {endpoint}\n")
        lines.append(f"**Parameters**: {analysis['total_count']} total, {analysis['required_count']} required\n")

        # Required parameters
        required_params = [p for p in params if p["required"]]
        if required_params:
            lines.append("\n### Required Parameters\n")
            for p in required_params:
                lines.append(f"- **`{p['name']}`** (`{p['type']}`)")
                if p["description"]:
                    lines.append(f": {p['description']}")
                lines.append("\n")

        # Optional parameters
        optional_params = [p for p in params if not p["required"]]
        if optional_params:
            lines.append("\n### Optional Parameters\n")
            lines.append("| Parameter | Type | Default | Description |\n")
            lines.append("|-----------|------|---------|-------------|\n")
            for p in optional_params:
                default = f"`{p['default']}`" if p['default'] is not None else "-"
                desc = p['description'][:100] + "..." if len(p['description']) > 100 else p['description']
                lines.append(f"| `{p['name']}` | {p['type']} | {default} | {desc} |\n")

        lines.append("\n---\n\n")

    with open(output_file, "w") as f:
        f.writelines(lines)

def main():
    schemas_dir = Path(__file__).parent.parent / "outputs" / "schemas"

    if not schemas_dir.exists():
        print("❌ Schemas directory not found. Run fetch_schemas.py first.")
        return

    # Analyze all schemas
    schema_files = list(schemas_dir.glob("*.json"))
    schema_files = [f for f in schema_files if not f.name.startswith("_")]

    print(f"📊 Analyzing {len(schema_files)} schemas...")

    analyses = []
    for schema_file in schema_files:
        print(f"   Analyzing {schema_file.name}...", end=" ")
        try:
            analysis = analyze_schema(schema_file)
            analyses.append(analysis)
            print(f"✅ {analysis['total_count']} params")
        except Exception as e:
            print(f"❌ Error: {e}")

    # Generate markdown
    output_file = schemas_dir.parent / "MODEL_PARAMETERS.md"
    generate_markdown(analyses, output_file)

    print(f"\n✅ Documentation generated: {output_file}")
    print(f"📊 Summary:")
    print(f"   - {len(analyses)} models analyzed")
    total_params = sum(a["total_count"] for a in analyses)
    print(f"   - {total_params} total parameters documented")

if __name__ == "__main__":
    main()
