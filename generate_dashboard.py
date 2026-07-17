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

COLORS = ['#e3f2fd', '#e8f5e9', '#fff3e0', '#f3e5f5', '#ffebee', '#e0f7fa', '#fce4ec', '#f1f8e9', '#fff8e1', '#e8eaf6']
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
                            continue # Skip header
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
    if person not in person_color_map:
        person_color_map[person] = next(color_cycler)
    return person_color_map[person]

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
                        task = task.replace(term, f"{term} ({explanation})")
            
            parsed_rows.append({
                "quarter": year_quarter, "month": month_num, "date_range": date_range,
                "category": "lxr-1", "person": person, "tasks": task,
                "id": generate_row_id(date_range, person, task), "color": color
            })
            
    return parsed_rows

def generate_html(data_rows):
    print("🌐 Generating HTML file...")
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Task Assignments Dashboard</title>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; }
            h1 { color: #2c3e50; text-align: center; margin-bottom: 20px; }
            .dashboard-header { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
            .panel { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); flex: 1; min-width: 300px; }
            .chart-container { position: relative; height: 200px; display: flex; justify-content: center; margin-top:10px; }
            
            .control-group { margin-bottom: 15px; }
            .control-group label { display: block; font-weight: bold; margin-bottom: 5px; font-size: 14px; color: #2c3e50; }
            .stat-box { background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; border-radius: 4px; font-size: 18px; margin-top: 10px; }
            
            select, input[type="date"], button { padding: 8px; border-radius: 5px; border: 1px solid #ccc; font-size: 14px; width: 100%; box-sizing: border-box; margin-top: 5px;}
            button { cursor: pointer; font-weight: bold; transition: 0.2s; color: white; border: none; }
            button.btn-blue { background-color: #3498db; } button.btn-blue:hover { background-color: #2980b9; }
            button.btn-green { background-color: #27ae60; } button.btn-green:hover { background-color: #219150; }
            button.btn-orange { background-color: #e67e22; } button.btn-orange:hover { background-color: #d35400; }
            button.btn-purple { background-color: #9b59b6; } button.btn-purple:hover { background-color: #8e44ad; }

            th { background-color: #3498db; color: white; text-align: left; }
            td, th { padding: 10px; border-bottom: 1px solid #ddd; }
            table.dataTable tbody tr td { background-color: inherit !important; } 
            
            select.status-dropdown { padding: 5px; border-radius: 4px; font-weight: bold; width: 100%; }
            .status-pending { background-color: #ffeaa7; color: #d35400; border-color: #d35400; }
            .status-progress { background-color: #ffeaa7; color: #e67e22; border-color: #e67e22; }
            .status-completed { background-color: #d4efdf; color: #27ae60; border-color: #27ae60; }
            
            .btn-group { display: flex; gap: 10px; margin-top: 10px; }
        </style>
    </head>
    <body>
        <h1>📋 Interactive Task Assignments Dashboard</h1>
        
        <div class="dashboard-header">
            <!-- Panel 1: Chart -->
            <div class="panel">
                <h3 style="margin-top:0; color:#2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom:10px;">📊 Overall Status</h3>
                <div class="chart-container">
                    <canvas id="statusChart"></canvas>
                </div>
            </div>
            
            <!-- Panel 2: Quick Summary & Sync -->
            <div class="panel">
                <h3 style="margin-top:0; color:#2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom:10px;">📈 Quick Summary & Sync</h3>
                <div class="control-group">
                    <label>Filter Dashboard by Quarter:</label>
                    <select id="dashboardQuarterSelect">
                        <option value="All">All Quarters</option>
                    </select>
                </div>
                <div class="stat-box">
                    <strong>Total Completed:</strong> <span id="quarterCompletedCount">0</span>
                </div>
                <div style="margin-top: 15px;">
                    <label style="font-weight: bold; font-size: 14px; color: #2c3e50;">Team Sync:</label>
                    <div class="btn-group">
                        <button id="exportStateBtn" class="btn-orange" style="flex:1;">📤 Export Progress</button>
                        <button id="importStateBtn" class="btn-purple" style="flex:1;" onclick="document.getElementById('importStateFile').click()">📥 Import Progress</button>
                        <input type="file" id="importStateFile" style="display:none;" accept=".json">
                    </div>
                </div>
            </div>

            <!-- Panel 3: Custom Report Generator -->
            <div class="panel" style="background-color: #f0f8ff;">
                <h3 style="margin-top:0; color:#2c3e50; border-bottom: 2px solid #cce7ff; padding-bottom:10px;">📄 Generate Custom Report</h3>
                <div class="control-group">
                    <label>Team Member:</label>
                    <select id="reportPersonSelect"><option value="All">All Members</option></select>
                </div>
                <div class="control-group">
                    <label>Filter Timeframe By:</label>
                    <select id="reportTimeframeType">
                        <option value="quarter">Year & Quarter</option>
                        <option value="dateRange">Custom Date Range</option>
                    </select>
                </div>
                <div class="control-group" id="quarterFilterContainer">
                    <select id="reportQuarterSelect"><option value="All">All Quarters</option></select>
                </div>
                <div class="control-group" id="dateFilterContainer" style="display:none;">
                    <div style="display: flex; gap: 10px;">
                        <div style="flex:1;"><input type="date" id="reportStartDate"></div>
                        <div style="flex:1;"><input type="date" id="reportEndDate"></div>
                    </div>
                </div>
                <button id="generateReportBtn" class="btn-green">⬇️ Download Full Task Report</button>
            </div>
        </div>

        <div class="panel">
            <table id="taskTable" class="display" style="width:100%">
                <thead>
                    <tr>
                        <th>Year-Qtr</th>
                        <th>Month</th>
                        <th>Date Range</th>
                        <th>Task Category</th>
                        <th>Person</th>
                        <th>Tasks</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
        <script>
            let statusChart;
            let dataTable;

            function updateDropdownStyle(dropdown) {
                dropdown.removeClass('status-pending status-progress status-completed');
                if (dropdown.val() === 'Pending') dropdown.addClass('status-pending');
                if (dropdown.val() === 'In Progress') dropdown.addClass('status-progress');
                if (dropdown.val() === 'Completed') dropdown.addClass('status-completed');
            }

            function loadStatuses() {
                // FIXED: Now iterates over all DataTables nodes, even hidden paginated ones
                dataTable.rows().every(function() {
                    let node = this.node();
                    let dropdown = $(node).find('.status-dropdown');
                    let id = dropdown.attr('data-id');
                    let savedStatus = localStorage.getItem('task_status_' + id);
                    if (savedStatus) { 
                        dropdown.val(savedStatus); 
                    }
                    updateDropdownStyle(dropdown);
                });
            }

            function populateDynamicFilters() {
                let quarters = new Set();
                let persons = new Set();
                dataTable.rows().every(function() {
                    let data = this.data();
                    quarters.add(data[0]);
                    persons.add(data[4]);
                });
                Array.from(quarters).sort().forEach(q => {
                    $('#dashboardQuarterSelect').append(new Option(q, q));
                    $('#reportQuarterSelect').append(new Option(q, q));
                });
                Array.from(persons).sort().forEach(p => {
                    $('#reportPersonSelect').append(new Option(p, p));
                });
            }

            function updateDashboard() {
                let counts = { 'Pending': 0, 'In Progress': 0, 'Completed': 0 };
                let selectedQuarter = $('#dashboardQuarterSelect').val();
                let quarterCompleted = 0;

                // FIXED: Reads data directly from DOM nodes across all pages
                dataTable.rows().every(function() {
                    let rowNode = this.node();
                    let quarter = this.data()[0];
                    let status = $(rowNode).find('.status-dropdown').val();
                    
                    counts[status]++;
                    
                    if (status === 'Completed' && (selectedQuarter === 'All' || selectedQuarter === quarter)) {
                        quarterCompleted++;
                    }
                });

                statusChart.data.datasets[0].data = [counts['Completed'], counts['In Progress'], counts['Pending']];
                statusChart.update();
                $('#quarterCompletedCount').text(quarterCompleted);
            }

            $(document).ready(function() {
                dataTable = $('#taskTable').DataTable({
                    "pageLength": 50,
                    "order": [[ 0, 'asc' ], [ 1, 'asc' ], [ 2, 'asc' ]]
                });

                // Initialize Chart First
                let ctx = document.getElementById('statusChart').getContext('2d');
                statusChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Completed', 'In Progress', 'Pending'],
                        datasets: [{ data: [0, 0, 0], backgroundColor: ['#27ae60', '#e67e22', '#d35400'], borderWidth: 1 }]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                });

                loadStatuses();
                populateDynamicFilters();
                updateDashboard();

                // SMART SYNC: When a dropdown is changed
                $(document).on('change', '.status-dropdown', function() {
                    let newVal = $(this).val();
                    let changedId = $(this).attr('data-id');
                    
                    // Get the exact task text for the row that was just changed
                    let rowData = dataTable.row($(this).closest('tr')).data();
                    let taskTextToMatch = rowData[5]; 

                    // Find all rows with the identical task text and update them
                    dataTable.rows().every(function() {
                        let d = this.data();
                        if (d[5] === taskTextToMatch) {
                            let node = this.node();
                            let dd = $(node).find('.status-dropdown');
                            let targetId = dd.attr('data-id');
                            
                            dd.val(newVal);
                            updateDropdownStyle(dd);
                            localStorage.setItem('task_status_' + targetId, newVal);
                        }
                    });
                    updateDashboard();
                });

                $('#dashboardQuarterSelect').change(function() { updateDashboard(); });

                $('#reportTimeframeType').change(function() {
                    if($(this).val() === 'quarter') {
                        $('#quarterFilterContainer').show(); $('#dateFilterContainer').hide();
                    } else {
                        $('#quarterFilterContainer').hide(); $('#dateFilterContainer').show();
                    }
                });

                // EXPORT PROGRESS (JSON)
                $('#exportStateBtn').click(function() {
                    let state = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        if (key.startsWith('task_status_')) {
                            state[key] = localStorage.getItem(key);
                        }
                    }
                    let blob = new Blob([JSON.stringify(state)], { type: 'application/json' });
                    let link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    link.download = 'team_progress.json';
                    link.click();
                });

                // IMPORT PROGRESS (JSON)
                $('#importStateFile').change(function(e) {
                    let file = e.target.files[0];
                    if (!file) return;
                    let reader = new FileReader();
                    reader.onload = function(e) {
                        try {
                            let state = JSON.parse(e.target.result);
                            let importedCount = 0;
                            for (let key in state) {
                                if (key.startsWith('task_status_')) {
                                    // Only update if it's currently pending, or overwrite everything? Let's overwrite.
                                    localStorage.setItem(key, state[key]);
                                    importedCount++;
                                }
                            }
                            alert("Successfully imported " + importedCount + " task statuses!");
                            loadStatuses();
                            updateDashboard();
                        } catch (err) {
                            alert("Error reading file. Ensure it is a valid JSON progress file.");
                        }
                    };
                    reader.readAsText(file);
                });

                $('#generateReportBtn').click(function() {
                    let personFilter = $('#reportPersonSelect').val();
                    let timeframeType = $('#reportTimeframeType').val();
                    let quarterFilter = $('#reportQuarterSelect').val();
                    let startFilter = new Date($('#reportStartDate').val());
                    let endFilter = new Date($('#reportEndDate').val());
                    
                    if(!isNaN(endFilter)) endFilter.setHours(23, 59, 59);

                    let csvContent = "Year-Quarter,Month,Date Range,Task Category,Person,Tasks,Status\\n";
                    let matchCount = 0;
                    
                    dataTable.rows().every(function() {
                        let data = this.data();
                        let rowNode = this.node();
                        let status = $(rowNode).find('.status-dropdown').val();
                        
                        if (personFilter !== 'All' && data[4] !== personFilter) return;

                        if (timeframeType === 'quarter') {
                            if (quarterFilter !== 'All' && data[0] !== quarterFilter) return;
                        } else {
                            if (isNaN(startFilter) || isNaN(endFilter)) {
                                alert("Please select both dates."); return false; 
                            }
                            let dates = data[2].split('-');
                            if(dates.length === 2) {
                                let rowStart = new Date(dates[0].trim());
                                let rowEnd = new Date(dates[1].trim());
                                rowEnd.setHours(23, 59, 59);
                                if (rowStart > endFilter || rowEnd < startFilter) return; 
                            }
                        }

                        matchCount++;
                        let safeTask = data[5].replace(/"/g, '""');
                        csvContent += `${data[0]},${data[1]},${data[2]},${data[3]},${data[4]},"${safeTask}",${status}\\n`;
                    });

                    if (matchCount === 0) {
                        alert("No tasks found matching your criteria."); return;
                    }

                    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                    let link = document.createElement("a");
                    link.href = URL.createObjectURL(blob);
                    link.download = `${personFilter.replace(' ', '_')}_Full_Task_Report.csv`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                });
            });
        </script>
    </body>
    </html>
    """
    
    rows_html = ""
    for row in data_rows:
        dropdown = f"""
        <select class="status-dropdown" data-id="{row['id']}">
            <option value="Pending">Pending</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
        </select>
        """
        rows_html += f"<tr style='background-color: {row['color']}'><td>{row['quarter']}</td><td>{row['month']}</td><td>{row['date_range']}</td><td>{row['category']}</td><td>{row['person']}</td><td>{row['tasks']}</td><td>{dropdown}</td></tr>\n"
        
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_template.replace("{table_rows}", rows_html))

def process_documents():
    if not INPUT_FILES:
        print("❌ ERROR: No .docx files found in this folder.")
        return

    extracted_data = []
    
    for file in INPUT_FILES:
        try:
            doc = docx.Document(file)
            for t_idx, table in enumerate(doc.tables):
                current_date_range = "Unknown Date"
                
                for i, row in enumerate(table.rows):
                    cells = [cell.text.strip() for cell in row.cells]
                    unique_cells = []
                    for c in cells:
                        if c and c not in unique_cells:
                            unique_cells.append(c)
                            
                    if not unique_cells: continue
                    if "Date Range" in unique_cells[0] or "Task" in unique_cells[0]: continue
                        
                    if len(unique_cells) == 1 and '/' in unique_cells[0] and '-' in unique_cells[0]:
                        current_date_range = unique_cells[0]
                        continue
                        
                    if len(unique_cells) == 3:
                        category = unique_cells[0]
                        person = unique_cells[1]
                        raw_details = unique_cells[2]
                        date_range = current_date_range
                    elif len(unique_cells) >= 4:
                        if '/' in unique_cells[0]:
                            date_range = unique_cells[0]
                            category = unique_cells[1]
                            person = unique_cells[2]
                            raw_details = unique_cells[3]
                            current_date_range = date_range
                        else:
                            category = unique_cells[0]
                            person = unique_cells[1]
                            raw_details = unique_cells[2]
                            date_range = current_date_range
                    else:
                        continue
                        
                    try:
                        start_date_str = date_range.split('-')[0].strip()
                        parsed_date = datetime.datetime.strptime(start_date_str, "%m/%d/%Y")
                        month_num = parsed_date.strftime("%B")
                        year_str = parsed_date.strftime("%Y")
                        q_num = (parsed_date.month - 1) // 3 + 1
                        year_quarter = f"{year_str}-Q{q_num}"
                    except Exception:
                        month_num = "Unknown"
                        year_quarter = "Unknown"

                    new_rows = process_row_data(year_quarter, month_num, date_range, category, person, raw_details)
                    extracted_data.extend(new_rows)
                    
        except Exception as e:
            print(f"❌ ERROR reading {file}: {e}")

    if extracted_data:
        generate_html(extracted_data)
        print(f"✅ SUCCESS! Dashboard generated: {OUTPUT_FILE} ({len(extracted_data)} tasks).")
    else:
        print("⚠️ FINISHED: But no valid task data was extracted.")

if __name__ == "__main__":
    process_documents()
