import requests
from configs.config import (
    AZURE_ORG_URL,
    AZURE_PROJECT,          # URL‐encoded project name
    AZURE_PROJECT_RAW,      # Raw project name for WIQL
    AZURE_TEAM,             # URL‐encoded team name
    get_auth_header,
    logger
)

def get_current_iteration_path():
    url = (
        f"{AZURE_ORG_URL}/{AZURE_PROJECT}/{AZURE_TEAM}"
        "/_apis/work/teamsettings/iterations"
        "?$timeframe=current&api-version=6.0"
    )
    logger.info("Fetching current iteration from %s", url)
    try:
        resp = requests.get(url, headers=get_auth_header())
        resp.raise_for_status()
        iters = resp.json().get("value", [])
        if not iters:
            logger.warning("No current iteration returned.")
            return None
        path = iters[0]["path"]
        logger.info("Current iteration path: %s", path)
        return path
    except Exception as exc:
        logger.error("Failed to get iteration path: %s", exc)
        return None

def get_sprint_dates():
    """Return sprint start and finish dates for the current iteration."""
    url = (
        f"{AZURE_ORG_URL}/{AZURE_PROJECT}/{AZURE_TEAM}"
        "/_apis/work/teamsettings/iterations"
        "?$timeframe=current&api-version=6.0"
    )
    try:
        resp = requests.get(url, headers=get_auth_header())
        resp.raise_for_status()
        attrs = resp.json()["value"][0]["attributes"]
        return {
            "start_date": attrs.get("startDate"),
            "end_date": attrs.get("finishDate")
        }
    except Exception as exc:
        logger.error("Failed to fetch sprint dates: %s", exc)
        return None

def get_sprint_work_items():
    iteration_path = get_current_iteration_path()
    if not iteration_path:
        return []

    # 1) Fetch IDs via WIQL
    safe_path = iteration_path.replace("'", "''")
    wiql = {
        "query": (
            f"SELECT [System.Id] "
            f"FROM WorkItems "
            f"WHERE [System.IterationPath] = '{safe_path}' "
            f"AND [System.TeamProject] = '{AZURE_PROJECT_RAW}'"
        )
    }
    wiql_url = f"{AZURE_ORG_URL}/{AZURE_PROJECT}/_apis/wit/wiql?api-version=6.0"
    r = requests.post(wiql_url, headers=get_auth_header(), json=wiql)
    r.raise_for_status()
    work_items = r.json().get("workItems", [])
    ids = [wi["id"] for wi in work_items]

    if not ids:
        return []

    # Batch fetch details in chunks
    batch_url = f"{AZURE_ORG_URL}/{AZURE_PROJECT}/_apis/wit/workitemsbatch?api-version=6.0"
    chunk_size = 50
    all_items = []

    fields = [
        "System.Id",
        "System.Title",
        "System.State",
        "System.WorkItemType",
        "System.CreatedDate",
        "System.ClosedDate",
        "System.AssignedTo",
        "System.Parent",
        "Microsoft.VSTS.Scheduling.OriginalEstimate",
        "Microsoft.VSTS.Scheduling.RemainingWork",
        "Microsoft.VSTS.Scheduling.StoryPoints"
    ]

    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i + chunk_size]
        payload = {"ids": chunk, "fields": fields}
        try:
            resp = requests.post(batch_url, headers=get_auth_header(), json=payload)
            resp.raise_for_status()
            all_items.extend(resp.json().get("value", []))
        except Exception as exc:
            logger.warning("Batch %d-%d failed: %s", i + 1, i + len(chunk), exc)

    return all_items
