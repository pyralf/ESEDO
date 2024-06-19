from datetime import datetime, timedelta

def generate_time_steps():
    # Start- und Enddatum festlegen
    start_date = datetime(2020, 1, 1, 0, 0, 0)
    end_date = datetime(2020, 1, 31, 23, 59, 59)

    # Liste der Zeitstempel generieren
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime("%Y-%m-%d %H:%M:%S"))
        current_date += timedelta(hours=1)

    return date_list


# Ausgabe der Liste
for date in generate_time_steps():
    print(date)

