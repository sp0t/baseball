import subprocess
import datetime
import os

def backup_database():
    # Current date to append to the backup file's name
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    # Filename for the backup
    filename = f"backup/{date_str}.sql"
    
    # PostgreSQL credentials
    db_username = "postgres"
    db_host = "localhost"
    db_port = "5432"
    db_name = "betmlb"
    db_password = "lucamlb123"  # Be cautious with password handling

    # Setting the PGPASSWORD environment variable
    os.environ['PGPASSWORD'] = db_password

    # Command to run pg_dump
    command = f"pg_dump -U {db_username} -h {db_host} -p {db_port} -d {db_name} -f {filename}"
    
    try:
        # Execute the pg_dump command
        subprocess.run(command, check=True, shell=True)
        print("Backup successful")
    finally:
        # Ensure that the password is cleared from the environment variables after running
        del os.environ['PGPASSWORD']

# Run the backup function
backup_database()
