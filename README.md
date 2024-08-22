# HEALTH BUDDY: HEALTH INFORMATION CHATBOT

This project is a health information chatbot that provides users with medical information, helps locate 
nearby hospitals, and handles various health-related queries.

## Prerequisites

Before running this program, ensure you have the following installed:
- Python 3.8 or higher
- pip (Python package installer)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/ngh227/HealthBuddy.git
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add the following variables (replace with your actual API keys and database URL):
     ```
     GOOGLE_API_KEY=your_google_api_key
     JINAAI_API_KEY=your_jinaai_api_key
     GG_MAPS_API_KEY=your_google_maps_api_key
     TIDB_DATABASE_URL=your_tidb_database_url
     ```

## Running the Program

To start the chatbot, run the following command from the project root directory:

```
python app.py
```

Follow the prompts in the console to interact with the chatbot. You can ask health-related questions, request information about diseases, or ask for the nearest hospital.

## Features

- Health information retrieval
- Nearest hospital locator
- Chat history management
- Disease data preprocessing and storage

## Contact

Maeve Ho - maeveho25@gmail.com

Project Link: [https://github.com/ngh227/HealthBuddy.git](https://github.com/ngh227/HealthBuddy.git)