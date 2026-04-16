import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = ROOT / 'processed'


def load_json(name: str):
    path = PROCESSED_DIR / name
    if not path.exists():
        return {}
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def load_data_frame(name: str) -> pd.DataFrame:
    path = PROCESSED_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def format_percentage(value: float) -> str:
    return f"{value:.0f}%" if isinstance(value, (int, float)) else '0%'


def build_narrative(summary: dict) -> str:
    sentences = []
    if summary.get('largest_source_by_volume'):
        sentences.append(
            f"Your profile is dominated by {summary['largest_source_by_volume']} ({format_percentage(summary['largest_source_share'])} of activity)."
        )
    if summary.get('dominant_category'):
        sentences.append(
            f"The strongest category is {summary['dominant_category']}, with top themes around {', '.join([c['category'] for c in summary.get('top_categories', [])[:3]])}."
        )
    if summary.get('missing_sources'):
        sentences.append(
            f"Data gaps remain for {', '.join(summary['missing_sources']) or 'none'}, so the profile may underrepresent those areas."
        )
    if summary.get('most_active_day'):
        sentences.append(
            f"Your most active recent day is {summary['most_active_day']}."
        )
    if summary.get('data_completeness') is not None:
        sentences.append(
            f"Current completeness is {format_percentage(summary['data_completeness'])}, highlighting where more exports would help."
        )
    if not sentences:
        return 'The dashboard is ready once you run a refresh with your local exports. It will show source mix, time trends, categories, and coverage now.'
    return ' '.join(sentences)


def tidy_index(df: pd.DataFrame, label: str):
    return df.set_index(label)


def render_title():
    st.set_page_config(page_title='JoshProfile Dashboard', layout='wide')
    st.title('JoshProfile Personal Intelligence')
    st.markdown(
        'A locally generated personal dashboard for your imported activity, documents, categories, and source coverage.'
    )


def render_overview(summary: dict):
    st.subheader('Overview')
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Activity rows', summary.get('total_activity_rows', 0))
    col2.metric('Documents', summary.get('total_documents', 0))
    col3.metric('Entities', summary.get('total_entities', 0))
    col4.metric('Sources ingested', summary.get('source_count', 0))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric('Largest source', summary.get('largest_source_by_volume', 'unknown'))
    col6.metric('Most active day', summary.get('most_active_day', 'unknown'))
    col7.metric('Dominant category', summary.get('dominant_category', 'unknown'))
    col8.metric('Completeness', format_percentage(summary.get('data_completeness', 0)))

    if summary.get('missing_data'):
        expected_count = len(summary['missing_data'].get('expected_sources', []))
        present_count = len(summary['missing_data'].get('present_sources', []))
        st.markdown(f'**Source inventory:** {present_count}/{expected_count} expected sources present')

    st.markdown('### Profile Snapshot')
    st.write(build_narrative(summary))


def render_trend_charts(summary: dict):
    st.subheader('Trends')
    source_df = pd.DataFrame(summary.get('top_sources', []))
    category_df = pd.DataFrame(summary.get('top_categories', []))
    action_df = pd.DataFrame(summary.get('top_actions', []))
    hourly_df = pd.DataFrame(summary.get('hourly', [])).set_index('hour')
    weekday_df = pd.DataFrame(summary.get('weekday', [])).set_index('weekday')
    trend_series = load_json('trend_series.json')
    daily_df = pd.DataFrame(trend_series.get('daily', [])).set_index('date') if trend_series.get('daily') else pd.DataFrame()
    weekly_df = pd.DataFrame(trend_series.get('weekly', [])).set_index('week') if trend_series.get('weekly') else pd.DataFrame()

    st.markdown('#### Activity over time')
    if not daily_df.empty:
        st.line_chart(daily_df['count'])
    if not weekly_df.empty:
        st.markdown('##### Weekly trend')
        st.line_chart(weekly_df['count'])

    st.markdown('#### Source mix')
    if not source_df.empty:
        st.bar_chart(source_df.set_index('source')['count'])

    st.markdown('#### Category mix')
    if not category_df.empty:
        st.bar_chart(category_df.set_index('category')['count'])

    cols = st.columns(2)
    with cols[0]:
        st.markdown('#### Hour of day')
        if not hourly_df.empty:
            st.bar_chart(hourly_df['count'])
    with cols[1]:
        st.markdown('#### Day of week')
        if not weekday_df.empty:
            st.bar_chart(weekday_df['count'])

    st.markdown('#### Action mix')
    if not action_df.empty:
        st.bar_chart(action_df.set_index('action')['count'])


def render_recent_vs_long_term(summary: dict):
    st.subheader('Recent Shift')
    recent_df = pd.DataFrame(summary.get('recent_top_categories', []))
    long_df = pd.DataFrame(summary.get('long_term_categories', []))
    if not recent_df.empty:
        st.markdown('##### Recent 30-day category leaders')
        st.bar_chart(recent_df.set_index('category')['count'])
    if not long_df.empty:
        st.markdown('##### Long-term category leaders')
        st.bar_chart(long_df.set_index('category')['count'])
    st.markdown('##### Category drift')
    drift_df = pd.DataFrame(summary.get('category_drifts', []))
    if not drift_df.empty:
        st.table(drift_df.head(8))


def render_outlook_insights(summary: dict):
    if not summary.get('outlook_total'):
        return
    st.subheader('Outlook Intelligence')
    cols = st.columns(3)
    cols[0].metric('Outlook emails', summary.get('outlook_mail_count', 0))
    cols[1].metric('Outlook events', summary.get('outlook_calendar_count', 0))
    positive_share = sum(item.get('share', 0) for item in summary.get('outlook_sentiment', []) if item.get('sentiment') == 'positive')
    cols[2].metric('Outlook positive mood', f"{round(positive_share * 100, 0)}%")

    sentiment_df = pd.DataFrame(summary.get('outlook_sentiment', []))
    if not sentiment_df.empty:
        sentiment_df = sentiment_df.set_index('sentiment')
        st.markdown('##### Email sentiment')
        st.bar_chart(sentiment_df['count'])

    sender_df = pd.DataFrame(summary.get('outlook_top_senders', []))
    if not sender_df.empty:
        sender_df = sender_df.set_index('sender')
        st.markdown('##### Top Outlook senders')
        st.bar_chart(sender_df['count'])


def render_source_health(coverage: list, gaps: dict):
    st.subheader('Data Gaps & Coverage')
    st.markdown('#### Source health')
    if coverage:
        df = pd.DataFrame(coverage)
        if 'status' in df.columns:
            df = df[['name', 'status', 'files_discovered', 'records_extracted']]
        st.dataframe(df)

    if gaps:
        expected = gaps.get('expected_sources', [])
        present = gaps.get('present_sources', [])
        if expected:
            st.markdown('#### Expected sources')
            st.write(', '.join(expected))
            st.markdown('#### Present sources')
            st.write(', '.join(present or []))

    missing = gaps.get('missing_sources', [])
    if missing:
        st.markdown('#### Missing source imports')
        st.write(', '.join(missing))
    else:
        st.markdown('#### Missing source imports')
        st.write('No expected sources are missing from the current profile.')


def render_documents(document_types: list, docs: pd.DataFrame):
    st.subheader('Documents')
    if document_types:
        dt = pd.DataFrame(document_types).set_index('file_type')
        st.bar_chart(dt['count'])
    if not docs.empty:
        st.markdown('#### Latest imported documents')
        st.dataframe(docs.head(10))


def render_insights(summary: dict, top_creators: list, activity: pd.DataFrame):
    st.subheader('Top Patterns')
    if top_creators:
        creators_df = pd.DataFrame(top_creators).set_index('creator')
        st.markdown('##### Top creators / channels / artists')
        st.bar_chart(creators_df['count'])
    if not activity.empty:
        st.markdown('##### Strongest themes')
        st.write(', '.join([row['category'] for row in summary.get('top_categories', [])[:5]]))
        st.markdown('##### Recent top categories')
        st.write(', '.join([row['category'] for row in summary.get('recent_top_categories', [])[:5]]))
        st.markdown('##### Most repeated action types')
        st.write(', '.join([row['action'] for row in summary.get('top_actions', [])[:5]]))


def render_filters(activity: pd.DataFrame, summary: dict):
    st.sidebar.title('Filters')
    sources = sorted(activity['source'].dropna().unique()) if not activity.empty else []
    categories = sorted(activity['category'].dropna().unique()) if not activity.empty else []
    actions = sorted(activity['action'].dropna().unique()) if not activity.empty else []
    source_filter = st.sidebar.multiselect('Source', options=sources, default=sources)
    category_filter = st.sidebar.multiselect('Category', options=categories, default=categories)
    action_filter = st.sidebar.multiselect('Action', options=actions, default=actions)
    if not activity.empty:
        min_date = activity['timestamp'].min().date()
        max_date = activity['timestamp'].max().date()
        date_range = st.sidebar.date_input('Date range', [min_date, max_date], min_value=min_date, max_value=max_date)
        if len(date_range) == 2:
            start, end = date_range
            activity = activity[(activity['timestamp'].dt.date >= start) & (activity['timestamp'].dt.date <= end)]
    else:
        activity = activity
    if sources:
        activity = activity[activity['source'].isin(source_filter)]
    if categories:
        activity = activity[activity['category'].isin(category_filter)]
    if actions:
        activity = activity[activity['action'].isin(action_filter)]
    return activity


def main():
    render_title()
    summary = load_json('dashboard_summary.json')
    coverage = load_json('source_coverage.json')
    document_types = load_json('document_types.json')
    data_gaps = load_json('data_gaps.json')
    activity = load_data_frame('normalized_activity.csv')
    documents = load_data_frame('normalized_documents.csv')
    entities = load_data_frame('normalized_entities.csv')

    if not activity.empty:
        activity['timestamp'] = pd.to_datetime(activity['timestamp'], errors='coerce')
        activity['category'] = activity['category'].fillna('Uncategorized')
        activity['action'] = activity['action'].fillna('Other')

    activity = render_filters(activity, summary)

    render_overview(summary)
    render_trend_charts(summary)
    render_recent_vs_long_term(summary)
    render_outlook_insights(summary)
    render_source_health(coverage, data_gaps)
    render_documents(document_types, documents)
    render_insights(summary, summary.get('top_creators', []), activity)

    st.sidebar.markdown('---')
    st.sidebar.write('Run `python app.py refresh` after dropping new exports into raw/.')


if __name__ == '__main__':
    main()
