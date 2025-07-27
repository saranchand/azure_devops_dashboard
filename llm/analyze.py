import ollama

def get_ai_insights(metrics):
    prompt = f"""
You are a sprint analytics expert. Based on:
- Total Stories: {metrics['total_stories']}
- Bugs in Stories: {metrics['bugs_in_stories']}
- Quality %: {metrics['quality_percent']}%
- Effort Exceeded: {metrics['effort_exceeded_count']}
- Lead Time: {metrics['average_lead_time']} days

Give a clear summary if the sprint is at **high risk**, **on track**, or **healthy**. Then suggest 2 improvements.
"""
    response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]
