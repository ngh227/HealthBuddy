# HEALTH BUDDY: HEALTH INFORMATION CHATBOT

This project is a RAG-based (Retrieval-Augmented Generation) health information chatbot that provides users with reliable medical information, helps locate nearby hospitals, and handles various health-related queries.

## Features

- Provides accurate health informatiion sourced from [https://medlineplus.gov/medlineplus-connect/](MedlinePlus Connect)
- Utilizes TiDB's vector search capabilities for efficient information retrieval that will be used for prompt engineering
- Generates embeddings using TiDB Embeddings AI for enhanced vector search
- Locates nearby hospitals based on user location
- Responsibly handles potential diagnosis requests by referring users to healthcare professionals
- Generates human-like responses using Google's Gemini Pro language model

## Prerequisites

Before running this program, ensure you have the following installed:
- Python 3.8+
- pip (Python package installer)
- Flask (for web interface)
- TiDB (for vector storage and search)
- TiDB Embeddings AI (for generating text embeddings)
- Google Gemini Pro (for natural language generation)
- MedlinePlus Connect API (for health information retrieval)

## Data Source and Proccessing

This chatbot uses health information directly from MedlinePlus Connect, a service that provides up-to-date, high-quality health information. The process works as follows:

1. We maintain a CSV file (disease_codes.csv) containing disease names and their corresponding ICD-10 codes.
2. Using these codes, we fetch detailed health information from MedlinePlus Connect.
3. The fetched information is processed and then embedded using TiDB Embeddings AI.
4. These embeddings are stored in our TiDB vector store for quick and efficient retrieval.

**Note**: The provided disease_codes.csv file contains 14 diseases and their ICD-10 codes for demonstration purposes. You can easily expand the chatbot's knowledge base by adding more diseases and their corresponding ICD-10 codes to this file.

This approach ensures that our chatbot always provides the most current and reliable health information available, with optimized search capabilities through vector representations.

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
5. Prepare the disease codes:
   - Ensure `disease_codes.csv` is present in the root directory
   - The CSV should have two columns: disease name and ICD-10 code
   - The file comes pre-populated with 14 diseases for demonstration
   - You can add more diseases and their ICD-10 codes to expand the chatbot's knowledge base


## Running the Program

To start the chatbot, run the following command from the project root directory:

```
python app.py
```

Open on your local browser: http://127.0.0.1:5000

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Maeve Ho - maeveho25@gmail.com

Project Link: [https://github.com/ngh227/HealthBuddy.git](https://github.com/ngh227/HealthBuddy.git)
