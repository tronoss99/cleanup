import pymysql
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_env_variable(var_name, default=None, required=False):
    value = os.environ.get(var_name, default)
    if required and not value:
        raise ValueError(f"La variable de entorno {var_name} es requerida pero no está definida.")
    return value

def cleanup_inactive_devices():
    DB_HOST = get_env_variable('DB_HOST', required=True)
    DB_USER = get_env_variable('DB_USER', required=True)
    DB_PASSWORD = get_env_variable('DB_PASSWORD', required=True)
    DB_NAME = get_env_variable('DB_NAME', required=True)
    DB_PORT = int(get_env_variable('DB_PORT', 3306))
    TIMEOUT_MINUTES = int(get_env_variable('TIMEOUT_MINUTES', 2))

    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            threshold_time = datetime.now() - timedelta(minutes=TIMEOUT_MINUTES)
            select_query = """
                SELECT device_id, user_id FROM devices
                WHERE last_ping < %s
            """
            cursor.execute(select_query, (threshold_time,))
            inactive_devices = cursor.fetchall()
            
            if not inactive_devices:
                logger.info("No hay dispositivos inactivos para limpiar.")
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
                
                logger.info(f"Dispositivo {device_id} del usuario {user_id} eliminado correctamente.")
            
            connection.commit()
            logger.info(f"Se limpiaron {len(inactive_devices)} dispositivos inactivos.")
    except pymysql.MySQLError as e:
        logger.error(f"Error durante la limpieza: {e}")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
    finally:
        if 'connection' in locals() and connection:
            connection.close()

if __name__ == "__main__":
    cleanup_inactive_devices()
