

class LiveStatusQueryError(Exception):
    messages = {
        200: 'OK',
        404: 'Invalid GET request, no such table \'%s\'',
        450: 'Invalid GET request, no such column \'%s\'',
        452: 'Completely invalid GET request \'%s\'',
        500: 'Internal server error: %r',
    }

