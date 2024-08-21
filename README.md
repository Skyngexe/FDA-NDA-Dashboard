# FDA-NDA-Dashboard
## The FDA-NDA-Dashboard is an interactive tool designed to present novel drug approval data from the FDA. This dashboard leverages data scraped by a separate repository, [FDA Novel Drugs Approvals Web Scraper](https://github.com/Skyngexe/fda_nda_scraper) which automically collects and stores the data in a MongoDB database . 
Click here to view the [Dashboard](https://fda-nda-dashboard.onrender.com/)
### Key Features:
- Real-Time Data Visualization: The dashboard updates automatically with the latest drug approval data.
- Interactive Charts: Built with Plotly Dash, the dashboard allows users to explore data through dynamic charts and graphs.

### Technologies Used:
- Plotly Dash: For building interactive visualizations.
- MongoDB: Used for storing and retrieving scraped data.
- Python: Backend logic and data processing.

## Getting Started 
### Prerequisites
Ensure you have set up the [FDA NDA scraper](https://github.com/Skyngexe/fda_nda_scraper) and have access to its MongoDB database.

### Setting up the dashboard
1. Clone this repository  
`git clone git@github.com:Skyngexe/FDA-NDA-Dashboard.git`
3. Install the required dependencies listed in requirements.txt
4. To run the dashboard locally `python app.py`
5. Deploy the dashboard with [render](https://render.com)



