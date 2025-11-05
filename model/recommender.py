import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class FoodRecommender:
    def __init__(self, data_path):
        # Load dataset
        self.df = pd.read_csv(data_path)
        self.df = self.df.fillna('')

        # Combine features for better contextual similarity
        self.df['combined'] = (
            self.df['Cuisines'].astype(str) + ' ' +
            self.df['Restaurant Name'].astype(str) + ' ' +
            self.df['City'].astype(str)
        )

        # Build vectorizer
        self.vectorizer = CountVectorizer(stop_words='english')
        self.feature_matrix = self.vectorizer.fit_transform(self.df['combined'])
        self.similarity = cosine_similarity(self.feature_matrix, self.feature_matrix)

    def recommend(self, restaurant_name, city_name, top_n=10):
        """
        Recommend similar restaurants to the given restaurant within the same city.
        Filters out duplicate restaurant names for cleaner results.
        """
        # Normalize input
        restaurant_name = restaurant_name.strip().lower()
        city_name = city_name.strip().lower()

        # Normalize dataset
        self.df['Restaurant Name'] = self.df['Restaurant Name'].astype(str).str.lower()
        self.df['City'] = self.df['City'].astype(str).str.lower()

        # Find base restaurant in that city
        matches = self.df[
            (self.df['Restaurant Name'].str.contains(restaurant_name, case=False, na=False)) &
            (self.df['City'].str.contains(city_name, case=False, na=False))
            ]

        if matches.empty:
            return []

        # Take the first match as base
        idx = matches.index[0]

        # Compute similarity
        scores = list(enumerate(self.similarity[idx]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        # Prepare results within same city
        results = []
        seen_names = set()  # track duplicates

        for i in scores[1:]:
            data = self.df.iloc[i[0]]

            # Skip different city or same restaurant
            if data['City'] != city_name or data['Restaurant Name'] == restaurant_name:
                continue

            name = data['Restaurant Name'].strip().title()

            # Skip duplicates by name
            if name in seen_names:
                continue
            seen_names.add(name)

            results.append((
                name,
                data['Cuisines'],
                data['City'].title(),
                round(i[1], 3)
            ))

            if len(results) >= top_n:
                break

        return results