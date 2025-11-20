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
        cuisine_q = cuisine.strip().lower() if cuisine else ""
        city_q = city.strip().lower() if city else ""

        # ----- SAFE CLEANUPS ON DF COLUMNS -----
        # Ensure helper clean columns exist
        if "City Clean" not in self.df.columns:
            self.df["City Clean"] = self.df["City"].astype(str).str.strip().str.lower()
        if "Restaurant Name Clean" not in self.df.columns:
            self.df["Restaurant Name Clean"] = self.df["Restaurant Name"].astype(str).str.strip().str.lower()

        # Normalize price into integer "PriceClean" where possible
        def safe_price(x):
            try:
                return int(float(x))
            except Exception:
                return None

        if "Price Clean" not in self.df.columns:
            self.df["Price Clean"] = self.df.get("Price range", "").apply(safe_price)

        # Normalize rating to float safely
        def safe_rating(x):
            try:
                return float(x)
            except Exception:
                return 0.0

        if "Rating Clean" not in self.df.columns:
            self.df["Rating Clean"] = self.df.get("Aggregate rating", "").apply(safe_rating)

        # ----- FLEXIBLE FILTERING -----
        mask = pd.Series(True, index=self.df.index)

        # city: use contains on cleaned column (tolerant)
        if city_q:
            mask &= self.df["City Clean"].str.contains(city_q, na=False)

        # cuisine: contains (tolerant)
        if cuisine_q:
            mask &= self.df["Cuisines"].astype(str).str.lower().str.contains(cuisine_q, na=False)

        # price: allow approximate matching (+-1) because dataset formats vary
        if price is not None:
            try:
                # price from UI is usually int already
                price_int = int(price)
                # Accept entries with PriceClean near the selected price OR missing PriceClean (fallback)
                mask_price = (
                    self.df["Price Clean"].notna() &
                    (self.df["Price Clean"] >= (price_int - 1)) &
                    (self.df["Price Clean"] <= (price_int + 1))
                )
                # Combine: prefer those matching price window but allow rows with missing price if none matched
                mask &= (mask_price | self.df["Price Clean"].isna())
            except Exception:
                # if conversion fails, do not filter by price
                pass

        # rating: numeric compare
        if rating is not None:
            try:
                rating_val = float(rating)
                mask &= self.df["Rating Clean"] >= rating_val
            except Exception:
                pass

        filtered = self.df[mask]

        # ----- FALLBACKS if filtered is empty (be progressively more permissive) -----
        if filtered.empty:
            # 1) Relax price (ignore price), keep city & cuisine & rating
            mask2 = pd.Series(True, index=self.df.index)
            if city_q:
                mask2 &= self.df["City Clean"].str.contains(city_q, na=False)
            if cuisine_q:
                mask2 &= self.df["Cuisines"].astype(str).str.lower().str.contains(cuisine_q, na=False)
            if rating is not None:
                try:
                    mask2 &= self.df["Rating Clean"] >= float(rating)
                except Exception:
                    pass
            filtered = self.df[mask2]

        if filtered.empty:
            # 2) Relax cuisine too (keep only city & rating)
            mask3 = pd.Series(True, index=self.df.index)
            if city_q:
                mask3 &= self.df["City Clean"].str.contains(city_q, na=False)
            if rating is not None:
                try:
                    mask3 &= self.df["Rating Clean"] >= float(rating)
                except Exception:
                    pass
            filtered = self.df[mask3]

        if filtered.empty:
            # 3) Relax to city only (no rating)
            if city_q:
                filtered = self.df[self.df["City Clean"].str.contains(city_q, na=False)]

        if filtered.empty:
            # 4) Give up and use full dataset as last resort (so user always gets results)
            filtered = self.df.copy()

        # ----- SCORING: use similarity metric as ranking (average similarity proxy) -----
        sims = []
        for idx in filtered.index:
            sims.append((idx, float(self.similarity[idx].mean())))

        sims = sorted(sims, key=lambda x: x[1], reverse=True)

        # ----- BUILD RESULTS -----
        results = []
        seen = set()
        for idx, sc in sims:
            row = self.df.iloc[idx]
            name = row["Restaurant Name"].strip().title()
            if name in seen:
                continue
            seen.add(name)

            try:
                lat = float(row.get("Latitude", 0) or 0)
                lon = float(row.get("Longitude", 0) or 0)
            except Exception:
                lat, lon = 0.0, 0.0

            addr = row.get("Address", "") if "Address" in row.index else ""

            results.append((
                name,
                row.get("Cuisines", ""),
                row.get("City", "").title(),
                round(sc, 3),
                lat,
                lon,
                addr
            ))

            if len(results) >= top_n:
                break

        return results