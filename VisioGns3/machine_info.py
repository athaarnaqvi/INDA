import xml.etree.ElementTree as ET
import os

# Define XML namespace
NAMESPACES = {'visio': 'http://schemas.microsoft.com/office/visio/2012/main'}

def parse_pages_xml(pages_xml):
    """
    Parse pages.xml to extract machine shapes with IDs and Master IDs.
    
    :param pages_xml: Path to the pages.xml file.
    :return: Dictionary mapping shape IDs to master IDs.
    """
    tree = ET.parse(pages_xml)
    root = tree.getroot()

    shapes = {}
    for shape in root.findall(".//visio:Shape", NAMESPACES):
        shape_id = shape.get("ID")
        master_id = shape.get("Master")
        if shape_id and master_id:
            shapes[shape_id] = master_id  # Store shape ID → Master ID

    return shapes

def parse_masters_xml(masters_xml):
    """
    Parse masters.xml to map Master IDs to device names while filtering out unwanted shapes.
    
    :param masters_xml: Path to the masters.xml file.
    :return: Dictionary mapping master IDs to machine names.
    """
    tree = ET.parse(masters_xml)
    root = tree.getroot()

    masters = {}
    for master in root.findall(".//visio:Master", NAMESPACES):
        master_id = master.get("ID")
        master_name = master.get("Name")
        if master_id and master_name:
            # Filter out unwanted names
            if "Rack Frame" in master_name or "Dynamic connector" in master_name:
                continue  
            masters[master_id] = master_name.replace(" ", "")  # Remove spaces

    return masters

def extract_machine_names(pages_xml, masters_xml, output_txt):
    """
    Extract machine names using pages.xml and masters.xml, then save them to a file.
    
    :param pages_xml: Path to the pages.xml file.
    :param masters_xml: Path to the masters.xml file.
    :param output_txt: Path to the output text file.
    """
    # Parse XML files
    shapes = parse_pages_xml(pages_xml)
    masters = parse_masters_xml(masters_xml)

    machine_names = set()  # Use set to avoid duplicates

    # Process each shape and map it to a machine name
    for shape_id, master_id in shapes.items():
        machine_name = masters.get(master_id)
        if machine_name:  # Skip if filtered out
            full_name = f"{machine_name}{shape_id}"
            machine_names.add(full_name)

    # Save machine names to file
    with open(output_txt, 'w') as f:
        for name in sorted(machine_names):
            f.write(name + '\n')

    print(f"Machine names have been saved to {output_txt}")

if __name__ == "__main__":
    # Define file paths
    pages_xml = os.path.expanduser("~/INDA/VisioGns3/extracted_vsdx/visio/pages/page1.xml")
    masters_xml = os.path.expanduser("~/INDA/VisioGns3/extracted_vsdx/visio/masters/masters.xml")
    output_txt = os.path.expanduser("~/INDA/VisioGns3/machine_names.txt")

    extract_machine_names(pages_xml, masters_xml, output_txt)

