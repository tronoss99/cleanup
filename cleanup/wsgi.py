from cleanup import cleanup_inactive_devices

def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    cleanup_inactive_devices()
    return [b'Limpieza completada con éxito']
