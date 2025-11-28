from imports import *

def loop_songs(sp, csv_path="data/short_playlist_data.csv", output_csv="data/formatted_features.csv"):
    all_features = []
    base = "https://api.reccobeats.com/v1/audio-features"

    df = pd.read_csv(csv_path)
    if "track_id" not in df.columns:
        raise RuntimeError(f"'track_id' column not found in {csv_path}")
    track_ids = df["track_id"].dropna().astype(str).tolist()

    batch_size = 40
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]
        params = {"ids": ",".join(batch)}
        try:
            r = requests.get(base, params=params)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"Request error for batch {i} ({len(batch)} ids): {e}")
            time.sleep(1.0)
            try:
                r = requests.get(base, params=params)
                r.raise_for_status()
                data = r.json()
            except Exception as e2:
                print(f"Second attempt failed for batch {i}: {e2}")
                continue

        if isinstance(data, dict):
            if "audio_features" in data:
                features_list = data["audio_features"] or []
            elif "features" in data:
                features_list = data["features"] or []
            elif "data" in data:
                features_list = data["data"] or []
            elif "items" in data:
                features_list = data["items"] or []
            else:
                candidates = [v for v in data.values() if isinstance(v, list)]
                features_list = candidates[0] if candidates else []
        elif isinstance(data, list):
            features_list = data
        else:
            features_list = []

        if features_list:
            all_features.extend(features_list)

        print(f"Processed {min(i + batch_size, len(track_ids))} / {len(track_ids)}")
        time.sleep(0.2)  


    features_df = pd.DataFrame(all_features)

    column_order = ["id", "href", "danceability", "energy", "key", "loudness",
                    "mode", "speechiness", "acousticness", "instrumentalness",
                    "liveness", "valence", "tempo"]

    existing_columns = [col for col in column_order if col in features_df.columns]
    if existing_columns:
        remaining = [col for col in features_df.columns if col not in existing_columns]
        features_df = features_df[existing_columns + remaining]

    features_df.to_csv(output_csv, index=False)
    print(features_df.head())
    
    cleaned_df = clean_data(csv_path=output_csv)
    
    return cleaned_df

def clean_data(csv_path="data/formatted_features.csv"):
    df=pd.read_csv(csv_path)

    scaler=StandardScaler()
    
    df=df.drop_duplicates(subset="id").dropna(subset=["danceability","energy","valence"])
    numeric_cols=["danceability","energy","loudness","speechiness","acousticness","instrumentalness","liveness","valence","tempo"]
    df[numeric_cols]=df[numeric_cols].astype(float)



    df_copy=df.copy()
    df_copy[numeric_cols]=scaler.fit_transform(df[numeric_cols])

    df_copy.to_csv(csv_path, index=False)
    return df_copy


def generate_vector(all_tracks, playlist_tracks):

    # playlist_set=all_tracks[all_tracks["id"].isin(playlist_tracks["id"].values)].fillna(0)
    playlist_set=playlist_tracks.fillna(0)
    other_set=all_tracks.fillna(0)

    # other_set=all_tracks[~all_tracks["id"].isin(playlist_tracks["id"].values)].fillna(0)

    numeric_cols=["danceability","energy","loudness","speechiness","acousticness","instrumentalness","liveness","valence","tempo"]
    playlist_features=playlist_set[numeric_cols].fillna(0)

    playlist_vector=playlist_features.mean(axis=0)

    return playlist_vector, other_set

def recommend(all_tracks, playlist_tracks, top_n=25):

    playlist_vector, other_set=generate_vector(all_tracks, playlist_tracks)
    print(playlist_vector)
    numeric_cols=["danceability","energy","loudness","speechiness","acousticness","instrumentalness","liveness","valence","tempo"]

    similarity=cosine_similarity([
        playlist_vector.values],
        other_set[numeric_cols].values
    )[0]

    other_set=other_set.copy()
    other_set["similarity"]=similarity

    recommendations=other_set.sort_values("similarity", ascending=False).head(top_n)

    return recommendations[["id","similarity"]]


def get_song_names(recommended_songs):
    ids=recommended_songs["id"].astype(str).tolist()
    base = "https://api.reccobeats.com/v1/track"
    BATCH_SIZE, DELAY = 40, 0.2
    results = []

    for i in range(0, len(ids), BATCH_SIZE):
        batch=ids[i:i + BATCH_SIZE]
        r = requests.get(base, params={"ids": ",".join(batch)})
        r.raise_for_status()
        tracks = r.json().get("content", [])
        for track in tracks:
            title = track.get("trackTitle", "N/A")
            artists_data = track.get("artists", [])
            if isinstance(artists_data, str):
                try:
                    artists_data = ast.literal_eval(artists_data)
                except Exception:
                    artists_data = []
            artists = ", ".join(a.get("name", "Unknown") for a in artists_data) or "Unknown"
            results.append({"trackTitle": title, "artists": artists})
        time.sleep(DELAY)

    pd.DataFrame(results).to_csv("data/tracks_info.csv", index=False, encoding="utf-8-sig")
    print("Done")




