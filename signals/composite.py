def composite_score(df, news_score):
    vol = volume_spike_score(df)
    muted = muted_price(df)

    if news_score > 0.7 and muted:
        return 0

    return vol
