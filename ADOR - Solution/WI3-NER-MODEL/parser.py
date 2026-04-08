# parser.py
# Core parsing logic: extract from tables, enrich, validate, build output

import re
import logging
from pathlib import Path
from docx import Document

from fields import fuzzy_match, TARGET_ENTITIES
from schema import SCHEMA

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)


def extract_from_tables(doc: Document) -> dict:
    entities = {}

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]

            if len(cells) < 2 or not cells[0] or not cells[1]:
                continue
            if cells[0] == cells[1]:
                continue

            key   = cells[0].strip().lower()
            value = cells[1].strip()

            entity_name, matched_variant, is_fuzzy, dist = fuzzy_match(key)

            if entity_name and entity_name in TARGET_ENTITIES:
                if entity_name not in entities:
                    entities[entity_name] = value
                    if is_fuzzy:
                        log.info(f"FUZZY : '{cells[0]}' ~ '{matched_variant}' (dist={dist}) -> {entity_name}")
                    else:
                        log.info(f"EXACT : '{cells[0]}' -> {entity_name}")

    return entities


def validate_entities(entities: dict) -> list:
    errors = []
    for field, rules in SCHEMA.items():
        value = entities.get(field, None)

        if value is None and rules["required"]:
            errors.append(f"MISSING required field: '{field}'")

        if value is not None and rules["pattern"]:
            if not re.match(rules["pattern"], value):
                errors.append(f"FORMAT ERROR: '{field}' = '{value}' does not match '{rules['format']}'")

    return errors


def parse_docx(file_path: str) -> dict:
    log.info(f"Parsing: {file_path}")
    doc      = Document(file_path)
    entities = extract_from_tables(doc)
    errors   = validate_entities(entities)

    return {
        "source":        Path(file_path).name,
        "engine":        "rule_based_parser",
        "document_type": "term_sheet_docx",
        "entities":      {k: entities.get(k, None) for k in TARGET_ENTITIES},
        "errors":        errors,
    }
