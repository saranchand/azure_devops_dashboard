import pandas as pd

def create_dataframe(work_items):
    """
    Create DataFrame from Azure DevOps work items.
    Processes raw JSON data before pandas normalization to avoid KeyError.
    """
    if not work_items:
        return pd.DataFrame()
    
    processed_items = []
    
    for item in work_items:
        fields = item.get("fields", {})
        assigned_to = fields.get("System.AssignedTo", {})
        
        # Extract data from nested fields structure
        processed_item = {
            "ID": item.get("id"),
            "Title": fields.get("System.Title"),
            "State": fields.get("System.State"),
            "AssignedTo": assigned_to.get("displayName") if isinstance(assigned_to, dict) else None,
            "OriginalEstimate": float(fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate", 0) or 0),
            "RemainingWork": float(fields.get("Microsoft.VSTS.Scheduling.RemainingWork", 0) or 0),
            "StoryPoints": float(fields.get("Microsoft.VSTS.Scheduling.StoryPoints", 0) or 0),
            "Parent": fields.get("System.Parent"),
            "WorkItemType": fields.get("System.WorkItemType"),
            "CreatedDate": fields.get("System.CreatedDate"),
            "ClosedDate": fields.get("System.ClosedDate")
        }
        processed_items.append(processed_item)
    
    df = pd.DataFrame(processed_items)
    
    # Convert date columns
    if not df.empty:
        df["CreatedDate"] = pd.to_datetime(df["CreatedDate"], errors='coerce')
        df["ClosedDate"] = pd.to_datetime(df["ClosedDate"], errors='coerce')
    
    return df

def calculate_metrics(df):
    """Calculate sprint metrics from the processed DataFrame"""
    if df.empty:
        return {
            "total_stories": 0,
            "bugs_in_stories": 0,
            "quality_percent": 100.0,
            "effort_exceeded_count": 0,
            "planned_task_hours": 0.0,
            "completed_task_hours": 0.0,
            "average_lead_time": 0.0
        }, df
    
    metrics = {}
    
    # Total Stories
    stories = df[df["WorkItemType"].isin(["User Story", "Product Backlog Item"])]
    metrics["total_stories"] = len(stories)
    
    # Bugs inside stories (bugs linked with a parent)
    bugs = df[df["WorkItemType"] == "Bug"]
    bugs_with_parents = bugs[bugs["Parent"].notnull()]
    metrics["bugs_in_stories"] = len(bugs_with_parents)
    
    # Quality: Percentage of stories without bugs inside
    if metrics["total_stories"] > 0:
        quality = 100.0 * (1 - (metrics["bugs_in_stories"] / metrics["total_stories"]))
        metrics["quality_percent"] = round(max(0, quality), 2)
    else:
        metrics["quality_percent"] = 100.0
    
    # Effort exceeded: Stories where Remaining > Original Estimate
    effort_exceeded = df[df["RemainingWork"] > df["OriginalEstimate"]]
    metrics["effort_exceeded_count"] = len(effort_exceeded)
    
    # Task planned vs completed
    tasks = df[df["WorkItemType"] == "Task"]
    planned = tasks["OriginalEstimate"].sum()
    completed = (tasks["OriginalEstimate"] - tasks["RemainingWork"]).sum()
    metrics["planned_task_hours"] = round(planned, 2)
    metrics["completed_task_hours"] = round(max(0, completed), 2)
    
    # Average Lead Time (days) for completed work items
    done_items = df[df["State"].isin(["Done", "Closed", "Resolved"])].copy()
    done_items = done_items.dropna(subset=["CreatedDate", "ClosedDate"])
    if not done_items.empty:
        done_items["LeadTimeDays"] = (done_items["ClosedDate"] - done_items["CreatedDate"]).dt.days
        metrics["average_lead_time"] = round(done_items["LeadTimeDays"].mean(), 2)
    else:
        metrics["average_lead_time"] = 0.0
    
    return metrics, df
