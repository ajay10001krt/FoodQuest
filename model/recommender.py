import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class FoodRecommender:
    def __init__(self, data_path):
        # Load dataset
        self.df = pd.read_csv(data_path).fillna('')
        # create clean columns for robust matching
        self.df['Restaurant Name Clean'] = self.df['Restaurant Name'].astype(str).str.strip().str.lower()
        self.df['City Clean'] = self.df['City'].astype(str).str.strip().str.lower()
        # Combined features for similarity
        self.df['combined'] = (
            self.df['Cuisines'].astype(str) + ' ' +
            self.df['Restaurant Name'].astype(str) + ' ' +
            self.df['City'].astype(str)
        )
        # Vectorize & similarity matrix
        self.vectorizer = CountVectorizer(stop_words='english')
        self.feature_matrix = self.vectorizer.fit_transform(self.df['combined'])
        self.similarity = cosine_similarity(self.feature_matrix, self.feature_matrix)

    # ---------- Restaurant-based recommendation ----------
    def recommend(self, restaurant_name, city_name, top_n=10):
        rn = restaurant_name.strip().lower()
        cn = city_name.strip().lower()

        # Try exact match first (clean columns)
        exact_matches = self.df[
            (self.df['Restaurant Name Clean'] == rn) &
            (self.df['City Clean'] == cn)
        ]

        # If no exact match, fallback to contains on name within the city
        if exact_matches.empty:
            exact_matches = self.df[
                (self.df['Restaurant Name'].str.lower().str.contains(rn, na=False)) &
                (self.df['City Clean'] == cn)
            ]

        if exact_matches.empty:
            return []

        base_idx = exact_matches.index[0]

        # similarity scores against base
        scores = list(enumerate(self.similarity[base_idx]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        results = []
        seen = set()

        for idx, sc in scores:
            if idx == base_idx:
                continue
            row = self.df.iloc[idx]

            # ensure same city
            if row['City Clean'] != cn:
                continue

            name = row['Restaurant Name'].strip().title()
            if name in seen:
                continue
            seen.add(name)

            # lat/lon safe conversion
            try:
                lat = float(row.get('Latitude', 0) or 0)
                lon = float(row.get('Longitude', 0) or 0)
            except Exception:
                lat, lon = 0.0, 0.0

            address = row.get("Address", "")  # <- dataset address column
            results.append((
                name,
                row.get('Cuisines', ''),
                row.get('City', '').title(),
                round(sc, 3),
                lat,
                lon,
                address
            ))

            if len(results) >= top_n:
                break

        return results

    # ---------- Preferences-based recommendation ----------
    def recommend_by_preferences(self, cuisine, city, price, rating, top_n=10):
        # normalize inputs
        cuisine_q = cuisine.strip().lower() if cuisine else ''
        city_q = city.strip().lower() if city else ''

        # Filter by explicit preferences first (city, price, rating, cuisine)
        mask = pd.Series(True, index=self.df.index)
        if cuisine_q:
            mask &= self.df['Cuisines'].astype(str).str.lower().str.contains(cuisine_q, na=False)
        if city_q:
            mask &= self.df['City Clean'] == city_q
        if price is not None:
            mask &= (self.df['Price range'] == price)
        if rating is not None:
            mask &= (self.df['Aggregate rating'] >= rating)

        filtered = self.df[mask]
        if filtered.empty:
            return []

        # rank filtered items using similarity (use their own feature vectors)
        sims = []
        for idx in filtered.index:
            # compute similarity of this row to the rest (or use self similarity diagonal as proxy)
            # we will use average similarity to other items in filtered as a proxy score
            sims.append((idx, float(self.similarity[idx].mean())))

        sims = sorted(sims, key=lambda x: x[1], reverse=True)

        results = []
        seen = set()
        for idx, sc in sims:
            row = self.df.iloc[idx]
            name = row['Restaurant Name'].strip().title()
            if name in seen:
                continue
            seen.add(name)

            try:
                lat = float(row.get('Latitude', 0) or 0)
                lon = float(row.get('Longitude', 0) or 0)
            except Exception:
                lat, lon = 0.0, 0.0

            address = row.get("Address", "")
            results.append((
                name,
                row.get('Cuisines', ''),
                row.get('City', '').title(),
                round(sc, 3),
                lat,
                lon,
                address
            ))

            if len(results) >= top_n:
                break

        return results