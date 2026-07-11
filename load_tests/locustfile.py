from locust import HttpUser, task, between

class GoodCitizen(HttpUser):
    """A normal user sending a steady, slow stream of traffic."""
    wait_time = between(1, 2)
    weight = 3  # 3 times more common than the spiky user

    @task
    def steady_request(self):
        with self.client.get("/api/data", headers={"X-API-Key": "good_tenant"}, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Good citizen was incorrectly rate limited!")

class SpikyUser(HttpUser):
    """A user trying to burst multiple requests instantly."""
    wait_time = between(5, 10) # Waits quietly, then unleashes a burst
    weight = 1

    @task
    def burst_request(self):
        # Unleash a burst of 50 simultaneous-like requests
        for _ in range(50):
            with self.client.get("/api/data", headers={"X-API-Key": "spiky_tenant"}, catch_response=True) as response:
                # We EXPECT 429s here because their limit is only 10.
                if response.status_code == 429:
                    # If it's a 429, that means our rate limiter successfully protected the API
                    response.success() 
                elif response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Unexpected status: {response.status_code}")