import docx
import re
import datetime
import glob
import hashlib
import itertools
import os
import csv

print("🚀 Starting the dashboard generation script...")

INPUT_FILES = [f for f in glob.glob("*.docx") if not f.startswith("~$")]
print(f"📂 Found {len(INPUT_FILES)} matching .docx file(s) in: {os.getcwd()}")

OUTPUT_FILE = "dashboard.html"
DECODING_FILE = "decoding_key.csv"

# UPDATED: Distinct categorical pastel palette
COLORS = [
    '#ffadad', # Light Pink
    '#ffd6a5', # Light Orange
    '#fdffb6', # Light Yellow
    '#caffbf', # Light Green
    '#9bf6ff', # Light Cyan
    '#a0c4ff', # Light Blue
    '#bdb2ff', # Light Purple
    '#ffc6ff', # Light Magenta
    '#e5e5e5', # Light Gray
    '#ffebcc', # Peach
    '#dcedc1', # Mint
    '#f8c8dc'  # Rose
]

person_color_map = {}
color_cycler = itertools.cycle(COLORS)

def load_decoding_key():
    decoding_dict = {}
    if os.path.exists(DECODING_FILE):
        print(f"🔍 Found '{DECODING_FILE}'. Attempting to read...")
        try:
            with open(DECODING_FILE, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if len(row) >= 2:
                        term = row[0].strip()
                        explanation = row[1].strip()
                        if term.lower() == 'term': 
                            continue 
                        if term:
                            decoding_dict[term] = explanation
                            print(f"   ✔️ Loaded definition: {term} -> {explanation}")
        except Exception as e:
            print(f"❌ Error reading {DECODING_FILE}: {e}")
            
        print(f"🔑 Successfully loaded {len(decoding_dict)} terms from key file.")
    else:
        print(f"⚠️ '{DECODING_FILE}' not found. Generating template...")
        with open(DECODING_FILE, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Term', 'Explanation'])
            writer.writerow(['10116[tax]', 'rat'])
            writer.writerow(['RSGD-19909', 'curation of fusion XMs'])
        return load_decoding_key()
        
    return decoding_dict

RAW_DECODING_MAP = load_decoding_key()
DECODING_MAP = {k: v for k, v in sorted(RAW_DECODING_MAP.items(), key=lambda item: len(item[0]), reverse=True)}

def get_person_color(person):
    # Normalize the name (ignore case and extra spaces) to ensure identical coloring
    match_key = " ".join(person.split()).upper()
    if match_key not in person_color_map:
        person_color_map[match_key] = next(color_cycler)
    return person_color_map[match_key]

def generate_row_id(date_range, person, task):
    unique_string = f"{date_range}_{person}_{task}".encode('utf-8')
    return hashlib.md5(unique_string).hexdigest()

def process_row_data(year_quarter, month_num, date_range, category, person, raw_details):
    parsed_rows = []
    color = get_person_color(person)
    
    if category.upper() == 'MAIL':
        parsed_rows.append({
            "quarter": year_quarter, "month": month_num, "date_range": date_range,
            "category": "MAIL", "person": person, "tasks": "MAIL",
            "id": generate_row_id(date_range, person, "MAIL"), "color": color
        })
    elif category.upper() == 'PRIOR1':
        parsed_rows.append({
            "quarter": year_quarter, "month": month_num, "date_range": date_range,
            "category": "PRIOR1", "person": person, "tasks": "Priority 1",
            "id": generate_row_id(date_range, person, "Priority 1"), "color": color
        })
        
    tasks = [t.strip() for t in raw_details.split(';') if t.strip()]
    
    for task in tasks:
        task = re.sub(r'\s+AND(?:NOT)?\s+\(?(?:\d+|[XY])\[chr\].*', '', task, flags=re.IGNORECASE)
        task = re.sub(r'\s+AND(?:NOT)?\s+chr\s+.*', '', task, flags=re.IGNORECASE)
        task = task.strip()
        
        if task:
            for term, explanation in DECODING_MAP.items():
                if term in task:
                    if f"({explanation})" not in task:
                        task = task.replace
