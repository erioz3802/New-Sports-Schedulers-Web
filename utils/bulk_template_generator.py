# utils/bulk_template_generator.py - WORKING Hybrid Solution with xlsxwriter
import tempfile
import os
from datetime import datetime

def get_data_functions():
    """Safely import data helper functions"""
    try:
        from utils.data_helpers import get_admin_leagues, get_all_locations, get_available_officials
        return get_admin_leagues, get_all_locations, get_available_officials
    except ImportError as e:
        print(f"Warning: Data helpers not available: {e}")
        return None, None, None

def generate_games_only_template(admin_id):
    """Generate Excel template with HYBRID solution using xlsxwriter"""
    
    try:
        import xlsxwriter
    except ImportError:
        raise Exception("xlsxwriter not installed. Run: pip install xlsxwriter")
    
    # Get data helper functions
    get_admin_leagues, get_all_locations, get_available_officials = get_data_functions()
    
    if not get_admin_leagues or not get_all_locations:
        raise Exception("Data helper functions not available")
    
    # Get admin's accessible data
    leagues = get_admin_leagues(admin_id)
    locations = get_all_locations()
    
    print(f"Debug: Found {len(leagues)} leagues and {len(locations)} locations")
    
    if not leagues:
        raise Exception("No leagues available for this admin. Please create leagues first.")
    
    if not locations:
        raise Exception("No locations available. Please create locations first.")
    
    # Save to temporary file
    temp_dir = tempfile.mkdtemp()
    filename = f"Games_Template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = os.path.join(temp_dir, filename)
    
    # Create workbook with xlsxwriter
    workbook = xlsxwriter.Workbook(file_path)
    
    # Create main worksheet
    worksheet = workbook.add_worksheet('Games Import')
    
    # Define formats
    dropdown_header_format = workbook.add_format({
        'bold': True,
        'font_color': 'white',
        'bg_color': '#4CAF50',  # Green for dropdowns
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    manual_header_format = workbook.add_format({
        'bold': True,
        'font_color': 'white',
        'bg_color': '#366092',  # Blue for manual/autocomplete
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    reference_header_format = workbook.add_format({
        'bold': True,
        'font_color': 'white',
        'bg_color': '#FF9800',  # Orange for reference
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    sample_format = workbook.add_format({
        'bg_color': '#E8F5E8',
        'italic': True,
        'font_color': '#2E7D32'
    })
    
    reference_format = workbook.add_format({
        'bg_color': '#FFF3E0',
        'font_size': 10
    })
    
    # 🎯 HYBRID SOLUTION HEADERS
    headers = [
        ('League Name', 'dropdown'),           # A - Dropdown
        ('Level', 'dropdown'),                # B - Dropdown 
        ('Date (YYYY-MM-DD)', 'manual'),      # C - Manual entry
        ('Time (HH:MM)', 'manual'),           # D - Manual entry
        ('Location Name', 'manual'),          # E - Autocomplete (manual with reference)
        ('Field/Court', 'manual'),            # F - Manual entry
        ('Home Team', 'manual'),              # G - Manual entry
        ('Away Team', 'manual'),              # H - Manual entry
        ('Notes', 'manual'),                  # I - Manual entry
        ('Special Instructions', 'manual'),   # J - Manual entry
        ('', 'spacer'),                       # K - Spacer
        ('', 'spacer'),                       # L - Spacer  
        ('LEAGUE REFERENCE', 'reference'),    # M - Reference list
        ('LOCATION REFERENCE', 'reference')   # N - Reference list
    ]
    
    # Write headers with color coding
    for col, (header, header_type) in enumerate(headers):
        if header:  # Skip empty headers
            if header_type == 'dropdown':
                worksheet.write(0, col, header, dropdown_header_format)
            elif header_type == 'reference':
                worksheet.write(0, col, header, reference_header_format)
            else:
                worksheet.write(0, col, header, manual_header_format)
            
            # Set column widths
            if header in ['League Name', 'Location Name']:
                worksheet.set_column(col, col, 25)
            elif header in ['Home Team', 'Away Team']:
                worksheet.set_column(col, col, 18)
            elif 'REFERENCE' in header:
                worksheet.set_column(col, col, 25)
            elif header in ['Notes', 'Special Instructions']:
                worksheet.set_column(col, col, 30)
            else:
                worksheet.set_column(col, col, 15)
    
    # 🔽 Create League dropdown (Column A)
    league_names = [league['name'] for league in leagues]
    worksheet.data_validation('A2:A1000', {
        'validate': 'list',
        'source': league_names,
        'dropdown': True,
        'error_message': 'Please select a league from the dropdown list.'
    })
    
    # 🔽 Create Level dropdown (Column B) - All possible levels
    all_levels = set()
    for league in leagues:
        if league.get('level'):
            all_levels.add(league['level'])
    
    # Add common levels if none found
    if not all_levels:
        all_levels = {'High School', 'College', 'Middle School', 'Elementary', 'Adult Rec', 'Youth'}
    
    level_list = sorted(list(all_levels))
    worksheet.data_validation('B2:B1000', {
        'validate': 'list',
        'source': level_list,
        'dropdown': True,
        'error_message': 'Please select a level from the dropdown list.'
    })
    
    # Date validation (Column C)
    worksheet.data_validation('C2:C1000', {
        'validate': 'date',
        'criteria': '>=',
        'value': datetime.now().date(),
        'error_message': 'Please enter a valid future date in YYYY-MM-DD format.'
    })
    
    # Time validation (Column D)
    worksheet.data_validation('D2:D1000', {
        'validate': 'time',
        'error_message': 'Please enter time in HH:MM format (e.g., 14:30).'
    })
    
    # 📋 Populate reference lists (Columns M, N)
    # League reference (Column M)
    for row, league in enumerate(leagues, 1):
        worksheet.write(row, 12, league['name'], reference_format)
    
    # Location reference (Column N)
    for row, location in enumerate(locations, 1):
        worksheet.write(row, 13, location['name'], reference_format)
    
    # Add sample data showing proper usage
    if leagues and locations:
        sample_data = [
            leagues[0]['name'],        # League dropdown
            'High School',             # Level dropdown
            '2025-12-31',             # Date
            '19:00',                  # Time
            locations[0]['name'],     # Location (type exact name)
            'Field 1',                # Field
            'Eagles',                 # Home team
            'Hawks',                  # Away team
            'Championship game',      # Notes
            'Report 30 min early'     # Instructions
        ]
        
        for col, value in enumerate(sample_data):
            worksheet.write(1, col, value, sample_format)
    
    # Add instructions worksheet
    create_instructions_worksheet_games_only(workbook, leagues, locations)
    
    # Close workbook
    workbook.close()
    
    print(f"Template saved to: {file_path}")
    return file_path, filename

def generate_games_with_assignments_template(admin_id):
    """Generate Excel template with assignments and HYBRID solution"""
    
    try:
        import xlsxwriter
    except ImportError:
        raise Exception("xlsxwriter not installed. Run: pip install xlsxwriter")
    
    # Get data helper functions
    get_admin_leagues, get_all_locations, get_available_officials = get_data_functions()
    
    if not all([get_admin_leagues, get_all_locations, get_available_officials]):
        raise Exception("Data helper functions not available")
    
    # Get admin's accessible data
    leagues = get_admin_leagues(admin_id)
    locations = get_all_locations()
    officials = get_available_officials(admin_id)
    
    print(f"Debug: Found {len(leagues)} leagues, {len(locations)} locations, {len(officials)} officials")
    
    if not leagues:
        raise Exception("No leagues available for this admin. Please create leagues first.")
    
    if not locations:
        raise Exception("No locations available. Please create locations first.")
    
    # Save to temporary file
    temp_dir = tempfile.mkdtemp()
    filename = f"Games_with_Assignments_Template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = os.path.join(temp_dir, filename)
    
    # Create workbook with xlsxwriter
    workbook = xlsxwriter.Workbook(file_path)
    
    # Create main worksheet
    worksheet = workbook.add_worksheet('Games with Assignments')
    
    # Define formats
    dropdown_header_format = workbook.add_format({
        'bold': True,
        'font_color': 'white',
        'bg_color': '#4CAF50',  # Green for dropdowns
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    manual_header_format = workbook.add_format({
        'bold': True,
        'font_color': 'white',
        'bg_color': '#366092',  # Blue for manual/autocomplete
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    reference_header_format = workbook.add_format({
        'bold': True,
        'font_color': 'white',
        'bg_color': '#FF9800',  # Orange for reference
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    sample_format = workbook.add_format({
        'bg_color': '#E8F5E8',
        'italic': True,
        'font_color': '#2E7D32'
    })
    
    reference_format = workbook.add_format({
        'bg_color': '#FFF3E0',
        'font_size': 10
    })
    
    # 🎯 HYBRID SOLUTION HEADERS
    headers = [
        ('League Name', 'dropdown'),           # A - Dropdown
        ('Level', 'dropdown'),                # B - Dropdown 
        ('Date (YYYY-MM-DD)', 'manual'),      # C - Manual entry
        ('Time (HH:MM)', 'manual'),           # D - Manual entry
        ('Location Name', 'manual'),          # E - Autocomplete (manual with reference)
        ('Field/Court', 'manual'),            # F - Manual entry
        ('Home Team', 'manual'),              # G - Manual entry
        ('Away Team', 'manual'),              # H - Manual entry
        ('Official 1 Name', 'manual'),        # I - Autocomplete (manual with reference)
        ('Official 1 Position', 'manual'),    # J - Manual entry
        ('Official 2 Name', 'manual'),        # K - Autocomplete (manual with reference)
        ('Official 2 Position', 'manual'),    # L - Manual entry
        ('Official 3 Name', 'manual'),        # M - Autocomplete (manual with reference)
        ('Official 3 Position', 'manual'),    # N - Manual entry
        ('Notes', 'manual'),                  # O - Manual entry
        ('Special Instructions', 'manual'),   # P - Manual entry
        ('', 'spacer'),                       # Q - Spacer
        ('', 'spacer'),                       # R - Spacer  
        ('LEAGUE REFERENCE', 'reference'),    # S - Reference list
        ('LOCATION REFERENCE', 'reference'),  # T - Reference list
        ('OFFICIAL REFERENCE', 'reference')   # U - Reference list
    ]
    
    # Write headers with color coding
    for col, (header, header_type) in enumerate(headers):
        if header:  # Skip empty headers
            if header_type == 'dropdown':
                worksheet.write(0, col, header, dropdown_header_format)
            elif header_type == 'reference':
                worksheet.write(0, col, header, reference_header_format)
            else:
                worksheet.write(0, col, header, manual_header_format)
            
            # Set column widths
            if header in ['League Name', 'Location Name']:
                worksheet.set_column(col, col, 20)
            elif header in ['Home Team', 'Away Team']:
                worksheet.set_column(col, col, 16)
            elif 'Official' in header and 'Name' in header:
                worksheet.set_column(col, col, 18)
            elif 'Official' in header and 'Position' in header:
                worksheet.set_column(col, col, 12)
            elif 'REFERENCE' in header:
                worksheet.set_column(col, col, 25)
            elif header in ['Notes', 'Special Instructions']:
                worksheet.set_column(col, col, 25)
            else:
                worksheet.set_column(col, col, 12)
    
    # 🔽 Create League dropdown (Column A)
    league_names = [league['name'] for league in leagues]
    worksheet.data_validation('A2:A1000', {
        'validate': 'list',
        'source': league_names,
        'dropdown': True,
        'error_message': 'Please select a league from the dropdown list.'
    })
    
    # 🔽 Create Level dropdown (Column B) - All possible levels
    all_levels = set()
    for league in leagues:
        if league.get('level'):
            all_levels.add(league['level'])
    
    # Add common levels if none found
    if not all_levels:
        all_levels = {'High School', 'College', 'Middle School', 'Elementary', 'Adult Rec', 'Youth'}
    
    level_list = sorted(list(all_levels))
    worksheet.data_validation('B2:B1000', {
        'validate': 'list',
        'source': level_list,
        'dropdown': True,
        'error_message': 'Please select a level from the dropdown list.'
    })
    
    # Date validation (Column C)
    worksheet.data_validation('C2:C1000', {
        'validate': 'date',
        'criteria': '>=',
        'value': datetime.now().date(),
        'error_message': 'Please enter a valid future date in YYYY-MM-DD format.'
    })
    
    # Time validation (Column D)
    worksheet.data_validation('D2:D1000', {
        'validate': 'time',
        'error_message': 'Please enter time in HH:MM format (e.g., 14:30).'
    })
    
    # 📋 Populate reference lists (Columns S, T, U)
    # League reference (Column S)
    for row, league in enumerate(leagues, 1):
        worksheet.write(row, 18, league['name'], reference_format)
    
    # Location reference (Column T)
    for row, location in enumerate(locations, 1):
        worksheet.write(row, 19, location['name'], reference_format)
    
    # Official reference (Column U)
    for row, official in enumerate(officials, 1):
        full_name = f"{official['first_name']} {official['last_name']}"
        worksheet.write(row, 20, full_name, reference_format)
    
    # Add sample data showing proper usage
    if leagues and locations:
        sample_data = [
            leagues[0]['name'],                   # League dropdown
            'High School',                        # Level dropdown
            '2025-12-31',                        # Date
            '19:00',                             # Time
            locations[0]['name'],                # Location (type exact name)
            'Field 1',                           # Field
            'Eagles',                            # Home team
            'Hawks',                             # Away team
            f"{officials[0]['first_name']} {officials[0]['last_name']}" if officials else '',  # Official 1 (type exact name)
            'Referee',                           # Position 1
            f"{officials[1]['first_name']} {officials[1]['last_name']}" if len(officials) > 1 else '',  # Official 2
            'Umpire' if len(officials) > 1 else '',  # Position 2
            '',                                  # Official 3 (empty)
            '',                                  # Position 3 (empty)
            'Championship game',                 # Notes
            'Report 30 min early'               # Instructions
        ]
        
        for col, value in enumerate(sample_data):
            worksheet.write(1, col, value, sample_format)
    
    # Add instructions worksheet
    create_instructions_worksheet_with_assignments(workbook, leagues, locations, officials)
    
    # Close workbook
    workbook.close()
    
    print(f"Template saved to: {file_path}")
    return file_path, filename

def create_instructions_worksheet_games_only(workbook, leagues, locations):
    """Create instructions worksheet for games only template"""
    
    instructions_ws = workbook.add_worksheet('Instructions')
    
    # Formats
    title_format = workbook.add_format({
        'font_size': 16,
        'bold': True,
        'font_color': '#366092'
    })
    
    section_format = workbook.add_format({
        'font_size': 14,
        'bold': True,
        'font_color': '#4CAF50'
    })
    
    text_format = workbook.add_format({
        'font_size': 12,
        'text_wrap': True
    })
    
    # Set column width
    instructions_ws.set_column(0, 0, 80)
    
    row = 0
    
    # Title
    instructions_ws.write(row, 0, "🎯 Sports Scheduler - Hybrid Template (Games Only)", title_format)
    row += 2
    
    # Features section
    instructions_ws.write(row, 0, "✅ WHAT YOU HAVE - PERFECT HYBRID SOLUTION:", section_format)
    row += 1
    
    features = [
        "🔽 League Dropdown (Column A) - Working dropdown with your leagues",
        "🔽 Level Dropdown (Column B) - Dropdown with all available levels",
        "📝 Location Autocomplete (Column E) - Type exact location names",
        "📋 Reference Lists (Columns M-N) - Shows valid names for copy/paste"
    ]
    
    for feature in features:
        instructions_ws.write(row, 0, feature, text_format)
        row += 1
    
    row += 1
    instructions_ws.write(row, 0, "🎨 COLOR CODING SYSTEM:", section_format)
    row += 1
    
    color_codes = [
        "🟢 GREEN Headers = Dropdown menus (League, Level)",
        "🔵 BLUE Headers = Manual entry with autocomplete help (Location)",
        "🟠 ORANGE Headers = Reference lists for copy/paste"
    ]
    
    for code in color_codes:
        instructions_ws.write(row, 0, code, text_format)
        row += 1
    
    row += 1
    instructions_ws.write(row, 0, "📝 HOW TO USE THIS TEMPLATE:", section_format)
    row += 1
    
    usage_instructions = [
        "1. League Name (A): Click dropdown arrow and select your league",
        "2. Level (B): Click dropdown arrow and select appropriate level",
        "3. Date (C): Enter in YYYY-MM-DD format (e.g., 2025-12-31)",
        "4. Time (D): Enter in HH:MM format (e.g., 19:00 for 7:00 PM)",
        "5. Location (E): Type EXACT location name (see Column N reference)",
        "6. Field/Court (F): Enter field name (e.g., Field 1, Court A)",
        "7. Team Names (G,H): Enter home and away team names",
        "8. Notes/Instructions (I,J): Add any special information"
    ]
    
    for instruction in usage_instructions:
        instructions_ws.write(row, 0, instruction, text_format)
        row += 1

def create_instructions_worksheet_with_assignments(workbook, leagues, locations, officials):
    """Create instructions worksheet for games with assignments template"""
    
    instructions_ws = workbook.add_worksheet('Instructions')
    
    # Formats
    title_format = workbook.add_format({
        'font_size': 16,
        'bold': True,
        'font_color': '#366092'
    })
    
    section_format = workbook.add_format({
        'font_size': 14,
        'bold': True,
        'font_color': '#4CAF50'
    })
    
    text_format = workbook.add_format({
        'font_size': 12,
        'text_wrap': True
    })
    
    # Set column width
    instructions_ws.set_column(0, 0, 80)
    
    row = 0
    
    # Title
    instructions_ws.write(row, 0, "🎯 Sports Scheduler - Hybrid Template (Games with Assignments)", title_format)
    row += 2
    
    # Features section
    instructions_ws.write(row, 0, "✅ WHAT YOU HAVE - PERFECT HYBRID SOLUTION:", section_format)
    row += 1
    
    features = [
        "🔽 League Dropdown (Column A) - Working dropdown with your leagues",
        "🔽 Level Dropdown (Column B) - Dropdown with all available levels",
        "📝 Location Autocomplete (Column E) - Type exact location names",
        "📝 Official Autocomplete (Columns I, K, M) - Type exact official names",
        "📋 Reference Lists (Columns S-U) - Shows valid names for copy/paste"
    ]
    
    for feature in features:
        instructions_ws.write(row, 0, feature, text_format)
        row += 1
    
    row += 1
    instructions_ws.write(row, 0, "🎨 COLOR CODING SYSTEM:", section_format)
    row += 1
    
    color_codes = [
        "🟢 GREEN Headers = Dropdown menus (League, Level)",
        "🔵 BLUE Headers = Manual entry with autocomplete help (Location, Officials)",
        "🟠 ORANGE Headers = Reference lists for copy/paste"
    ]
    
    for code in color_codes:
        instructions_ws.write(row, 0, code, text_format)
        row += 1
    
    row += 1
    instructions_ws.write(row, 0, "📝 HOW TO USE THIS TEMPLATE:", section_format)
    row += 1
    
    usage_instructions = [
        "1. League Name (A): Click dropdown arrow and select your league",
        "2. Level (B): Click dropdown arrow and select appropriate level",
        "3. Date (C): Enter in YYYY-MM-DD format (e.g., 2025-12-31)",
        "4. Time (D): Enter in HH:MM format (e.g., 19:00 for 7:00 PM)",
        "5. Location (E): Type EXACT location name (see Column T reference)",
        "6. Field/Court (F): Enter field name (e.g., Field 1, Court A)",
        "7. Team Names (G,H): Enter home and away team names",
        "8. Officials (I,K,M): Type EXACT official names (see Column U reference)",
        "9. Positions (J,L,N): Enter positions (Referee, Umpire, Judge, etc.)",
        "10. Notes/Instructions (O,P): Add any special information"
    ]
    
    for instruction in usage_instructions:
        instructions_ws.write(row, 0, instruction, text_format)
        row += 1
    
    row += 1
    instructions_ws.write(row, 0, "💡 PRO TIPS FOR SUCCESS:", section_format)
    row += 1
    
    pro_tips = [
        "• Use the reference columns (S, T, U) to copy/paste exact names",
        "• Names must match EXACTLY - use copy/paste for accuracy",
        "• Remove sample rows before uploading",
        "• Preview your import before final save",
        "• Double-check dates are in the future"
    ]
    
    for tip in pro_tips:
        instructions_ws.write(row, 0, tip, text_format)
        row += 1