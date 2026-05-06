from datetime import date

# Info admin
EMAIL_ADMIN = "seradjor@gmail.com"

# Duración de la jornada laboral (en horas)
WORKDAY_DURATION = 6.0

# Franja horaria posible apertura centro de trabajo,
MIN_HOUR = 8.0 
MAX_HOUR = 22.0

# Valores económicos
OVERTIME_HOUR = 1.5
HOLIDAY_HOUR = 2.0

# Festivos 2026
HOLIDAYS_2026 = {
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
REPORT_DATE_FORMAT = "%d/%m/%Y"
DATE_FORMAT = "%Y-%m-%d"
