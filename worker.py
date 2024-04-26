import subprocess
import datetime

def backup_database():
    # Current date to append to the backup file's name
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Filename for the backup
    filename = f"backup_{date_str}.sql"
    
    # Command to run pg_dump
    command = f"pg_dump -U postgres -h localhost -p 5432 -d luca -f {filename}"
    
    try:
        # Execute the pg_dump command
        subprocess.run(command, check=True, shell=True)
        print("Backup successful")
    except subprocess.CalledProcessError as e:
        print(f"Error during backup: {e}")

# Run the backup function
backup_database()
