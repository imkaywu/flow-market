def volume_spike_score(df):
    z = df.iloc[-1]["volume_z"]
    return min(z / 5, 1.0)  # normalize
