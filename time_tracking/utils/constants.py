from datetime import date

# Info admin
EMAIL_ADMIN = "seradjor@gmail.com"

# Duración de la jornada laboral (en horas)
DURACION_JORNADA = 6

# Valores económicos
HORA_EXTRA = 1.5
HORA_FESTIVO = 2.0

# Festivos 2026
FESTIVOS_2026 = {
    date(2026, 1, 1), 
    date(2026, 1, 6),  
    date(2026, 3, 19),  
    date(2026, 3, 29),  
    date(2026, 5, 1),   
    date(2026, 8, 15),  
    date(2026, 10, 12), 
    date(2026, 11, 1),  
    date(2026, 12, 6),  
    date(2026, 12, 8),  
    date(2026, 12, 25)
}

# Formatos 
FORMATO_FECHA = "%d/%m/%Y"
FORMATO_HORA = "%H:%M"
