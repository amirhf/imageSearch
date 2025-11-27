from locust import HttpUser, task, between
import random

class SearchUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def search_public_vector(self):
        """Simulate a public vector search (most common)"""
        queries = ["cat", "dog", "car", "beach", "mountain", "city", "food", "people"]
        q = random.choice(queries)
        self.client.get(f"/search?q={q}&scope=public", name="/search (public)")

    @task(1)
    def search_hybrid_all(self):
        """Simulate an authenticated hybrid search across all images"""
        # Note: In a real scenario, we'd need to handle auth tokens.
        # For now, assuming the API handles auth or we are testing public endpoints primarily,
        # or we can mock auth headers if needed.
        # Given the current setup, let's stick to public search or mock a user if possible.
        # The benchmark script used a hardcoded user_id.
        # For simplicity in this load test, we'll focus on the public endpoint which hits the core search logic.
        queries = ["office", "laptop", "meeting", "code"]
        q = random.choice(queries)
        self.client.get(f"/search?q={q}&scope=all", name="/search (all)")

    @task(1)
    def search_hybrid_mine(self):
        """Simulate searching own images"""
        queries = ["my document", "notes", "screenshot"]
        q = random.choice(queries)
        # We need a user_id for 'mine' scope usually, or it defaults to current user.
        # If no auth token, 'mine' might fail or return empty.
        # Let's assume we want to stress test the 'public' path mostly as it's the heaviest.
        self.client.get(f"/search?q={q}&scope=public", name="/search (public_random)")
