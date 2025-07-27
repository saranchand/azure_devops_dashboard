import pandas as pd
from datetime import datetime, timedelta

def generate_burndown_and_burnup(df, days=10):
    total = df["OriginalEstimate"].sum()
    dates = [datetime.today().date() + timedelta(d) for d in range(days)]

    ideal = [total - (i * total/days) for i in range(days)]
    actual = ideal.copy()  # Replace with tracking if you have history
    complete = [total - val for val in actual]

    return pd.DataFrame({
        "Date": dates,
        "IdealRemainingWork": ideal,
        "ActualRemainingWork": actual,
        "CompletedWork": complete
    })
