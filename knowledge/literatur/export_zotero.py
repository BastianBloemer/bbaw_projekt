import sqlite3
import json

DB = "/tmp/claude-1000/-home-bastian-Dokumente/ac7da092-4503-4c71-9796-7cff9873957e/scratchpad/zotero_copy.sqlite"
OUT = "/home/bastian/Dokumente/knowledge/literatur/literatur.json"

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

# top-level bibliographic items only: exclude attachments, notes, annotations
cur.execute("""
    SELECT i.itemID, i.key, i.libraryID, it.typeName
    FROM items i
    JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
    WHERE i.itemID NOT IN (SELECT itemID FROM itemAttachments)
      AND i.itemID NOT IN (SELECT itemID FROM itemNotes)
      AND it.typeName NOT IN ('annotation', 'note', 'attachment')
    ORDER BY i.itemID
""")
items = cur.fetchall()

library_names = {1: "Persönliche Bibliothek"}
cur.execute("SELECT libraryID, name FROM groups")
for row in cur.fetchall():
    library_names[row["libraryID"]] = row["name"]

def get_field_value(item_id, field_name):
    cur.execute("""
        SELECT idv.value
        FROM itemData idat
        JOIN fields f ON idat.fieldID = f.fieldID
        JOIN itemDataValues idv ON idat.valueID = idv.valueID
        WHERE idat.itemID = ? AND f.fieldName = ?
    """, (item_id, field_name))
    row = cur.fetchone()
    return row["value"] if row else None

def get_creators(item_id):
    cur.execute("""
        SELECT c.firstName, c.lastName, ct.creatorType
        FROM itemCreators ic
        JOIN creators c ON ic.creatorID = c.creatorID
        JOIN creatorTypes ct ON ic.creatorTypeID = ct.creatorTypeID
        WHERE ic.itemID = ?
        ORDER BY ic.orderIndex
    """, (item_id,))
    result = []
    for row in cur.fetchall():
        name = " ".join(p for p in [row["firstName"], row["lastName"]] if p)
        result.append({"name": name, "type": row["creatorType"]})
    return result

def get_tags(item_id):
    cur.execute("""
        SELECT t.name FROM itemTags it JOIN tags t ON it.tagID = t.tagID
        WHERE it.itemID = ?
    """, (item_id,))
    return [row["name"] for row in cur.fetchall()]

def get_collections(item_id):
    cur.execute("""
        SELECT c.collectionName FROM collectionItems ci JOIN collections c ON ci.collectionID = c.collectionID
        WHERE ci.itemID = ?
    """, (item_id,))
    return [row["collectionName"] for row in cur.fetchall()]

FIELDS = {
    "title": "title",
    "date": "date",
    "publicationTitle": "publicationTitle",
    "publisher": "publisher",
    "DOI": "DOI",
    "url": "url",
    "abstractNote": "abstractNote",
    "language": "language",
    "ISBN": "ISBN",
}

output = []
for item in items:
    item_id = item["itemID"]
    entry = {
        "key": item["key"],
        "itemType": item["typeName"],
        "library": library_names.get(item["libraryID"], f"library {item['libraryID']}"),
    }
    for out_name, field_name in FIELDS.items():
        val = get_field_value(item_id, field_name)
        if val:
            entry[out_name] = val
    creators = get_creators(item_id)
    if creators:
        entry["creators"] = creators
    tags = get_tags(item_id)
    if tags:
        entry["tags"] = tags
    collections = get_collections(item_id)
    if collections:
        entry["collections"] = collections
    output.append(entry)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Exportiert: {len(output)} Einträge nach {OUT}")
