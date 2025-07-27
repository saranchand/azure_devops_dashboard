def color_for_quality(val):
    return "green" if val >= 80 else "orange" if val >= 60 else "red"

def color_for_effort_exceeded(val):
    return "green" if val == 0 else "orange" if val < 3 else "red"

def color_for_lead_time(val):
    return "green" if val <= 5 else "orange" if val <= 8 else "red"
