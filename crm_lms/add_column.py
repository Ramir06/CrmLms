import os
import sys
import django

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    
    # Add column directly via SQL
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'assignments_assignment' 
            AND column_name = 'block_after_deadline'
        """)
        
        if not cursor.fetchone():
            # Add the column
            cursor.execute("""
                ALTER TABLE assignments_assignment 
                ADD COLUMN block_after_deadline BOOLEAN DEFAULT FALSE
            """)
            print("Column 'block_after_deadline' added successfully!")
        else:
            print("Column 'block_after_deadline' already exists!")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
