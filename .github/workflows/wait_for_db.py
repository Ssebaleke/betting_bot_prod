import time
import psycopg2
import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django management command that waits for database to be available."""
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--max_retries',
            type=int,
            default=30,
            help='Maximum number of retry attempts (default: 30)'
        )
        parser.add_argument(
            '--sleep_time',
            type=int,
            default=2,
            help='Seconds to sleep between retries (default: 2)'
        )
    
    def handle(self, *args, **options):
        max_retries = options['max_retries']
        sleep_time = options['sleep_time']
        
        self.stdout.write(self.style.NOTICE(f'Waiting for database... (max {max_retries * sleep_time} seconds)'))
        
        # Get database connection parameters
        db_config = {
            'host': os.environ.get('DB_HOST', 'db'),
            'database': os.environ.get('POSTGRES_DB', 'betbot'),
            'user': os.environ.get('POSTGRES_USER', 'betbot'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'betbot'),
            'port': os.environ.get('DB_PORT', '5432')
        }
        
        for attempt in range(1, max_retries + 1):
            try:
                self.stdout.write(f'Attempt {attempt}/{max_retries}: Connecting to {db_config["host"]}:{db_config["port"]}...')
                
                conn = psycopg2.connect(
                    host=db_config['host'],
                    database=db_config['database'],
                    user=db_config['user'],
                    password=db_config['password'],
                    port=db_config['port']
                )
                
                # Test connection with a simple query
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()
                cursor.close()
                conn.close()
                
                self.stdout.write(self.style.SUCCESS('✅ Database connection successful!'))
                return
                
            except psycopg2.OperationalError as e:
                if attempt < max_retries:
                    self.stdout.write(self.style.WARNING(f'Database not ready: {e}'))
                    self.stdout.write(f'Retrying in {sleep_time} seconds...')
                    time.sleep(sleep_time)
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to connect to database after {max_retries} attempts'))
                    self.stdout.write(self.style.ERROR(f'Last error: {e}'))
                    self.stdout.write(self.style.ERROR('Check that:'))
                    self.stdout.write(self.style.ERROR('1. PostgreSQL container is running'))
                    self.stdout.write(self.style.ERROR('2. Database credentials are correct'))
                    self.stdout.write(self.style.ERROR('3. Network connectivity between containers'))
                    exit(1)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))
                exit(1)