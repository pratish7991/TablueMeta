import os
import zipfile
import xml.etree.ElementTree as ET

def extract_twb_from_twbx(twbx_path, output_dir="twb_extracted"):
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(twbx_path, "r") as z:
        for f in z.namelist():
            if f.lower().endswith(".twb"):
                twb_path = os.path.join(output_dir, os.path.basename(f))
                with open(twb_path, "wb") as out:
                    out.write(z.read(f))
                return twb_path
    raise FileNotFoundError("No .twb file found inside the .twbx")

def parse_twb_metadata(twb_path):
    tree = ET.parse(twb_path)
    root = tree.getroot()
    metadata = {
        "dashboards": [],
        "worksheets": [],
        "calculated_fields": []
    }

    # Extract dashboard names
    for dash in root.findall(".//dashboard"):
        name = dash.get("name")
        if name:
            metadata["dashboards"].append(name)

    # Extract worksheet names
    for ws in root.findall(".//worksheet"):
        name = ws.get("name")
        if name:
            metadata["worksheets"].append(name)

    # Extract text from text objects (titles, labels)
    texts = []
    for t in root.findall(".//text"):
        if t.text and t.text.strip():
            texts.append(t.text.strip())
    metadata["text_objects"] = texts

    # Extract calculated field names
    for col in root.findall(".//column"):
        calc = col.get("calculation")
        name = col.get("name")
        if calc and name:
            metadata["calculated_fields"].append(name)

    return metadata

if __name__ == "__main__":
    twbx_file = "TableauFinance.twbx"
    twb_path = extract_twb_from_twbx(twbx_file)
    meta = parse_twb_metadata(twb_path)
    print("Extracted Metadata:")
    print(meta)
