import pymysql
import os
from datetime import datetime, timedelta

def cleanup_inactive_devices():
    DB_HOST = os.environ.get('DB_HOST')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_NAME = os.environ.get('DB_NAME')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    TIMEOUT_MINUTES = int(os.environ.get('TIMEOUT_MINUTES', 2))
    
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            threshold_time = datetime.now() - timedelta(minutes=TIMEOUT_MINUTES)
            
            select_query = """
                SELECT device_id, user_id FROM devices
                WHERE last_ping < %s
            """
            cursor.execute(select_query, (threshold_time,))
            inactive_devices = cursor.fetchall()
            
            if not inactive_devices:
                print("No hay dispositivos inactivos para limpiar.")
                return
            
            for device in inactive_devices:
                device_id = device['device_id']
                user_id = device['user_id']
                
                delete_query = """
                    DELETE FROM devices
                    WHERE user_id = %s AND device_id = %s
                """
                cursor.execute(delete_query, (user_id, device_id))
                
                update_query = """
                    UPDATE users
                    SET active_devices = active_devices - 1
                    WHERE id = %s AND active_devices > 0
                """
                cursor.execute(update_query, (user_id,))
                
                print(f"Dispositivo {device_id} del usuario {user_id} eliminado.")
            
            connection.commit()
            print(f"Se limpiaron {len(inactive_devices)} dispositivos inactivos.")
    except Exception as e:
        print(f"Error durante la limpieza: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    cleanup_inactive_devices()
