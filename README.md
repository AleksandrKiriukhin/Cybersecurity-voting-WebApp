# Secure University Voting System with Homomorphic Encryption

## 📌 Project Overview

This project is a secure web-based voting system designed for university student government elections. The application ensures **anonymity, vote secrecy, and correctness of vote counting** by leveraging **Paillier homomorphic encryption**.

The system allows students to cast votes securely while enabling encrypted aggregation of results without revealing individual votes.

---

## 🔐 Key Features

* 🗳️ **Secure Voting System** – enables students to participate in elections in a safe and controlled environment
* 🔒 **Anonymity & Privacy** – votes are encrypted to ensure full voter anonymity and secrecy
* ➕ **Homomorphic Vote Counting** – uses Paillier encryption to aggregate votes without decryption
* ✅ **Integrity of Results** – guarantees correct vote tallying without exposing individual data
* 🔑 **Authentication System** – secure login mechanism for authorized voters
* 📱 **Responsive UI** – clean and user-friendly interface adapted to different devices

---

## 🔍 How It Works

* Each vote is encrypted using the **Paillier cryptosystem**
* Encrypted votes are aggregated directly (without decryption)
* Final result is decrypted only once, ensuring correctness and privacy
* No individual vote can be traced back to a specific user

---

## 🎨 Design

The frontend interface was implemented based on the following Figma design:

👉 https://www.figma.com/design/2RrNlFs3Q9l33oRm3ncoSp/University-voting-web-app-design?t=ScvWqc0nIvLZef03-0

The design focuses on:

* simplicity and clarity
* accessibility
* intuitive voting flow

---

## 🛠️ Technologies Used

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python (Flask)
* **Database:** PostgreSQL
* **Libraries & Tools:** bcrypt, psycopg2
* **Cryptography:** Paillier Homomorphic Encryption

---

## ⚠️ Repository Note

Due to the size and complexity of cryptographic libraries and dependencies, this repository includes only:

* frontend source code
* backend application logic

Additional cryptographic and environment-specific dependencies are not included.

---

## 💡 Key Responsibilities

* Designed and developed a secure voting architecture
* Implemented homomorphic encryption for privacy-preserving vote counting
* Built backend logic using Flask and PostgreSQL
* Developed responsive frontend based on Figma design
* Ensured security best practices in authentication and data handling

---

## 📈 Learning Outcomes

This project allowed me to gain practical experience in:

* applied cryptography and secure systems design
* homomorphic encryption (Paillier scheme)
* backend development with Flask and databases
* building privacy-focused web applications

---

## 📬 Contact

Feel free to connect with me or explore my other projects!
