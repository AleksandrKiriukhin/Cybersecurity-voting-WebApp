from locust import HttpUser, task, between
import random
import string
from bs4 import BeautifulSoup
import re

class VotingUser(HttpUser):
    wait_time = between(1, 1)
    host = "https://127.0.0.1:5000"

    def on_start(self):

        self.client.verify = False

        suffix = ''.join(random.choices(string.digits, k=5))
        print(f"wygenerowany suffix = {suffix}")
        self.email = f"s{suffix}@student.ubb.edu.pl"
        self.password = "12345678Aa@"

        register_resp = self.client.post("/register", data={
            "first_name": "Test",
            "last_name": "User",
            "email": self.email,
            "password": self.password,
            "department_id": "1",
            "g-recaptcha-response": "dummy"
        })

        if register_resp.status_code != 200 or not register_resp.json().get("success", False):
            raise Exception(f"Rejestracja nieudana: {register_resp.text}")

        login = self.client.post("/login", data={
            "email": self.email,
            "password": self.password,
            "g-recaptcha-response": "dummy"
        })

        if login.status_code != 200:
            raise Exception("Login nieudany")

    @task
    def vote_flow(self):
        main = self.client.get("/main-page")
        print(f"udało się wejść na main-page")
        if main.status_code != 200:
            print(f"Nie udało się wejść na main-page: {main.status_code}")
            return

        soup = BeautifulSoup(main.text, "html.parser")
        votings = [a['href'] for a in soup.select('.single-voting-box a[href*="/vote/"]')]
        print(f"udało się znalezc glosowania: {votings}")
        
        if not votings:
            print("Brak dostępnych głosowań")
            return

        voting_url = votings[0]
        print(f"Wchodzę na głosowanie: {voting_url}")

        vote_page = self.client.get(voting_url)
        soup = BeautifulSoup(vote_page.text, "html.parser")

        candidate = soup.select_one('.place-for-tick[data-candidate-id]')
        if not candidate:
            print("Nie znaleziono kandydata")
            return

        candidate_id = candidate['data-candidate-id']

        
        match = re.search(r'/vote/([0-9a-fA-F-]+)', voting_url)
        if not match:
            print("Nie znaleziono election_id")
            return
        election_id = match.group(1)

        vote_resp = self.client.post(
            "/api/submit_vote",
            json={
                "election_id": election_id,
                "selected_candidate_ids": [int(candidate_id)]
            }
        )

        print(f"Oddanie głosu status: {vote_resp.status_code}, body: {vote_resp.text}")
