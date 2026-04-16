import pandas as pd
import numpy as np
from itertools import combinations


def triage_metrics(df_issues: pd.DataFrame, df_events: pd.DataFrame) -> dict:
    median_first_response = df_issues["time_to_first_response"].median()
    median_time_to_label = df_issues["time_to_first_label"].median()
    unlabeled_count = int((df_issues["labels"].apply(len) == 0).sum())
    return {
        "median_first_response_days": round(median_first_response, 1) if pd.notna(median_first_response) else None,
        "median_time_to_label_days": round(median_time_to_label, 1) if pd.notna(median_time_to_label) else None,
        "unlabeled_count": unlabeled_count,
    }


def contributor_metrics(df_issues: pd.DataFrame, df_events: pd.DataFrame) -> dict:
    now = pd.Timestamp.now(tz="UTC")
    ninety_days_ago = now - pd.Timedelta(days=90)
    creators = set(df_issues["creator"].dropna().unique())
    event_authors = set(df_events["author"].dropna().unique()) if not df_events.empty else set()
    all_contributors = creators | event_authors
    all_contributors.discard("")
    recent_creators = set(df_issues[df_issues["created_date"] >= ninety_days_ago]["creator"].dropna().unique())
    recent_event_authors = set()
    if not df_events.empty:
        recent_event_authors = set(df_events[df_events["event_date"] >= ninety_days_ago]["author"].dropna().unique())
    active_contributors = (recent_creators | recent_event_authors) - {""}
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_created = df_issues.groupby("creator")["created_date"].min()
    first_event = pd.Series(dtype="datetime64[ns, UTC]")
    if not df_events.empty:
        first_event = df_events.groupby("author")["event_date"].min()
    all_first = pd.concat([first_created, first_event]).groupby(level=0).min()
    new_this_month = int((all_first >= current_month_start).sum())
    six_months_ago = now - pd.Timedelta(days=180)
    last_created = df_issues.groupby("creator")["created_date"].max()
    last_event_auth = pd.Series(dtype="datetime64[ns, UTC]")
    if not df_events.empty:
        last_event_auth = df_events.groupby("author")["event_date"].max()
    all_last = pd.concat([last_created, last_event_auth]).groupby(level=0).max()
    returning_count = 0
    for user in active_contributors:
        if user in all_first.index and user in all_last.index:
            first = all_first[user]
            if pd.notna(first) and first < six_months_ago:
                returning_count += 1
    creator_counts = df_issues["creator"].value_counts().rename("issues_created")
    if not df_events.empty:
        comment_events = df_events[df_events["event_type"] == "commented"]
        comment_counts = comment_events["author"].value_counts().rename("comments")
        event_counts = df_events["author"].value_counts().rename("total_events")
    else:
        comment_counts = pd.Series(dtype="int64", name="comments")
        event_counts = pd.Series(dtype="int64", name="total_events")
    top_df = pd.concat([creator_counts, comment_counts, event_counts], axis=1).fillna(0).astype(int)
    top_df = top_df.sort_values("total_events", ascending=False).head(20)
    top_df.index.name = "user"
    top_df = top_df.reset_index()
    return {
        "total_contributors": len(all_contributors),
        "active_90d": len(active_contributors),
        "new_this_month": new_this_month,
        "returning": returning_count,
        "top_contributors": top_df,
    }


def trend_metrics(df_issues: pd.DataFrame) -> dict:
    bugs = df_issues[df_issues["is_bug"]]
    features = df_issues[df_issues["is_feature"]]
    bug_count = len(bugs)
    feature_count = len(features)
    ratio = round(bug_count / feature_count, 2) if feature_count > 0 else 0
    df_copy = df_issues.copy()
    df_copy["year_month"] = df_copy["created_date"].dt.to_period("M")
    monthly_bugs = bugs.groupby(bugs["created_date"].dt.to_period("M")).size().rename("bugs")
    monthly_features = features.groupby(features["created_date"].dt.to_period("M")).size().rename("features")
    monthly = pd.concat([monthly_bugs, monthly_features], axis=1).fillna(0).astype(int)
    monthly.index.name = "month"
    monthly = monthly.reset_index()
    monthly["month"] = monthly["month"].dt.to_timestamp()
    all_labels = sorted(set(l for labels in df_issues["labels"] for l in labels))
    now = pd.Timestamp.now(tz="UTC")
    three_mo_ago = now - pd.Timedelta(days=90)
    six_mo_ago = now - pd.Timedelta(days=180)
    growth_rows = []
    for label in all_labels:
        mask = df_issues["labels"].apply(lambda ls: label in ls)
        recent = int(mask[df_issues["created_date"] >= three_mo_ago].sum())
        prior = int(mask[(df_issues["created_date"] >= six_mo_ago) & (df_issues["created_date"] < three_mo_ago)].sum())
        if prior > 0:
            growth = round((recent - prior) / prior * 100, 1)
        elif recent > 0:
            growth = 100.0
        else:
            growth = 0.0
        growth_rows.append({"label": label, "recent_count": recent, "prior_count": prior, "growth_pct": growth})
    growth_df = pd.DataFrame(growth_rows).sort_values("growth_pct", ascending=False)
    return {
        "bug_count": bug_count,
        "feature_count": feature_count,
        "bug_feature_ratio": ratio,
        "monthly_trends": monthly,
        "label_growth": growth_df,
    }


def staleness_metrics(df_issues: pd.DataFrame) -> dict:
    open_issues = df_issues[df_issues["state"] == "open"]
    stale_count = int((open_issues["staleness_bucket"] == "Stale").sum())
    zombie_count = int((open_issues["staleness_bucket"] == "Zombie").sum())
    no_response = int((open_issues["event_count"] == 0).sum())
    bucket_counts = open_issues["staleness_bucket"].value_counts().to_dict()
    attention = open_issues[
        open_issues["staleness_bucket"].isin(["Stale", "Zombie"])
    ][["number", "title", "labels", "last_activity", "days_since_last_activity", "staleness_bucket", "url"]].copy()
    attention = attention.sort_values("days_since_last_activity", ascending=False)
    return {
        "stale_count": stale_count,
        "zombie_count": zombie_count,
        "no_response_count": no_response,
        "bucket_distribution": bucket_counts,
        "attention_list": attention,
    }


def resolution_metrics(df_issues: pd.DataFrame, df_events: pd.DataFrame) -> dict:
    closed = df_issues[df_issues["state"] == "closed"]
    median_days = closed["days_to_close"].median()
    if not df_events.empty:
        reopened_issues = df_events[df_events["event_type"] == "ReopenedEvent"]["issue_number"].nunique()
    else:
        reopened_issues = 0
    total_issues = len(df_issues)
    reopen_rate = round(reopened_issues / total_issues * 100, 1) if total_issues > 0 else 0
    df_copy = df_issues.copy()
    df_copy["year_month"] = df_copy["created_date"].dt.to_period("M")
    monthly_created = df_copy.groupby("year_month").size().rename("created")
    monthly_closed = closed.groupby(closed["created_date"].dt.to_period("M")).size().rename("closed")
    monthly = pd.concat([monthly_created, monthly_closed], axis=1).fillna(0).astype(int)
    monthly.index.name = "month"
    monthly = monthly.reset_index()
    monthly["month"] = monthly["month"].dt.to_timestamp()
    if not df_events.empty:
        reopen_counts = (
            df_events[df_events["event_type"] == "ReopenedEvent"]
            .groupby("issue_number").size().rename("reopen_count")
            .sort_values(ascending=False).head(10)
        )
        most_reopened = df_issues[df_issues["number"].isin(reopen_counts.index)][
            ["number", "title", "state", "labels", "url"]
        ].copy()
        most_reopened = most_reopened.merge(
            reopen_counts, left_on="number", right_index=True
        ).sort_values("reopen_count", ascending=False)
    else:
        most_reopened = pd.DataFrame(columns=["number", "title", "state", "labels", "url", "reopen_count"])
    now = pd.Timestamp.now(tz="UTC")
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    closed_this_month = int((closed["updated_date"] >= current_month_start).sum())
    created_this_month = int((df_issues["created_date"] >= current_month_start).sum())
    net_open = created_this_month - closed_this_month
    return {
        "median_days_to_close": round(median_days, 1) if pd.notna(median_days) else None,
        "reopen_rate": reopen_rate,
        "closed_this_month": closed_this_month,
        "net_open_this_month": net_open,
        "monthly_rates": monthly,
        "most_reopened": most_reopened,
    }


def label_metrics(df_issues: pd.DataFrame) -> dict:
    all_labels = [l for labels in df_issues["labels"] for l in labels]
    unique_labels = len(set(all_labels))
    avg_labels_per_issue = round(len(all_labels) / len(df_issues), 1) if len(df_issues) > 0 else 0
    unlabeled_count = int((df_issues["labels"].apply(len) == 0).sum())
    label_series = pd.Series(all_labels)
    label_counts = label_series.value_counts().reset_index()
    label_counts.columns = ["label", "count"]
    pair_counts = {}
    for labels in df_issues["labels"]:
        if len(labels) >= 2:
            for pair in combinations(sorted(set(labels)), 2):
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
    co_occurrence = pd.DataFrame(
        [{"label_pair": f"{a} + {b}", "count": c} for (a, b), c in pair_counts.items()]
    )
    if not co_occurrence.empty:
        co_occurrence = co_occurrence.sort_values("count", ascending=False).head(20)
    return {
        "unique_labels": unique_labels,
        "avg_labels_per_issue": avg_labels_per_issue,
        "unlabeled_count": unlabeled_count,
        "label_counts": label_counts,
        "co_occurrence": co_occurrence,
    }
